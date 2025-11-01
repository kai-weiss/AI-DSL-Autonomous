from __future__ import annotations

import argparse
import itertools
import math
import os
import random
import time
from pathlib import Path
from threading import Lock
from typing import Callable, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from Backend.Optim.optimise import load_model, variable_bounds, make_evaluator
from Backend.Optim.Algo.NSGA2 import NSGAII
from Backend.Optim.Algo.SMSEMOA import SMSEMOA
from Backend.Optim.Algo.MOEAD import MOEAD
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
    front = front[np.argsort(front[:, 0])]
    hv, prev_f1 = 0.0, ref[1]
    for f0, f1 in front:
        hv += max(0.0, ref[0] - f0) * max(0.0, prev_f1 - f1)
        prev_f1 = f1
    return hv


def igd_plus(front: np.ndarray, ref_set: np.ndarray) -> float:
    if len(front) == 0:
        return float("inf")
    dists = []
    for r in ref_set:
        if np.any(np.all(front <= r, axis=1)):  # dominated ref point
            dists.append(0.0)
        else:
            dists.append(np.min(np.linalg.norm(front - r, axis=1)))
    return float(np.mean(dists))


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
        batch_size=min(pop_size, 4),
        seed=seed,
        workers=workers,
    )
    pop, history, evaluations, stopped = alg.run(
        log_history=True, plateau_detector=plateau
    )
    objs = [ind.objectives for ind in pop]
    final_front = nondominated(objs)
    history_fronts = [np.asarray(front, dtype=float) for front in history]
    return final_front, history_fronts, evaluations, stopped


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
    "random_search": (random_search, False),
}

PLATEAU_WINDOW = 15
PLATEAU_EPSILON = 1e-4


class MemoisedEvaluator:
    """Thread-safe memoisation wrapper around the expensive objective call."""

    def __init__(self, evaluate, names: Iterable[str]):
        self._evaluate = evaluate
        self._names = tuple(names)
        self._cache: Dict[Tuple[float, ...], Tuple[float, ...]] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def __call__(self, values: Dict[str, float]):
        key = tuple(float(values[name]) for name in self._names)
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                self._hits += 1
                return cached

        result = tuple(float(v) for v in self._evaluate(dict(values)))

        with self._lock:
            # Another thread might have populated the cache while we were evaluating.
            cached = self._cache.get(key)
            if cached is not None:
                self._hits += 1
                return cached

            self._cache[key] = result
            self._misses += 1
            return result

    def stats(self) -> Dict[str, float]:
        with self._lock:
            data: Dict[str, float] = {
                "hits": self._hits,
                "misses": self._misses,
                "entries": len(self._cache),
            }

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
        evaluator_factory: Callable[[], MemoisedEvaluator],
        runs: int,
        gens: int,
        pop: int,
        *,
        worker_threads: int | None = None,
):
    runner, has_gens = ALGORITHMS[key]

    run_records = []
    cache_totals = {
        "hits": 0,
        "misses": 0,
        "entries": 0,
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
            front, history, evaluations, stopped = runner(
                bounds,
                evaluator,
                gens,
                pop,
                seed,
                workers=worker_threads,
                plateau=plateau,
            )
        else:
            front, history, evaluations, stopped = runner(
                bounds,
                evaluator,
                budget,
                seed,
                gens,
                pop,
                plateau=plateau,
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
            }
        )

        cache_stats = evaluator.stats()
        cache_totals["hits"] += int(cache_stats.get("hits", 0) or 0)
        cache_totals["misses"] += int(cache_stats.get("misses", 0) or 0)
        cache_totals["entries"] += int(cache_stats.get("entries", 0) or 0)

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


def main():
    dsl = "C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/Data/DSLInput/Overtaking_Hard.adsl"
    # algorithms = 'sms-emoa', 'nsga2', 'random_search', 'qehvi', 'moead'
    algorithms = 'nsga2', 'sms-emoa', 'qehvi'

    # runs = 10
    # generations = 80
    # pop = 60
    runs = 10
    generations = 80
    pop = 60
    worker_threads = os.cpu_count() or 1
    print(os.cpu_count())

    model = load_model(dsl)
    bounds = variable_bounds(model.optimisation.variables)
    var_names = tuple(bounds.keys())
    num_objectives = len(model.optimisation.objectives)

    def evaluator_factory() -> MemoisedEvaluator:
        return MemoisedEvaluator(make_evaluator(model), var_names)

    results = {}
    all_fronts: List[np.ndarray] = []
    overall_cache_totals = {
        "hits": 0,
        "misses": 0,
        "entries": 0,
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
        totals = data.get("cache_totals") or {}
        for key in overall_cache_totals:
            overall_cache_totals[key] += totals.get(key, 0)

    ref_set = nondominated(np.vstack(all_fronts))
    ref_point = np.max(ref_set, axis=0) * 1.1
    mins, ranges = _min_max_params(ref_set)
    norm_ref_set = _normalise(ref_set, mins, ranges)

    rng = np.random.default_rng(42)
    summary_rows = []
    convergence_records = []
    metric_tables: Dict[str, pd.DataFrame] = {}

    for alg, data in results.items():
        rows = []
        for rec in data["runs"]:
            front = rec["front"]
            hv_value = hypervolume_2d(front, tuple(ref_point))
            norm_front = _normalise(front, mins, ranges)
            igd_value = igd_plus(norm_front, norm_ref_set)
            rows.append(
                {
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
                }
            )

            for gen_idx, gen_front in enumerate(rec["history"], start=1):
                hv_gen = hypervolume_2d(gen_front, tuple(ref_point))
                convergence_records.append(
                    {
                        "Algorithm": alg,
                        "run": rec["run"],
                        "Generation": gen_idx,
                        "HV": hv_gen,
                    }
                )

        df = pd.DataFrame(rows)
        if df.empty:
            continue
        df.to_csv(Path(f"results_{alg}.csv"), index=False)
        metric_tables[alg] = df.set_index("run")
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
            }
        )
        print(f"Saved per-run metrics for {alg} → results_{alg}.csv")

    summary_df = pd.DataFrame(summary_rows)
    if not summary_df.empty:
        print("\n=== Summary ===")
        print(summary_df.to_markdown(index=False, floatfmt=".4g"))

    if metric_tables:
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

    convergence_df = pd.DataFrame(convergence_records)
    if not convergence_df.empty:
        agg = convergence_df.groupby(["Algorithm", "Generation"])['HV']
        conv_summary = agg.agg(
            median="median",
            q1=lambda s: s.quantile(0.25),
            q3=lambda s: s.quantile(0.75),
        ).reset_index()
        conv_summary.to_csv(Path("hv_convergence.csv"), index=False)
        print("Saved HV convergence curves → hv_convergence.csv")

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

    if test_rows:
        tests_df = pd.DataFrame(test_rows)
        print("\n=== Wilcoxon signed-rank tests ===")
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
    share = None
    if eval_seconds > 0.0:
        share = (verify_seconds / eval_seconds) * 100.0
    extra = f" ({share:.1f}% of evaluation time)" if share is not None else ""
    print(
        "  verifyta subprocess time: "
        f"{verify_seconds:.3f}s across {verify_calls} calls{extra}"
    )


if __name__ == "__main__":
    main()
