from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Callable
from datetime import timedelta
import random
import time
from threading import Lock
import math

import numpy as np

from Backend.UPPAAL.UppaalVerifier import UppaalVerifier
from DSL.parser import parse_source
from DSL.visitor import ASTBuilder
from DSL.metamodel import Model
from Backend.Optim.Algo.common import Individual
from Backend.Optim.Algo.NSGA2 import NSGAII
from Backend.Optim.Algo.SMSEMOA import SMSEMOA
from Backend.Optim.Algo.MOEAD import MOEAD
from Backend.Optim.Algo.qehvi import QEHVIOptimizer
from Backend.Optim.model_ops import variable_bounds, apply_values, _enumerate_chains



def load_model(path: str) -> Model:
    source = Path(path).read_text(encoding="utf-8")
    tree = parse_source(source)
    builder = ASTBuilder()
    builder.visit(tree)
    return builder.model


def _worst_end2end_latency(model: Model) -> float:
    """Upper-bound end-to-end latency of every chain, assuming
    fixed-priority, periodic activation and immediate data hand-off"""
    worst = 0.0
    for comps, conns in _enumerate_chains(model):
        worst = max(worst, _chain_latency_ms(model, comps, conns))
    return worst


def _comp_of(endpoint: str) -> str:
    """'A.Task.port' → 'A.Task' (component part only)."""
    return endpoint.rsplit(".", 1)[0]


def _chain_latency_ms(model, endpoints, conns):
    L = 0.0
    seen = set()  # avoid counting the same task twice
    for ep in endpoints:
        comp_name = _comp_of(ep)
        if comp_name in seen:
            continue
        seen.add(comp_name)
        comp = model.components.get(comp_name)
        if comp and comp.wcet:
            L += comp.wcet.total_seconds() * 1_000
    for c in conns:  # keep latency_budget term
        if c.latency_budget:
            L += c.latency_budget.total_seconds() * 1_000
    return L


def _ind_id(ind) -> int:
    """Return a hashable identifier for an Individual (its memory id)"""
    return id(ind)


def _max_core_utilisation(model: Model) -> float:
    """Return the maximum WCET/period ratio for all components"""
    util = 0.0
    for c in model.components.values():
        if c.wcet and c.period and c.period.total_seconds() > 0:
            util += c.wcet.total_seconds() / c.period.total_seconds()
    return util


def _ms(td: timedelta) -> str:
    """Return td formatted as ms"""
    return f"{int(td.total_seconds() * 1000)}ms"


def _objective_name(obj: str) -> str:
    """Return the plain objective name"""
    obj = obj.strip().rstrip(';').lower()

    # drop the optimiser verb
    for prefix in ("minimise", "minimize", "maximise", "maximize"):
        if obj.startswith(prefix):
            obj = obj[len(prefix):].strip()
            break

    obj = obj.replace(' ', '_')

    if "core_utilisation" in obj:
        return f"min_{obj.replace('max_', '')}"
    if "end2end_latency" in obj:
        return f"best_{obj.replace('worst_', '')}"

    # generic fallback
    return obj


def _objective_direction(raw: str) -> str:
    """
    Return min or max objective in the DSL
    """
    s = raw.strip().lower()
    return "max" if s.startswith(("maximise", "maximize")) else "min"


def _normalise_expression(expr: str) -> str:
    """Insert spacing around common operators to improve readability"""

    operators = ["==", "!=", "<=", ">=", "&&", "||", "<", ">", "+", "-", "*", "/"]
    for op in operators:
        expr = expr.replace(op, f" {op} ")
    return " ".join(expr.split())


def emit_model(model: Model) -> str:
    """Serialize model back into the DSL format"""
    lines: List[str] = []

    system_name = getattr(model, "system_name", None) or "System"
    lines.append(f"SYSTEM {system_name} {{")

    cpu_items: list[tuple[str, str]] = []
    cpu_cfg = getattr(model, "cpu", None)
    if cpu_cfg is not None:
        scheduler = cpu_cfg.scheduler or cpu_cfg.attributes.get("scheduler")
        if scheduler:
            cpu_items.append(("scheduler", scheduler))
        if cpu_cfg.class_order:
            order_txt = "[ " + " > ".join(cpu_cfg.class_order) + " ]"
            cpu_items.append(("class_order", order_txt))
        elif "class_order" in cpu_cfg.attributes:
            cpu_items.append(("class_order", cpu_cfg.attributes["class_order"]))

        for key, value in cpu_cfg.attributes.items():
            if key in {"scheduler", "class_order"}:
                continue
            cpu_items.append((key, str(value)))
    elif getattr(model, "cpu_attrs", None):
        cpu_items = [(k, str(v)) for k, v in model.cpu_attrs]

    if cpu_items:
        lines.append("    CPU {")
        for key, value in cpu_items:
            lines.append(f"        {key} = {value};")
        lines.append("    }")
        lines.append("")

    emitted: set[str] = set()

    def emit_component(comp, indent: str) -> List[str]:
        block: List[str] = [f"{indent}COMPONENT {comp.name} {{"]
        if comp.period is not None:
            block.append(f"{indent}    period = {_ms(comp.period)};")
        if comp.deadline is not None:
            block.append(f"{indent}    deadline = {_ms(comp.deadline)};")
        if comp.wcet is not None:
            block.append(f"{indent}    WCET = {_ms(comp.wcet)};")
        if comp.priority is not None:
            block.append(f"{indent}    priority = {comp.priority};")
        if getattr(comp, "criticality_class", None) is not None:
            block.append(f"{indent}    class = {comp.criticality_class};")
        block.append(f"{indent}}}")
        return block

    for vehicle in getattr(model, "vehicle_order", []):
        comps = model.vehicles.get(vehicle, [])
        lines.append(f"    VEHICLE {vehicle} {{")
        for idx, comp_name in enumerate(comps):
            comp = model.components.get(comp_name)
            if not comp:
                continue
            lines.extend(emit_component(comp, "        "))
            emitted.add(comp_name)
            if idx != len(comps) - 1:
                lines.append("")
        lines.append("    }")
        lines.append("")

    for comp_name, comp in model.components.items():
        if comp_name in emitted:
            continue
        lines.extend(emit_component(comp, "    "))
        lines.append("")

    for conn in getattr(model, "connections", []):
        lines.append(
            f"    CONNECT {conn.name}: {conn.src} -> {conn.dst} {{"
        )
        if conn.latency_budget is not None:
            lines.append(
                f"        latency_budget = {_ms(conn.latency_budget)};"
            )
        lines.append("    }")
        lines.append("")

    if model.properties:
        for name, text in model.properties.items():
            lines.append(f"    PROPERTY {name}:")
            indent = "      "
            escaped = text.replace("\\", "\\\\").replace('"', '\\"')
            formatted = escaped.replace("\n", f"\n{indent}")
            lines.append(f"{indent}\"{formatted}\";")
            lines.append("")

    spec = getattr(model, "optimisation", None)
    if spec and getattr(spec, "variables", None):
        lines.append("    OPTIMISATION {")
        lines.append("        VARIABLES {")
        for var in spec.variables:
            lower = _ms(var.lower)
            upper = _ms(var.upper)
            lines.append(
                f"            {var.ref} range {lower} .. {upper};"
            )
        lines.append("        }")
        if spec.objectives:
            lines.append("        OBJECTIVES{")
            for obj in spec.objectives:
                lines.append(f"            {obj}")
            lines.append("        }")
        if spec.constraints:
            lines.append("        CONSTRAINTS{")
            for c in spec.constraints:
                lines.append(
                    f"            assert {_normalise_expression(c)};"
                )
            lines.append("        }")
        lines.append("    }")

    lines.append("}")

    cleaned: List[str] = []
    for line in lines:
        if line == "" and cleaned and cleaned[-1] == "":
            continue
        cleaned.append(line)

    return "\n".join(cleaned) + "\n"


class _GaussianStats:
    """Welford updates for a single Gaussian-distributed feature."""

    def __init__(self, n_features: int) -> None:
        self.count = 0
        self.mean = np.zeros(n_features, dtype=float)
        self.m2 = np.zeros(n_features, dtype=float)

    def update(self, sample: np.ndarray) -> None:
        self.count += 1
        delta = sample - self.mean
        self.mean += delta / self.count
        delta2 = sample - self.mean
        self.m2 += delta * delta2

    @property
    def variance(self) -> np.ndarray:
        if self.count <= 1:
            return np.ones_like(self.mean)
        return self.m2 / (self.count - 1)


class _OnlineGaussianNB:
    """A light-weight Naive Bayes classifier trained incrementally."""

    def __init__(self, n_features: int, var_smoothing: float = 1e-6) -> None:
        self.n_features = n_features
        self.var_smoothing = var_smoothing
        self._classes: Dict[bool, _GaussianStats] = {}

    def partial_fit(self, x: np.ndarray, label: bool) -> None:
        stats = self._classes.get(label)
        if stats is None:
            stats = _GaussianStats(self.n_features)
            self._classes[label] = stats
        stats.update(x)

    def predict_proba(self, x: np.ndarray) -> float | None:
        if len(self._classes) < 2:
            return None

        total = sum(stats.count for stats in self._classes.values())
        if total == 0:
            return None

        log_probs: Dict[bool, float] = {}
        for label, stats in self._classes.items():
            if stats.count == 0:
                continue
            prior = stats.count / total
            var = stats.variance + self.var_smoothing
            log_likelihood = -0.5 * np.sum(
                np.log(2 * math.pi * var) + ((x - stats.mean) ** 2) / var
            )
            log_probs[label] = math.log(prior) + log_likelihood

        if len(log_probs) < 2:
            return None

        max_log = max(log_probs.values())
        exp_probs = {k: math.exp(v - max_log) for k, v in log_probs.items()}
        norm = sum(exp_probs.values())
        if norm == 0:
            return None
        return exp_probs.get(True, 0.0) / norm

    @property
    def ready(self) -> bool:
        return all(stats.count >= 3 for stats in self._classes.values())


class _RidgeRegressor:
    """Small ridge regressor solved via normal equations."""

    def __init__(self, n_features: int, ridge: float = 1e-5, min_samples: int = 6) -> None:
        self.n_features = n_features
        self.ridge = ridge
        self.min_samples = min_samples
        self._X: list[np.ndarray] = []
        self._y: list[float] = []
        self._coef: np.ndarray | None = None

    def add_sample(self, x: np.ndarray, y: float) -> None:
        self._X.append(np.append(x, 1.0))
        self._y.append(float(y))
        if len(self._X) >= self.min_samples:
            self._fit()

    def _fit(self) -> None:
        if not self._X or not self._y:
            return

        if len(self._X) != len(self._y):
            # Trim to the smallest consistent window if incremental updates raced.
            size = min(len(self._X), len(self._y))
            self._X = self._X[-size:]
            self._y = self._y[-size:]

        X = np.vstack(self._X)
        y = np.array(self._y, dtype=float)
        XtX = X.T @ X
        XtX += self.ridge * np.eye(XtX.shape[0])
        Xty = X.T @ y
        self._coef = np.linalg.solve(XtX, Xty)

    def predict(self, x: np.ndarray) -> float | None:
        if self._coef is None:
            return None
        ext = np.append(x, 1.0)
        return float(ext @ self._coef)

    @property
    def ready(self) -> bool:
        return self._coef is not None


def make_evaluator(base_model: Model) -> Callable[[Dict[str, float]], List[float]]:
    verifier = UppaalVerifier()
    constraints = getattr(base_model.optimisation, "constraints", [])

    bounds = variable_bounds(base_model.optimisation.variables)
    var_names = list(bounds.keys())
    ranges = {
        name: max(bounds[name][1] - bounds[name][0], 1e-9) for name in var_names
    }

    def _normalise(values: Dict[str, float]) -> np.ndarray:
        features = []
        for name in var_names:
            low, _ = bounds[name]
            rng = ranges[name]
            val = values.get(name, low)
            norm = (val - low) / rng
            norm = min(max(norm, 0.0), 1.0)
            features.append(norm)
        return np.array(features, dtype=float)

    timing_lock = Lock()
    timings = {
        "evaluate_total": 0.0,
        "evaluate_calls": 0,
        "verifyta_total": 0.0,
        "verifyta_calls": 0,
    }

    state_lock = Lock()
    state = {
        "total_evaluations": 0,
        "last_verified_eval": 0,
    }

    min_early_verifications = max(10, len(var_names) * 4)
    min_verify_ratio = 0.1
    max_skip_without_verify = 25

    def _register_evaluation() -> int:
        with state_lock:
            state["total_evaluations"] += 1
            return state["total_evaluations"]

    def _should_force_verify(eval_index: int) -> bool:
        with timing_lock:
            verify_calls = timings["verifyta_calls"]
        with state_lock:
            last_verified = state["last_verified_eval"]
            total_so_far = state["total_evaluations"]

        if verify_calls < min_early_verifications:
            return True

        if eval_index - last_verified >= max_skip_without_verify:
            return True

        completed = max(total_so_far, 1)
        ratio = verify_calls / completed
        return ratio < min_verify_ratio

    feasibility_filter = _OnlineGaussianNB(len(var_names))
    regressors: list[_RidgeRegressor] = []
    pareto_front: list[list[float]] = []
    obj_mins: list[float] = []
    obj_maxs: list[float] = []
    domination_margin = 0.02

    def _dominates(a: List[float], b: List[float], eps: float = 1e-9) -> bool:
        return all(x <= y + eps for x, y in zip(a, b)) and any(
            x < y - eps for x, y in zip(a, b)
        )

    def _update_pareto_front(point: List[float]) -> None:
        nonlocal pareto_front
        for existing in pareto_front:
            if _dominates(existing, point):
                return
        new_front: list[list[float]] = []
        for existing in pareto_front:
            if not _dominates(point, existing):
                new_front.append(existing)
        new_front.append(point)
        pareto_front = new_front

    def _predicted_dominated(predicted: List[float]) -> bool:
        if not pareto_front or not obj_mins or not obj_maxs:
            return False
        scales: list[float] = []
        for mn, mx in zip(obj_mins, obj_maxs):
            span = mx - mn
            base = max(abs(mn), 1.0)
            scales.append(span if span > 1e-6 else base)
        for reference in pareto_front:
            dominated = True
            for idx, (pred, ref) in enumerate(zip(predicted, reference)):
                margin = domination_margin * scales[idx]
                if pred + margin < ref:
                    dominated = False
                    break
            if dominated:
                return True
        return False

    def evaluate(values: Dict[str, float]) -> List[float]:
        nonlocal regressors, obj_mins, obj_maxs
        eval_index = _register_evaluation()
        start_eval = time.perf_counter()
        features = _normalise(values)

        try:
            if (

                    pareto_front
                    and regressors
                    and all(r.ready for r in regressors)
            ):
                predicted = [r.predict(features) for r in regressors]
                if all(p is not None for p in predicted) and _predicted_dominated(
                        [float(p) for p in predicted]
                ):
                    if not _should_force_verify(eval_index):
                        return [1e9, 1e9]

            if (
                    constraints
                    and feasibility_filter.ready
            ):
                proba = feasibility_filter.predict_proba(features)
                if proba is not None and proba < 0.25:
                    if not _should_force_verify(eval_index):
                        return [1e9, 1e9]

            assignments = {
                name: timedelta(milliseconds=v) for name, v in values.items()
            }
            candidate = apply_values(base_model, assignments)

            # Verify constraints via Uppaal
            feasible = True
            if constraints:
                verify_start = time.perf_counter()
                res = verifier.check(candidate, constraints)
                verify_elapsed = time.perf_counter() - verify_start
                with timing_lock:
                    timings["verifyta_total"] += verify_elapsed
                    timings["verifyta_calls"] += 1
                with state_lock:
                    state["last_verified_eval"] = eval_index
                feasible = not any(r is False or r is None for r in res.values())
                feasibility_filter.partial_fit(features, feasible)
                if not feasible:
                    return [1e9, 1e9]
            else:
                feasibility_filter.partial_fit(features, True)

            latency = _worst_end2end_latency(candidate)
            utilisation = _max_core_utilisation(candidate)
            objectives = [latency, utilisation]

            if not regressors:
                regressors = [_RidgeRegressor(len(var_names)) for _ in objectives]
                obj_mins = [float("inf")] * len(objectives)
                obj_maxs = [float("-inf")] * len(objectives)

            for idx, (reg, target) in enumerate(zip(regressors, objectives)):
                reg.add_sample(features, target)
                obj_mins[idx] = min(obj_mins[idx], target)
                obj_maxs[idx] = max(obj_maxs[idx], target)

            _update_pareto_front(objectives)
            return objectives
        finally:
            elapsed = time.perf_counter() - start_eval
            with timing_lock:
                timings["evaluate_total"] += elapsed
                timings["evaluate_calls"] += 1

    evaluate._timings = timings
    evaluate._timings_lock = timing_lock

    return evaluate


ALGORITHMS = {
    "nsga2": NSGAII,
    "sms-emoa": SMSEMOA,
    "qehvi": QEHVIOptimizer,
    "moead": MOEAD,
}


def main(path: str, generations: int = 500, algorithm: str = "nsga2"):
    model = load_model(path)
    if not hasattr(model, "optimisation"):
        raise ValueError("Model has no OPTIMISATION block")
    bounds = variable_bounds(model.optimisation.variables)

    evaluate = make_evaluator(model)

    algo_key = algorithm.lower()
    if algo_key not in ALGORITHMS:
        raise ValueError(
            f"Unknown optimisation algorithm '{algorithm}'. "
            f"Available options: {', '.join(sorted(ALGORITHMS))}"
        )

    algo_cls = ALGORITHMS[algo_key]
    algo = algo_cls(bounds, evaluate, generations=generations)
    population = algo.run()

    obj_specs = [
        (idx,
         _objective_name(raw),
         _objective_direction(raw))
        for idx, raw in enumerate(model.optimisation.objectives)
    ]

    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "Data" / "OptimOutput"
    out_dir.mkdir(parents=True, exist_ok=True)

    chosen_ids: set[int] = set()

    for idx, clean_name, direction in obj_specs:
        pop_sorted = sorted(
            population,
            key=lambda ind: ind.objectives[idx],
            reverse=(direction == "max"),
        )
        # pick the first Individual whose id we haven’t used yet
        best = next(
            (ind for ind in pop_sorted if _ind_id(ind) not in chosen_ids),
            None,
        )
        if best is None:
            if not pop_sorted:
                raise RuntimeError(
                    "Optimiser returned an empty population; cannot select winner"
                )
            best = pop_sorted[0]
        chosen_ids.add(_ind_id(best))

        assignments = {
            n: timedelta(milliseconds=v) for n, v in best.values.items()
        }
        candidate = apply_values(model, assignments)
        (out_dir / f"{clean_name}.adsl").write_text(
            emit_model(candidate), encoding="utf-8"
        )

    # Return best individual overall (rank 0, highest crowding distance)
    best = sorted(population, key=lambda x: (x.rank, -x.crowding_distance))[0]
    assignments = {n: timedelta(milliseconds=v) for n, v in best.values.items()}
    new_model = apply_values(model, assignments)
    return new_model, best


if __name__ == "__main__":
    m, ind = main("C:/Users/kaiwe/Documents/Master/Masterarbeit/Projekt/Data/DSLInput/Overtaking_Hard.adsl", generations=10, algorithm="nsga2")
    # print(m)
    print("Best individual:", ind.values, ind.objectives)
