from __future__ import annotations

import logging
from typing import Dict, Optional

from .base import BaseBehaviour, ComponentContext
from .common import (
    OVERTAKE_ACK_KEY,
    OVERTAKE_REQUEST_KEY,
    call_tm_method,
    connections_by_src,
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

        if state.get("phase") == "idle":
            self._acknowledged = False
            return

        if self._acknowledged:
            return

        request = context.scenario.properties.get(OVERTAKE_REQUEST_KEY)
        if not isinstance(request, dict):
            return

        if request.get("to_vehicle") not in {None, context.vehicle_spec.name}:
            return

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

        context.scenario.properties[OVERTAKE_ACK_KEY] = ack_payload
        state["phase"] = "acknowledged"
        state["ack_count"] = int(state.get("ack_count", 0)) + 1
        self._acknowledged = True
        LOGGER.info(
            "Vehicle '%s' granted overtaking permission to '%s'",
            context.vehicle_spec.name,
            request.get("from_vehicle"),
        )
