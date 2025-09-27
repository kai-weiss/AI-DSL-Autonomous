from __future__ import annotations

import argparse
import itertools
import math
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from Backend.Optim.optimise import load_model, variable_bounds, make_evaluator
from Backend.Optim.Algo.NSGA2 import NSGAII
from Backend.Optim.Algo.SMSEMOA import SMSEMOA


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
def run_nsga2(bounds, evaluate, generations, pop_size, seed):
    random.seed(seed)
    np.random.seed(seed)
    alg = NSGAII(
        bounds,
        evaluate,
        generations=generations,
        pop_size=pop_size,
    )
    pop, history, evaluations = alg.run(log_history=True)
    objs = [ind.objectives for ind in pop]
    final_front = nondominated(objs)
    history_fronts = [np.asarray(h, dtype=float) for h in history]
    return final_front, history_fronts, evaluations


def run_sms_emoa(bounds, evaluate, generations, pop_size, seed):
    random.seed(seed)
    np.random.seed(seed)
    alg = SMSEMOA(
        bounds,
        evaluate,
        generations=generations,
        pop_size=pop_size,
    )
    pop, history, evaluations = alg.run(log_history=True)
    objs = [ind.objectives for ind in pop]
    final_front = nondominated(objs)
    history_fronts = [np.asarray(h, dtype=float) for h in history]
    return final_front, history_fronts, evaluations


def random_search(bounds, evaluate, budget, seed, generations, pop_size):
    rnd = random.Random(seed)
    objs: List[List[float]] = []
    history: List[np.ndarray] = []
    for idx in range(budget):
        point = {k: rnd.uniform(lo, hi) for k, (lo, hi) in bounds.items()}
        objs.append(evaluate(point))
        if (idx + 1) % pop_size == 0:
            history.append(nondominated(objs).copy())
    final_front = nondominated(objs)
    history_fronts = [np.asarray(front, dtype=float) for front in history]
    return final_front, history_fronts, budget


ALGORITHMS = {
    "nsga2": (run_nsga2, True),
    "sms-emoa": (run_sms_emoa, True),
    "random_search": (random_search, False),
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
        ranks[order[i : j + 1]] = rank
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


def evaluate_algorithm(
    key: str,
    dsl: str,
    runs: int,
    gens: int,
    pop: int,
):
    runner, has_gens = ALGORITHMS[key]
    mdl = load_model(dsl)
    bounds = variable_bounds(mdl.optimisation.variables)
    evaluator = make_evaluator(mdl)

    run_records = []
    for r in range(runs):
        seed = 17 + r
        budget = gens * pop
        start = time.perf_counter()
        if has_gens:
            front, history, evaluations = runner(bounds, evaluator, gens, pop, seed)
        else:
            front, history, evaluations = runner(bounds, evaluator, budget, seed, gens, pop)
        runtime = time.perf_counter() - start
        front = np.asarray(front, dtype=float)
        history = [np.asarray(h, dtype=float) for h in history]
        if front.size == 0:
            continue
        run_records.append(
            {
                "run": r,
                "front": front,
                "history": history,
                "runtime": runtime,
                "evaluations": evaluations,
            }
        )

    return {
        "runs": run_records,
        "has_generations": has_gens,
    }


def main():
    dsl = "C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/DSL/Input/2.adsl"
    algorithms = 'sms-emoa', 'nsga2', 'random_search'
    runs = 10
    generations = 80
    pop = 60

    results = {}
    all_fronts: List[np.ndarray] = []
    for alg in algorithms:
        if alg not in ALGORITHMS:
            raise ValueError(f"Unknown algorithm '{alg}'")
        data = evaluate_algorithm(alg, dsl, runs, generations, pop)
        results[alg] = data
        for rec in data["runs"]:
            all_fronts.append(rec["front"])

    if not all_fronts:
        print("No successful runs recorded.")
        return

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
                "Evaluations/run": int(df["evaluations"].median()),
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


if __name__ == "__main__":
    main()
