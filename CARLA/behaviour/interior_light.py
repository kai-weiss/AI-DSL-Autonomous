from __future__ import annotations

import logging
from typing import Optional
import carla

from ..model import ComponentSpec, VehicleSpec
from .base import BaseBehaviour, ComponentContext

LOGGER = logging.getLogger(__name__)


class InteriorLightBehaviour(BaseBehaviour):
    """Toggle the vehicle's interior light using the CARLA API."""

    _interior_flag: Optional[int]

    def __init__(self) -> None:
        self._toggled = False
        self._interior_flag = None

    @classmethod
    def from_specs(
        cls,
        component: ComponentSpec,
        vehicle: VehicleSpec,
    ) -> "InteriorLightBehaviour":
        return cls()

    def setup(self, context: ComponentContext) -> None:
        self._toggle_interior_light(context)

    def tick(self, context: ComponentContext, dt: float) -> None:  # noqa: ARG002 - behaviour API
        if not self._toggled:
            self._toggle_interior_light(context)

    def teardown(self, context: ComponentContext) -> None:  # noqa: ARG002 - behaviour API
        self._toggled = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _toggle_interior_light(self, context: ComponentContext) -> None:
        actor = context.actor
        if actor is None:
            LOGGER.debug(
                "Interior light behaviour requested for component '%s' but no actor is bound",
                context.component_spec.name,
            )
            return

        vehicle_light_state = self._resolve_vehicle_light_state()
        if vehicle_light_state is None:
            LOGGER.warning("CARLA installation does not expose VehicleLightState; skipping lights setup")
            return

        interior_flag = self._resolve_interior_flag(vehicle_light_state)
        if interior_flag is None:
            LOGGER.warning("VehicleLightState does not define an interior light flag; skipping toggle")
            return

        try:
            current_state = actor.get_light_state()
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception(
                "Failed to read current light state for vehicle '%s' (component '%s')",
                context.vehicle_spec.name,
                context.component_spec.name,
            )
            return

        try:
            current_mask = int(current_state)
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.debug("Unable to coerce current light state to integer; aborting toggle")
            return

        if current_mask & interior_flag:
            new_mask = current_mask & ~interior_flag
            status = "deactivated"
        else:
            new_mask = current_mask | interior_flag
            status = "activated"

        try:
            new_state = vehicle_light_state(new_mask)
        except Exception:  # pragma: no cover - depends on CARLA API
            new_state = new_mask

        try:
            actor.set_light_state(new_state)
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception(
                "Failed to toggle interior light for vehicle '%s' (component '%s')",
                context.vehicle_spec.name,
                context.component_spec.name,
            )
            return

        LOGGER.info("Interior light %s for vehicle '%s'", status, context.vehicle_spec.name)
        self._toggled = True

    def _resolve_vehicle_light_state(self) -> Optional[type]:
        try:
            return getattr(carla, "VehicleLightState", None)
        except Exception:  # pragma: no cover - depends on CARLA API
            return None

    def _resolve_interior_flag(self, light_state_cls: type) -> Optional[int]:
        if self._interior_flag is not None:
            return self._interior_flag

        candidate = getattr(light_state_cls, "Interior", None)
        if candidate is None and hasattr(light_state_cls, "__members__"):
            members = getattr(light_state_cls, "__members__", {})
            if isinstance(members, dict):
                candidate = members.get("Interior") or members.get("INTERIOR") or members.get("interior")

        if candidate is None:
            return None

        try:
            self._interior_flag = int(candidate)
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.debug("Unable to coerce interior light flag to integer")
            self._interior_flag = None
        return self._interior_flag
