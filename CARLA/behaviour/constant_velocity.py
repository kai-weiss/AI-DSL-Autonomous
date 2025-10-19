from __future__ import annotations

import logging
from typing import Any, Optional

try:  # pragma: no cover - optional dependency
    import carla  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    carla = None  # type: ignore[assignment]

from ..model import ComponentSpec, VehicleSpec
from .base import BaseBehaviour, ComponentContext

LOGGER = logging.getLogger(__name__)


class ConstantVelocityBehaviour(BaseBehaviour):
    """Maintain a constant forward velocity for the vehicle."""

    def __init__(self, target_speed: float) -> None:
        self._target_speed = target_speed

    @classmethod
    def from_specs(
        cls,
        component: ComponentSpec,
        vehicle: VehicleSpec,
    ) -> "ConstantVelocityBehaviour":
        speed = component.config.get("target_speed") or component.config.get("speed")
        if speed is None:
            speed = vehicle.metadata.get("default_speed")
        parsed = _parse_speed(speed)
        if parsed is None:
            raise ValueError(
                f"Constant velocity behaviour requires 'target_speed' for component '{component.name}'",
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
        if carla is None:
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
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Failed to enable constant velocity for vehicle '%s'", context.vehicle_spec.name)

    def teardown(self, context: ComponentContext) -> None:
        actor = context.actor
        if actor is None:
            return
        try:
            actor.disable_constant_velocity()  # type: ignore[attr-defined]
        except AttributeError:  # pragma: no cover - depends on CARLA API
            LOGGER.debug("Actor did not provide constant velocity controls")
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception(
                "Failed to disable constant velocity for vehicle '%s'", context.vehicle_spec.name
            )


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
