from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Callable
from datetime import timedelta
import random

from Backend.UPPAAL.UppaalVerifier import UppaalVerifier
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


def _worst_end2end_latency(model: Model) -> float:
    """Return the maximum connection latency in *model* in milliseconds."""
    worst = 0.0
    for conn in getattr(model, "connections", []):
        lb = getattr(conn, "latency_budget", None)
        if lb is not None:
            ms = lb.total_seconds() * 1000.0
            if ms > worst:
                worst = ms
    return worst


def _max_core_utilisation(model: Model) -> float:
    """Return the maximum WCET/period ratio for all components."""
    util = 0.0
    for comp in model.components.values():
        if comp.period and comp.wcet and comp.period.total_seconds() > 0:
            ratio = comp.wcet.total_seconds() / comp.period.total_seconds()
            util = max(util, ratio)
    return util


def _ms(td: timedelta) -> str:
    """Return *td* formatted as '<ms>ms'."""
    return f"{int(td.total_seconds() * 1000)}ms"


def _objective_name(obj: str) -> str:
    """Return the plain objective name without 'minimise/maximise' or ';'."""
    obj = obj.strip().rstrip(";")
    for prefix in ("minimise", "minimize", "maximise", "maximize"):
        if obj.startswith(prefix):
            return obj[len(prefix):]
    return obj


def emit_model(model: Model) -> str:
    """Serialize *model* back into the DSL format."""
    lines: List[str] = []

    for comp in model.components.values():
        lines.append(f"COMPONENT {comp.name} {{")
        if comp.period is not None:
            lines.append(f"    period   = {_ms(comp.period)};")
        if comp.deadline is not None:
            lines.append(f"    deadline = {_ms(comp.deadline)};")
        if comp.wcet is not None:
            lines.append(f"    WCET     = {_ms(comp.wcet)};")
        lines.append("}")
        lines.append("")

    for conn in getattr(model, "connections", []):
        lines.append(f"CONNECT {conn.src} -> {conn.dst} {{")
        if conn.latency_budget is not None:
            lines.append(f"    latency_budget = {_ms(conn.latency_budget)};")
        lines.append("}")
        lines.append("")

    for name, text in model.properties.items():
        lines.append(f"PROPERTY {name}: \"{text}\";")
    if model.properties:
        lines.append("")

    spec = getattr(model, "optimisation", None)
    if spec and getattr(spec, "variables", None):
        lines.append("OPTIMISATION {")
        lines.append("    VARIABLES {")
        for var in spec.variables:
            l = _ms(var.lower)
            h = _ms(var.upper)
            lines.append(f"        {var.ref} range {l} .. {h};")
        lines.append("    }")
        if spec.objectives:
            lines.append("    OBJECTIVES{")
            for obj in spec.objectives:
                print(obj)
                lines.append(f"        {obj}")
            lines.append("    }")
        if spec.constraints:
            lines.append("    CONSTRAINTS{")
            for c in spec.constraints:
                lines.append(f"        assert {c};")
            lines.append("    }")
        lines.append("}")

    return "\n".join(lines) + "\n"


def make_evaluator(base_model: Model) -> Callable[[Dict[str, float]], List[float]]:
    verifier = UppaalVerifier()
    constraints = getattr(base_model.optimisation, "constraints", [])

    def evaluate(values: Dict[str, float]) -> List[float]:
        assignments = {
            name: timedelta(milliseconds=v) for name, v in values.items()
        }
        candidate = apply_values(base_model, assignments)

        # Verify constraints via Uppaal (if available)
        if constraints:
            res = verifier.check(candidate, constraints)
            if any(r is False or r is None for r in res.values()):
                # Penalise invalid solutions heavily
                return [1e9, 1e9]

        latency = _worst_end2end_latency(candidate)
        utilisation = _max_core_utilisation(candidate)
        return [latency, utilisation]

    return evaluate


def main(path: str, generations: int = 500):
    model = load_model(path)
    if not hasattr(model, "optimisation"):
        raise ValueError("Model has no OPTIMISATION block")
    bounds = variable_bounds(model.optimisation.variables)
    evaluate = make_evaluator(model)

    algo = NSGAII(bounds, evaluate, generations=generations)
    population = algo.run()

    # Export best individual for each objective separately
    obj_names = [_objective_name(o) for o in model.optimisation.objectives]
    out_dir = Path("Output")
    out_dir.mkdir(exist_ok=True)
    for idx, obj_name in enumerate(obj_names):
        best = min(population, key=lambda ind: ind.objectives[idx])
        assignments = {
            n: timedelta(milliseconds=v) for n, v in best.values.items()
        }
        candidate = apply_values(model, assignments)
        (out_dir / f"{obj_name}.adsl").write_text(emit_model(candidate), "utf-8")

    # Return best individual overall (rank 0, highest crowding distance)
    best = sorted(population, key=lambda x: (x.rank, -x.crowding_distance))[0]
    assignments = {n: timedelta(milliseconds=v) for n, v in best.values.items()}
    new_model = apply_values(model, assignments)
    return new_model, best


if __name__ == "__main__":
    m, ind = main("C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/DSL/Input/1.adsl", generations=1)
    print("Best individual:", ind.values, ind.objectives)

