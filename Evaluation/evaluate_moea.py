from __future__ import annotations

import argparse
import itertools
import math
import os
import random
import time
from collections import defaultdict
from pathlib import Path
from threading import Lock
from typing import Callable, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from Backend.Optim.optimise import load_model, variable_bounds, make_evaluator
from Backend.Optim.Algo.NSGA2 import NSGAII
from Backend.Optim.Algo.SMSEMOA import SMSEMOA
from Backend.Optim.Algo.MOEAD import MOEAD
from Backend.Optim.Algo.epsilon_constraint import EpsilonConstraint
from Backend.Optim.Algo.qehvi import QEHVIOptimizer
from Backend.Optim.Algo.common import PlateauDetector


#  Pareto helper
def nondominated(points: np.ndarray | List[List[float]]) -> np.ndarray:
    pts = np.asarray(points, dtype=float)
    if len(pts) == 0:
        return pts
    keep = []
    for i, p in enumerate(pts):
        dominated = np.any(np.all(pts <= p, axis=1) & np.any(pts < p, axis=1))
        if not dominated:
            keep.append(i)
    return pts[keep]


#  Indicators (2-objective minimisation)
def hypervolume_2d(front: np.ndarray, ref: Tuple[float, float]) -> float:
    if len(front) == 0:
        return 0.0

    front = np.asarray(front, dtype=float)
    front = front[np.all(np.isfinite(front), axis=1)]
    if len(front) == 0:
        return 0.0
    front = front[np.argsort(front[:, 0])]

    hv = 0.0
    best_f1 = ref[1]
    for f0, f1 in front:
        width = max(0.0, ref[0] - float(f0))
        if width == 0.0:
            continue

        #  Clip f1 to the current best value and the reference point to ensure
        #  that the rectangles never extend outside of the dominated region.
        f1_clipped = min(float(f1), best_f1, ref[1])
        height = max(0.0, best_f1 - f1_clipped)
        if height == 0.0:
            continue

        hv += width * height
        best_f1 = f1_clipped

    return hv


def _bounding_box_volume(ref_point: np.ndarray, mins: np.ndarray) -> float:
    extents = np.maximum(ref_point - mins, 0.0)
    extents = np.maximum(extents, 1e-12)
    return float(np.prod(extents))


def _hypervolume_with_fallback(
        front: np.ndarray,
        base_ref: np.ndarray,
        fallback_ref: np.ndarray,
        base_mins: np.ndarray,
        fallback_mins: np.ndarray,
) -> float:
    hv_value = hypervolume_2d(front, tuple(base_ref))
    if hv_value > 0.0:
        return hv_value

    if front.size == 0:
        return 0.0

    needs_relaxation = np.any(front > base_ref)
    if not needs_relaxation:
        return hv_value

    base_volume = _bounding_box_volume(base_ref, base_mins)

    hv_fallback = hypervolume_2d(front, tuple(fallback_ref))
    if hv_fallback > 0.0:
        fallback_volume = _bounding_box_volume(fallback_ref, fallback_mins)
        if fallback_volume > 0.0 and math.isfinite(fallback_volume):
            scale = base_volume / fallback_volume
            return hv_fallback * scale

    local_ref = np.max(front, axis=0) * 1.1
    local_mins, _ = _min_max_params(front)
    local_volume = _bounding_box_volume(local_ref, local_mins)
    if local_volume > 0.0 and math.isfinite(local_volume):
        hv_local = hypervolume_2d(front, tuple(local_ref))
        if hv_local > 0.0:
            scale = base_volume / local_volume
            return hv_local * scale

    return 0.0


def igd_plus(front: np.ndarray, ref_set: np.ndarray) -> float:
    """Compute the IGD+ indicator for minimisation problems."""

    if len(front) == 0:
        return float("inf")

    front = np.atleast_2d(np.asarray(front, dtype=float))
    ref_set = np.atleast_2d(np.asarray(ref_set, dtype=float))

    # Filter out any non-finite points that could otherwise contaminate the
    # distance computation and blow up the IGD+ value.
    front = front[np.all(np.isfinite(front), axis=1)]
    ref_set = ref_set[np.all(np.isfinite(ref_set), axis=1)]

    if front.size == 0 or ref_set.size == 0:
        return float("inf")

    deltas = np.maximum(front[:, None, :] - ref_set[None, :, :], 0.0)
    distances = np.linalg.norm(deltas, axis=2)
    min_distances = np.min(distances, axis=0)

    return float(np.mean(min_distances))


#  Algorithm runners
def run_nsga2(bounds, evaluate, generations, pop_size, seed, *, workers=None, plateau=None):
    random.seed(seed)
    np.random.seed(seed)
    alg = NSGAII(
        bounds,
        evaluate,
        generations=generations,
        pop_size=pop_size,
        workers=workers,
    )
    pop, history, evaluations, stopped = alg.run(
        log_history=True, plateau_detector=plateau
    )
    objs = [ind.objectives for ind in pop]
    final_front = nondominated(objs)
    history_fronts = [np.asarray(h, dtype=float) for h in history]
    return final_front, history_fronts, evaluations, stopped


def run_sms_emoa(bounds, evaluate, generations, pop_size, seed, *, workers=None, plateau=None):
    random.seed(seed)
    np.random.seed(seed)
    alg = SMSEMOA(
        bounds,
        evaluate,
        generations=generations,
        pop_size=pop_size,
        workers=workers,
    )
    pop, history, evaluations, stopped = alg.run(
        log_history=True, plateau_detector=plateau
    )
    objs = [ind.objectives for ind in pop]
    final_front = nondominated(objs)
    history_fronts = [np.asarray(h, dtype=float) for h in history]
    return final_front, history_fronts, evaluations, stopped


def run_qehvi(bounds, evaluate, generations, pop_size, seed, *, workers=None, plateau=None):
    random.seed(seed)
    np.random.seed(seed)
    alg = QEHVIOptimizer(
        bounds,
        evaluate,
        generations=generations,
        pop_size=pop_size,
        batch_size=min(pop_size, 1),
        seed=seed,
        workers=workers,
    )
    result = alg.run(
        log_history=True, plateau_detector=plateau
    )
    if len(result) == 4:
        pop, history, evaluations, stopped = result
        feasibility_history = None
    else:
        pop, history, evaluations, stopped, feasibility_history = result
    objs = [ind.objectives for ind in pop]
    final_front = nondominated(objs)
    history_fronts = [np.asarray(front, dtype=float) for front in history]
    return final_front, history_fronts, evaluations, stopped, feasibility_history


def run_moead(bounds, evaluate, generations, pop_size, seed, *, workers=None, plateau=None):
    random.seed(seed)
    np.random.seed(seed)
    alg = MOEAD(
        bounds,
        evaluate,
        generations=generations,
        pop_size=pop_size,
        workers=workers,
    )
    pop, history, evaluations, stopped = alg.run(
        log_history=True, plateau_detector=plateau
    )
    objs = [ind.objectives for ind in pop]
    final_front = nondominated(objs)
    history_fronts = [np.asarray(front, dtype=float) for front in history]
    return final_front, history_fronts, evaluations, stopped


def run_eps_constraint(
        bounds,
        evaluate,
        generations,
        pop_size,
        seed,
        *,
        workers=None,
        plateau=None,
):
    random.seed(seed)
    np.random.seed(seed)
    alg = EpsilonConstraint(
        bounds,
        evaluate,
        generations=generations,
        pop_size=pop_size,
        seed=seed,
    )
    pop, history, evaluations, stopped = alg.run(
        log_history=True, plateau_detector=plateau
    )
    objs = [ind.objectives for ind in pop]
    final_front = nondominated(objs)
    # num_obj = alg.num_objectives
    history_fronts = [np.asarray(front, dtype=float) for front in history]
    return final_front, history_fronts, evaluations, stopped


def random_search(bounds, evaluate, budget, seed, generations, pop_size, *, plateau=None):
    rnd = random.Random(seed)
    objs: List[List[float]] = []
    history: List[np.ndarray] = []
    stopped_early = False
    for idx in range(budget):
        point = {k: rnd.uniform(lo, hi) for k, (lo, hi) in bounds.items()}
        objs.append(evaluate(point))
        if (idx + 1) % pop_size == 0:
            front = nondominated(objs).copy()
            history.append(front)
            if plateau and plateau.update(front.tolist(), len(history)):
                stopped_early = True
                break
    final_front = nondominated(objs)
    history_fronts = [np.asarray(front, dtype=float) for front in history]
    return final_front, history_fronts, len(objs), stopped_early


ALGORITHMS = {
    "nsga2": (run_nsga2, True),
    "sms-emoa": (run_sms_emoa, True),
    "qehvi": (run_qehvi, True),
    "moead": (run_moead, True),
    "eps-constraint": (run_eps_constraint, True),
    "random_search": (random_search, False),
}

PLATEAU_WINDOW = 15
PLATEAU_EPSILON = 1e-4


class MemoisedEvaluator:
    """Thread-safe memoisation wrapper around the expensive objective call."""

    def __init__(self, evaluate, names: Iterable[str]):
        self._evaluate = evaluate
        self._names = tuple(names)
        self._cache: Dict[
            Tuple[float, ...], Tuple[Tuple[float, ...], bool]
        ] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
        self._total_calls = 0
        self._feasible_calls = 0
        self._infeasible_calls = 0

    def __call__(self, values: Dict[str, float]):
        key = tuple(float(values[name]) for name in self._names)
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                self._hits += 1
                self._total_calls += 1
                feasible = cached[1]
                if feasible:
                    self._feasible_calls += 1
                else:
                    self._infeasible_calls += 1
                return cached[0]

        result = tuple(float(v) for v in self._evaluate(dict(values)))
        feasible = self._is_feasible(result)

        with self._lock:
            # Another thread might have populated the cache while we were evaluating.
            cached = self._cache.get(key)
            if cached is not None:
                self._hits += 1
                self._total_calls += 1
                feasible = cached[1]
                if feasible:
                    self._feasible_calls += 1
                else:
                    self._infeasible_calls += 1
                return cached[0]

            self._cache[key] = (result, feasible)
            self._misses += 1
            self._total_calls += 1
            if feasible:
                self._feasible_calls += 1
            else:
                self._infeasible_calls += 1
            return result

    @staticmethod
    def _is_feasible(values: Tuple[float, ...]) -> bool:
        return all(math.isfinite(v) and v < 1e9 for v in values)

    def stats(self) -> Dict[str, float]:
        with self._lock:
            data: Dict[str, float] = {
                "hits": self._hits,
                "misses": self._misses,
                "entries": len(self._cache),
                "total_calls": self._total_calls,
                "feasible_calls": self._feasible_calls,
                "infeasible_calls": self._infeasible_calls,
            }

            if self._total_calls:
                data["feasibility_rate"] = (
                        self._feasible_calls / self._total_calls
                )

        timing_data = self.timing_snapshot()
        if timing_data is not None:
            data.update(timing_data)
            eval_total = timing_data["evaluate_seconds"]
            verify_total = timing_data["verifyta_seconds"]
            if eval_total > 0.0:
                data["verifyta_percentage"] = (verify_total / eval_total) * 100.0

        return data

    def timing_snapshot(self) -> Dict[str, float] | None:
        timing = getattr(self._evaluate, "_timings", None)
        timing_lock = getattr(self._evaluate, "_timings_lock", None)
        if timing is None or timing_lock is None:
            return None

        with timing_lock:
            evaluate_total = float(timing.get("evaluate_total", 0.0))
            evaluate_calls = int(timing.get("evaluate_calls", 0))
            verify_total = float(timing.get("verifyta_total", 0.0))
            verify_calls = int(timing.get("verifyta_calls", 0))

        return {
            "evaluate_seconds": evaluate_total,
            "evaluate_calls": evaluate_calls,
            "verifyta_seconds": verify_total,
            "verifyta_calls": verify_calls,
        }


def _min_max_params(ref_set: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    mins = np.min(ref_set, axis=0)
    maxs = np.max(ref_set, axis=0)
    ranges = np.where(maxs > mins, maxs - mins, 1.0)
    return mins, ranges


def _normalise(points: np.ndarray, mins: np.ndarray, ranges: np.ndarray) -> np.ndarray:
    if points.size == 0:
        return points.copy()
    return (points - mins) / ranges


def bootstrap_ci(
        values: np.ndarray,
        *,
        func=np.median,
        alpha: float = 0.05,
        n_boot: int = 2000,
        rng: np.random.Generator | None = None,
) -> Tuple[float, float]:
    if values.size == 0:
        return float("nan"), float("nan")
    rng = rng or np.random.default_rng()
    stats = []
    for _ in range(n_boot):
        sample = rng.choice(values, size=values.size, replace=True)
        stats.append(func(sample))
    lower = float(np.percentile(stats, alpha / 2 * 100))
    upper = float(np.percentile(stats, (1 - alpha / 2) * 100))
    return lower, upper


def _format_ci(ci: Tuple[float, float]) -> str:
    if any(math.isnan(v) for v in ci):
        return "nan"
    return f"[{ci[0]:.4g}, {ci[1]:.4g}]"


def _rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values)
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j]] == values[order[j + 1]]:
            j += 1
        rank = 0.5 * (i + j) + 1.0
        ranks[order[i: j + 1]] = rank
        i = j + 1
    return ranks


def wilcoxon_signed_rank(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    if x.shape != y.shape:
        raise ValueError("Wilcoxon signed-rank test requires paired samples of equal length")
    diff = x - y
    mask = diff != 0
    diff = diff[mask]
    if diff.size == 0:
        return 0.0, 1.0
    abs_diff = np.abs(diff)
    ranks = _rankdata(abs_diff)
    w_pos = float(np.sum(ranks[diff > 0]))
    w_neg = float(np.sum(ranks[diff < 0]))
    statistic = min(w_pos, w_neg)

    n = diff.size
    expected = n * (n + 1) / 4
    tie_counts = np.unique(abs_diff, return_counts=True)[1]
    tie_correction = np.sum(tie_counts ** 3 - tie_counts)
    variance = (n * (n + 1) * (2 * n + 1) - tie_correction) / 24
    if variance == 0:
        return statistic, 1.0
    z = (abs(w_pos - expected) - 0.5) / math.sqrt(variance)
    cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    p_value = 2.0 * (1.0 - cdf)
    return statistic, max(0.0, min(1.0, p_value))


def _memoised_evaluator(evaluate, names):
    cache: Dict[Tuple[float, ...], Tuple[float, ...]] = {}
    lock = Lock()

    def wrapper(values: Dict[str, float]):
        key = tuple(float(values[name]) for name in names)
        with lock:
            cached = cache.get(key)
        if cached is not None:
            return cached
        result = tuple(float(v) for v in evaluate(dict(values)))
        with lock:
            cache[key] = result
        return result

    return wrapper


def evaluate_algorithm(
        key: str,
        bounds: Dict[str, Tuple[float, float]],
        num_objectives: int,
        evaluator_factory: Callable[..., MemoisedEvaluator],
        runs: int,
        gens: int,
        pop: int,
        *,
        worker_threads: int | None = None,
):
    runner, has_gens = ALGORITHMS[key]
    require_full_verification = key == "eps-constraint"

    run_records = []
    cache_totals = {
        "hits": 0,
        "misses": 0,
        "entries": 0,
        "total_calls": 0,
        "feasible_calls": 0,
        "infeasible_calls": 0,
        "evaluate_seconds": 0.0,
        "evaluate_calls": 0.0,
        "verifyta_seconds": 0.0,
        "verifyta_calls": 0.0,
    }

    def _timing_delta(
            after: Dict[str, float] | None,
            before: Dict[str, float] | None,
            key: str,
    ) -> float:
        if after is None or before is None:
            return float("nan")
        return after.get(key, 0.0) - before.get(key, 0.0)

    for r in range(runs):
        evaluator = evaluator_factory()
        seed = 17 + r
        budget = gens * pop
        start = time.perf_counter()
        timing_before = evaluator.timing_snapshot()
        plateau = None
        if num_objectives == 2:
            plateau = PlateauDetector(epsilon=PLATEAU_EPSILON, window=PLATEAU_WINDOW)
        if has_gens:
            result = runner(
                bounds,
                evaluator,
                gens,
                pop,
                seed,
                workers=worker_threads,
                plateau=plateau,
            )
        else:
            result = runner(
                bounds,
                evaluator,
                budget,
                seed,
                gens,
                pop,
                plateau=plateau,
            )
        if len(result) == 4:
            front, history, evaluations, stopped = result
            feasibility_history = None
        elif len(result) == 5:
            front, history, evaluations, stopped, feasibility_history = result
        else:
            raise ValueError(
                "Unexpected runner result length; expected 4 or 5 values"
            )
        runtime = time.perf_counter() - start
        timing_after = evaluator.timing_snapshot()
        front = np.asarray(front, dtype=float)
        history = [np.asarray(h, dtype=float) for h in history]
        if front.size == 0:
            continue
        if timing_before is None or timing_after is None:
            eval_seconds = float("nan")
            eval_calls = float("nan")
            verify_seconds = float("nan")
            verify_calls = float("nan")
            verify_pct = float("nan")
        else:
            eval_seconds = _timing_delta(timing_after, timing_before, "evaluate_seconds")
            verify_seconds = _timing_delta(timing_after, timing_before, "verifyta_seconds")
            eval_calls = _timing_delta(timing_after, timing_before, "evaluate_calls")
            verify_calls = _timing_delta(timing_after, timing_before, "verifyta_calls")

            eval_seconds = max(0.0, eval_seconds)
            verify_seconds = max(0.0, verify_seconds)
            eval_calls = max(0.0, eval_calls)
            verify_calls = max(0.0, verify_calls)

            verify_pct = (
                (verify_seconds / eval_seconds) * 100.0
                if eval_seconds > 0.0
                else float("nan")
            )

            eval_calls = int(round(eval_calls))
            verify_calls = int(round(verify_calls))

        cache_stats = evaluator.stats()
        run_records.append(
            {
                "run": r,
                "front": front,
                "history": history,
                "runtime": runtime,
                "evaluations": evaluations,
                "stopped_early": stopped,
                "generations_completed": len(history),
                "evaluate_seconds": eval_seconds,
                "evaluate_calls": eval_calls,
                "verifyta_seconds": verify_seconds,
                "verifyta_calls": verify_calls,
                "verifyta_percentage": verify_pct,
                "feasible_calls": cache_stats.get("feasible_calls"),
                "infeasible_calls": cache_stats.get("infeasible_calls"),
                "total_calls": cache_stats.get("total_calls"),
                "feasibility_rate": cache_stats.get("feasibility_rate"),
                "feasibility_history": (
                    list(feasibility_history) if feasibility_history else None
                ),
            }
        )

        cache_totals["hits"] += int(cache_stats.get("hits", 0) or 0)
        cache_totals["misses"] += int(cache_stats.get("misses", 0) or 0)
        cache_totals["entries"] += int(cache_stats.get("entries", 0) or 0)
        cache_totals["total_calls"] += int(cache_stats.get("total_calls", 0) or 0)
        cache_totals["feasible_calls"] += int(
            cache_stats.get("feasible_calls", 0) or 0
        )
        cache_totals["infeasible_calls"] += int(
            cache_stats.get("infeasible_calls", 0) or 0
        )

        eval_seconds_total = cache_stats.get("evaluate_seconds")
        if isinstance(eval_seconds_total, (int, float)) and not math.isnan(
                float(eval_seconds_total)
        ):
            cache_totals["evaluate_seconds"] += float(eval_seconds_total)

        eval_calls_total = cache_stats.get("evaluate_calls")
        if isinstance(eval_calls_total, (int, float)) and not math.isnan(
                float(eval_calls_total)
        ):
            cache_totals["evaluate_calls"] += float(eval_calls_total)

        verify_seconds_total = cache_stats.get("verifyta_seconds")
        if isinstance(verify_seconds_total, (int, float)) and not math.isnan(
                float(verify_seconds_total)
        ):
            cache_totals["verifyta_seconds"] += float(verify_seconds_total)

        verify_calls_total = cache_stats.get("verifyta_calls")
        if isinstance(verify_calls_total, (int, float)) and not math.isnan(
                float(verify_calls_total)
        ):
            cache_totals["verifyta_calls"] += float(verify_calls_total)

    return {
        "runs": run_records,
        "has_generations": has_gens,
        "cache_totals": cache_totals,
    }


def _summarise_algorithm_runs(
        scenario_name: str,
        results: Dict[str, Dict[str, object]],
        all_fronts: List[np.ndarray],
        num_objectives: int,
) -> Dict[str, object]:
    if all_fronts:
        stacked_fronts = np.vstack(all_fronts)
    else:
        stacked_fronts = np.empty((0, num_objectives), dtype=float)

    if stacked_fronts.size == 0:
        ref_set = stacked_fronts
        ref_point = np.zeros(num_objectives, dtype=float)
        hv_mins = np.zeros(num_objectives, dtype=float)
        igd_mins = hv_mins.copy()
        igd_ranges = np.ones(num_objectives, dtype=float)
        fallback_ref_point = ref_point.copy()
        fallback_mins = hv_mins.copy()
    else:
        ref_set = nondominated(stacked_fronts)
        if ref_set.size == 0:
            ref_set = stacked_fronts
        ref_point = np.max(ref_set, axis=0) * 1.1
        hv_mins, _ = _min_max_params(ref_set)
        fallback_ref_point = np.max(stacked_fronts, axis=0) * 1.1
        stacked_mins, stacked_ranges = _min_max_params(stacked_fronts)
        fallback_mins = stacked_mins
        igd_mins = stacked_mins
        igd_ranges = stacked_ranges

    norm_ref_set = _normalise(ref_set, igd_mins, igd_ranges)

    rng = np.random.default_rng(42)
    summary_rows = []
    convergence_records = []
    feasibility_records = []
    metric_tables: Dict[str, pd.DataFrame] = {}

    for alg, data in results.items():
        rows = []
        for rec in data["runs"]:
            front = rec["front"]
            hv_value = _hypervolume_with_fallback(
                front,
                ref_point,
                fallback_ref_point,
                hv_mins,
                fallback_mins,
            )
            norm_front = _normalise(front, igd_mins, igd_ranges)
            igd_value = igd_plus(norm_front, norm_ref_set)
            rows.append(
                {
                    "Scenario": scenario_name,
                    "run": rec["run"],
                    "HV": hv_value,
                    "IGD+": igd_value,
                    "runtime_s": rec["runtime"],
                    "evaluations": rec["evaluations"],
                    "generations": rec["generations_completed"],
                    "stopped_early": rec["stopped_early"],
                    "evaluate_time_s": rec.get("evaluate_seconds"),
                    "evaluate_calls": rec.get("evaluate_calls"),
                    "verifyta_time_s": rec.get("verifyta_seconds"),
                    "verifyta_calls": rec.get("verifyta_calls"),
                    "verifyta_pct": rec.get("verifyta_percentage"),
                    "feasible_calls": rec.get("feasible_calls"),
                    "infeasible_calls": rec.get("infeasible_calls"),
                    "total_calls": rec.get("total_calls"),
                    "feasibility_rate": rec.get("feasibility_rate"),
                }
            )

            feas_history = rec.get("feasibility_history") or []
            for gen_idx, gen_front in enumerate(rec["history"], start=1):
                hv_gen = _hypervolume_with_fallback(
                    gen_front,
                    ref_point,
                    fallback_ref_point,
                    hv_mins,
                    fallback_mins,
                )
                convergence_records.append(
                    {
                        "Scenario": scenario_name,
                        "Algorithm": alg,
                        "run": rec["run"],
                        "Generation": gen_idx,
                        "HV": hv_gen,
                    }
                )
                if gen_idx - 1 < len(feas_history):
                    feasibility_records.append(
                        {
                            "Scenario": scenario_name,
                            "Algorithm": alg,
                            "run": rec["run"],
                            "Generation": gen_idx,
                            "FeasibleRate": float(feas_history[gen_idx - 1]),
                        }
                    )

        df = pd.DataFrame(rows)
        if df.empty:
            continue
        output_path = Path(f"../Data/EvalOutput/results_{scenario_name}_{alg}.csv")
        df.to_csv(output_path, index=False)
        metric_tables[alg] = df.set_index(["Scenario", "run"])
        hv_iqr = df["HV"].quantile(0.75) - df["HV"].quantile(0.25)
        igd_iqr = df["IGD+"].quantile(0.75) - df["IGD+"].quantile(0.25)
        hv_ci = bootstrap_ci(df["HV"].to_numpy(), rng=rng)
        igd_ci = bootstrap_ci(df["IGD+"].to_numpy(), rng=rng)
        runtime_iqr = df["runtime_s"].quantile(0.75) - df["runtime_s"].quantile(0.25)
        eval_time_med = df["evaluate_time_s"].median()
        verify_time_med = df["verifyta_time_s"].median()
        verify_pct_med = df["verifyta_pct"].median()
        eval_calls_med = df["evaluate_calls"].median()
        verify_calls_med = df["verifyta_calls"].median()
        eval_calls_display = (
            np.nan if pd.isna(eval_calls_med) else int(round(float(eval_calls_med)))
        )
        verify_calls_display = (
            np.nan if pd.isna(verify_calls_med) else int(round(float(verify_calls_med)))
        )
        eval_calls_per_run = int(round(df["evaluations"].median()))
        summary_rows.append(
            {
                "Scenario": scenario_name,
                "Algorithm": alg,
                "HV (median)": df["HV"].median(),
                "HV (IQR)": hv_iqr,
                "HV median 95% CI": _format_ci(hv_ci),
                "IGD+ (median)": df["IGD+"].median(),
                "IGD+ (IQR)": igd_iqr,
                "IGD+ median 95% CI": _format_ci(igd_ci),
                "Runtime (median s)": df["runtime_s"].median(),
                "Runtime (IQR s)": runtime_iqr,
                "Evaluations/run": eval_calls_per_run,
                "Eval time (median s)": eval_time_med,
                "Eval calls/run": eval_calls_display,
                "Verifyta time (median s)": verify_time_med,
                "Verifyta calls/run": verify_calls_display,
                "Verifyta share (median %)": verify_pct_med,
                "Feasible calls/run": df["feasible_calls"].median(),
                "Infeasible calls/run": df["infeasible_calls"].median(),
                "Feasibility rate (median)": df["feasibility_rate"].median(),
            }
        )
        print(
            f"Saved per-run metrics for {alg} ({scenario_name}) → "
            f"{output_path.name}"
        )

    scenario_summary = pd.DataFrame(summary_rows)
    if not scenario_summary.empty:
        print(f"\n=== Summary for {scenario_name} ===")
        print(scenario_summary.to_markdown(index=False, floatfmt=".4g"))

    convergence_df = pd.DataFrame(convergence_records)
    if not convergence_df.empty:
        conv_summary = (
            convergence_df.groupby(["Scenario", "Algorithm", "Generation"])["HV"]
            .agg(
                median="median",
                q1=lambda s: s.quantile(0.25),
                q3=lambda s: s.quantile(0.75),
            )
            .reset_index()
        )
        conv_path = Path(f"../Data/EvalOutput/hv_convergence_{scenario_name}.csv")
        conv_summary.to_csv(conv_path, index=False)
        print(
            f"Saved HV convergence curves for {scenario_name} → "
            f"{conv_path.name}"
        )

    feasibility_df = pd.DataFrame(feasibility_records)
    if not feasibility_df.empty:
        feas_summary = (
            feasibility_df.groupby(["Scenario", "Algorithm", "Generation"])[
                "FeasibleRate"
            ]
            .agg(
                median="median",
                q1=lambda s: s.quantile(0.25),
                q3=lambda s: s.quantile(0.75),
            )
            .reset_index()
        )
        feas_path = Path(f"../Data/EvalOutput/feasibility_convergence_{scenario_name}.csv")
        feas_summary.to_csv(feas_path, index=False)
        print(
            f"Saved feasibility convergence curves for {scenario_name} → "
            f"{feas_path.name}"
        )
    else:
        feas_summary = pd.DataFrame()

    return {
        "summary": scenario_summary,
        "metric_tables": metric_tables,
        "convergence": convergence_df,
        "feasibility": feasibility_df,
    }


def evaluate_scenario(
        dsl_path: Path,
        algorithms: Iterable[str],
        runs: int,
        generations: int,
        pop: int,
        worker_threads: int,
) -> Dict[str, object]:
    scenario_name = dsl_path.stem
    print(f"\n=== Evaluating scenario: {scenario_name} ===")

    model = load_model(str(dsl_path))
    bounds = variable_bounds(model.optimisation.variables)
    var_names = tuple(bounds.keys())
    num_objectives = len(model.optimisation.objectives)

    def evaluator_factory(
            *,
            min_verify_ratio: float | None = None,
    ) -> MemoisedEvaluator:
        kwargs = {}
        if min_verify_ratio is not None:
            kwargs["min_verify_ratio"] = min_verify_ratio
        return MemoisedEvaluator(make_evaluator(model, **kwargs), var_names)

    results: Dict[str, Dict[str, object]] = {}
    all_fronts: List[np.ndarray] = []
    run_records: List[Dict[str, object]] = []
    cache_totals = {
        "hits": 0,
        "misses": 0,
        "entries": 0,
        "total_calls": 0,
        "feasible_calls": 0,
        "infeasible_calls": 0,
        "evaluate_seconds": 0.0,
        "evaluate_calls": 0.0,
        "verifyta_seconds": 0.0,
        "verifyta_calls": 0.0,
    }

    for alg in algorithms:
        if alg not in ALGORITHMS:
            raise ValueError(f"Unknown algorithm '{alg}'")
        data = evaluate_algorithm(
            alg,
            bounds,
            num_objectives,
            evaluator_factory,
            runs,
            generations,
            pop,
            worker_threads=worker_threads,
        )
        results[alg] = data
        for rec in data["runs"]:
            all_fronts.append(rec["front"])
            run_records.append(
                {
                    "Scenario": scenario_name,
                    "Algorithm": alg,
                    "run": rec["run"],
                    "front": rec["front"],
                    "runtime_s": rec.get("runtime"),
                    "evaluations": rec.get("evaluations"),
                    "evaluate_time_s": rec.get("evaluate_seconds"),
                    "evaluate_calls": rec.get("evaluate_calls"),
                    "verifyta_time_s": rec.get("verifyta_seconds"),
                    "verifyta_calls": rec.get("verifyta_calls"),
                    "verifyta_pct": rec.get("verifyta_percentage"),
                    "feasible_calls": rec.get("feasible_calls"),
                    "infeasible_calls": rec.get("infeasible_calls"),
                    "total_calls": rec.get("total_calls"),
                    "feasibility_rate": rec.get("feasibility_rate"),
                }
            )
        totals = data.get("cache_totals") or {}
        for key in cache_totals:
            cache_totals[key] += totals.get(key, 0)

    summary = _summarise_algorithm_runs(
        scenario_name,
        results,
        all_fronts,
        num_objectives,
    )

    return {
        "cache_totals": cache_totals,
        "summary": summary["summary"],
        "metric_tables": summary["metric_tables"],
        "convergence": summary["convergence"],
        "feasibility": summary["feasibility"],
        "run_records": run_records,
    }


def _combine_metric_tables(metric_tables: Dict[str, List[pd.DataFrame]]):
    combined = {}
    for alg, tables in metric_tables.items():
        if not tables:
            continue
        combined[alg] = pd.concat(tables, axis=0).sort_index()
    return combined


def _print_metric_tables(metric_tables: Dict[str, pd.DataFrame]) -> None:
    if not metric_tables:
        return

    print("\nEvaluation counts per algorithm:")
    for alg, table in metric_tables.items():
        counts = sorted(table["evaluations"].unique())
        print(f"  {alg}: {counts}")

    print("\nverifyta usage per algorithm:")
    for alg, table in metric_tables.items():
        if {
            "verifyta_time_s",
            "verifyta_calls",
            "verifyta_pct",
        } - set(table.columns):
            print(f"  {alg}: verifyta metrics unavailable")
            continue

        verify_times = table["verifyta_time_s"]
        verify_calls = table["verifyta_calls"]
        verify_pct = table["verifyta_pct"]

        if not (verify_times.notna().any() or verify_calls.notna().any()):
            print(f"  {alg}: verifyta metrics unavailable")
            continue

        total_time = float(np.nansum(verify_times.to_numpy(dtype=float)))
        total_calls = float(np.nansum(verify_calls.to_numpy(dtype=float)))
        median_share = float(np.nanmedian(verify_pct.to_numpy(dtype=float)))
        if math.isnan(median_share):
            share_text = "median share n/a"
        else:
            share_text = f"median share {median_share:.2f}%"

        print(
            f"  {alg}: {total_calls:.0f} calls taking {total_time:.3f}s ({share_text})"
        )

    print("\nFeasibility rates per algorithm:")
    for alg, table in metric_tables.items():
        if "feasibility_rate" not in table.columns:
            print(f"  {alg}: feasibility metrics unavailable")
            continue
        rates = table["feasibility_rate"].dropna()
        if rates.empty:
            print(f"  {alg}: feasibility metrics unavailable")
            continue
        median_rate = float(rates.median())
        mean_rate = float(rates.mean())
        print(
            f"  {alg}: median {median_rate * 100:.2f}% (mean {mean_rate * 100:.2f}%)"
        )


def _aggregate_summary_tables(metric_tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(123)
    for alg, table in metric_tables.items():
        df = table.reset_index()
        hv_iqr = df["HV"].quantile(0.75) - df["HV"].quantile(0.25)
        igd_iqr = df["IGD+"].quantile(0.75) - df["IGD+"].quantile(0.25)
        hv_ci = bootstrap_ci(df["HV"].to_numpy(), rng=rng)
        igd_ci = bootstrap_ci(df["IGD+"].to_numpy(), rng=rng)
        runtime_iqr = df["runtime_s"].quantile(0.75) - df["runtime_s"].quantile(0.25)
        eval_calls_med = df["evaluate_calls"].median()
        verify_calls_med = df["verifyta_calls"].median()
        eval_calls_display = (
            np.nan if pd.isna(eval_calls_med) else int(round(float(eval_calls_med)))
        )
        verify_calls_display = (
            np.nan if pd.isna(verify_calls_med) else int(round(float(verify_calls_med)))
        )
        rows.append(
            {
                "Algorithm": alg,
                "HV (median)": df["HV"].median(),
                "HV (IQR)": hv_iqr,
                "HV median 95% CI": _format_ci(hv_ci),
                "IGD+ (median)": df["IGD+"].median(),
                "IGD+ (IQR)": igd_iqr,
                "IGD+ median 95% CI": _format_ci(igd_ci),
                "Runtime (median s)": df["runtime_s"].median(),
                "Runtime (IQR s)": runtime_iqr,
                "Evaluations/run": int(round(df["evaluations"].median())),
                "Eval time (median s)": df["evaluate_time_s"].median(),
                "Eval calls/run": eval_calls_display,
                "Verifyta time (median s)": df["verifyta_time_s"].median(),
                "Verifyta calls/run": verify_calls_display,
                "Verifyta share (median %)": df["verifyta_pct"].median(),
                "Feasible calls/run": df["feasible_calls"].median(),
                "Infeasible calls/run": df["infeasible_calls"].median(),
                "Feasibility rate (median)": df["feasibility_rate"].median(),
            }
        )
    return pd.DataFrame(rows)


def _global_cross_scenario_summary(
        run_records: List[Dict[str, object]]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if not run_records:
        return pd.DataFrame(), pd.DataFrame()

    filtered: List[Dict[str, object]] = []
    all_points: List[np.ndarray] = []
    for rec in run_records:
        front = rec.get("front")
        if isinstance(front, np.ndarray) and front.size > 0:
            filtered.append(rec)
            all_points.append(front)

    if not filtered or not all_points:
        return pd.DataFrame(), pd.DataFrame()

    stacked = np.vstack(all_points)
    if not np.isfinite(stacked).all():
        mask = np.all(np.isfinite(stacked), axis=1)
        stacked = stacked[mask]
    if stacked.size == 0:
        return pd.DataFrame(), pd.DataFrame()
    num_objectives = stacked.shape[1]
    if num_objectives != 2:
        raise ValueError(
            "Global cross-scenario summary currently supports only two objectives"
        )

    global_mins = np.min(stacked, axis=0)
    global_maxs = np.max(stacked, axis=0)
    global_ranges = np.where(global_maxs > global_mins, global_maxs - global_mins, 1.0)

    def _normalise_front(front: np.ndarray) -> np.ndarray:
        norm = (front - global_mins) / global_ranges
        return np.asarray(norm, dtype=float)

    normalised_fronts = []
    valid_filtered: List[Dict[str, object]] = []
    for rec in filtered:
        norm = _normalise_front(rec["front"])
        if norm.size == 0:
            continue
        norm = np.asarray(norm, dtype=float)
        mask = np.all(np.isfinite(norm), axis=1)
        norm = norm[mask]
        if norm.size == 0:
            continue
        normalised_fronts.append(norm)
        valid_filtered.append(rec)

    if not normalised_fronts:
        return pd.DataFrame(), pd.DataFrame()

    filtered = valid_filtered
    stacked_norm = np.vstack(normalised_fronts)
    global_reference_front = nondominated(stacked_norm)
    if global_reference_front.size == 0:
        global_reference_front = stacked_norm

    global_max_norm = np.max(stacked_norm, axis=0)
    ref_point = global_max_norm + 0.1

    def _safe_float(value: object) -> float:
        if value is None:
            return float("nan")
        try:
            result = float(value)
        except (TypeError, ValueError):
            return float("nan")
        return result if math.isfinite(result) else float("nan")

    per_run_rows = []
    for rec, norm_front in zip(filtered, normalised_fronts):
        if norm_front.size == 0:
            continue
        norm_front = nondominated(norm_front)
        hv_value = hypervolume_2d(norm_front, tuple(ref_point))
        igd_value = igd_plus(norm_front, global_reference_front)
        per_run_rows.append(
            {
                "Scenario": rec["Scenario"],
                "Algorithm": rec["Algorithm"],
                "run": rec.get("run"),
                "HV": hv_value,
                "IGD+": igd_value,
                "runtime_s": _safe_float(rec.get("runtime_s")),
                "evaluations": _safe_float(rec.get("evaluations")),
                "evaluate_time_s": _safe_float(rec.get("evaluate_time_s")),
                "evaluate_calls": _safe_float(rec.get("evaluate_calls")),
                "verifyta_time_s": _safe_float(rec.get("verifyta_time_s")),
                "verifyta_calls": _safe_float(rec.get("verifyta_calls")),
                "verifyta_pct": _safe_float(rec.get("verifyta_pct")),
                "feasible_calls": _safe_float(rec.get("feasible_calls")),
                "infeasible_calls": _safe_float(rec.get("infeasible_calls")),
                "total_calls": _safe_float(rec.get("total_calls")),
                "feasibility_rate": _safe_float(rec.get("feasibility_rate")),
            }
        )

    per_run_df = pd.DataFrame(per_run_rows)
    if per_run_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    def _finite_array(series: pd.Series) -> np.ndarray:
        arr = series.to_numpy(dtype=float)
        return arr[np.isfinite(arr)]

    def _iqr_from_series(series: pd.Series) -> float:
        values = _finite_array(series)
        if values.size == 0:
            return float("nan")
        q75, q25 = np.quantile(values, [0.75, 0.25])
        return float(q75 - q25)

    def _median_from_series(series: pd.Series) -> float:
        values = _finite_array(series)
        if values.size == 0:
            return float("nan")
        return float(np.median(values))

    rng = np.random.default_rng(2024)
    summary_rows = []
    for alg, df_alg in per_run_df.groupby("Algorithm"):
        hv_values = _finite_array(df_alg["HV"])
        igd_values = _finite_array(df_alg["IGD+"])

        hv_median = float(np.median(hv_values)) if hv_values.size else float("nan")
        igd_median = float(np.median(igd_values)) if igd_values.size else float("nan")
        hv_iqr = _iqr_from_series(df_alg["HV"])
        igd_iqr = _iqr_from_series(df_alg["IGD+"])
        hv_ci = bootstrap_ci(hv_values, rng=rng) if hv_values.size else (float("nan"), float("nan"))
        igd_ci = bootstrap_ci(igd_values, rng=rng) if igd_values.size else (float("nan"), float("nan"))

        runtime_median = _median_from_series(df_alg["runtime_s"])
        runtime_iqr = _iqr_from_series(df_alg["runtime_s"])
        evaluations_median = _median_from_series(df_alg["evaluations"])
        eval_time_median = _median_from_series(df_alg["evaluate_time_s"])
        eval_calls_median = _median_from_series(df_alg["evaluate_calls"])
        verify_time_median = _median_from_series(df_alg["verifyta_time_s"])
        verify_calls_median = _median_from_series(df_alg["verifyta_calls"])
        verify_share_median = _median_from_series(df_alg["verifyta_pct"])
        feasible_calls_median = _median_from_series(df_alg["feasible_calls"])
        infeasible_calls_median = _median_from_series(df_alg["infeasible_calls"])
        feasibility_rate_median = _median_from_series(df_alg["feasibility_rate"])

        total_feasible = df_alg["feasible_calls"].dropna().sum()
        total_calls = df_alg["total_calls"].dropna().sum()
        feasibility_rate_overall = (
            float(total_feasible) / float(total_calls)
            if total_calls and total_calls > 0
            else float("nan")
        )

        def _to_int_or_nan(value: float) -> float:
            if not math.isfinite(value):
                return float("nan")
            return float(int(round(value)))

        summary_rows.append(
            {
                "Algorithm": alg,
                "HV (median)": hv_median,
                "HV (IQR)": hv_iqr,
                "HV median 95% CI": _format_ci(hv_ci),
                "IGD+ (median)": igd_median,
                "IGD+ (IQR)": igd_iqr,
                "IGD+ median 95% CI": _format_ci(igd_ci),
                "Runtime (median s)": runtime_median,
                "Runtime (IQR s)": runtime_iqr,
                "Evaluations/run": _to_int_or_nan(evaluations_median),
                "Eval time (median s)": eval_time_median,
                "Eval calls/run": _to_int_or_nan(eval_calls_median),
                "Verifyta time (median s)": verify_time_median,
                "Verifyta calls/run": _to_int_or_nan(verify_calls_median),
                "Verifyta share (median %)": verify_share_median,
                "Feasible calls/run": feasible_calls_median,
                "Infeasible calls/run": infeasible_calls_median,
                "Feasibility rate (median)": feasibility_rate_median,
                "Feasibility rate (overall)": feasibility_rate_overall,
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    if not summary_df.empty:
        column_order = [
            "Algorithm",
            "HV (median)",
            "HV (IQR)",
            "HV median 95% CI",
            "IGD+ (median)",
            "IGD+ (IQR)",
            "IGD+ median 95% CI",
            "Runtime (median s)",
            "Runtime (IQR s)",
            "Evaluations/run",
            "Eval time (median s)",
            "Eval calls/run",
            "Verifyta time (median s)",
            "Verifyta calls/run",
            "Verifyta share (median %)",
            "Feasible calls/run",
            "Infeasible calls/run",
            "Feasibility rate (median)",
            "Feasibility rate (overall)",
        ]
        summary_df = summary_df[column_order]
    return summary_df, per_run_df


def _wilcoxon_tests(metric_tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    test_rows = []
    for left, right in itertools.combinations(metric_tables.keys(), 2):
        merged = metric_tables[left].join(
            metric_tables[right],
            how="inner",
            lsuffix=f"_{left}",
            rsuffix=f"_{right}",
        )
        if merged.empty:
            continue
        hv_stat, hv_p = wilcoxon_signed_rank(
            merged[f"HV_{left}"].to_numpy(),
            merged[f"HV_{right}"].to_numpy(),
        )
        igd_stat, igd_p = wilcoxon_signed_rank(
            merged[f"IGD+_{left}"].to_numpy(),
            merged[f"IGD+_{right}"].to_numpy(),
        )
        test_rows.append(
            {
                "Comparison": f"{left} vs {right}",
                "HV W": hv_stat,
                "HV p-value": hv_p,
                "IGD+ W": igd_stat,
                "IGD+ p-value": igd_p,
            }
        )
    return pd.DataFrame(test_rows)


def main():
    parser = argparse.ArgumentParser(description="Evaluate MOEAs across DSL scenarios")
    parser.add_argument(
        "--dsl-dir",
        type=Path,
        default=Path("../Data/DSLInput"),
        help="Directory containing DSL .adsl files",
    )
    parser.add_argument(
        "--algorithms",
        nargs="+",
        default=['random_search', 'nsga2', 'sms-emoa', 'qehvi', 'moead', 'eps-constraint'],
        # 'random_search', 'nsga2', 'sms-emoa', 'qehvi', 'moead', 'eps-constraint'
        help="Algorithms to evaluate",
    )
    parser.add_argument("--runs", type=int, default=10, help="Number of runs per algorithm")
    parser.add_argument(
        "--generations",
        type=int,
        default=80,
        help="Number of generations for evolutionary algorithms",
    )
    parser.add_argument(
        "--pop",
        type=int,
        default=60,
        help="Population size for evolutionary algorithms",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker threads for evaluation (default: CPU count)",
    )

    args = parser.parse_args()

    if args.dsl_dir.is_file():
        dsl_paths = [args.dsl_dir]
    else:
        dsl_paths = sorted(args.dsl_dir.glob("*.adsl"))

    if not dsl_paths:
        raise FileNotFoundError(
            f"No DSL files found in {args.dsl_dir.resolve()!s}"
        )

    worker_threads = args.workers if args.workers is not None else os.cpu_count() or 1
    print(f"Worker threads: {worker_threads}")

    overall_cache_totals = {
        "hits": 0,
        "misses": 0,
        "entries": 0,
        "total_calls": 0,
        "feasible_calls": 0,
        "infeasible_calls": 0,
        "evaluate_seconds": 0.0,
        "evaluate_calls": 0.0,
        "verifyta_seconds": 0.0,
        "verifyta_calls": 0.0,
    }

    metric_table_lists: Dict[str, List[pd.DataFrame]] = defaultdict(list)
    convergence_records = []
    feasibility_records = []
    global_run_records: List[Dict[str, object]] = []

    for dsl_path in dsl_paths:
        scenario_data = evaluate_scenario(
            dsl_path,
            args.algorithms,
            args.runs,
            args.generations,
            args.pop,
            worker_threads,
        )

        for key in overall_cache_totals:
            overall_cache_totals[key] += scenario_data["cache_totals"].get(key, 0)

        for alg, table in scenario_data["metric_tables"].items():
            metric_table_lists[alg].append(table)

        convergence_records.append(scenario_data["convergence"])
        feasibility_records.append(scenario_data["feasibility"])
        global_run_records.extend(scenario_data.get("run_records", []))

    combined_metric_tables = _combine_metric_tables(metric_table_lists)

    overall_summary = _aggregate_summary_tables(combined_metric_tables)
    if not overall_summary.empty:
        print("\n=== Aggregated summary across scenarios ===")
        print(overall_summary.to_markdown(index=False, floatfmt=".4g"))

    global_summary, global_runs = _global_cross_scenario_summary(global_run_records)
    if not global_summary.empty:
        print("\n=== Global cross-scenario summary (normalised metrics) ===")
        print(
            "Note: HV and IGD+ recomputed after global min–max normalisation "
            "with a shared reference point and reference front."
        )
        print(global_summary.to_markdown(index=False, floatfmt=".4g"))
        global_summary.to_csv(Path("global_cross_scenario_summary.csv"), index=False)
        global_runs.to_csv(Path("global_cross_scenario_runs.csv"), index=False)

    _print_metric_tables(combined_metric_tables)

    combined_convergence = [df for df in convergence_records if not df.empty]
    if combined_convergence:
        convergence_df = pd.concat(combined_convergence, axis=0)
        conv_summary = (
            convergence_df.groupby(["Algorithm", "Generation"])["HV"]
            .agg(
                median="median",
                q1=lambda s: s.quantile(0.25),
                q3=lambda s: s.quantile(0.75),
            )
            .reset_index()
        )
        conv_summary.to_csv(Path("../Data/EvalOutput/hv_convergence.csv"), index=False)
        print("Saved aggregated HV convergence curves → hv_convergence.csv")

    combined_feasibility = [df for df in feasibility_records if not df.empty]
    if combined_feasibility:
        feasibility_df = pd.concat(combined_feasibility, axis=0)
        feas_summary = (
            feasibility_df.groupby(["Algorithm", "Generation"])["FeasibleRate"]
            .agg(
                median="median",
                q1=lambda s: s.quantile(0.25),
                q3=lambda s: s.quantile(0.75),
            )
            .reset_index()
        )
        feas_summary.to_csv(Path("../Data/EvalOutput/feasibility_convergence.csv"), index=False)
        print(
            "Saved aggregated feasibility convergence curves → "
            "feasibility_convergence.csv"
        )

    tests_df = _wilcoxon_tests(combined_metric_tables)
    if not tests_df.empty:
        print("\n=== Wilcoxon signed-rank tests (aggregated) ===")
        print(tests_df.to_markdown(index=False, floatfmt=".4g"))

    print(
        "\nMemoised evaluator cache: "
        f"{int(overall_cache_totals['hits'])} hits / "
        f"{int(overall_cache_totals['misses'])} misses "
        f"({int(overall_cache_totals['entries'])} unique assignments across all runs)"
    )

    eval_seconds = float(overall_cache_totals["evaluate_seconds"])
    eval_calls = int(round(overall_cache_totals["evaluate_calls"]))
    verify_seconds = float(overall_cache_totals["verifyta_seconds"])
    verify_calls = int(round(overall_cache_totals["verifyta_calls"]))

    print(
        "Evaluator runtime: "
        f"{eval_seconds:.3f}s across {eval_calls} executions"
    )
    share = (verify_seconds / eval_seconds) * 100.0 if eval_seconds > 0.0 else None
    extra = f" ({share:.1f}% of evaluation time)" if share is not None else ""
    print(
        "  verifyta subprocess time: "
        f"{verify_seconds:.3f}s across {verify_calls} calls{extra}"
    )

    total_calls = int(round(overall_cache_totals["total_calls"]))
    feasible_calls = int(round(overall_cache_totals["feasible_calls"]))
    infeasible_calls = int(round(overall_cache_totals["infeasible_calls"]))
    feasibility_rate = (
        (feasible_calls / total_calls) * 100.0 if total_calls > 0 else float("nan")
    )
    print(
        "  Feasibility overall: "
        f"{feasible_calls} feasible / {infeasible_calls} infeasible "
        f"({total_calls} total, {feasibility_rate:.2f}% feasible)"
    )


if __name__ == "__main__":
    main()
