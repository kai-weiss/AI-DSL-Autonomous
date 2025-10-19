from __future__ import annotations

import logging
import math
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
        self._overtake_stage: Optional[str] = None
        self._original_lane_id: Optional[int] = None
        self._target_lane_id: Optional[int] = None
        self._overtake_direction: Optional[str] = None
        self._stuck_timer = 0.0

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

        if carla is not None:
            try:  # pragma: no cover - depends on CARLA API
                world = actor.get_world()
                car_map = world.get_map() if world is not None else None
            except Exception:
                LOGGER.exception("Unable to resolve world information for overtaking lane setup")
                car_map = None
            if car_map is not None:
                try:
                    current_wp = car_map.get_waypoint(
                        actor.get_location(),
                        project_to_road=True,
                        lane_type=carla.LaneType.Driving,
                    )
                except Exception:
                    LOGGER.exception("Failed to query current waypoint while preparing overtake")
                    current_wp = None
                if current_wp is not None:
                    direction, target_lane = self._choose_overtake_lane(current_wp)
                    if target_lane is None:
                        LOGGER.warning(
                            "Vehicle '%s' cannot find adjacent lane to start overtaking; aborting",
                            context.vehicle_spec.name,
                        )
                        self._finish_overtake(context, force=True)
                        return
                    self._original_lane_id = current_wp.lane_id
                    self._target_lane_id = target_lane.lane_id
                    self._overtake_direction = direction
                    self._overtake_stage = "change_out"
                else:
                    LOGGER.warning(
                        "Vehicle '%s' cannot resolve waypoint for overtaking; aborting",
                        context.vehicle_spec.name,
                    )
                    self._finish_overtake(context, force=True)
                    return
            else:
                LOGGER.warning(
                    "Vehicle '%s' missing map information for manual overtaking; aborting",
                    context.vehicle_spec.name,
                )
                self._finish_overtake(context, force=True)
                return
        else:
            LOGGER.warning(
                "Vehicle '%s' cannot perform manual overtake without CARLA API; aborting",
                context.vehicle_spec.name,
            )
            self._finish_overtake(context, force=True)
            return

        if traffic_manager is not None:
            call_tm_method(traffic_manager, "vehicle_percentage_speed_difference", actor, -50.0)

        self._activate_manual_override(context, actor)
        state = ensure_overtake_state(context)
        state["phase"] = "executing"
        state["lead_vehicle"] = self._lead_vehicle
        self._started = True
        self._elapsed = 0.0
        self._lane_change_requested = False
        self._return_requested = False

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

        if traffic_manager is not None:
            call_tm_method(traffic_manager, "vehicle_percentage_speed_difference", actor, -50.0)

        self._apply_manual_control(context, actor, metrics)
        if not self._started:
            return

        self._elapsed += dt

        if self._elapsed >= 15.0:
            LOGGER.warning(
                "Vehicle '%s' timed out while overtaking '%s'; forcing completion",
                context.vehicle_spec.name,
                self._lead_vehicle,
            )
            self._finish_overtake(context, force=True)

    def _apply_manual_control(
        self, context: ComponentContext, actor: Any, metrics: Optional[Dict[str, float]]
    ) -> None:
        if carla is None:
            return

        try:  # pragma: no cover - depends on CARLA API
            world = actor.get_world()
            car_map = world.get_map() if world is not None else None
        except Exception:
            LOGGER.exception("Unable to access world for manual overtaking control")
            return

        if car_map is None:
            return

        try:
            current_wp = car_map.get_waypoint(
                actor.get_location(),
                project_to_road=True,
                lane_type=carla.LaneType.Driving,
            )
        except Exception:
            LOGGER.exception("Unable to resolve current waypoint for manual overtaking control")
            return

        if current_wp is None:
            return

        if self._update_overtake_stage(context, current_wp, metrics):
            return

        control = self._compute_lane_following_control(actor, current_wp, metrics)
        if control is None:
            return

        try:
            actor.apply_control(control)
        except Exception:
            LOGGER.exception("Failed to apply manual control for overtaking vehicle")

    def _update_overtake_stage(
        self,
        context: ComponentContext,
        current_wp: Any,
        metrics: Optional[Dict[str, float]],
    ) -> bool:
        if self._overtake_stage is None and self._target_lane_id is not None:
            self._overtake_stage = "change_out"

        if self._overtake_stage == "change_out" and current_wp.lane_id == self._target_lane_id:
            LOGGER.info(
                "Vehicle '%s' moved onto overtaking lane", context.vehicle_spec.name
            )
            self._lane_change_requested = True
            self._overtake_stage = "overtaking"

        if self._overtake_stage == "overtaking":
            passed_lead = metrics is None or metrics.get("longitudinal", 0.0) > 8.0
            if passed_lead:
                LOGGER.info(
                    "Vehicle '%s' cleared lead vehicle and will return to original lane",
                    context.vehicle_spec.name,
                )
                self._return_requested = True
                self._overtake_stage = "returning"

        if self._overtake_stage == "returning":
            if current_wp.lane_id == self._original_lane_id:
                LOGGER.info(
                    "Vehicle '%s' returned to original lane after overtaking",
                    context.vehicle_spec.name,
                )
                self._finish_overtake(context)
                return True

        return False

    def _compute_lane_following_control(
        self, actor: Any, current_wp: Any, metrics: Optional[Dict[str, float]]
    ) -> Optional[Any]:
        if carla is None:
            return None

        if self._overtake_stage is None:
            return None

        target_wp = None
        if self._overtake_stage == "change_out":
            target_wp = self._adjacent_lane_waypoint(current_wp, self._overtake_direction)
        elif self._overtake_stage == "overtaking":
            target_wp = self._forward_waypoint(current_wp)
        elif self._overtake_stage == "returning":
            if current_wp.lane_id != self._original_lane_id:
                opposite = "right" if self._overtake_direction == "left" else "left"
                target_wp = self._adjacent_lane_waypoint(current_wp, opposite)
            else:
                target_wp = self._forward_waypoint(current_wp)

        if target_wp is None:
            return None

        try:  # pragma: no cover - depends on CARLA API
            vehicle_transform = actor.get_transform()
        except Exception:
            LOGGER.exception("Unable to read vehicle transform while computing control")
            return None

        control = carla.VehicleControl()
        control.hand_brake = False
        control.brake = 0.0
        control.throttle = self._compute_throttle(metrics)
        control.steer = self._compute_steer(vehicle_transform, target_wp.transform)

        return control

    def _compute_throttle(self, metrics: Optional[Dict[str, float]]) -> float:
        throttle = 0.65

        if metrics is not None:
            if metrics.get("longitudinal", 0.0) < 2.0:
                throttle = 0.75
            elif metrics["longitudinal"] > 12.0:
                throttle = 0.5

        if self._overtake_stage == "returning":
            throttle = min(throttle, 0.6)

        return max(0.4, min(0.85, throttle))

    def _compute_steer(self, vehicle_transform: Any, target_transform: Any) -> float:
        yaw = math.radians(vehicle_transform.rotation.yaw)
        forward_x = math.cos(yaw)
        forward_y = math.sin(yaw)
        right_x = -forward_y
        right_y = forward_x

        dx = target_transform.location.x - vehicle_transform.location.x
        dy = target_transform.location.y - vehicle_transform.location.y

        target_yaw = math.radians(target_transform.rotation.yaw)
        heading_error = target_yaw - yaw
        while heading_error > math.pi:
            heading_error -= 2 * math.pi
        while heading_error < -math.pi:
            heading_error += 2 * math.pi

        lateral_error = dx * right_x + dy * right_y

        steer = 0.8 * heading_error + 0.08 * lateral_error

        return max(-1.0, min(1.0, steer))

    def _forward_waypoint(self, waypoint: Any) -> Optional[Any]:
        if waypoint is None or carla is None:
            return None

        next_wps = waypoint.next(6.0)
        if next_wps:
            return next_wps[0]

        return waypoint

    def _adjacent_lane_waypoint(self, waypoint: Any, direction: Optional[str]) -> Optional[Any]:
        if waypoint is None or direction is None or carla is None:
            return None

        lane_getter = waypoint.get_left_lane if direction == "left" else waypoint.get_right_lane
        candidate = lane_getter()
        if candidate is None or candidate.lane_type != carla.LaneType.Driving:
            for lookahead in waypoint.next(2.5):
                lane_getter = lookahead.get_left_lane if direction == "left" else lookahead.get_right_lane
                candidate = lane_getter()
                if candidate is not None and candidate.lane_type == carla.LaneType.Driving:
                    break

        if candidate is None or candidate.lane_type != carla.LaneType.Driving:
            return None

        next_wps = candidate.next(4.0)
        if next_wps:
            return next_wps[0]

        return candidate

    def _choose_overtake_lane(self, waypoint: Any) -> tuple[Optional[str], Optional[Any]]:
        if carla is None:
            return (None, None)

        lanes = []

        lane_change_flag = waypoint.lane_change
        if lane_change_flag in {carla.LaneChange.Left, carla.LaneChange.Both}:
            left = waypoint.get_left_lane()
            if self._is_valid_adjacent_lane(waypoint, left):
                lanes.append(("left", left))

        if lane_change_flag in {carla.LaneChange.Right, carla.LaneChange.Both}:
            right = waypoint.get_right_lane()
            if self._is_valid_adjacent_lane(waypoint, right):
                lanes.append(("right", right))

        if not lanes:
            return (None, None)

        for direction, lane in lanes:
            if lane.lane_id == waypoint.lane_id:
                continue
            if waypoint.lane_id == 0 or lane.lane_id == 0:
                return direction, lane
            if (lane.lane_id > 0) == (waypoint.lane_id > 0):
                return direction, lane

        return lanes[0]

    def _is_valid_adjacent_lane(self, waypoint: Any, adjacent: Optional[Any]) -> bool:
        if carla is None or adjacent is None:
            return False

        if adjacent.lane_type != carla.LaneType.Driving:
            return False

        if adjacent.lane_id == waypoint.lane_id:
            return False

        if waypoint.lane_id != 0 and adjacent.lane_id != 0:
            if (adjacent.lane_id > 0) != (waypoint.lane_id > 0):
                return False

        return True

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
        self._overtake_stage = None
        self._original_lane_id = None
        self._target_lane_id = None
        self._overtake_direction = None
        self._stuck_timer = 0.0
