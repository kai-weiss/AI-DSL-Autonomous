from __future__ import annotations

import logging
from typing import Any, Optional

import carla

from .base import BaseBehaviour, ComponentContext
from .common import record_collision_event

LOGGER = logging.getLogger(__name__)


class EmergencyStopBehaviour(BaseBehaviour):
    """Monitor collision events and trigger an emergency stop."""

    def __init__(self) -> None:
        self._sensor: Any = None
        self._collision_detected = False
        self._emergency_brake_applied = False
        self._collision_logged = False
        self._last_other_actor: Any = None

    def setup(self, context: ComponentContext) -> None:
        actor = context.actor
        world = context.world
        if actor is None or world is None:
            LOGGER.warning(
                "Emergency stop behaviour requested for component '%s' but world/actor is unavailable",
                context.component_spec.name,
            )
            return

        try:
            blueprint_library = world.get_blueprint_library()
            collision_bp = blueprint_library.find("sensor.other.collision")
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Unable to acquire collision sensor blueprint")
            return

        transform = carla.Transform(carla.Location(x=0.0, z=1.0))

        try:
            sensor = world.spawn_actor(collision_bp, transform, attach_to=actor)
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Failed to attach collision sensor to vehicle '%s'", context.vehicle_spec.name)
            return

        def _on_collision(event: Any) -> None:  # noqa: ANN401 - callback interface
            LOGGER.warning(
                "Collision detected for vehicle '%s' (actor %s)",
                context.vehicle_spec.name,
                getattr(event, "other_actor", None),
            )
            self._collision_detected = True
            self._collision_logged = False
            self._last_other_actor = getattr(event, "other_actor", None)

        try:
            sensor.listen(_on_collision)
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Failed to start collision sensor listener")
            try:
                sensor.destroy()
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.debug("Failed to clean up collision sensor after listen failure")
            return

        self._sensor = sensor
        LOGGER.info("Emergency stop collision monitoring enabled for vehicle '%s'", context.vehicle_spec.name)

    def tick(self, context: ComponentContext, dt: float) -> None:  # noqa: ARG002 - behaviour API
        if self._collision_detected and not self._collision_logged:
            record_collision_event(context, other_actor=self._last_other_actor)
            self._collision_logged = True

        if not self._collision_detected or self._emergency_brake_applied:
            return
        self._perform_emergency_stop(context)

    def teardown(self, context: ComponentContext) -> None:  # noqa: ARG002 - behaviour API
        self._shutdown_sensor()
        self._collision_detected = False
        self._emergency_brake_applied = False
        self._collision_logged = False
        self._last_other_actor = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _perform_emergency_stop(self, context: ComponentContext) -> None:
        actor = context.actor
        if actor is None:
            LOGGER.warning(
                "Collision detected for '%s' but vehicle actor is missing; unable to stop",
                context.vehicle_spec.name,
            )
            return

        control: Optional[Any] = None

        try:
            control = carla.VehicleControl(throttle=0.0, brake=1.0, hand_brake=True)
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Unable to create CARLA VehicleControl for emergency stop")
            control = None

        if control is None:
            control = {"throttle": 0.0, "brake": 1.0, "hand_brake": True}

        apply_control = getattr(actor, "apply_control", None)
        if callable(apply_control):
            try:
                apply_control(control)
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.exception("Failed to apply emergency brake control")
        else:
            LOGGER.warning("Vehicle actor does not support apply_control; emergency braking skipped")

        set_autopilot = getattr(actor, "set_autopilot", None)
        if callable(set_autopilot):
            try:
                set_autopilot(False)
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.debug("Failed to disable autopilot during emergency stop")

        self._emergency_brake_applied = True
        LOGGER.error(
            "Emergency stop executed for vehicle '%s' after collision",
            context.vehicle_spec.name,
        )

    def _shutdown_sensor(self) -> None:
        sensor = self._sensor
        if sensor is None:
            return
        try:
            stop = getattr(sensor, "stop", None)
            if callable(stop):
                stop()
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.debug("Failed to stop collision sensor cleanly")
        try:
            sensor.destroy()
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.debug("Failed to destroy collision sensor during teardown")
        self._sensor = None
