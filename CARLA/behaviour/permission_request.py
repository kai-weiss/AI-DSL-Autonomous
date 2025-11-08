from __future__ import annotations

import logging
from typing import Dict, Optional

try:  # pragma: no cover - optional dependency
    import carla  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    carla = None  # type: ignore[assignment]

from .base import BaseBehaviour, ComponentContext
from .common import (
    OVERTAKE_REQUEST_KEY,
    call_tm_method,
    connections_by_src,
    emit_connection_event,
    ensure_overtake_state,
    relative_state,
    resolve_traffic_manager,
    resolve_vehicle_actor,
    timedelta_to_seconds,
)

LOGGER = logging.getLogger(__name__)


class PermissionRequestBehaviour(BaseBehaviour):
    """Simulate the transmission of an overtaking permission request."""

    def __init__(self) -> None:
        self._request_active = False
        self._lead_vehicle: Optional[str] = None
        self._latency_budgets: Dict[str, Optional[float]] = {}
        self._carla_unavailable = False

    def setup(self, context: ComponentContext) -> None:
        LOGGER.info("Vehicle '%s' ready to issue overtaking request", context.vehicle_spec.name)

        self._lead_vehicle = self._lead_vehicle or self._resolve_lead_vehicle(context)
        self._latency_budgets = {
            connection.name: timedelta_to_seconds(connection.latency_budget)
            for connection in connections_by_src(context.component_spec, context.scenario)
        }

        state = ensure_overtake_state(context)
        if self._lead_vehicle:
            state.setdefault("lead_vehicle", self._lead_vehicle)
        state.setdefault("overtaker", context.vehicle_spec.name)

        actor = context.actor
        traffic_manager = resolve_traffic_manager(context, context.vehicle_spec.name)
        if traffic_manager is not None and actor is not None:
            if call_tm_method(traffic_manager, "vehicle_percentage_speed_difference", actor, -50.0):
                LOGGER.info(
                    "Configured vehicle '%s' for fast approach (speed offset -50%%)",
                    context.vehicle_spec.name,
                )
        elif actor is None:
            LOGGER.debug(
                "Vehicle '%s' has no CARLA actor bound; overtaking logic will rely on scenario state only",
                context.vehicle_spec.name,
            )
        else:
            if carla is None:
                self._carla_unavailable = True
                LOGGER.debug(
                    "CARLA API unavailable; overtaking request will rely on logical triggers only",
                )
            else:  # pragma: no cover - depends on CARLA API
                try:
                    actor.set_autopilot(True)
                except Exception:
                    LOGGER.exception("Failed to ensure autopilot for vehicle '%s'", context.vehicle_spec.name)

    def tick(self, context: ComponentContext, dt: float) -> None:
        state = ensure_overtake_state(context)

        if state.get("phase") == "idle":
            cooldown = max(state.get("cooldown", 0.0) or 0.0, 0.0)
            if cooldown > 0.0:
                cooldown = max(0.0, cooldown - dt)
                state["cooldown"] = cooldown
                return
            self._request_active = False

        if self._request_active or state.get("phase") != "idle":
            return

        if not self._lead_vehicle:
            self._lead_vehicle = self._resolve_lead_vehicle(context)
            if not self._lead_vehicle and not self._carla_unavailable:
                LOGGER.debug(
                    "No lead vehicle identified for overtaking request component '%s'",
                    context.component_spec.name,
                )
                return

        if self._carla_unavailable:
            self._emit_request(context, reason="carla_unavailable")
            return

        actor = context.actor
        lead_actor = resolve_vehicle_actor(context, self._lead_vehicle) if self._lead_vehicle else None
        if actor is None or lead_actor is None:
            return

        try:
            follower_transform = actor.get_transform()
            leader_transform = lead_actor.get_transform()
        except Exception:  # pragma: no cover - depends on CARLA API
            LOGGER.exception("Failed to evaluate vehicle transforms during overtaking trigger check")
            return

        metrics = relative_state(leader_transform, follower_transform)
        longitudinal = metrics["longitudinal"]
        lateral = metrics["lateral"]

        if longitudinal < 0.0 and abs(longitudinal) <= 15.0 and abs(lateral) <= 4.0:
            self._emit_request(context, metrics=metrics, reason="proximity_trigger")

    def _emit_request(
        self,
        context: ComponentContext,
        *,
        metrics: Optional[Dict[str, float]] = None,
        reason: str,
    ) -> None:
        payload = {
            "from_vehicle": context.vehicle_spec.name,
            "to_vehicle": self._lead_vehicle,
            "component": context.component_spec.name,
            "period_s": timedelta_to_seconds(context.component_spec.period),
            "wcet_s": timedelta_to_seconds(context.component_spec.wcet),
            "deadline_s": timedelta_to_seconds(context.component_spec.deadline),
            "priority": context.component_spec.priority,
            "link_budgets_s": dict(self._latency_budgets),
            "reason": reason,
        }
        if metrics:
            payload["relative_pose"] = metrics

        emit_connection_event(context, payload)
        context.scenario.properties[OVERTAKE_REQUEST_KEY] = payload

        state = ensure_overtake_state(context)
        state["phase"] = "awaiting_ack"
        state["lead_vehicle"] = self._lead_vehicle
        state["overtaker"] = context.vehicle_spec.name
        state.pop("cooldown", None)
        state["request_count"] = int(state.get("request_count", 0)) + 1

        self._request_active = True
        LOGGER.info(
            "Vehicle '%s' requested overtaking permission from '%s' (%s)",
            context.vehicle_spec.name,
            self._lead_vehicle,
            reason,
        )

    def _resolve_lead_vehicle(self, context: ComponentContext) -> Optional[str]:
        for connection in connections_by_src(context.component_spec, context.scenario):
            target = getattr(connection, "dst", "")
            if target and "." in target:
                return target.split(".", 1)[0]

        for vehicle in getattr(context.scenario, "vehicles", []):
            if vehicle.name != context.vehicle_spec.name:
                return vehicle.name
        return None