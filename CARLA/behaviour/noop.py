from __future__ import annotations

import logging

from .base import BaseBehaviour, ComponentContext

LOGGER = logging.getLogger(__name__)


class NoOpBehaviour(BaseBehaviour):
    """Behaviour that performs no action."""

    def setup(self, context: ComponentContext) -> None:
        LOGGER.debug(
            "Component '%s' on vehicle '%s' has no runtime behaviour",
            context.component_spec.name,
            context.vehicle_spec.name,
        )
