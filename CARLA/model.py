from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict, Iterable, Optional


@dataclass(slots=True)
class LocationSpec:
    """Simple representation of a CARLA location."""

    x: float
    y: float
    z: float


@dataclass(slots=True)
class RotationSpec:
    """Simple representation of a CARLA rotation."""

    pitch: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0


@dataclass(slots=True)
class SpawnPointSpec:
    """Spawn point expressed either as an index or an explicit transform."""

    index: int | None = None
    location: LocationSpec | None = None
    rotation: RotationSpec | None = None

    def has_transform(self) -> bool:
        return self.location is not None or self.rotation is not None


@dataclass(slots=True)
class ComponentSpec:
    """Runtime information for a single component in the DSL model."""

    name: str
    period: timedelta | None = None
    deadline: timedelta | None = None
    wcet: timedelta | None = None
    priority: int | None = None
    behaviour: str | None = None
    config: Dict[str, Any] = field(default_factory=dict)
    vehicle: str | None = None


@dataclass(slots=True)
class ConnectionSpec:
    """Logical connection between two component endpoints."""

    name: str
    src: str
    dst: str
    latency_budget: timedelta | None = None


@dataclass(slots=True)
class VehicleSpec:
    """Representation of a vehicle configured in the DSL model."""

    name: str
    components: list[ComponentSpec] = field(default_factory=list)
    blueprint: str | None = None
    spawn: SpawnPointSpec | None = None
    autopilot: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def component_names(self) -> Iterable[str]:
        return (component.name for component in self.components)


@dataclass(slots=True)
class WorldSettingsSpec:
    """Subset of CARLA world settings controlled by the interpreter."""

    map_name: str | None = None
    synchronous_mode: bool = True
    fixed_delta_seconds: float | None = 0.05
    weather: Dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class ScenarioSpec:
    """Full scenario description parsed from the DSL JSON export."""

    name: str
    vehicles: list[VehicleSpec] = field(default_factory=list)
    connections: list[ConnectionSpec] = field(default_factory=list)
    world: WorldSettingsSpec = field(default_factory=WorldSettingsSpec)
    properties: Dict[str, str] = field(default_factory=dict)

    def vehicle_by_name(self, name: str) -> Optional[VehicleSpec]:
        for vehicle in self.vehicles:
            if vehicle.name == name:
                return vehicle
        return None

    def components(self) -> Iterable[ComponentSpec]:
        for vehicle in self.vehicles:
            yield from vehicle.components

    def component_by_name(self, name: str) -> Optional[ComponentSpec]:
        for component in self.components():
            if component.name == name:
                return component
        return None