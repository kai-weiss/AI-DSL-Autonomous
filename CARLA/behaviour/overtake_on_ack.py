from __future__ import annotations

import logging
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency
    import carla  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    carla = None  # type: ignore[assignment]

from .base import BaseBehaviour, ComponentContext
from .common import (
    OVERTAKE_ACK_KEY,
    OVERTAKE_REQUEST_KEY,
    call_tm_method,
    ensure_overtake_state,
    relative_state,
    resolve_traffic_manager,
    resolve_vehicle_actor,
)

LOGGER = logging.getLogger(__name__)


class OvertakeOnAckBehaviour(BaseBehaviour):
    """Activate a simple overtake manoeuvre once permission is granted."""

    def __init__(self) -> None:
        self._started = False
        self._lead_vehicle: Optional[str] = None
        self._elapsed = 0.0
        self._lane_change_requested = False
        self._return_requested = False
        self._manual_control = False
        self._lane_change_last_request = 0.0
        self._return_last_request = 0.0

    def setup(self, context: ComponentContext) -> None:
        LOGGER.info("Vehicle '%s' waiting for overtaking permission", context.vehicle_spec.name)

        state = ensure_overtake_state(context)
        state.setdefault("overtaker", context.vehicle_spec.name)

        self._lead_vehicle = self._lead_vehicle or state.get("lead_vehicle")

    def tick(self, context: ComponentContext, dt: float) -> None:
        state = ensure_overtake_state(context)

        if state.get("phase") == "idle":
            self._reset_cycle()
            return

        ack_payload = context.scenario.properties.get(OVERTAKE_ACK_KEY)
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
        traffic_manager = resolve_traffic_manager(context, context.vehicle_spec.name)

        if traffic_manager is not None:
            call_tm_method(traffic_manager, "vehicle_percentage_speed_difference", actor, -50.0)
        else:
            self._manual_control = True
            try:  # pragma: no cover - depends on CARLA API
                actor.set_autopilot(False)
            except Exception:
                LOGGER.exception("Unable to disable autopilot for manual overtake control")

        state = ensure_overtake_state(context)
        state["phase"] = "executing"
        state["lead_vehicle"] = self._lead_vehicle
        self._started = True
        self._elapsed = 0.0
        self._lane_change_requested = False
        self._return_requested = False
        self._lane_change_last_request = 0.0
        self._return_last_request = 0.0

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

        lead_actor = resolve_vehicle_actor(context, self._lead_vehicle) if self._lead_vehicle else None

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
                metrics = relative_state(leader_transform, follower_transform)
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.exception("Failed to obtain transform for lead vehicle '%s'", self._lead_vehicle)

        traffic_manager = resolve_traffic_manager(context, context.vehicle_spec.name)

        if traffic_manager is not None and not self._manual_control:
            request_interval = 1.0

            need_lane_change = not metrics or abs(metrics.get("lateral", 0.0)) < 1.0
            if (
                    not self._lane_change_requested
                    or (
                    need_lane_change
                    and self._elapsed - self._lane_change_last_request >= request_interval
            )
            ):
                if call_tm_method(traffic_manager, "force_lane_change", actor, False):
                    if not self._lane_change_requested:
                        LOGGER.info(
                            "Vehicle '%s' requested lane change to begin overtaking",
                            context.vehicle_spec.name,
                        )
                    else:
                        LOGGER.debug(
                            "Vehicle '%s' re-issued lane change request to maintain overtake",
                            context.vehicle_spec.name,
                        )
                    self._lane_change_requested = True
                    self._lane_change_last_request = self._elapsed

            call_tm_method(traffic_manager, "vehicle_percentage_speed_difference", actor, -50.0)

            if metrics and metrics["longitudinal"] > 8.0:
                need_return = abs(metrics["lateral"]) > 0.5
                if (
                        not self._return_requested
                        or (
                        need_return
                        and self._elapsed - self._return_last_request >= request_interval
                )
                ):
                    if call_tm_method(traffic_manager, "force_lane_change", actor, True):
                        if not self._return_requested:
                            LOGGER.info(
                                "Vehicle '%s' requested return to lane after passing",
                                context.vehicle_spec.name,
                            )
                        else:
                            LOGGER.debug(
                                "Vehicle '%s' re-issued lane return request while completing overtake",
                                context.vehicle_spec.name,
                            )
                        self._return_requested = True
                        self._return_last_request = self._elapsed

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
        if carla is None:
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

    def _activate_manual_override(self, context: ComponentContext, actor: Any) -> None:
        if self._manual_control:
            return

        try:  # pragma: no cover - depends on CARLA API
            actor.set_autopilot(False)
        except Exception:
            LOGGER.exception("Unable to disable autopilot for manual overtake control")
        else:
            self._manual_control = True
            self._stuck_timer = 0.0

    def _finish_overtake(self, context: ComponentContext, force: bool = False) -> None:
        actor = context.actor
        if actor is not None:
            try:
                actor.set_autopilot(True)
            except Exception:  # pragma: no cover - depends on CARLA API
                LOGGER.debug("Unable to restore autopilot state for '%s'", context.vehicle_spec.name)

        lead_actor = resolve_vehicle_actor(context, self._lead_vehicle) if self._lead_vehicle else None
        if lead_actor is not None:
            try:  # pragma: no cover - depends on CARLA API
                lead_actor.set_autopilot(True)
            except Exception:
                LOGGER.debug("Lead vehicle '%s' autopilot restoration skipped", self._lead_vehicle)

        state = ensure_overtake_state(context)
        state["phase"] = "idle"
        state["cooldown"] = 3.0
        state["completed_cycles"] = int(state.get("completed_cycles", 0)) + 1

        context.scenario.properties.pop(OVERTAKE_ACK_KEY, None)
        context.scenario.properties.pop(OVERTAKE_REQUEST_KEY, None)

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
        self._lane_change_last_request = 0.0
        self._return_last_request = 0.0
