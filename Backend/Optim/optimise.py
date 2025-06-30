from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from datetime import timedelta
import random

from DSL.parser import parse_source
from DSL.visitor import ASTBuilder
from DSL.metamodel import Model
from Algo.NSGA2 import NSGAII, Individual
from Backend.Optim.model_ops import variable_bounds, apply_values


def load_model(path: str) -> Model:
    source = Path(path).read_text(encoding="utf-8")
    tree = parse_source(source)
    builder = ASTBuilder()
    builder.visit(tree)
    return builder.model


def evaluate_dummy(values: Dict[str, float]) -> List[float]:
    # Placeholder objective calculation
    return [random.random(), random.random()]


def main(path: str, generations: int = 5):
    model = load_model(path)
    if not hasattr(model, "optimisation"):
        raise ValueError("Model has no OPTIMISATION block")
    bounds = variable_bounds(model.optimisation.variables)

    algo = NSGAII(bounds, evaluate_dummy, generations=generations)
    population = algo.run()

    # Apply best individual (rank 0, highest crowding)
    best = sorted(population, key=lambda x: (x.rank, -x.crowding_distance))[0]
    assignments = {
        name: timedelta(milliseconds=val)
        for name, val in best.values.items()
    }
    new_model = apply_values(model, assignments)
    return new_model, best


if __name__ == "__main__":
    m, ind = main("C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/DSL/Input/1.adsl")
    print("Best individual:", ind.values, ind.objectives)

