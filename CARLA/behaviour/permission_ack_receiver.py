from __future__ import annotations

import json
import logging
from typing import Any

from .base import BaseBehaviour, ComponentContext
from .common import consume_connection_events, emit_connection_event

LOGGER = logging.getLogger(__name__)


class PermissionAckReceiverBehaviour(BaseBehaviour):
    """Relay permission acknowledgements to downstream components."""

    def __init__(self) -> None:
        self._last_signature: str | None = None

    def tick(self, context: ComponentContext, dt: float) -> None:  # noqa: ARG002 - behaviour API
        deliveries = consume_connection_events(context)
        if not deliveries:
            return

        for delivery in deliveries:
            ack_payload = delivery.payload
            if not isinstance(ack_payload, dict):
                LOGGER.debug(
                    "Discarding non-dict payload '%r' received on permission acknowledgement", ack_payload
                )
                continue

            if ack_payload.get("to_vehicle") not in {None, context.vehicle_spec.name}:
                continue

            signature = self._serialise_payload(ack_payload)
            if signature == self._last_signature:
                continue

            event = {
                "type": "permission_ack",
                "vehicle": context.vehicle_spec.name,
                "component": context.component_spec.name,
                "from_vehicle": ack_payload.get("from_vehicle"),
                "payload": ack_payload,
            }

            emit_connection_event(context, event)

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
