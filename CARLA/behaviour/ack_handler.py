from __future__ import annotations

import logging
import math
from typing import Any, Dict, Optional
import carla

from .base import BaseBehaviour, ComponentContext
from .common import (
    OVERTAKE_ACK_KEY,
    OVERTAKE_REQUEST_KEY,
    call_tm_method,
    connections_by_src,
    consume_connection_events,
    emit_connection_event,
    ensure_overtake_state,
    resolve_traffic_manager,
    timedelta_to_seconds,
)

LOGGER = logging.getLogger(__name__)


class AckHandlerBehaviour(BaseBehaviour):
    """Respond to a pending overtaking permission request."""

    def __init__(self) -> None:
        self._acknowledged = False
        self._latency_budgets: Dict[str, Optional[float]] = {}
        self._delay_logged = False
        self._pending_request: Optional[Dict[str, Any]] = None

    def setup(self, context: ComponentContext) -> None:
        LOGGER.info("Vehicle '%s' ready to handle overtaking acknowledgements", context.vehicle_spec.name)
        self._latency_budgets = {
            connection.name: timedelta_to_seconds(connection.latency_budget)
            for connection in connections_by_src(context.component_spec, context.scenario)
        }

        actor = context.actor
        traffic_manager = resolve_traffic_manager(context, context.vehicle_spec.name)
        if traffic_manager is not None and actor is not None:
            if call_tm_method(traffic_manager, "vehicle_percentage_speed_difference", actor, 45.0):
                LOGGER.info(
                    "Configured vehicle '%s' as slow lead (speed offset +45%%)",
                    context.vehicle_spec.name,
                )

    def tick(self, context: ComponentContext, dt: float) -> None:  # noqa: ARG002 - behaviour API
        state = ensure_overtake_state(context)

        for delivery in consume_connection_events(context):
            payload = delivery.payload
            if isinstance(payload, dict):
                context.scenario.properties[OVERTAKE_REQUEST_KEY] = payload
                self._pending_request = payload
            else:
                LOGGER.debug(
                    "Received unsupported payload '%r' on overtaking request connection", payload
                )

        if state.get("phase") == "idle":
            self._acknowledged = False
            self._delay_logged = False
            self._pending_request = None
            return

        if self._acknowledged:
            return

        request = self._pending_request or context.scenario.properties.get(OVERTAKE_REQUEST_KEY)
        if not isinstance(request, dict):
            return

        if request.get("to_vehicle") not in {None, context.vehicle_spec.name}:
            return

        actor = context.actor
        if actor is not None and self._should_delay_for_curve(actor):
            if not self._delay_logged:
                LOGGER.info(
                    "Vehicle '%s' postponing overtaking permission while navigating a curve or a junction",
                    context.vehicle_spec.name,
                )
                self._delay_logged = True
            return

        self._delay_logged = False

        ack_payload = {
            "from_vehicle": context.vehicle_spec.name,
            "to_vehicle": request.get("from_vehicle"),
            "component": context.component_spec.name,
            "period_s": timedelta_to_seconds(context.component_spec.period),
            "wcet_s": timedelta_to_seconds(context.component_spec.wcet),
            "deadline_s": timedelta_to_seconds(context.component_spec.deadline),
            "priority": context.component_spec.priority,
            "link_budgets_s": dict(self._latency_budgets),
            "request": request,
        }

        emit_connection_event(context, ack_payload)
        context.scenario.properties[OVERTAKE_ACK_KEY] = ack_payload
        state["phase"] = "acknowledged"
        state["ack_count"] = int(state.get("ack_count", 0)) + 1
        self._acknowledged = True
        self._pending_request = None
        LOGGER.info(
            "Vehicle '%s' granted overtaking permission to '%s'",
            context.vehicle_spec.name,
            request.get("from_vehicle"),
        )

    def _should_delay_for_curve(self, actor: Any) -> bool:
        if carla is None:
            return False

        try:  # pragma: no cover - depends on CARLA API
            world = actor.get_world()
            car_map = world.get_map() if world is not None else None
        except Exception:
            LOGGER.exception("Unable to access world while evaluating overtaking permission")
            return False

        if car_map is None:
            return False

        try:
            current_wp = car_map.get_waypoint(
                actor.get_location(),
                project_to_road=True,
                lane_type=carla.LaneType.Driving,
            )
        except Exception:
            LOGGER.exception("Unable to resolve waypoint while evaluating overtaking permission")
            return False

        if current_wp is None:
            return False

        return self._is_curved_segment(current_wp)

    def _is_curved_segment(self, waypoint: Any) -> bool:
        if carla is None or waypoint is None:
            return False

        try:
            if waypoint.is_junction:
                return True
        except AttributeError:
            pass

        try:
            start_transform = waypoint.transform
            start_location = start_transform.location
            start_yaw = start_transform.rotation.yaw
        except AttributeError:
            return True

        start_heading = math.radians(start_yaw)
        forward_vector = (math.cos(start_heading), math.sin(start_heading))
        right_vector = (-forward_vector[1], forward_vector[0])

        incremental_threshold = 3.0
        net_threshold = 5.0
        cumulative_threshold = 8.0
        lateral_threshold = 0.7

        step_distance = 5.0
        max_distance = 40.0

        cumulative_yaw = 0.0
        max_step_yaw = 0.0
        max_lateral_offset = 0.0

        samples = 0
        travelled = 0.0
        current = waypoint

        while travelled < max_distance:
            next_wps = current.next(step_distance)
            if not next_wps:
                break

            candidate = None
            branch_detected = False
            for potential in next_wps:
                same_lane = (
                    potential.road_id == current.road_id
                    and potential.lane_id == current.lane_id
                )
                if same_lane:
                    candidate = potential
                    break
            if candidate is None:
                candidate = next_wps[0]
                branch_detected = True
            else:
                branch_detected = any(
                    wp.road_id != current.road_id or wp.lane_id != current.lane_id
                    for wp in next_wps
                )

            try:
                candidate_transform = candidate.transform
                candidate_location = candidate_transform.location
                candidate_yaw = candidate_transform.rotation.yaw
            except AttributeError:
                return True

            delta_yaw = self._normalize_yaw_delta(
                candidate_yaw - current.transform.rotation.yaw
            )
            cumulative_yaw += abs(delta_yaw)
            max_step_yaw = max(max_step_yaw, abs(delta_yaw))

            net_delta = self._normalize_yaw_delta(candidate_yaw - start_yaw)

            dx = candidate_location.x - start_location.x
            dy = candidate_location.y - start_location.y
            lateral_offset = dx * right_vector[0] + dy * right_vector[1]
            max_lateral_offset = max(max_lateral_offset, abs(lateral_offset))

            samples += 1
            travelled += step_distance
            current = candidate

            if (
                abs(delta_yaw) > incremental_threshold
                or abs(net_delta) > net_threshold
                or cumulative_yaw > cumulative_threshold
                or abs(lateral_offset) > lateral_threshold
                or branch_detected
            ):
                return True

        if samples == 0:
            return True

        final_net = self._normalize_yaw_delta(
            current.transform.rotation.yaw - start_yaw
        )

        if (
            abs(final_net) > net_threshold
            or cumulative_yaw > cumulative_threshold
            or max_step_yaw > incremental_threshold
            or max_lateral_offset > lateral_threshold
        ):
            return True

        return False

    @staticmethod
    def _normalize_yaw_delta(delta: float) -> float:
        while delta > 180.0:
            delta -= 360.0
        while delta < -180.0:
            delta += 360.0
        return delta