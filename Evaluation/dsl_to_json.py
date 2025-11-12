"""Convert scenario DSL files into CARLA JSON inputs."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict
from DSL import parser as dsl_parser
from DSL.visitor import ASTBuilder

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Default template information derived from existing CARLA input examples.
DEFAULT_WORLD = {
    "map": "Town10HD_Opt",
    "synchronous_mode": True,
    "fixed_delta_seconds": 0.05,
}

DEFAULT_VEHICLE_BLUEPRINTS = {
    "A": "vehicle.mini.cooper",
    "B": "vehicle.lincoln.mkz",
}

DEFAULT_VEHICLE_SPAWNS: dict[str, dict[str, Any]] = {
    "A": {"map_point": 7},
    "B": {"like_vehicle": "A", "delay": 8.0},
}

DEFAULT_VEHICLE_SETUP_COMPONENTS: dict[str, dict[str, Any]] = {
    "A": {
        "name": "Setup_A",
        "vehicle": "A",
        "behaviour": "tm_autopilot_setup_A",
        "config": {"ignore_lights_percentage": 0},
    },
    "B": {
        "name": "Setup_B",
        "vehicle": "B",
        "behaviour": "tm_autopilot_setup_B",
        "config": {"ignore_lights_percentage": 0},
    },
}

# Known behaviour mappings for components.
COMPONENT_BEHAVIOURS: dict[str, dict[str, Any]] = {
    "Setup_A": {"behaviour": "tm_autopilot_setup_A", "config": {"ignore_lights_percentage": 0}},
    "Setup_B": {"behaviour": "tm_autopilot_setup_B", "config": {"ignore_lights_percentage": 0}},
    "InteriorLight_A": {"behaviour": "interior_light"},
    "Perception_A": {"behaviour": "autopilot"},
    "AckHandler_A": {"behaviour": "ack_handler"},
    "Crash_B": {"behaviour": "emergency_stop"},
    "Perception_B": {"behaviour": "autopilot"},
    "PermissionReqTx_B": {"behaviour": "request_permission"},
    "PermissionAckRx_B": {"behaviour": "permission_ack_receiver"},
    "TrajectoryPlanner_B": {"behaviour": "tm_overtake_on_ack"},
    "Controller_B": {"behaviour": "constant_velocity"},
}


def _timedelta_to_ms(value: timedelta | None) -> str | None:
    if value is None:
        return None
    milliseconds = int(value.total_seconds() * 1000)
    return f"{milliseconds}ms"


def build_json_model(model) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    """Translate the intermediate DSL model into the CARLA JSON schema."""
    vehicles: Dict[str, Dict[str, Any]] = {}
    for vehicle in model.vehicle_order:
        components = model.vehicles.get(vehicle, [])
        if vehicle in DEFAULT_VEHICLE_SETUP_COMPONENTS:
            setup_name = DEFAULT_VEHICLE_SETUP_COMPONENTS[vehicle]["name"]
            if setup_name not in components:
                components = [setup_name, *components]
        vehicles[vehicle] = {
            "blueprint": DEFAULT_VEHICLE_BLUEPRINTS.get(vehicle, "vehicle.audi.a2"),
            "autopilot": False,
            "spawn": DEFAULT_VEHICLE_SPAWNS.get(vehicle, {"map_point": 0}).copy(),
            "components": components,
        }

    components_json: list[Dict[str, Any]] = []
    seen_names: set[str] = set()
    for comp in model.components.values():
        entry: Dict[str, Any] = {"name": comp.name}
        if comp.vehicle:
            entry["vehicle"] = comp.vehicle
        behaviour = COMPONENT_BEHAVIOURS.get(comp.name)
        if behaviour:
            entry.update({k: v for k, v in behaviour.items() if k != "config"})
            if "config" in behaviour:
                entry["config"] = behaviour["config"].copy()
        else:
            entry["behaviour"] = "generic_component"

        if period := _timedelta_to_ms(comp.period):
            entry["period"] = period
        if deadline := _timedelta_to_ms(comp.deadline):
            entry["deadline"] = deadline
        if wcet := _timedelta_to_ms(comp.wcet):
            entry["wcet"] = wcet
        if comp.priority is not None:
            entry["priority"] = comp.priority
        components_json.append(entry)
        seen_names.add(entry["name"])

    for vehicle, setup in DEFAULT_VEHICLE_SETUP_COMPONENTS.items():
        if setup["name"] in seen_names:
            continue
        entry = {k: (v.copy() if isinstance(v, dict) else v) for k, v in setup.items()}
        components_json.append(entry)
        seen_names.add(setup["name"])

    connections_json = []
    for conn in model.connections:
        entry = {
            "name": conn.name,
            "src": conn.src,
            "dst": conn.dst,
        }
        if conn.latency_budget is not None:
            entry["latency_budget"] = _timedelta_to_ms(conn.latency_budget)
        connections_json.append(entry)

    return {
        "system": model.system_name,
        "world": DEFAULT_WORLD.copy(),
        "vehicles": vehicles,
        "components": components_json,
        "connections": connections_json,
    }


def convert_file(dsl_path: Path, output_path: Path) -> Path:
    source = dsl_path.read_text(encoding="utf-8")
    tree = dsl_parser.parse_source(source)
    builder = ASTBuilder()
    builder.visit(tree)

    json_model = build_json_model(builder.model)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(json_model, indent=2) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert DSL scenario files to CARLA JSON inputs.")
    parser.add_argument("dsl_file",
                        nargs="?",
                        default=Path("../Data/DSLInput/Overtaking_Hard.adsl"),
                        help="Path to the .adsl file to convert")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output path (directory or file). Defaults to Data/CARLAInput/<scenario>.json",
    )
    args = parser.parse_args()

    dsl_path = args.dsl_file
    if not dsl_path.exists():
        raise FileNotFoundError(f"DSL file not found: {dsl_path}")

    if args.output is None or args.output.is_dir():
        output_dir = args.output if args.output else Path("../Data/CARLAInput")
        output_path = output_dir / (dsl_path.stem + ".json")
    else:
        output_path = args.output

    result_path = convert_file(dsl_path, output_path)
    print(f"Generated {result_path}")


if __name__ == "__main__":
    main()
