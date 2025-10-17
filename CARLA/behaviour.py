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