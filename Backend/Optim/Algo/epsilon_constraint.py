from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import numpy as np

from .common import Individual, PlateauDetector
"""Epsilon-constraint scalarisation paired with CMA-ES and LNS tweaks."""

_INF_PENALTY = 1e8
_DEFAULT_LEVELS = 7
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
        self._front_history: List[List[List[float]]] = []
        self._infeasible_value = _INF_PENALTY
        self._constraint_tol = 1e-6
        self._penalty_scale = 1.0

        self._discrete_steps: Dict[int, float] = self._infer_discrete_steps()

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
        self._penalty_scale = self._estimate_penalty_scale(warmup)

        history: List[List[List[float]]] = []
        stopped_early = False
        generation_idx = 0

        for objectives in warmup:
            if all(
                    math.isfinite(v) and v < self._infeasible_value for v in objectives
            ):
                self._feasible_points.append(list(objectives))

        for sweep_idx, epsilons in enumerate(epsilon_schedule):
            remaining_generations = max(self.generations - generation_idx, 0)
            if remaining_generations <= 0:
                break

            iterations_left = len(epsilon_schedule) - sweep_idx
            base_iters = max(1, remaining_generations // iterations_left)
            # distribute remainder evenly across later sweeps
            if base_iters + generation_idx > self.generations:
                base_iters = self.generations - generation_idx
            if base_iters <= 0:
                base_iters = 1

            best, completed, stopped = self._run_cma_es(
                epsilons,
                base_iters,
                history,
                log_history,
                plateau_detector,
                generation_idx,
            )
            generation_idx += completed

            if best is not None:
                vec, objs = best
                vec, objs = self._discrete_lns(vec, objs, epsilons)
                if self._is_feasible(objs, epsilons):
                    self._solutions.append(
                        _Solution(vector=np.array(vec, dtype=float), objectives=objs)
                    )

            if stopped:
                stopped_early = True
                break

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
    ) -> tuple[tuple[np.ndarray, List[float]] | None, int, bool]:
        mean = np.array([(lo + hi) / 2.0 for lo, hi in self.bounds], dtype=float)
        sigma = np.maximum((self.bounds[:, 1] - self.bounds[:, 0]) / 3.0, 1e-3)
        mu = max(1, self.pop_size // 2)
        best_feasible: tuple[np.ndarray, List[float]] | None = None
        success_window: deque[int] = deque(maxlen=8)
        completed = 0

        for _ in range(iterations):
            candidates: List[
                Tuple[float, np.ndarray, List[float], bool]
            ] = []
            for _ in range(self.pop_size):
                step = self.rng.normal(size=self.dim) * sigma
                sample = mean + step
                sample = np.clip(sample, self.bounds[:, 0], self.bounds[:, 1])
                sample = self._apply_discrete(sample)
                objectives = list(self._evaluate_vector(sample))
                feasible = self._is_feasible(objectives, epsilons)
                score = self._scalar_score(objectives, epsilons)
                candidates.append((score, sample, objectives, feasible))
                if feasible:
                    if best_feasible is None or objectives[0] < best_feasible[1][0]:
                        best_feasible = (sample.copy(), objectives)

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

            feasible_objs = [obj for _, _, obj, feas in candidates if feas]
            if feasible_objs:
                for obj in feasible_objs:
                    self._feasible_points.append(list(obj))
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
                return best_feasible, completed, True

        return best_feasible, completed, False

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
                    objs = list(self._evaluate_vector(candidate))
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
    def _evaluate_vector(self, vector: np.ndarray) -> Sequence[float]:
        values = {name: float(v) for name, v in zip(self.names, vector)}
        result = tuple(float(x) for x in self.evaluate(values))
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
        for _ in range(warmup_size):
            point = [
                self.rng.uniform(lo, hi) for lo, hi in self.bounds
            ]
            point = self._apply_discrete(np.array(point, dtype=float))
            objectives = list(self._evaluate_vector(point))
            samples.append(objectives)
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

        epsilon_lists: List[List[float]] = []
        for obj_idx in range(1, self.num_objectives):
            values = [sample[obj_idx] for sample in valid_samples]
            if not values:
                epsilon_lists.append([float("inf")])
                continue
            low = float(min(values))
            high = float(max(values))
            if math.isclose(low, high):
                epsilon_lists.append([float("inf"), high])
                continue
            levels = np.linspace(low, high, self.epsilon_levels)
            seq = [float("inf")]
            seq.extend(float(v) for v in sorted(set(levels), reverse=True))
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
    def _estimate_penalty_scale(self, samples: List[List[float]]) -> float:
        primary_vals = [
            s[0]
            for s in samples
            if math.isfinite(s[0]) and s[0] < self._infeasible_value
        ]
        if not primary_vals:
            return 100.0
        span = max(primary_vals) - min(primary_vals)
        base = max(abs(min(primary_vals)), 1.0)
        scale = max(span, base)
        return max(10.0, scale * 10.0)

    # ------------------------------------------------------------------
    def _infer_discrete_steps(self) -> Dict[int, float]:
        steps: Dict[int, float] = {}
        for idx, name in enumerate(self.names):
            lower_name = name.lower()
            if "priority" in lower_name:
                steps[idx] = 1.0
        return steps


__all__ = ["EpsilonConstraint"]
