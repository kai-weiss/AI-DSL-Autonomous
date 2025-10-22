from __future__ import annotations

from typing import Dict, Optional

from ..model import ComponentSpec, VehicleSpec
from .ack_handler import AckHandlerBehaviour
from .autopilot import AutopilotBehaviour, TrafficManagerAutopilotBehaviour
from .base import BehaviourFactory, ComponentBehaviour
from .constant_velocity import ConstantVelocityBehaviour
from .emergency_stop import EmergencyStopBehaviour
from .interior_light import InteriorLightBehaviour
from .noop import NoOpBehaviour
from .overtake_on_ack import OvertakeOnAckBehaviour
from .permission_ack_receiver import PermissionAckReceiverBehaviour
from .permission_request import PermissionRequestBehaviour


class BehaviourRegistry:
    """Registry mapping behaviour identifiers to factories."""

    def __init__(self) -> None:
        self._factories: Dict[str, BehaviourFactory] = {}

    def register(self, name: str, factory: BehaviourFactory) -> None:
        self._factories[name.lower()] = factory

    def create(
        self,
        name: Optional[str],
        component: ComponentSpec,
        vehicle: VehicleSpec,
    ) -> ComponentBehaviour:
        key = (name or "noop").lower()
        if key not in self._factories:
            raise KeyError(f"Unknown behaviour '{name}' for component '{component.name}'")
        return self._factories[key](component, vehicle)

    @classmethod
    def with_default_behaviours(cls) -> "BehaviourRegistry":
        registry = cls()
        registry.register("noop", lambda *_: NoOpBehaviour())
        registry.register("autopilot", lambda c, v: AutopilotBehaviour())
        registry.register("constant_velocity", ConstantVelocityBehaviour.from_specs)
        registry.register("interior_light", InteriorLightBehaviour.from_specs)
        registry.register("emergency_stop", lambda *_: EmergencyStopBehaviour())
        registry.register("permission_ack_receiver", lambda *_: PermissionAckReceiverBehaviour())
        registry.register("tm_autopilot_setup_a", TrafficManagerAutopilotBehaviour.from_specs)
        registry.register("tm_autopilot_setup_b", TrafficManagerAutopilotBehaviour.from_specs)
        registry.register("ack_handler", lambda *_: AckHandlerBehaviour())
        registry.register("request_permission", lambda *_: PermissionRequestBehaviour())
        registry.register("tm_overtake_on_ack", lambda *_: OvertakeOnAckBehaviour())
        return registry