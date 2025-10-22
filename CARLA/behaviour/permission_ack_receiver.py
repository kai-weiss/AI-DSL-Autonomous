from __future__ import annotations

import json
import logging
from typing import Any

from .base import BaseBehaviour, ComponentContext
from .common import OVERTAKE_ACK_KEY, component_output_buffer

LOGGER = logging.getLogger(__name__)


class PermissionAckReceiverBehaviour(BaseBehaviour):
    """Relay permission acknowledgements to downstream components."""

    def __init__(self) -> None:
        self._last_signature: str | None = None

    def tick(self, context: ComponentContext, dt: float) -> None:  # noqa: ARG002 - behaviour API
        properties = getattr(context.scenario, "properties", None)
        if not isinstance(properties, dict):
            LOGGER.debug("Scenario properties missing; cannot observe permission acknowledgements")
            return

        ack_payload = properties.get(OVERTAKE_ACK_KEY)
        if not isinstance(ack_payload, dict):
            return

        if ack_payload.get("to_vehicle") not in {None, context.vehicle_spec.name}:
            return

        signature = self._serialise_payload(ack_payload)
        if signature == self._last_signature:
            return

        event = {
            "type": "permission_ack",
            "vehicle": context.vehicle_spec.name,
            "component": context.component_spec.name,
            "from_vehicle": ack_payload.get("from_vehicle"),
            "payload": ack_payload,
        }

        buffer = component_output_buffer(context)
        buffer.append(event)

        self._last_signature = signature
        LOGGER.info(
            "Vehicle '%s' received overtaking acknowledgement from '%s'",
            context.vehicle_spec.name,
            ack_payload.get("from_vehicle"),
        )

    @staticmethod
    def _serialise_payload(payload: Any) -> str:
        try:
            return json.dumps(payload, sort_keys=True, default=str)
        except TypeError:
            return repr(payload)
