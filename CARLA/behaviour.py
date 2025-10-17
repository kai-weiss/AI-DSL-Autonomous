from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Protocol, TYPE_CHECKING

from .model import ComponentSpec, VehicleSpec

if TYPE_CHECKING:  # pragma: no cover - type checking only
    import carla

LOGGER = logging.getLogger(__name__)


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
        LOGGER.debug("Component '%s' on vehicle '%s' has no runtime behaviour", context.component_spec.name, context.vehicle_spec.name)


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
        super().setup(context)
        actor = context.actor
        if actor is None:
            return

        try:
            import carla  # type: ignore
        except ModuleNotFoundError:  # pragma: no cover - runtime environment without CARLA
            LOGGER.debug("CARLA Python API is unavailable; skipping traffic manager setup")
            return

        world = context.world
        get_client = getattr(world, "get_client", None)
        if not callable(get_client):
            LOGGER.debug("World object does not expose a CARLA client; cannot configure traffic manager")
            return

        try:
            client = get_client()
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Failed to obtain CARLA client from world; traffic manager setup skipped")
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
            return

        if traffic_manager is None:
            LOGGER.debug("CARLA traffic manager not available; skipping configuration")
            return

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


class _PermissionRequestBehaviour(_BaseBehaviour):
    """Simulate the transmission of an overtaking permission request."""

    def __init__(self) -> None:
        self._requested = False

    def setup(self, context: ComponentContext) -> None:
        LOGGER.info("Vehicle '%s' ready to issue overtaking request", context.vehicle_spec.name)

    def tick(self, context: ComponentContext, dt: float) -> None:
        if self._requested:
            return
        context.scenario.properties["overtake_request"] = "pending"
        self._requested = True
        LOGGER.info("Vehicle '%s' requested overtaking permission", context.vehicle_spec.name)


class _AckHandlerBehaviour(_BaseBehaviour):
    """Respond to a pending overtaking permission request."""

    def __init__(self) -> None:
        self._acknowledged = False

    def setup(self, context: ComponentContext) -> None:
        LOGGER.info("Vehicle '%s' ready to handle overtaking acknowledgements", context.vehicle_spec.name)

    def tick(self, context: ComponentContext, dt: float) -> None:
        if self._acknowledged:
            return
        if context.scenario.properties.get("overtake_request") == "pending":
            context.scenario.properties["permission_ack"] = "granted"
            self._acknowledged = True
            LOGGER.info("Vehicle '%s' granted overtaking permission", context.vehicle_spec.name)


class _OvertakeOnAckBehaviour(_BaseBehaviour):
    """Activate a simple overtake manoeuvre once permission is granted."""

    def __init__(self) -> None:
        self._started = False

    def setup(self, context: ComponentContext) -> None:
        LOGGER.info("Vehicle '%s' waiting for overtaking permission", context.vehicle_spec.name)

    def tick(self, context: ComponentContext, dt: float) -> None:
        if self._started:
            return
        if context.scenario.properties.get("permission_ack") == "granted":
            self._started = True
            LOGGER.info("Vehicle '%s' initiating overtake manoeuvre", context.vehicle_spec.name)


class _ConstantVelocityBehaviour(_BaseBehaviour):
    """Maintain a constant forward velocity for the vehicle."""

    def __init__(self, target_speed: float) -> None:
        self._target_speed = target_speed

    @classmethod
    def from_specs(cls, component: ComponentSpec, vehicle: VehicleSpec) -> "_ConstantVelocityBehaviour":
        speed = component.config.get("target_speed") or component.config.get("speed")
        if speed is None:
            speed = vehicle.metadata.get("default_speed")
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