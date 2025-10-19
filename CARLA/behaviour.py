from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, Protocol, TYPE_CHECKING

from .model import ComponentSpec, VehicleSpec

if TYPE_CHECKING:  # pragma: no cover - type checking only
    import carla

LOGGER = logging.getLogger(__name__)

_VEHICLE_REGISTRY_KEY = "_vehicle_actor_ids"
_TRAFFIC_MANAGER_PORTS_KEY = "_traffic_manager_ports"
_TRAFFIC_MANAGER_CACHE_KEY = "_traffic_manager_cache"
_CARLA_CLIENT_KEY = "_carla_client"

# Exported constant used by other modules when caching the CARLA client reference.
CARLA_CLIENT_PROPERTY = _CARLA_CLIENT_KEY
_OVERTAKE_STATE_KEY = "_overtake_state"
_OVERTAKE_REQUEST_KEY = "overtake_request"
_OVERTAKE_ACK_KEY = "permission_ack"


@dataclass(slots=True)
class ComponentContext:
    """Context passed to component behaviours during execution."""

    scenario: Any
    world: Any
    vehicle_spec: VehicleSpec
    component_spec: ComponentSpec
    actor: Optional["carla.Actor"]


class ComponentBehaviour(Protocol):
    """Interface implemented by component behaviours."""

    def setup(self, context: ComponentContext) -> None:
        ...

    def tick(self, context: ComponentContext, dt: float) -> None:
        ...

    def teardown(self, context: ComponentContext) -> None:
        ...


BehaviourFactory = Callable[[ComponentSpec, VehicleSpec], ComponentBehaviour]


def _component_full_name(component: ComponentSpec) -> str:
    if component.vehicle:
        return f"{component.vehicle}.{component.name}"
    return component.name


def _timedelta_to_seconds(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value.total_seconds())
    except AttributeError:
        return None


def _ensure_overtake_state(context: ComponentContext) -> Dict[str, Any]:
    state = context.scenario.properties.setdefault(_OVERTAKE_STATE_KEY, {})
    if "phase" not in state:
        state["phase"] = "idle"
    return state


def _vehicle_actor_id(context: ComponentContext, vehicle_name: str) -> Optional[int]:
    registry = context.scenario.properties.get(_VEHICLE_REGISTRY_KEY)
    if not isinstance(registry, dict):
        return None
    actor_id = registry.get(vehicle_name)
    if actor_id is None:
        return None
    try:
        return int(actor_id)
    except (TypeError, ValueError):
        return None


def _resolve_vehicle_actor(context: ComponentContext, vehicle_name: str):
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


def _traffic_manager_registry(context: ComponentContext) -> Dict[str, Any]:
    registry = context.scenario.properties.setdefault(_TRAFFIC_MANAGER_CACHE_KEY, {})
    if not isinstance(registry, dict):
        registry = {}
        context.scenario.properties[_TRAFFIC_MANAGER_CACHE_KEY] = registry
    return registry


def _store_traffic_manager_port(context: ComponentContext, vehicle_name: str, port: Optional[int]) -> None:
    ports = context.scenario.properties.setdefault(_TRAFFIC_MANAGER_PORTS_KEY, {})
    if isinstance(ports, dict):
        ports[vehicle_name] = port


def _resolve_traffic_manager(context: ComponentContext, vehicle_name: str):
    registry = _traffic_manager_registry(context)
    if vehicle_name in registry:
        return registry[vehicle_name]

    client = _resolve_carla_client(context)
    if client is None:
        return None

    tm_port = None
    ports = context.scenario.properties.get(_TRAFFIC_MANAGER_PORTS_KEY)
    if isinstance(ports, dict):
        tm_port = ports.get(vehicle_name)

    try:
        traffic_manager = client.get_trafficmanager(tm_port) if tm_port else client.get_trafficmanager()
    except Exception:  # pragma: no cover - depends on CARLA API
        LOGGER.exception("Unable to resolve traffic manager for vehicle '%s'", vehicle_name)
        return None

    registry[vehicle_name] = traffic_manager
    return traffic_manager


def _call_tm_method(traffic_manager: Any, method_name: str, *args: Any) -> bool:
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


def _resolve_carla_client(context: ComponentContext) -> Any | None:
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
        client = properties.get(_CARLA_CLIENT_KEY)
        if client is not None:
            return client

    if world is not None and not callable(getattr(world, "get_client", None)):
        LOGGER.debug("World object does not expose a CARLA client; cannot configure traffic manager")

    return None


def _relative_state(reference_transform: Any, follower_transform: Any) -> Dict[str, float]:
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


def _connections_by_src(component: ComponentSpec, scenario: Any) -> Iterable[Any]:
    full_name = _component_full_name(component)
    for connection in getattr(scenario, "connections", []):
        if getattr(connection, "src", None) == full_name:
            yield connection


def _connections_by_dst(component: ComponentSpec, scenario: Any) -> Iterable[Any]:
    full_name = _component_full_name(component)
    for connection in getattr(scenario, "connections", []):
        if getattr(connection, "dst", None) == full_name:
            yield connection


class BehaviourRegistry:
    """Registry mapping behaviour identifiers to factories."""

    def __init__(self) -> None:
        self._factories: Dict[str, BehaviourFactory] = {}

    def register(self, name: str, factory: BehaviourFactory) -> None:
        self._factories[name.lower()] = factory

    def create(self, name: Optional[str], component: ComponentSpec, vehicle: VehicleSpec) -> ComponentBehaviour:
        key = (name or "noop").lower()
        if key not in self._factories:
            raise KeyError(f"Unknown behaviour '{name}' for component '{component.name}'")
        return self._factories[key](component, vehicle)

    @classmethod
    def with_default_behaviours(cls) -> "BehaviourRegistry":
        registry = cls()
        registry.register("noop", lambda *_: _NoOpBehaviour())
        registry.register("autopilot", lambda c, v: _AutopilotBehaviour())
        registry.register("constant_velocity", _ConstantVelocityBehaviour.from_specs)
        registry.register("tm_autopilot_setup_a", _TrafficManagerAutopilotBehaviour.from_specs)
        registry.register("tm_autopilot_setup_b", _TrafficManagerAutopilotBehaviour.from_specs)
        registry.register("ack_handler", lambda *_: _AckHandlerBehaviour())
        registry.register("request_permission", lambda *_: _PermissionRequestBehaviour())
        registry.register("tm_overtake_on_ack", lambda *_: _OvertakeOnAckBehaviour())
        return registry


class _BaseBehaviour:
    def setup(self, context: ComponentContext) -> None:  # pragma: no cover - default implementation
        pass

    def tick(self, context: ComponentContext, dt: float) -> None:  # pragma: no cover
        pass

    def teardown(self, context: ComponentContext) -> None:  # pragma: no cover
        pass


class _NoOpBehaviour(_BaseBehaviour):
    """Behaviour that performs no action."""

    def setup(self, context: ComponentContext) -> None:
        LOGGER.debug("Component '%s' on vehicle '%s' has no runtime behaviour", context.component_spec.name,
                     context.vehicle_spec.name)


class _AutopilotBehaviour(_BaseBehaviour):
    """Enable CARLA's built-in autopilot for the associated vehicle."""

    def setup(self, context: ComponentContext) -> None:
        actor = context.actor
        if actor is None:
            LOGGER.warning(
                "Autopilot behaviour requested for component '%s' but no CARLA actor is bound",
                context.component_spec.name,
            )
            return
        try:
            actor.set_autopilot(True)
            LOGGER.info(
                "Autopilot enabled for vehicle '%s' (component '%s')",
                context.vehicle_spec.name,
                context.component_spec.name,
            )
        except AttributeError:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Vehicle actor does not support autopilot")

        self._enable_autopilot(actor, context)

    def _enable_autopilot(self, actor: Any, context: ComponentContext,
                          tm_port: Optional[int] = None) -> bool:
        try:
            if tm_port is None:
                actor.set_autopilot(True)
            else:
                actor.set_autopilot(True, tm_port)
        except AttributeError:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Vehicle actor does not support autopilot")
            return False
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception(
                "Failed to enable autopilot for vehicle '%s' (component '%s')",
                context.vehicle_spec.name,
                context.component_spec.name,
            )
            return False
        else:
            if tm_port is None:
                LOGGER.info(
                    "Autopilot enabled for vehicle '%s' (component '%s')",
                    context.vehicle_spec.name,
                    context.component_spec.name,
                )
            else:
                LOGGER.info(
                    "Autopilot enabled for vehicle '%s' via TM port %s (component '%s')",
                    context.vehicle_spec.name,
                    tm_port,
                    context.component_spec.name,
                )
            return True

class _TrafficManagerAutopilotBehaviour(_AutopilotBehaviour):
    """Autopilot behaviour that also configures the CARLA traffic manager."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__()
        self._config = dict(config or {})

    @classmethod
    def from_specs(
            cls, component: ComponentSpec, vehicle: VehicleSpec
    ) -> "_TrafficManagerAutopilotBehaviour":
        return cls(component.config)

    def setup(self, context: ComponentContext) -> None:
        actor = context.actor
        if actor is None:
            super().setup(context)
            return

        try:
            import carla  # type: ignore
        except ModuleNotFoundError:  # pragma: no cover - runtime environment without CARLA
            LOGGER.debug("CARLA Python API is unavailable; skipping traffic manager setup")
            if not self._enable_autopilot(actor, context):
                super().setup(context)
            return

        client = _resolve_carla_client(context)
        if client is None:
            LOGGER.debug("Unable to obtain CARLA client; traffic manager setup skipped")
            if not self._enable_autopilot(actor, context):
                super().setup(context)
            return

        tm_port = self._parse_int_config("tm_port") or self._parse_int_config("port")
        try:
            traffic_manager = (
                client.get_trafficmanager(tm_port)
                if tm_port is not None
                else client.get_trafficmanager()
            )
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Unable to acquire CARLA traffic manager")
            if not self._enable_autopilot(actor, context):
                super().setup(context)
            return

        if traffic_manager is None:
            LOGGER.debug("CARLA traffic manager not available; skipping configuration")
            if not self._enable_autopilot(actor, context):
                super().setup(context)
            return

        try:
            port = traffic_manager.get_port()  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - depends on CARLA API
            port = tm_port
        _store_traffic_manager_port(context, context.vehicle_spec.name, port)
        registry = _traffic_manager_registry(context)
        registry[context.vehicle_spec.name] = traffic_manager

        self._synchronise_traffic_manager(context, traffic_manager)

        if not self._enable_autopilot(actor, context, port):
            super().setup(context)
        self._apply_tm_configuration(traffic_manager, actor)

    def _parse_int_config(self, key: str) -> Optional[int]:
        if key not in self._config:
            return None
        try:
            return int(self._config[key])
        except (TypeError, ValueError):
            LOGGER.warning("Invalid integer value '%s' for traffic manager option '%s'", self._config[key], key)
            return None

    def _apply_tm_configuration(self, traffic_manager: Any, actor: Any) -> None:
        config = self._config
        if not config:
            return

        def _call(method_name: str, *args: Any) -> None:
            method = getattr(traffic_manager, method_name, None)
            if not callable(method):
                LOGGER.debug("Traffic manager does not provide method '%s'", method_name)
                return
            try:
                method(actor, *args)
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.exception("Traffic manager call '%s' failed", method_name)

        if "speed_offset" in config:
            try:
                percentage = float(config["speed_offset"])
                _call("vehicle_percentage_speed_difference", percentage)
            except (TypeError, ValueError):
                LOGGER.warning("Invalid speed_offset '%s' for traffic manager", config["speed_offset"])

        if "auto_lane_change" in config:
            _call("auto_lane_change", bool(config["auto_lane_change"]))

        if "ignore_lights_percentage" in config:
            try:
                percentage = float(config["ignore_lights_percentage"])
                _call("ignore_lights_percentage", percentage)
            except (TypeError, ValueError):
                LOGGER.warning(
                    "Invalid ignore_lights_percentage '%s' for traffic manager",
                    config["ignore_lights_percentage"],
                )

        if "distance_to_leading_vehicle" in config:
            try:
                distance = float(config["distance_to_leading_vehicle"])
                _call("distance_to_leading_vehicle", distance)
            except (TypeError, ValueError):
                LOGGER.warning(
                    "Invalid distance_to_leading_vehicle '%s' for traffic manager",
                    config["distance_to_leading_vehicle"],
                )

        if "collision_detection" in config:
            _call("collision_detection", bool(config["collision_detection"]))

    def _synchronise_traffic_manager(self, context: ComponentContext, traffic_manager: Any) -> None:
        synchronous: Optional[bool] = None

        world = context.world
        get_settings = getattr(world, "get_settings", None) if world is not None else None
        if callable(get_settings):
            try:
                settings = get_settings()
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.exception("Failed to query CARLA world settings for TM synchronisation")
            else:
                synchronous = bool(getattr(settings, "synchronous_mode", synchronous))

        if synchronous is None:
            scenario_world = getattr(context.scenario, "world", None)
            if scenario_world is not None:
                synchronous = bool(getattr(scenario_world, "synchronous_mode", False))

        if synchronous is None:
            return

        if _call_tm_method(traffic_manager, "set_synchronous_mode", bool(synchronous)):
            LOGGER.info(
                "Traffic manager synchronous mode %s for vehicle '%s'",
                "enabled" if synchronous else "disabled",
                context.vehicle_spec.name,
            )

class _PermissionRequestBehaviour(_BaseBehaviour):
    """Simulate the transmission of an overtaking permission request."""

    def __init__(self) -> None:
        self._request_active = False
        self._lead_vehicle: Optional[str] = None
        self._latency_budgets: Dict[str, Optional[float]] = {}
        self._cooldown_remaining = 0.0
        self._carla_unavailable = False

    def setup(self, context: ComponentContext) -> None:
        LOGGER.info("Vehicle '%s' ready to issue overtaking request", context.vehicle_spec.name)

        self._lead_vehicle = self._lead_vehicle or self._resolve_lead_vehicle(context)
        self._latency_budgets = {
            connection.name: _timedelta_to_seconds(connection.latency_budget)
            for connection in _connections_by_src(context.component_spec, context.scenario)
        }

        state = _ensure_overtake_state(context)
        if self._lead_vehicle:
            state.setdefault("lead_vehicle", self._lead_vehicle)
        state.setdefault("overtaker", context.vehicle_spec.name)

        actor = context.actor
        traffic_manager = _resolve_traffic_manager(context, context.vehicle_spec.name)
        if traffic_manager is not None and actor is not None:
            if _call_tm_method(traffic_manager, "vehicle_percentage_speed_difference", actor, -50.0):
                LOGGER.info(
                    "Configured vehicle '%s' for fast approach (speed offset -35%%)",
                    context.vehicle_spec.name,
                )
        elif actor is None:
            LOGGER.debug(
                "Vehicle '%s' has no CARLA actor bound; overtaking logic will rely on scenario state only",
                context.vehicle_spec.name,
            )
        else:
            try:
                import carla  # type: ignore
            except ModuleNotFoundError:
                self._carla_unavailable = True
                LOGGER.debug(
                    "CARLA API unavailable; overtaking request will rely on logical triggers only",
                )
            else:  # pragma: no cover - depends on CARLA API
                try:
                    actor.set_autopilot(True)
                except Exception:
                    LOGGER.exception("Failed to ensure autopilot for vehicle '%s'", context.vehicle_spec.name)

    def tick(self, context: ComponentContext, dt: float) -> None:
        state = _ensure_overtake_state(context)

        if state.get("phase") == "idle":
            cooldown = max(state.get("cooldown", 0.0) or 0.0, 0.0)
            if cooldown > 0.0:
                cooldown = max(0.0, cooldown - dt)
                state["cooldown"] = cooldown
                self._cooldown_remaining = cooldown
                return
            self._request_active = False
            self._cooldown_remaining = 0.0
        else:
            self._cooldown_remaining = state.get("cooldown", self._cooldown_remaining)

        if self._request_active or state.get("phase") != "idle":
            return

        if not self._lead_vehicle:
            self._lead_vehicle = self._resolve_lead_vehicle(context)
            if not self._lead_vehicle and not self._carla_unavailable:
                LOGGER.debug("No lead vehicle identified for overtaking request component '%s'",
                             context.component_spec.name)
                return

        if self._carla_unavailable:
            self._emit_request(context, reason="carla_unavailable")
            return

        actor = context.actor
        lead_actor = _resolve_vehicle_actor(context, self._lead_vehicle) if self._lead_vehicle else None
        if actor is None or lead_actor is None:
            return

        try:
            follower_transform = actor.get_transform()
            leader_transform = lead_actor.get_transform()
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Failed to evaluate vehicle transforms during overtaking trigger check")
            return

        metrics = _relative_state(leader_transform, follower_transform)
        longitudinal = metrics["longitudinal"]
        lateral = metrics["lateral"]

        if longitudinal < 0.0 and abs(longitudinal) <= 15.0 and abs(lateral) <= 4.0:
            self._emit_request(context, metrics=metrics, reason="proximity_trigger")

    def _emit_request(self, context: ComponentContext, *, metrics: Optional[Dict[str, float]] = None,
                      reason: str) -> None:
        payload = {
            "from_vehicle": context.vehicle_spec.name,
            "to_vehicle": self._lead_vehicle,
            "component": context.component_spec.name,
            "period_s": _timedelta_to_seconds(context.component_spec.period),
            "wcet_s": _timedelta_to_seconds(context.component_spec.wcet),
            "deadline_s": _timedelta_to_seconds(context.component_spec.deadline),
            "priority": context.component_spec.priority,
            "link_budgets_s": dict(self._latency_budgets),
            "reason": reason,
        }
        if metrics:
            payload["relative_pose"] = metrics

        context.scenario.properties[_OVERTAKE_REQUEST_KEY] = payload

        state = _ensure_overtake_state(context)
        state["phase"] = "awaiting_ack"
        state["lead_vehicle"] = self._lead_vehicle
        state["overtaker"] = context.vehicle_spec.name
        state.pop("cooldown", None)
        state["request_count"] = int(state.get("request_count", 0)) + 1

        self._request_active = True
        LOGGER.info(
            "Vehicle '%s' requested overtaking permission from '%s' (%s)",
            context.vehicle_spec.name,
            self._lead_vehicle,
            reason,
        )

    def _resolve_lead_vehicle(self, context: ComponentContext) -> Optional[str]:
        for connection in _connections_by_src(context.component_spec, context.scenario):
            target = getattr(connection, "dst", "")
            if target and "." in target:
                return target.split(".", 1)[0]

        for vehicle in getattr(context.scenario, "vehicles", []):
            if vehicle.name != context.vehicle_spec.name:
                return vehicle.name
        return None


class _AckHandlerBehaviour(_BaseBehaviour):
    """Respond to a pending overtaking permission request."""

    def __init__(self) -> None:
        self._acknowledged = False
        self._latency_budgets: Dict[str, Optional[float]] = {}

    def setup(self, context: ComponentContext) -> None:
        LOGGER.info("Vehicle '%s' ready to handle overtaking acknowledgements", context.vehicle_spec.name)
        self._latency_budgets = {
            connection.name: _timedelta_to_seconds(connection.latency_budget)
            for connection in _connections_by_src(context.component_spec, context.scenario)
        }

        actor = context.actor
        traffic_manager = _resolve_traffic_manager(context, context.vehicle_spec.name)
        if traffic_manager is not None and actor is not None:
            if _call_tm_method(traffic_manager, "vehicle_percentage_speed_difference", actor, 45.0):
                LOGGER.info(
                    "Configured vehicle '%s' as slow lead (speed offset +45%%)",
                    context.vehicle_spec.name,
                )

    def tick(self, context: ComponentContext, dt: float) -> None:
        state = _ensure_overtake_state(context)

        if state.get("phase") == "idle":
            self._acknowledged = False
            return

        if self._acknowledged:
            return

        request = context.scenario.properties.get(_OVERTAKE_REQUEST_KEY)
        if not isinstance(request, dict):
            return

        if request.get("to_vehicle") not in {None, context.vehicle_spec.name}:
            return

        ack_payload = {
            "from_vehicle": context.vehicle_spec.name,
            "to_vehicle": request.get("from_vehicle"),
            "component": context.component_spec.name,
            "period_s": _timedelta_to_seconds(context.component_spec.period),
            "wcet_s": _timedelta_to_seconds(context.component_spec.wcet),
            "deadline_s": _timedelta_to_seconds(context.component_spec.deadline),
            "priority": context.component_spec.priority,
            "link_budgets_s": dict(self._latency_budgets),
            "request": request,
        }

        context.scenario.properties[_OVERTAKE_ACK_KEY] = ack_payload
        state["phase"] = "acknowledged"
        state["ack_count"] = int(state.get("ack_count", 0)) + 1
        self._acknowledged = True
        LOGGER.info(
            "Vehicle '%s' granted overtaking permission to '%s'",
            context.vehicle_spec.name,
            request.get("from_vehicle"),
        )


class _OvertakeOnAckBehaviour(_BaseBehaviour):
    """Activate a simple overtake manoeuvre once permission is granted."""

    def __init__(self) -> None:
        self._started = False
        self._lead_vehicle: Optional[str] = None
        self._elapsed = 0.0
        self._lane_change_requested = False
        self._return_requested = False
        self._manual_control = False

    def setup(self, context: ComponentContext) -> None:
        LOGGER.info("Vehicle '%s' waiting for overtaking permission", context.vehicle_spec.name)

        state = _ensure_overtake_state(context)
        state.setdefault("overtaker", context.vehicle_spec.name)

        self._lead_vehicle = self._lead_vehicle or state.get("lead_vehicle")

    def tick(self, context: ComponentContext, dt: float) -> None:
        state = _ensure_overtake_state(context)

        if state.get("phase") == "idle":
            self._reset_cycle()
            return

        ack_payload = context.scenario.properties.get(_OVERTAKE_ACK_KEY)
        if not isinstance(ack_payload, dict):
            return

        if ack_payload.get("to_vehicle") not in {None, context.vehicle_spec.name}:
            return

        if not self._started:
            self._begin_overtake(context, ack_payload)

        if self._started:
            self._update_overtake(context, dt)

    def _begin_overtake(self, context: ComponentContext, ack_payload: Dict[str, Any]) -> None:
        actor = context.actor
        if actor is None:
            LOGGER.debug("No actor bound to overtaking vehicle '%s'", context.vehicle_spec.name)
            return

        self._lead_vehicle = ack_payload.get("from_vehicle") or self._lead_vehicle
        traffic_manager = _resolve_traffic_manager(context, context.vehicle_spec.name)

        if traffic_manager is not None:
            _call_tm_method(traffic_manager, "vehicle_percentage_speed_difference", actor, -50.0)
        else:
            self._manual_control = True
            try:  # pragma: no cover - depends on CARLA API
                actor.set_autopilot(False)
            except Exception:
                LOGGER.exception("Unable to disable autopilot for manual overtake control")

        state = _ensure_overtake_state(context)
        state["phase"] = "executing"
        state["lead_vehicle"] = self._lead_vehicle
        self._started = True
        self._elapsed = 0.0
        self._lane_change_requested = False
        self._return_requested = False

        LOGGER.info(
            "Vehicle '%s' initiating overtake of '%s'",
            context.vehicle_spec.name,
            self._lead_vehicle,
        )

    def _update_overtake(self, context: ComponentContext, dt: float) -> None:
        actor = context.actor
        if actor is None:
            LOGGER.debug("Overtaking vehicle '%s' lost actor reference", context.vehicle_spec.name)
            self._finish_overtake(context, force=True)
            return

        lead_actor = _resolve_vehicle_actor(context, self._lead_vehicle) if self._lead_vehicle else None

        try:
            follower_transform = actor.get_transform()
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Failed to obtain transform for overtaking vehicle")
            self._finish_overtake(context, force=True)
            return

        metrics = None
        if lead_actor is not None:
            try:
                leader_transform = lead_actor.get_transform()
                metrics = _relative_state(leader_transform, follower_transform)
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.exception("Failed to obtain transform for lead vehicle '%s'", self._lead_vehicle)

        traffic_manager = _resolve_traffic_manager(context, context.vehicle_spec.name)

        if traffic_manager is not None:
            if not self._lane_change_requested:
                if _call_tm_method(traffic_manager, "force_lane_change", actor, True):
                    self._lane_change_requested = True
                    LOGGER.info("Vehicle '%s' requested lane change to begin overtaking", context.vehicle_spec.name)
            _call_tm_method(traffic_manager, "vehicle_percentage_speed_difference", actor, -50.0)

            if metrics and not self._return_requested and metrics["longitudinal"] > 8.0:
                if _call_tm_method(traffic_manager, "force_lane_change", actor, False):
                    self._return_requested = True
                    LOGGER.info("Vehicle '%s' requested return to lane after passing", context.vehicle_spec.name)
        else:
            self._apply_manual_control(actor, metrics)

        self._elapsed += dt

        if metrics and metrics["longitudinal"] > 12.0 and abs(metrics["lateral"]) < 1.5:
            self._finish_overtake(context)
        elif self._elapsed >= 15.0:
            LOGGER.warning(
                "Vehicle '%s' timed out while overtaking '%s'; forcing completion",
                context.vehicle_spec.name,
                self._lead_vehicle,
            )
            self._finish_overtake(context, force=True)

    def _apply_manual_control(self, actor: Any, metrics: Optional[Dict[str, float]]) -> None:
        try:
            import carla  # type: ignore
        except ModuleNotFoundError:
            return

        control = carla.VehicleControl()
        control.throttle = 0.8
        control.brake = 0.0
        control.hand_brake = False

        if metrics is None:
            control.steer = 0.2
        else:
            if metrics["longitudinal"] < 6.0:
                control.steer = 0.25
            elif metrics["longitudinal"] < 12.0:
                control.steer = 0.0
            else:
                control.steer = -0.25 if metrics["lateral"] > 0 else 0.25

        try:  # pragma: no cover - depends on CARLA API
            actor.apply_control(control)
        except Exception:
            LOGGER.exception("Failed to apply manual control for overtaking vehicle")

    def _finish_overtake(self, context: ComponentContext, force: bool = False) -> None:
        actor = context.actor
        if actor is not None:
            try:
                actor.set_autopilot(True)
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.debug("Unable to restore autopilot state for '%s'", context.vehicle_spec.name)

        lead_actor = _resolve_vehicle_actor(context, self._lead_vehicle) if self._lead_vehicle else None
        if lead_actor is not None:
            try:  # pragma: no cover - depends on CARLA API
                lead_actor.set_autopilot(True)
            except Exception:
                LOGGER.debug("Lead vehicle '%s' autopilot restoration skipped", self._lead_vehicle)

        state = _ensure_overtake_state(context)
        state["phase"] = "idle"
        state["cooldown"] = 3.0
        state["completed_cycles"] = int(state.get("completed_cycles", 0)) + 1

        context.scenario.properties.pop(_OVERTAKE_ACK_KEY, None)
        context.scenario.properties.pop(_OVERTAKE_REQUEST_KEY, None)

        self._reset_cycle()

        LOGGER.info(
            "Vehicle '%s' completed overtaking sequence%s",
            context.vehicle_spec.name,
            " (forced)" if force else "",
        )

    def _reset_cycle(self) -> None:
        self._started = False
        self._elapsed = 0.0
        self._lane_change_requested = False
        self._return_requested = False
        self._manual_control = False


class _ConstantVelocityBehaviour(_BaseBehaviour):
    """Maintain a constant forward velocity for the vehicle."""

    def __init__(self, target_speed: float) -> None:
        self._target_speed = target_speed

    @classmethod
    def from_specs(cls, component: ComponentSpec, vehicle: VehicleSpec) -> "_ConstantVelocityBehaviour":
        speed = component.config.get("target_speed") or component.config.get("speed")
        print("test")
        if speed is None:
            speed = vehicle.metadata.get("default_speed")
            print("default")
        print(speed)
        parsed = _parse_speed(speed)
        if parsed is None:
            raise ValueError(
                f"Constant velocity behaviour requires 'target_speed' for component '{component.name}'"
            )
        return cls(parsed)

    def setup(self, context: ComponentContext) -> None:
        actor = context.actor
        if actor is None:
            LOGGER.warning(
                "Constant velocity behaviour requested for component '%s' but no actor is bound",
                context.component_spec.name,
            )
            return
        try:
            import carla  # imported lazily to keep module importable without CARLA
        except ModuleNotFoundError:  # pragma: no cover - runtime environment without CARLA
            LOGGER.error("CARLA Python API is not available; cannot enable constant velocity")
            return

        try:
            transform = actor.get_transform()
            forward = transform.get_forward_vector()
            vector = carla.Vector3D(
                forward.x * self._target_speed,
                forward.y * self._target_speed,
                forward.z * self._target_speed,
            )
            actor.enable_constant_velocity(vector)
            LOGGER.info(
                "Set constant velocity %.2f m/s for vehicle '%s'",
                self._target_speed,
                context.vehicle_spec.name,
            )
        except AttributeError:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Vehicle actor does not support constant velocity")

    def teardown(self, context: ComponentContext) -> None:
        actor = context.actor
        if actor is None:
            return
        try:
            actor.disable_constant_velocity()  # type: ignore[attr-defined]
        except AttributeError:  # pragma: no cover - depends on CARLA API
            LOGGER.debug("Actor did not provide constant velocity controls")


def _parse_speed(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text.endswith("mps"):
            text = text[:-3]
        elif text.endswith("m/s"):
            text = text[:-3]
        elif text.endswith("kmh"):
            return float(text[:-3]) / 3.6
        elif text.endswith("km/h"):
            return float(text[:-4]) / 3.6
        try:
            return float(text)
        except ValueError:  # pragma: no cover - logged for debugging
            LOGGER.warning("Unable to parse speed value '%s'", value)
            return None
    return None
