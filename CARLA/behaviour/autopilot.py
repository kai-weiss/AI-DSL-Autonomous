from __future__ import annotations

import logging
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency
    import carla  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    carla = None  # type: ignore[assignment]

from ..model import ComponentSpec, VehicleSpec
from .base import BaseBehaviour, ComponentContext
from .common import (
    call_tm_method,
    resolve_carla_client,
    store_traffic_manager_port,
    traffic_manager_registry,
)

LOGGER = logging.getLogger(__name__)


class AutopilotBehaviour(BaseBehaviour):
    """Enable CARLA's built-in autopilot for the associated vehicle."""

    def setup(self, context: ComponentContext) -> None:
        actor = context.actor
        if actor is None:
            LOGGER.warning(
                "Autopilot behaviour requested for component '%s' but no CARLA actor is bound",
                context.component_spec.name,
            )
            return
        if not self._enable_autopilot(actor, context):
            LOGGER.debug("Unable to enable autopilot for vehicle '%s'", context.vehicle_spec.name)

    def _enable_autopilot(
        self,
        actor: Any,
        context: ComponentContext,
        tm_port: Optional[int] = None,
    ) -> bool:
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


class TrafficManagerAutopilotBehaviour(AutopilotBehaviour):
    """Autopilot behaviour that also configures the CARLA traffic manager."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__()
        self._config = dict(config or {})

    @classmethod
    def from_specs(
        cls,
        component: ComponentSpec,
        vehicle: VehicleSpec,
    ) -> "TrafficManagerAutopilotBehaviour":
        return cls(component.config)

    def setup(self, context: ComponentContext) -> None:
        actor = context.actor
        if actor is None:
            super().setup(context)
            return

        if carla is None:
            LOGGER.debug("CARLA Python API is unavailable; skipping traffic manager setup")
            if not self._enable_autopilot(actor, context):
                super().setup(context)
            return

        client = resolve_carla_client(context)
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
        store_traffic_manager_port(context, context.vehicle_spec.name, port)
        registry = traffic_manager_registry(context)
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
            LOGGER.warning(
                "Invalid integer value '%s' for traffic manager option '%s'",
                self._config[key],
                key,
            )
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
                LOGGER.warning(
                    "Invalid speed_offset '%s' for traffic manager",
                    config["speed_offset"],
                )

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

        if call_tm_method(traffic_manager, "set_synchronous_mode", bool(synchronous)):
            LOGGER.info(
                "Traffic manager synchronous mode %s for vehicle '%s'",
                "enabled" if synchronous else "disabled",
                context.vehicle_spec.name,
            )