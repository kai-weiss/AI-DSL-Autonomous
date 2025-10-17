from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from .model import (
    ComponentSpec,
    ConnectionSpec,
    LocationSpec,
    RotationSpec,
    ScenarioSpec,
    SpawnPointSpec,
    VehicleSpec,
    WorldSettingsSpec,
)

LOGGER = logging.getLogger(__name__)


def load_scenario(source: str | Path | Mapping[str, Any]) -> ScenarioSpec:
    """Load a :class:`ScenarioSpec` from a JSON document or path."""

    if isinstance(source, Mapping):
        data = dict(source)
        base_path = Path(".")
    else:
        path = Path(source)
        base_path = path.parent
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)

    name = data.get("system") or data.get("system_name") or "Scenario"
    properties = _normalise_properties(data.get("properties") or {})

    components = _parse_components(data.get("components"))
    vehicles = _parse_vehicles(
        data.get("vehicles"),
        data.get("vehicle_order"),
        components,
        properties,
        data.get("carla", {}).get("vehicles", {}),
    )

    connections = _parse_connections(data.get("connections") or [])
    world = _parse_world_settings(
        data.get("world"), properties, data.get("carla", {}).get("world"), base_path
    )

    return ScenarioSpec(
        name=name,
        vehicles=vehicles,
        connections=connections,
        world=world,
        properties=properties,
    )


def _normalise_properties(raw: Any) -> Dict[str, str]:
    if isinstance(raw, Mapping):
        return {str(k): str(v) for k, v in raw.items()}
    LOGGER.debug("Ignoring non-mapping properties payload: %s", raw)
    return {}


def _parse_components(raw: Any) -> Dict[str, ComponentSpec]:
    components: Dict[str, ComponentSpec] = {}
    if isinstance(raw, Mapping):
        iterable: Iterable[tuple[str, Any]] = raw.items()
    elif isinstance(raw, list):
        iterable = []
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            name = item.get("name")
            if not isinstance(name, str):
                continue
            iterable.append((name, item))  # type: ignore[arg-type]
    else:
        LOGGER.debug("No components section found in JSON export")
        return components

    for name, payload in iterable:
        if not isinstance(payload, Mapping):
            LOGGER.warning("Component '%s' payload is not a mapping: %s", name, payload)
            continue
        components[name] = _component_from_payload(name, payload)
    return components


def _component_from_payload(name: str, payload: Mapping[str, Any]) -> ComponentSpec:
    period = _parse_duration(payload.get("period"))
    deadline = _parse_duration(payload.get("deadline"))
    wcet = _parse_duration(payload.get("wcet"))
    priority = _parse_int(payload.get("priority"))
    behaviour = payload.get("behaviour") or payload.get("behavior")
    vehicle = payload.get("vehicle")

    config: Dict[str, Any] = {}
    if isinstance(payload.get("config"), Mapping):
        config.update(payload["config"])  # type: ignore[index]

    known_keys = {"name", "period", "deadline", "wcet", "priority", "behaviour", "behavior", "vehicle", "config"}
    for key, value in payload.items():
        if key in known_keys:
            continue
        config[key] = value

    return ComponentSpec(
        name=name,
        period=period,
        deadline=deadline,
        wcet=wcet,
        priority=priority,
        behaviour=str(behaviour) if behaviour else None,
        config=config,
        vehicle=str(vehicle) if vehicle else None,
    )


def _parse_connections(raw: Any) -> list[ConnectionSpec]:
    connections: list[ConnectionSpec] = []
    if not isinstance(raw, Iterable):
        LOGGER.debug("No connections section found in JSON export")
        return connections

    for item in raw:
        if not isinstance(item, Mapping):
            LOGGER.warning("Skipping non-mapping connection entry: %s", item)
            continue
        name = item.get("name") or "connection"
        src = item.get("src") or item.get("source")
        dst = item.get("dst") or item.get("target")
        if not isinstance(src, str) or not isinstance(dst, str):
            LOGGER.warning("Connection '%s' missing endpoints: %s", name, item)
            continue
        latency = _parse_duration(item.get("latency_budget") or item.get("latency"))
        connections.append(
            ConnectionSpec(
                name=str(name),
                src=src,
                dst=dst,
                latency_budget=latency,
            )
        )
    return connections


def _parse_vehicles(
    raw: Any,
    order: Any,
    components: Dict[str, ComponentSpec],
    properties: Dict[str, str],
    carla_cfg: Any,
) -> list[VehicleSpec]:
    vehicles: list[VehicleSpec] = []
    order_list: list[str] = []
    if isinstance(order, list):
        order_list = [str(item) for item in order if isinstance(item, str)]

    raw_mapping: Dict[str, Any] = {}
    if isinstance(raw, Mapping):
        raw_mapping = {str(k): v for k, v in raw.items()}
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            name = item.get("name")
            if not isinstance(name, str):
                continue
            raw_mapping[name] = item
    else:
        LOGGER.debug("No vehicles section found in JSON export")

    # Ensure deterministic iteration order
    if not order_list:
        order_list = list(raw_mapping)

    for vehicle_name in order_list:
        payload = raw_mapping.get(vehicle_name, {})
        spec = _vehicle_from_payload(
            vehicle_name,
            payload,
            components,
            properties,
            carla_cfg.get(vehicle_name) if isinstance(carla_cfg, Mapping) else None,
        )
        vehicles.append(spec)

    # pick up any vehicles that were not in the declared order
    remaining = set(raw_mapping) - set(order_list)
    for vehicle_name in sorted(remaining):
        payload = raw_mapping[vehicle_name]
        spec = _vehicle_from_payload(
            vehicle_name,
            payload,
            components,
            properties,
            carla_cfg.get(vehicle_name) if isinstance(carla_cfg, Mapping) else None,
        )
        vehicles.append(spec)

    # For components that declare a vehicle but the vehicle has no explicit entry
    declared = {spec.name for spec in vehicles}
    orphan_components = [c for c in components.values() if c.vehicle and c.vehicle not in declared]
    for component in orphan_components:
        spec = VehicleSpec(name=component.vehicle, components=[component])
        _apply_vehicle_overrides(spec, properties, None)
        vehicles.append(spec)

    # Add components that were not assigned to any vehicle block
    assigned_components = {
        component.name
        for vehicle in vehicles
        for component in vehicle.components
    }
    for component in components.values():
        if component.name in assigned_components:
            continue
        fallback_name = component.vehicle or "Standalone"
        existing = next((v for v in vehicles if v.name == fallback_name), None)
        if existing is None:
            existing = VehicleSpec(name=fallback_name)
            _apply_vehicle_overrides(existing, properties, None)
            vehicles.append(existing)
        existing.components.append(component)

    return vehicles


def _vehicle_from_payload(
    name: str,
    payload: Any,
    components: Dict[str, ComponentSpec],
    properties: Dict[str, str],
    extra_cfg: Any,
) -> VehicleSpec:
    component_names: list[str] = []
    blueprint: str | None = None
    autopilot = False
    metadata: Dict[str, Any] = {}
    spawn_spec: SpawnPointSpec | None = None

    if isinstance(payload, Mapping):
        raw_components = payload.get("components")
        if isinstance(raw_components, list):
            for entry in raw_components:
                if isinstance(entry, str):
                    component_names.append(entry)
                elif isinstance(entry, Mapping) and isinstance(entry.get("name"), str):
                    component_names.append(entry["name"])
        elif isinstance(raw_components, Mapping):
            component_names.extend(str(k) for k in raw_components.keys())
        blueprint = payload.get("blueprint")
        autopilot = _parse_bool(payload.get("autopilot"))
        metadata = {
            str(k): v
            for k, v in payload.items()
            if k
            not in {
                "name",
                "components",
                "blueprint",
                "autopilot",
                "spawn_point",
                "spawn",
            }
        }
        spawn_spec = _parse_spawn_point(
            payload.get("spawn_point") if "spawn_point" in payload else payload.get("spawn")
        )

    # Merge in components that reference this vehicle by name
    if not component_names:
        component_names = [comp_name for comp_name, comp in components.items() if comp.vehicle == name]

    attached_components = [components[c] for c in component_names if c in components]

    spec = VehicleSpec(
        name=name,
        components=attached_components,
        blueprint=str(blueprint) if blueprint else None,
        autopilot=autopilot,
        metadata=metadata,
        spawn=spawn_spec,
    )

    _apply_vehicle_overrides(spec, properties, extra_cfg)
    return spec


def _apply_vehicle_overrides(
    vehicle: VehicleSpec,
    properties: Dict[str, str],
    extra_cfg: Any,
) -> None:
    prefix = f"carla.vehicle.{vehicle.name}."
    for key, value in properties.items():
        if key.lower().startswith(prefix.lower()):
            suffix = key[len(prefix) :]
            _assign_vehicle_property(vehicle, suffix, value)

    if isinstance(extra_cfg, Mapping):
        for key, value in extra_cfg.items():
            _assign_vehicle_property(vehicle, str(key), value)


def _assign_vehicle_property(vehicle: VehicleSpec, key: str, value: Any) -> None:
    key_lower = key.lower()
    if key_lower == "blueprint":
        vehicle.blueprint = str(value)
    elif key_lower == "autopilot":
        vehicle.autopilot = _parse_bool(value)
    elif key_lower in {"spawn_point", "spawn"}:
        vehicle.spawn = _parse_spawn_point(value)
    else:
        vehicle.metadata[key] = value


def _parse_world_settings(
    raw: Any,
    properties: Dict[str, str],
    carla_cfg: Any,
    base_path: Path,
) -> WorldSettingsSpec:
    map_name = None
    synchronous_mode = True
    fixed_delta = None
    weather: Dict[str, float] = {}

    if isinstance(raw, Mapping):
        map_name = raw.get("map") or raw.get("map_name") or map_name
        synchronous_mode = _parse_bool(raw.get("synchronous_mode"), default=True)
        fixed_delta = _parse_float(raw.get("fixed_delta_seconds"))
        weather = _parse_weather(raw.get("weather"))

    if isinstance(carla_cfg, Mapping):
        map_name = carla_cfg.get("map") or carla_cfg.get("map_name") or map_name
        synchronous_mode = _parse_bool(
            carla_cfg.get("synchronous_mode"), default=synchronous_mode
        )
        fixed_delta = _parse_float(carla_cfg.get("fixed_delta_seconds")) or fixed_delta
        if "weather" in carla_cfg:
            weather.update(_parse_weather(carla_cfg.get("weather")))

    for key, value in properties.items():
        lower = key.lower()
        if lower in {"carla.map", "carla.world.map", "carla.world.map_name"}:
            map_name = str(value)
        elif lower == "carla.world.synchronous_mode":
            synchronous_mode = _parse_bool(value, default=synchronous_mode)
        elif lower == "carla.world.fixed_delta_seconds":
            parsed = _parse_float(value)
            if parsed is not None:
                fixed_delta = parsed
        elif lower.startswith("carla.weather."):
            weather_key = key.split(".", 2)[-1]
            parsed = _parse_float(value)
            if parsed is not None:
                weather[weather_key] = parsed

    if isinstance(map_name, str) and map_name.endswith(".xodr"):
        potential = base_path / map_name
        if potential.exists():
            map_name = str(potential)

    return WorldSettingsSpec(
        map_name=str(map_name) if map_name else None,
        synchronous_mode=synchronous_mode,
        fixed_delta_seconds=fixed_delta,
        weather=weather,
    )


def _parse_duration(value: Any) -> timedelta | None:
    if value is None:
        return None
    if isinstance(value, timedelta):
        return value
    if isinstance(value, (int, float)):
        return timedelta(milliseconds=float(value))
    if isinstance(value, str):
        text = value.strip().lower()
        if text.endswith("ms"):
            return timedelta(milliseconds=float(text[:-2]))
        if text.endswith("s"):
            return timedelta(seconds=float(text[:-1]))
        if text.endswith("us"):
            return timedelta(microseconds=float(text[:-2]))
        # generic fallback: interpret as milliseconds if numeric
        try:
            return timedelta(milliseconds=float(text))
        except ValueError:  # pragma: no cover - logged for debugging
            LOGGER.warning("Unable to parse duration '%s'", value)
            return None
    if isinstance(value, Mapping):
        if "ms" in value:
            return timedelta(milliseconds=float(value["ms"]))
        if "seconds" in value:
            return timedelta(seconds=float(value["seconds"]))
        if "microseconds" in value:
            return timedelta(microseconds=float(value["microseconds"]))
    LOGGER.warning("Unsupported duration payload: %s", value)
    return None


def _parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "yes", "on", "1"}:
            return True
        if text in {"false", "no", "off", "0"}:
            return False
    return default


def _parse_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _parse_weather(value: Any) -> Dict[str, float]:
    weather: Dict[str, float] = {}
    if isinstance(value, Mapping):
        for key, val in value.items():
            parsed = _parse_float(val)
            if parsed is not None:
                weather[str(key)] = parsed
    return weather


def _parse_spawn_point(value: Any) -> SpawnPointSpec | None:
    if value is None:
        return None
    if isinstance(value, SpawnPointSpec):
        return value
    if isinstance(value, int):
        return SpawnPointSpec(index=value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("index:"):
            index_text = text.split(":", 1)[1]
            parsed = _parse_int(index_text)
            if parsed is not None:
                return SpawnPointSpec(index=parsed)
        if text.startswith("map_point:"):
            map_point_text = text.split(":", 1)[1]
            parsed = _parse_int(map_point_text)
            if parsed is not None:
                return SpawnPointSpec(map_point=parsed)
        parts: Dict[str, float] = {}
        int_parts: Dict[str, int] = {}
        for piece in text.split(","):
            if "=" not in piece:
                continue
            key, raw = piece.split("=", 1)
            key = key.strip().lower()
            raw = raw.strip()
            if key in {"index", "map_point"}:
                parsed_int = _parse_int(raw)
                if parsed_int is not None:
                    int_parts[key] = parsed_int
                continue
            parsed = _parse_float(raw)
            if parsed is not None:
                parts[key] = parsed
        if parts or int_parts:
            loc = None
            rot = None
            if any(k in parts for k in {"x", "y", "z"}):
                loc = LocationSpec(
                    x=parts.get("x", 0.0),
                    y=parts.get("y", 0.0),
                    z=parts.get("z", 0.0),
                )
            if any(k in parts for k in {"pitch", "yaw", "roll"}):
                rot = RotationSpec(
                    pitch=parts.get("pitch", 0.0),
                    yaw=parts.get("yaw", 0.0),
                    roll=parts.get("roll", 0.0),
                )
            return SpawnPointSpec(
                index=int_parts.get("index"),
                map_point=int_parts.get("map_point"),
                location=loc,
                rotation=rot,
            )
        return None
    if isinstance(value, Mapping):
        index = _parse_int(value.get("index"))
        map_point = _parse_int(value.get("map_point"))
        loc_val = value.get("location")
        rot_val = value.get("rotation")
        if isinstance(loc_val, Mapping):
            loc = LocationSpec(
                x=_parse_float(loc_val.get("x")) or 0.0,
                y=_parse_float(loc_val.get("y")) or 0.0,
                z=_parse_float(loc_val.get("z")) or 0.0,
            )
        else:
            loc = None
        if isinstance(rot_val, Mapping):
            rot = RotationSpec(
                pitch=_parse_float(rot_val.get("pitch")) or 0.0,
                yaw=_parse_float(rot_val.get("yaw")) or 0.0,
                roll=_parse_float(rot_val.get("roll")) or 0.0,
            )
        else:
            rot = None
        if index is None and map_point is None and not loc and not rot:
            return None
        return SpawnPointSpec(index=index, map_point=map_point, location=loc, rotation=rot)
    return None