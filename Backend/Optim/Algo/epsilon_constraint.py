from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Sequence, Set, Tuple


import numpy as np

from .common import Individual, PlateauDetector
"""Epsilon-constraint scalarisation paired with CMA-ES and LNS tweaks."""

_INF_PENALTY = 1e8
_DEFAULT_LEVELS = 10
_LN_STEP_LIMIT = 2


def _dominates(a: Sequence[float], b: Sequence[float], eps: float = 1e-9) -> bool:
    return all(x <= y + eps for x, y in zip(a, b)) and any(
        x < y - eps for x, y in zip(a, b)
    )


def _nondominated(points: Iterable[Sequence[float]]) -> List[List[float]]:
    front: List[List[float]] = []
    for point in points:
        dominated = False
        for existing in front:
            if _dominates(existing, point):
                dominated = True
                break
        if dominated:
            continue
        new_front: List[List[float]] = []
        for existing in front:
            if not _dominates(point, existing):
                new_front.append(existing)
        new_front.append(list(point))
        front = new_front
    return front


def _crowding_distance(individuals: List[Individual]) -> None:
    if not individuals:
        return
    num_objs = len(individuals[0].objectives)
    for ind in individuals:
        ind.crowding_distance = 0.0
    for obj_idx in range(num_objs):
        sorted_inds = sorted(
            individuals, key=lambda ind: ind.objectives[obj_idx]
        )
        sorted_inds[0].crowding_distance = float("inf")
        sorted_inds[-1].crowding_distance = float("inf")
        min_val = sorted_inds[0].objectives[obj_idx]
        max_val = sorted_inds[-1].objectives[obj_idx]
        if math.isclose(max_val, min_val):
            continue
        scale = max_val - min_val
        for idx in range(1, len(sorted_inds) - 1):
            prev_val = sorted_inds[idx - 1].objectives[obj_idx]
            next_val = sorted_inds[idx + 1].objectives[obj_idx]
            sorted_inds[idx].crowding_distance += (next_val - prev_val) / scale


@dataclass
class _Solution:
    vector: np.ndarray
    objectives: List[float]


class EpsilonConstraint:
    """Sweep epsilon-constraint levels with a CMA-ES inner solver."""

    def __init__(
            self,
            variables: Dict[str, Tuple[float, float]],
            evaluate: Callable[[Dict[str, float]], Sequence[float]],
            *,
            pop_size: int = 30,
            generations: int = 60,
            epsilon_levels: int | None = None,
            seed: int | None = None,
    ) -> None:
        if pop_size <= 0:
            raise ValueError("pop_size must be positive")
        if generations <= 0:
            raise ValueError("generations must be positive")

        self.variables = variables
        self.evaluate = evaluate
        self.pop_size = pop_size
        self.generations = generations
        self.epsilon_levels = epsilon_levels or _DEFAULT_LEVELS
        self.names = list(self.variables.keys())
        self.bounds = np.array(
            [tuple(map(float, variables[name])) for name in self.names],
            dtype=float,
        )
        self.dim = len(self.names)
        self.rng = np.random.default_rng(seed)

        midpoint = {
            name: (lo + hi) / 2.0 for name, (lo, hi) in self.variables.items()
        }
        sample = tuple(float(x) for x in self.evaluate(midpoint))
        self.num_objectives = len(sample)
        if self.num_objectives < 2:
            raise ValueError(
                "Epsilon-constraint requires at least two objectives"
            )

        self._evaluations = 1  # midpoint sample above
        self._initial_sample = sample
        self._solutions: List[_Solution] = []
        self._feasible_points: List[List[float]] = []
        self._feasible_archive: List[_Solution] = []
        self._feasible_objective_keys: Set[Tuple[float, ...]] = set()
        self._front_history: List[List[List[float]]] = []
        self._infeasible_value = _INF_PENALTY
        self._constraint_tol = 1e-6
        self._penalty_scale = 1.0
        self._penalty_smoothing: List[float] = []

        self._discrete_steps: Dict[int, float] = self._infer_discrete_steps()
        self._max_feasibility_attempts = 50
        self._epsilon_delta_setter = getattr(
            self.evaluate, "_set_epsilon_delta_fraction", None
        )
        self._epsilon_delta_getter = getattr(
            self.evaluate, "_get_epsilon_delta_fraction", None
        )
        self._base_epsilon_delta = (
            float(self._epsilon_delta_getter())
            if self._epsilon_delta_getter is not None
            else None
        )
        self._delta_limit_multiplier = 8.0

        midpoint_vec = np.array(
            [midpoint[name] for name in self.names], dtype=float
        )
        self._midpoint_vector = midpoint_vec
        self._last_feasible_solution: tuple[np.ndarray, List[float]] | None = None
        inf_eps = [float("inf")] * (self.num_objectives - 1)
        if self._is_feasible(sample, inf_eps):
            self._register_feasible_solution(midpoint_vec, list(sample))

    # ------------------------------------------------------------------
    def _register_feasible_solution(
            self, vector: np.ndarray, objectives: Sequence[float]
    ) -> None:
        objs = [float(v) for v in objectives]
        if any(
                not math.isfinite(val) or val >= self._infeasible_value
                for val in objs
        ):
            return
        key = tuple(round(val, 9) for val in objs)
        if key in self._feasible_objective_keys:
            return
        stored = np.array(vector, dtype=float)
        self._feasible_objective_keys.add(key)
        self._feasible_points.append(objs)
        self._feasible_archive.append(
            _Solution(vector=stored, objectives=objs)
        )
        self._last_feasible_solution = (stored.copy(), list(objs))

    # ------------------------------------------------------------------
    def _find_seed_for_epsilon(
            self, epsilons: Sequence[float]
    ) -> tuple[np.ndarray, List[float]] | None:
        if self._last_feasible_solution is not None:
            vec, objs = self._last_feasible_solution
            if self._is_feasible(objs, epsilons):
                return vec.copy(), list(objs)
        if self._feasible_archive:
            sorted_archive = sorted(
                self._feasible_archive, key=lambda sol: sol.objectives[0]
            )
            for sol in sorted_archive:
                if self._is_feasible(sol.objectives, epsilons):
                    return sol.vector.copy(), list(sol.objectives)
        return None

    # ------------------------------------------------------------------
    def run(
            self,
            *,
            log_history: bool = False,
            plateau_detector: PlateauDetector | None = None,
    ) -> (
            List[Individual]
            | Tuple[List[Individual], List[List[List[float]]], int, bool]
    ):
        warmup = self._warmup_samples()
        epsilon_schedule = self._build_epsilon_schedule(warmup)
        penalty_scale, smoothing = self._estimate_penalty_parameters(warmup)
        self._penalty_scale = penalty_scale
        self._penalty_smoothing = smoothing

        history: List[List[List[float]]] = []
        stopped_early = False
        generation_idx = 0
        default_sigma = np.maximum(
            (self.bounds[:, 1] - self.bounds[:, 0]) / 3.0, 1e-3
        )
        followup_sigma = np.maximum(default_sigma / 2.0, 1e-3)
        warm_sigma: np.ndarray | None = None

        if (
                self._epsilon_delta_setter is not None
                and self._base_epsilon_delta is not None
        ):
            self._epsilon_delta_setter(self._base_epsilon_delta)

        level_overrides: Dict[int, List[float]] = {}
        level_fail_counts: Dict[int, int] = {}
        level_delta_fraction: Dict[int, float] = {}
        level_idx = 0

        while level_idx < len(epsilon_schedule):
            remaining_generations = max(self.generations - generation_idx, 0)
            if remaining_generations <= 0:
                break

            iterations_left = len(epsilon_schedule) - level_idx
            base_iters = max(1, remaining_generations // max(iterations_left, 1))
            if base_iters + generation_idx > self.generations:
                base_iters = self.generations - generation_idx
            if base_iters <= 0:
                base_iters = 1

            eps_override = level_overrides.get(level_idx)
            epsilons = list(
                eps_override if eps_override is not None else epsilon_schedule[level_idx]
            )

            seed = self._find_seed_for_epsilon(epsilons)
            if seed is None:
                if level_idx == 0:
                    level_idx += 1
                    continue
                level_overrides[level_idx] = list(epsilon_schedule[level_idx - 1])
                if (
                        self._epsilon_delta_setter is not None
                        and self._base_epsilon_delta is not None
                ):
                    level_delta_fraction[level_idx] = self._base_epsilon_delta
                    self._epsilon_delta_setter(self._base_epsilon_delta)
                continue

            seed_vec, seed_objs = seed
            current_delta = level_delta_fraction.get(level_idx, self._base_epsilon_delta)
            if (
                    self._epsilon_delta_setter is not None
                    and current_delta is not None
            ):
                self._epsilon_delta_setter(current_delta)

            best, completed, stopped, feasible_count, eval_count = self._run_cma_es(
                epsilons,
                base_iters,
                history,
                log_history,
                plateau_detector,
                generation_idx,
                mean=seed_vec,
                sigma=warm_sigma,
                seed=(seed_vec, seed_objs),
            )
            generation_idx += completed

            if stopped:
                stopped_early = True
                break

            retry_level = False
            if best is not None:
                best_vec, objs = best
                warm_sigma = followup_sigma.copy()
                vec = best_vec.copy()
                vec, objs = self._discrete_lns(vec, objs, epsilons)
                if self._is_feasible(objs, epsilons):
                    final_vec = np.array(vec, dtype=float)
                    solution = _Solution(vector=final_vec, objectives=objs)
                    self._solutions.append(solution)
                    self._register_feasible_solution(final_vec, objs)

            current_fail = level_fail_counts.get(level_idx, 0)
            if feasible_count <= 0:
                current_fail += eval_count
                if current_fail >= self._max_feasibility_attempts:
                    widened = False
                    if (
                            self._epsilon_delta_setter is not None
                            and self._base_epsilon_delta is not None
                    ):
                        current = level_delta_fraction.get(
                            level_idx, self._base_epsilon_delta
                        )
                        if current is None:
                            current = self._base_epsilon_delta
                        new_delta = min(
                            current * 2.0,
                            self._base_epsilon_delta * self._delta_limit_multiplier,
                        )
                        if new_delta > current + 1e-12:
                            level_delta_fraction[level_idx] = new_delta
                            self._epsilon_delta_setter(new_delta)
                            widened = True
                    if not widened and level_idx > 0:
                        level_overrides[level_idx] = list(
                            epsilon_schedule[level_idx - 1]
                        )
                        widened = True
                    current_fail = 0
                    if widened:
                        retry_level = True
            else:
                current_fail = 0
                if (
                        self._epsilon_delta_setter is not None
                        and self._base_epsilon_delta is not None
                ):
                    level_delta_fraction[level_idx] = self._base_epsilon_delta
                    self._epsilon_delta_setter(self._base_epsilon_delta)
            level_fail_counts[level_idx] = current_fail

            if retry_level:
                continue

            level_idx += 1

        individuals = self._build_population()

        if log_history:
            return individuals, history, self._evaluations, stopped_early
        return individuals

        # ------------------------------------------------------------------

    def _run_cma_es(
            self,
            epsilons: Sequence[float],
            iterations: int,
            history: List[List[List[float]]],
            log_history: bool,
            plateau_detector: PlateauDetector | None,
            generation_start: int,
            *,
            mean: np.ndarray | None = None,
            sigma: np.ndarray | None = None,
            seed: tuple[np.ndarray, Sequence[float]] | None = None,
    ) -> tuple[tuple[np.ndarray, List[float]] | None, int, bool, int, int]:
        default_mean = np.array(
            [(lo + hi) / 2.0 for lo, hi in self.bounds], dtype=float
        )
        if seed is not None:
            seed_vec, seed_objs = seed
            mean = np.array(seed_vec, dtype=float)
            mean = np.clip(mean, self.bounds[:, 0], self.bounds[:, 1])
            best_feasible: tuple[np.ndarray, List[float]] | None = (
                mean.copy(), [float(v) for v in seed_objs]
            )
        elif mean is None:
            mean = default_mean
            best_feasible = None
        else:
            mean = np.array(mean, dtype=float)
            mean = np.clip(mean, self.bounds[:, 0], self.bounds[:, 1])
            best_feasible = None

        default_sigma = np.maximum(
            (self.bounds[:, 1] - self.bounds[:, 0]) / 3.0, 1e-3
        )
        if sigma is None:
            sigma = default_sigma
        else:
            sigma = np.array(sigma, dtype=float)
            sigma = np.clip(sigma, 1e-3, None)

        mu = max(1, self.pop_size // 2)
        success_window: deque[int] = deque(maxlen=8)
        completed = 0
        feasible_count = 0
        total_evals = 0

        for _ in range(iterations):
            candidates: List[
                Tuple[float, np.ndarray, List[float], bool]
            ] = []
            iter_has_feasible = False
            for _ in range(self.pop_size):
                step = self.rng.normal(size=self.dim) * sigma
                sample = mean + step
                sample = np.clip(sample, self.bounds[:, 0], self.bounds[:, 1])
                sample = self._apply_discrete(sample)
                objectives = list(self._evaluate_vector(sample, epsilons))
                feasible = self._is_feasible(objectives, epsilons)
                score = self._scalar_score(objectives, epsilons)
                candidates.append((score, sample, objectives, feasible))
                total_evals += 1
                if feasible:
                    iter_has_feasible = True
                    feasible_count += 1
                    self._register_feasible_solution(sample, objectives)
                    if best_feasible is None or objectives[0] < best_feasible[1][0]:
                        best_feasible = (sample.copy(), list(objectives))

            candidates.sort(key=lambda item: item[0])
            top = candidates[:mu]
            mean = np.mean([vec for _, vec, _, _ in top], axis=0)
            spread = np.std([vec for _, vec, _, _ in top], axis=0)
            sigma = np.clip(0.5 * sigma + 0.5 * spread, 1e-3, None)

            best_iter = candidates[0]
            success_window.append(1 if best_iter[3] else 0)
            success_rate = sum(success_window) / len(success_window)
            if success_rate > 0.25:
                sigma *= 1.2
            elif success_rate < 0.15:
                sigma *= 0.82

            if iter_has_feasible:
                front = _nondominated(self._feasible_points)
            else:
                front = self._front_history[-1] if self._front_history else []

            front_copy = [list(pt) for pt in front]
            self._front_history.append(front_copy)
            if log_history:
                history.append(front_copy)

            completed += 1
            if (
                    plateau_detector
                    and front_copy
                    and plateau_detector.update(front_copy, generation_start + completed)
            ):
                return best_feasible, completed, True, feasible_count, total_evals

        return best_feasible, completed, False, feasible_count, total_evals

        # ------------------------------------------------------------------

    def _apply_discrete(self, vector: np.ndarray) -> np.ndarray:
        if not self._discrete_steps:
            return vector
        rounded = vector.copy()
        for idx, step in self._discrete_steps.items():
            val = rounded[idx]
            snapped = round(val / step) * step
            lo, hi = self.bounds[idx]
            rounded[idx] = float(np.clip(snapped, lo, hi))
        return rounded

    # ------------------------------------------------------------------
    def _discrete_lns(
            self,
            vector: np.ndarray,
            objectives: List[float],
            epsilons: Sequence[float],
    ) -> tuple[np.ndarray, List[float]]:
        if not self._discrete_steps:
            return vector, objectives

        best_vec = vector.copy()
        best_objs = list(objectives)
        for idx, step in self._discrete_steps.items():
            for _ in range(_LN_STEP_LIMIT):
                improved = False
                current = best_vec[idx]
                for delta in (-step, step):
                    candidate = best_vec.copy()
                    candidate[idx] = float(
                        np.clip(current + delta, self.bounds[idx][0], self.bounds[idx][1])
                    )
                    candidate = self._apply_discrete(candidate)
                    objs = list(self._evaluate_vector(candidate, epsilons))
                    if not self._is_feasible(objs, epsilons):
                        continue
                    if objs[0] + 1e-9 < best_objs[0]:
                        best_vec = candidate
                        best_objs = objs
                        improved = True
                        break
                if not improved:
                    break
        return best_vec, best_objs

    # ------------------------------------------------------------------
    def _evaluate_vector(
            self,
            vector: np.ndarray,
            epsilons: Sequence[float] | None = None,
    ) -> Sequence[float]:
        values = {name: float(v) for name, v in zip(self.names, vector)}
        token = None
        push = getattr(self.evaluate, "_push_active_epsilons", None)
        reset = getattr(self.evaluate, "_reset_active_epsilons", None)
        if epsilons is not None and push is not None and reset is not None:
            token = push(epsilons)
        try:
            result = tuple(float(x) for x in self.evaluate(values))
        finally:
            if token is not None:
                reset(token)
        self._evaluations += 1
        return result

    # ------------------------------------------------------------------
    def _scalar_score(
            self, objectives: Sequence[float], epsilons: Sequence[float]
    ) -> float:
        primary = float(objectives[0])
        if math.isnan(primary):
            return float("inf")
        penalty = 0.0
        for idx, eps in enumerate(epsilons, start=1):
            bound = float(eps)
            val = float(objectives[idx])
            if not math.isfinite(bound):
                continue
            violation = max(0.0, val - bound)
            if violation <= 0.0:
                continue
            smooth = (
                self._penalty_smoothing[idx - 1]
                if idx - 1 < len(self._penalty_smoothing)
                else 0.0
            )
            if smooth > 0.0:
                if violation <= smooth:
                    penalty += (violation * violation) / (2.0 * smooth)
                else:
                    penalty += violation - (smooth / 2.0)
            else:
                penalty += violation
        return primary + self._penalty_scale * penalty

    # ------------------------------------------------------------------
    def _is_feasible(
            self, objectives: Sequence[float], epsilons: Sequence[float]
    ) -> bool:
        for idx, value in enumerate(objectives):
            if not math.isfinite(value) or value >= self._infeasible_value:
                return False
            if idx == 0:
                continue
            bound = epsilons[idx - 1]
            if math.isfinite(bound) and value > bound + self._constraint_tol:
                return False
        return True

    # ------------------------------------------------------------------
    def _build_population(self) -> List[Individual]:
        if not self._solutions:
            return []

        unique: Dict[Tuple[float, ...], _Solution] = {}
        for sol in self._solutions:
            key = tuple(round(float(x), 6) for x in sol.objectives)
            existing = unique.get(key)
            if existing is None or sol.objectives[0] < existing.objectives[0]:
                unique[key] = sol

        solutions = list(unique.values())
        front = _nondominated(sol.objectives for sol in solutions)
        records: List[Individual] = []

        for sol in solutions:
            if sol.objectives not in front:
                continue
            values = {name: float(v) for name, v in zip(self.names, sol.vector)}
            records.append(
                Individual(
                    values=values,
                    objectives=list(sol.objectives),
                    rank=0,
                    crowding_distance=0.0,
                )
            )

        _crowding_distance(records)
        return records

    # ------------------------------------------------------------------
    def _warmup_samples(self) -> List[List[float]]:
        samples: List[List[float]] = [list(self._initial_sample)]
        warmup_size = max(self.pop_size, self.dim * 5)
        inf_eps = [float("inf")] * (self.num_objectives - 1)
        for _ in range(warmup_size):
            point = [self.rng.uniform(lo, hi) for lo, hi in self.bounds]
            point_arr = self._apply_discrete(np.array(point, dtype=float))
            objectives = list(self._evaluate_vector(point_arr))
            samples.append(objectives)
            if self._is_feasible(objectives, inf_eps):
                self._register_feasible_solution(point_arr, objectives)
        return samples

    # ------------------------------------------------------------------
    def _build_epsilon_schedule(
            self, samples: List[List[float]]
    ) -> List[List[float]]:
        if self.num_objectives <= 1:
            return [[]]

        valid_samples = [
            s
            for s in samples
            if all(math.isfinite(v) and v < self._infeasible_value for v in s)
        ]
        inf_eps = [float("inf")] * (self.num_objectives - 1)
        feasible_samples = [
            s for s in valid_samples if self._is_feasible(s, inf_eps)
        ]

        epsilon_lists: List[List[float]] = []
        for obj_idx in range(1, self.num_objectives):
            feasible_values = [sample[obj_idx] for sample in feasible_samples]
            source = feasible_values if len(feasible_values) >= 3 else None
            values = source if source is not None else [
                sample[obj_idx] for sample in valid_samples
            ]
            if not values:
                epsilon_lists.append([float("inf")])
                continue
            if source is not None:
                low = float(np.quantile(values, 0.2))
                high = float(np.quantile(values, 0.8))
            else:
                low = float(min(values))
                high = float(max(values))
            if math.isclose(low, high):
                epsilon_lists.append([float("inf"), high])
                continue
            if high < low:
                low, high = high, low
            if math.isclose(low, high):
                epsilon_lists.append([float("inf"), high])
                continue
            levels = np.linspace(high, low, self.epsilon_levels)
            seq = [float("inf")]
            prev = None
            for level in levels:
                val = float(level)
                if prev is None or not math.isclose(val, prev, rel_tol=1e-9, abs_tol=1e-9):
                    seq.append(val)
                    prev = val
            epsilon_lists.append(seq)

        if not epsilon_lists:
            return [[]]

        if len(epsilon_lists) == 1:
            return [[eps] for eps in epsilon_lists[0]]

        max_len = max(len(lst) for lst in epsilon_lists)
        schedule: List[List[float]] = []
        for idx in range(max_len):
            combo: List[float] = []
            for lst in epsilon_lists:
                combo.append(lst[min(idx, len(lst) - 1)])
            schedule.append(combo)
        return schedule

    # ------------------------------------------------------------------
    def _estimate_penalty_parameters(
            self, samples: List[List[float]]
    ) -> tuple[float, List[float]]:
        primary_vals = [
            s[0]
            for s in samples
            if math.isfinite(s[0]) and s[0] < self._infeasible_value
        ]
        if primary_vals:
            span = max(primary_vals) - min(primary_vals)
            base = max(abs(min(primary_vals)), 1.0)
            scale_source = span if span > 1e-9 else base
            penalty_scale = max(5.0, scale_source * 3.0)
        else:
            penalty_scale = 50.0

        smoothing: List[float] = []
        for obj_idx in range(1, self.num_objectives):
            values = [
                s[obj_idx]
                for s in samples
                if len(s) > obj_idx
                   and math.isfinite(s[obj_idx])
                   and s[obj_idx] < self._infeasible_value
            ]
            if len(values) >= 3:
                span = max(values) - min(values)
                base = max(abs(min(values)), 1.0)
                smooth = max(span * 0.1, base * 0.05)
            elif len(values) == 2:
                span = abs(values[1] - values[0])
                smooth = max(span * 0.5, 1.0)
            elif values:
                smooth = max(abs(values[0]), 1.0) * 0.1
            else:
                smooth = 1.0
            smoothing.append(max(float(smooth), 1e-6))

        return penalty_scale, smoothing

    # ------------------------------------------------------------------
    def _infer_discrete_steps(self) -> Dict[int, float]:
        steps: Dict[int, float] = {}
        for idx, name in enumerate(self.names):
            lower_name = name.lower()
            if "priority" in lower_name:
                steps[idx] = 1.0
        return steps

__all__ = ["EpsilonConstraint"]
