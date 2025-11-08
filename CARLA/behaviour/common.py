from __future__ import annotations

import logging
import math
from typing import Any, Dict, Iterable, List, Optional


from ..model import ComponentSpec
from .base import ComponentContext

import carla
from ..connections import ConnectionDelivery, ConnectionManager

LOGGER = logging.getLogger(__name__)

VEHICLE_REGISTRY_KEY = "_vehicle_actor_ids"
TRAFFIC_MANAGER_PORTS_KEY = "_traffic_manager_ports"
TRAFFIC_MANAGER_CACHE_KEY = "_traffic_manager_cache"
CARLA_CLIENT_PROPERTY = "_carla_client"
OVERTAKE_STATE_KEY = "_overtake_state"
OVERTAKE_REQUEST_KEY = "overtake_request"
OVERTAKE_ACK_KEY = "permission_ack"
COMPONENT_OUTPUTS_KEY = "_component_outputs"


def component_full_name(component: ComponentSpec) -> str:
    if component.vehicle:
        return f"{component.vehicle}.{component.name}"
    return component.name


def connections_by_src(component: ComponentSpec, scenario: Any) -> Iterable[Any]:
    full_name = component_full_name(component)
    for connection in getattr(scenario, "connections", []):
        if getattr(connection, "src", None) == full_name:
            yield connection


def component_output_buffer(context: ComponentContext) -> list[Any]:
    """Return the mutable output queue for the active component."""

    properties = getattr(context.scenario, "properties", None)
    if not isinstance(properties, dict):
        raise AttributeError("Scenario properties must be a mapping to use component outputs")

    outputs = properties.get(COMPONENT_OUTPUTS_KEY)
    if not isinstance(outputs, dict):
        outputs = {}
        properties[COMPONENT_OUTPUTS_KEY] = outputs

    component_name = component_full_name(context.component_spec)
    queue = outputs.get(component_name)
    if not isinstance(queue, list):
        queue = []
        outputs[component_name] = queue
    return queue


def timedelta_to_seconds(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value.total_seconds())
    except AttributeError:
        return None

def _resolve_connection_manager(context: ComponentContext) -> "ConnectionManager | None":
    manager = getattr(context, "connection_manager", None)
    if manager is None:
        LOGGER.debug(
            "Connection manager unavailable for component '%s'", context.component_spec.name
        )
    return manager


def emit_connection_event(
    context: ComponentContext,
    payload: Any,
    connection_name: str | None = None,
) -> None:
    manager = _resolve_connection_manager(context)
    if manager is None:
        return
    manager.send(context.component_spec, payload, context.sim_time, connection_name=connection_name)


def consume_connection_events(
    context: ComponentContext,
    connection_name: str | None = None,
) -> List["ConnectionDelivery"]:
    manager = _resolve_connection_manager(context)
    if manager is None:
        return []
    return manager.consume(context.component_spec, connection_name)


def ensure_overtake_state(context: ComponentContext) -> Dict[str, Any]:
    state = context.scenario.properties.setdefault(OVERTAKE_STATE_KEY, {})
    if "phase" not in state:
        state["phase"] = "idle"
    return state


def _vehicle_actor_id(context: ComponentContext, vehicle_name: str) -> Optional[int]:
    registry = context.scenario.properties.get(VEHICLE_REGISTRY_KEY)
    if not isinstance(registry, dict):
        return None
    actor_id = registry.get(vehicle_name)
    if actor_id is None:
        return None
    try:
        return int(actor_id)
    except (TypeError, ValueError):
        return None


def resolve_vehicle_actor(context: ComponentContext, vehicle_name: str):
    actor_id = _vehicle_actor_id(context, vehicle_name)
    if actor_id is None:
        return None
    world = context.world
    if world is None:
        return None
    get_actor = getattr(world, "get_actor", None)
    if not callable(get_actor):
        return None
    try:
        return get_actor(actor_id)
    except Exception:  # pragma: no cover - depends on CARLA API
        LOGGER.exception("Failed to resolve CARLA actor for vehicle '%s'", vehicle_name)
        return None


def traffic_manager_registry(context: ComponentContext) -> Dict[str, Any]:
    registry = context.scenario.properties.setdefault(TRAFFIC_MANAGER_CACHE_KEY, {})
    if not isinstance(registry, dict):
        registry = {}
        context.scenario.properties[TRAFFIC_MANAGER_CACHE_KEY] = registry
    return registry


def store_traffic_manager_port(context: ComponentContext, vehicle_name: str, port: Optional[int]) -> None:
    ports = context.scenario.properties.setdefault(TRAFFIC_MANAGER_PORTS_KEY, {})
    if isinstance(ports, dict):
        ports[vehicle_name] = port


def resolve_carla_client(context: ComponentContext) -> Any | None:
    world = context.world
    if world is not None:
        get_client = getattr(world, "get_client", None)
        if callable(get_client):
            try:
                return get_client()
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.exception("Failed to obtain CARLA client from world; traffic manager setup skipped")
                return None

    properties = getattr(context.scenario, "properties", None)
    if isinstance(properties, dict):
        client = properties.get(CARLA_CLIENT_PROPERTY)
        if client is not None:
            return client

    if world is not None and not callable(getattr(world, "get_client", None)):
        LOGGER.debug("World object does not expose a CARLA client; cannot configure traffic manager")

    return None


def resolve_traffic_manager(context: ComponentContext, vehicle_name: str):
    registry = traffic_manager_registry(context)
    if vehicle_name in registry:
        return registry[vehicle_name]

    client = resolve_carla_client(context)
    if client is None:
        return None

    tm_port = None
    ports = context.scenario.properties.get(TRAFFIC_MANAGER_PORTS_KEY)
    if isinstance(ports, dict):
        tm_port = ports.get(vehicle_name)

    try:
        traffic_manager = client.get_trafficmanager(tm_port) if tm_port else client.get_trafficmanager()
    except Exception:  # pragma: no cover - depends on CARLA API
        LOGGER.exception("Unable to resolve traffic manager for vehicle '%s'", vehicle_name)
        return None

    registry[vehicle_name] = traffic_manager
    return traffic_manager


def call_tm_method(traffic_manager: Any, method_name: str, *args: Any) -> bool:
    method = getattr(traffic_manager, method_name, None)
    if not callable(method):
        LOGGER.debug("Traffic manager has no method '%s'", method_name)
        return False
    try:
        method(*args)
        return True
    except Exception:  # pragma: no cover - depends on CARLA API
        LOGGER.exception("Traffic manager call '%s' failed", method_name)
        return False


def relative_state(reference_transform: Any, follower_transform: Any) -> Dict[str, float]:
    yaw_rad = math.radians(reference_transform.rotation.yaw)
    forward_x = math.cos(yaw_rad)
    forward_y = math.sin(yaw_rad)
    right_x = -forward_y
    right_y = forward_x

    dx = follower_transform.location.x - reference_transform.location.x
    dy = follower_transform.location.y - reference_transform.location.y

    longitudinal = dx * forward_x + dy * forward_y
    lateral = dx * right_x + dy * right_y
    distance = math.hypot(dx, dy)

    return {"longitudinal": longitudinal, "lateral": lateral, "distance": distance}
