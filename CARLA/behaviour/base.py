from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol, TYPE_CHECKING

from ..model import ComponentSpec, VehicleSpec

if TYPE_CHECKING:  # pragma: no cover - type checking only
    import carla


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


class BaseBehaviour:
    """Default implementation that subclasses can extend."""

    def setup(self, context: ComponentContext) -> None:  # pragma: no cover - default implementation
        pass

    def tick(self, context: ComponentContext, dt: float) -> None:  # pragma: no cover - default implementation
        pass

    def teardown(self, context: ComponentContext) -> None:  # pragma: no cover - default implementation
        pass