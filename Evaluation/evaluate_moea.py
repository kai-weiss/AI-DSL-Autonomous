from __future__ import annotations
import argparse, random, sys
from pathlib import Path
from typing import Callable, List, Tuple, Dict

import numpy as np
import pandas as pd

from Backend.Optim.optimise import load_model, variable_bounds, make_evaluator
from Backend.Optim.Algo.NSGA2 import NSGAII  # your GA


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
    alg = NSGAII(bounds, evaluate,
                 generations=generations)
    pop = alg.run()
    objs = [ind.objectives for ind in pop]
    return nondominated(objs).tolist()


def random_search(bounds, evaluate, budget, seed):
    rnd = random.Random(seed)
    objs = []
    for _ in range(budget):
        point = {k: rnd.uniform(lo, hi) for k, (lo, hi) in bounds.items()}
        objs.append(evaluate(point))
    return nondominated(objs).tolist()


ALGORITHMS = {
    "nsga2": (run_nsga2, True),
    "random_search": (random_search, False),
}


#  Experiment driver
def evaluate_algorithm(key: str, dsl: str, runs: int, gens: int, pop: int
                       ) -> pd.DataFrame:
    runner, has_gens = ALGORITHMS[key]
    mdl = load_model(dsl)
    bounds = variable_bounds(mdl.optimisation.variables)
    evl = make_evaluator(mdl)

    all_fronts, rows = [], []
    for r in range(runs):
        seed = 17 + r
        budget = gens * pop
        fronts = runner(bounds, evl, gens, pop, seed) if has_gens \
            else runner(bounds, evl, budget, seed)
        fronts = nondominated(fronts)
        if fronts.size == 0:
            continue
        rows.append({"run": r, "front": fronts})
        all_fronts.append(fronts)

    ref_set = nondominated(np.vstack(all_fronts))
    ref_pt = np.max(ref_set, axis=0) * 1.1

    metrics = []
    for rec in rows:
        f = rec["front"]
        metrics.append({
            "run": rec["run"],
            "HV": hypervolume_2d(f, tuple(ref_pt)),
            "IGD+": igd_plus(f, ref_set),
        })
    return pd.DataFrame(metrics)


def main():
    dsl = "C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/DSL/Input/2.adsl"
    algs = 'nsga2', 'random_search'
    runs = 2
    generations = 4
    pop = 20

    summary_rows = []

    for alg in algs:
        df = evaluate_algorithm(alg, dsl, runs, generations, pop)
        df.to_csv(Path(f"results_{alg}.csv"), index=False)
        iqr = df.quantile(0.75) - df.quantile(0.25)
        summary_rows.append({
            "Algorithm": alg,
            "HV (median)": df["HV"].median(),
            "HV (IQR)": iqr["HV"],
            "IGD+ (median)": df["IGD+"].median(),
            "IGD+ (IQR)": iqr["IGD+"],
        })
        print(f"Saved per-run metrics for {alg} → results_{alg}.csv")

    print("\n=== Summary ===")
    print(pd.DataFrame(summary_rows).to_markdown(index=False, floatfmt=".4g"))


if __name__ == "__main__":
    main()
