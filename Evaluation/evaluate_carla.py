"""Evaluate CARLA overtaking scenarios across multiple spawn points.

This script executes a set of CARLA DSL scenarios and reports three metrics
per run:

* Deadline miss rate across all scheduled component activations.
* Pipeline latency miss rate for the overtaking chain
* Successful overtaking, determined by the absence of collision events.

"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from CARLA.behaviour.common import COLLISION_LOG_KEY, PIPELINE_LOG_KEY
from CARLA.executor import CarlaScenarioExecutor
from CARLA.json_loader import load_scenario
from CARLA.model import ScenarioSpec, SpawnPointSpec


LOGGER = logging.getLogger(__name__)

DEFAULT_INPUT_DIR = Path(Path(__file__).resolve().parents[1] / "Data" / "CARLAInput")
PIPELINE_STAGES: tuple[str, ...] = (
    "Perception_B",
    "AckHandler_A",
    "PermissionAckRx_B",
    "TrajectoryPlanner_B",
    "Controller_B",
)
PIPELINE_LATENCY_BOUND_S = 0.149

DEFAULT_SCENARIOS: list[str] = ["test3.json", "test3.json", "test3.json", "test3.json"]


@dataclass(slots=True)
class EvaluationResult:
    scenario_name: str
    scenario_path: Path
    spawn_index: int
    deadline_miss_rate: float
    deadline_misses: int
    deadline_activations: int
    pipeline_miss_rate: float
    pipeline_misses: int
    pipeline_requests: int
    pipeline_details: List[Dict[str, Any]]
    collisions: List[Dict[str, Any]]

    @property
    def successful(self) -> bool:
        return not self.collisions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario": self.scenario_name,
            "scenario_path": str(self.scenario_path),
            "spawn_index": self.spawn_index,
            "deadline_miss_rate": self.deadline_miss_rate,
            "deadline_misses": self.deadline_misses,
            "deadline_activations": self.deadline_activations,
            "pipeline_miss_rate": self.pipeline_miss_rate,
            "pipeline_misses": self.pipeline_misses,
            "pipeline_requests": self.pipeline_requests,
            "pipeline_details": self.pipeline_details,
            "collisions": self.collisions,
            "successful_overtake": self.successful,
        }


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "scenarios",
        metavar="SCENARIO",
        nargs="*",
        default=[],
        help=(
            "Scenario identifiers or JSON paths under Data/CARLAInput. "
            "Specify four entries to evaluate."
        ),
    )
    parser.add_argument(
        "--spawn",
        dest="spawn_points",
        metavar="INDEX",
        nargs=3,
        type=int,
        default=[10, 47, 123],
        help=(
            "Three spawn point indices for vehicle A (map_point values). "
        ),
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory containing scenario JSON files (default: Data/CARLAInput)",
    )
    parser.add_argument("--host", default="localhost", help="CARLA server host")
    parser.add_argument("--port", type=int, default=2000, help="CARLA server port")
    parser.add_argument(
        "--timeout",
        type=float,
        default=300.0,
        help="CARLA client timeout in seconds",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Maximum simulation duration in seconds per run",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Optional maximum number of simulation steps per run",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Write the evaluation summary to the specified JSON file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity",
    )
    args = parser.parse_args(argv)

    if not args.scenarios:
        args.scenarios = list(DEFAULT_SCENARIOS)

    return args


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def resolve_scenario(identifier: str, base_dir: Path) -> Path:
    path = Path(identifier)
    if path.is_file():
        return path.resolve()

    if not path.suffix:
        candidate = base_dir / f"{identifier}.json"
        if candidate.is_file():
            return candidate.resolve()

    candidate = base_dir / identifier
    if candidate.is_file():
        return candidate.resolve()

    raise FileNotFoundError(
        f"Unable to locate scenario '{identifier}'. Expected a JSON file in {base_dir}."
    )


def prepare_scenario(scenario_path: Path, spawn_index: int) -> ScenarioSpec:
    scenario = load_scenario(scenario_path)
    vehicle_a = scenario.vehicle_by_name("A")
    vehicle_b = scenario.vehicle_by_name("B")

    if vehicle_a is None:
        raise ValueError(f"Scenario '{scenario_path}' does not define vehicle 'A'")
    vehicle_a.spawn = SpawnPointSpec(map_point=int(spawn_index))

    if vehicle_b is None:
        raise ValueError(f"Scenario '{scenario_path}' does not define vehicle 'B'")
    vehicle_b.spawn = SpawnPointSpec(reference_vehicle="A", delay_seconds=8.0)

    return scenario


def run_scenario(
    scenario: ScenarioSpec,
    *,
    host: str,
    port: int,
    timeout: float,
    duration: float,
    max_steps: Optional[int],
) -> None:
    executor = CarlaScenarioExecutor(scenario, host=host, port=port, timeout=timeout)
    try:
        executor.setup()
        executor.run(duration_seconds=duration, max_steps=max_steps)
    finally:
        executor.teardown()


def compute_deadline_metrics(scenario: ScenarioSpec) -> tuple[float, int, int]:
    registry = scenario.properties.get("_component_timing")
    total_misses = 0
    total_activations = 0
    if isinstance(registry, dict):
        for stats in registry.values():
            if not isinstance(stats, dict):
                continue
            try:
                activations = int(stats.get("activation_count") or 0)
                misses = int(stats.get("deadline_misses") or 0)
            except (TypeError, ValueError):
                continue
            total_activations += activations
            total_misses += misses

    rate = (total_misses / total_activations) if total_activations else 0.0
    return rate, total_misses, total_activations


def compute_pipeline_metrics(
    scenario: ScenarioSpec,
    *,
    latency_bound_s: float,
) -> tuple[float, int, int, List[Dict[str, Any]]]:
    registry = scenario.properties.get(PIPELINE_LOG_KEY)
    raw_events: List[Dict[str, Any]] = []
    if isinstance(registry, dict):
        events = registry.get("events")
        if isinstance(events, list):
            raw_events = [event for event in events if isinstance(event, dict)]

    stage_times: Dict[int, Dict[str, float]] = {}
    for event in raw_events:
        try:
            request_id = int(event.get("request_id"))
        except (TypeError, ValueError):
            continue
        stage = event.get("stage")
        if stage not in PIPELINE_STAGES:
            continue
        try:
            timestamp = float(event.get("time"))
        except (TypeError, ValueError):
            continue
        stages = stage_times.setdefault(request_id, {})
        if stage not in stages or timestamp < stages[stage]:
            stages[stage] = timestamp

    total_requests = len(stage_times)
    misses = 0
    details: List[Dict[str, Any]] = []

    for request_id, stages in sorted(stage_times.items()):
        missing = [stage for stage in PIPELINE_STAGES if stage not in stages]
        if missing:
            misses += 1
            details.append(
                {
                    "request_id": request_id,
                    "latency_s": None,
                    "deadline_missed": True,
                    "missing_stages": missing,
                }
            )
            continue

        latency = stages[PIPELINE_STAGES[-1]] - stages[PIPELINE_STAGES[0]]
        deadline_missed = latency > latency_bound_s + 1e-9
        if deadline_missed:
            misses += 1
        details.append(
            {
                "request_id": request_id,
                "latency_s": latency,
                "deadline_missed": deadline_missed,
                "missing_stages": [],
            }
        )

    rate = (misses / total_requests) if total_requests else 0.0
    return rate, misses, total_requests, details


def collect_collision_events(scenario: ScenarioSpec) -> List[Dict[str, Any]]:
    raw_events = scenario.properties.get(COLLISION_LOG_KEY)
    collisions: List[Dict[str, Any]] = []
    if not isinstance(raw_events, list):
        return collisions

    for event in raw_events:
        if not isinstance(event, dict):
            continue
        entry: Dict[str, Any] = {}
        entry["vehicle"] = event.get("vehicle")
        entry["component"] = event.get("component")
        try:
            entry["time"] = float(event.get("time"))
        except (TypeError, ValueError):
            entry["time"] = None
        if "other_actor" in event:
            entry["other_actor"] = event.get("other_actor")
        collisions.append(entry)

    return collisions


def evaluate_run(
    scenario_path: Path,
    spawn_index: int,
    *,
    host: str,
    port: int,
    timeout: float,
    duration: float,
    max_steps: Optional[int],
) -> EvaluationResult:
    scenario = prepare_scenario(scenario_path, spawn_index)
    LOGGER.info(
        "Running scenario '%s' with spawn index %s",
        scenario.name,
        spawn_index,
    )
    run_scenario(
        scenario,
        host=host,
        port=port,
        timeout=timeout,
        duration=duration,
        max_steps=max_steps,
    )

    deadline_rate, deadline_misses, deadline_activations = compute_deadline_metrics(scenario)
    pipeline_rate, pipeline_misses, pipeline_total, pipeline_details = compute_pipeline_metrics(
        scenario, latency_bound_s=PIPELINE_LATENCY_BOUND_S
    )
    collisions = collect_collision_events(scenario)

    return EvaluationResult(
        scenario_name=scenario.name,
        scenario_path=scenario_path,
        spawn_index=spawn_index,
        deadline_miss_rate=deadline_rate,
        deadline_misses=deadline_misses,
        deadline_activations=deadline_activations,
        pipeline_miss_rate=pipeline_rate,
        pipeline_misses=pipeline_misses,
        pipeline_requests=pipeline_total,
        pipeline_details=pipeline_details,
        collisions=collisions,
    )


def print_summary(results: Iterable[EvaluationResult]) -> None:
    results = list(results)
    if not results:
        LOGGER.warning("No evaluation results to summarise")
        return

    header = (
        "Scenario",
        "Spawn",
        "Deadline Miss Rate",
        "Deadline Misses/Activations",
        "Pipeline Miss Rate",
        "Pipeline Misses/Requests",
        "Successful",
    )
    print(" | ".join(header))
    print("-" * 110)

    total_deadline_misses = 0
    total_deadline_activations = 0
    total_pipeline_misses = 0
    total_pipeline_requests = 0

    for result in results:
        total_deadline_misses += result.deadline_misses
        total_deadline_activations += result.deadline_activations
        total_pipeline_misses += result.pipeline_misses
        total_pipeline_requests += result.pipeline_requests

        deadline_ratio = (
            f"{result.deadline_misses}/{result.deadline_activations}" if result.deadline_activations else "0/0"
        )
        pipeline_ratio = (
            f"{result.pipeline_misses}/{result.pipeline_requests}" if result.pipeline_requests else "0/0"
        )
        print(
            f"{result.scenario_name} | {result.spawn_index} | "
            f"{result.deadline_miss_rate:.4f} | {deadline_ratio} | "
            f"{result.pipeline_miss_rate:.4f} | {pipeline_ratio} | "
            f"{'yes' if result.successful else 'no'}"
        )

    overall_deadline_rate = (
        (total_deadline_misses / total_deadline_activations)
        if total_deadline_activations
        else 0.0
    )
    overall_pipeline_rate = (
        (total_pipeline_misses / total_pipeline_requests)
        if total_pipeline_requests
        else 0.0
    )

    print("-" * 110)
    print(
        "OVERALL | - | "
        f"{overall_deadline_rate:.4f} | {total_deadline_misses}/{total_deadline_activations or 0} | "
        f"{overall_pipeline_rate:.4f} | {total_pipeline_misses}/{total_pipeline_requests or 0} | "
        "-"
    )


def write_json_report(path: Path, results: Iterable[EvaluationResult]) -> None:
    payload = [result.to_dict() for result in results]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LOGGER.info("Wrote evaluation report to %s", path)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    configure_logging(args.log_level)

    scenario_paths = [resolve_scenario(identifier, args.base_dir) for identifier in args.scenarios]
    results: List[EvaluationResult] = []

    for scenario_path in scenario_paths:
        for spawn_index in args.spawn_points:
            try:
                result = evaluate_run(
                    scenario_path,
                    spawn_index,
                    host=args.host,
                    port=args.port,
                    timeout=args.timeout,
                    duration=args.duration,
                    max_steps=args.max_steps,
                )
            except Exception:  # pragma: no cover - runtime interaction with CARLA
                LOGGER.exception(
                    "Failed to evaluate scenario '%s' at spawn index %s",
                    scenario_path,
                    spawn_index,
                )
                continue
            results.append(result)

    print_summary(results)

    if args.output_json:
        write_json_report(args.output_json, results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())