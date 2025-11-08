from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .model import ComponentSpec, ConnectionSpec, ScenarioSpec

LOGGER = logging.getLogger(__name__)


def _component_full_name(component: ComponentSpec) -> str:
    if component.vehicle:
        return f"{component.vehicle}.{component.name}"
    return component.name


def _latency_budget_seconds(connection: ConnectionSpec) -> Optional[float]:
    budget = connection.latency_budget
    if budget is None:
        return None
    try:
        seconds = float(budget.total_seconds())
    except AttributeError:
        return None
    if seconds < 0.0:
        LOGGER.warning(
            "Connection '%s' declared negative latency budget %.6fs; clamping to immediate delivery",
            connection.name,
            seconds,
        )
        return 0.0
    return seconds


@dataclass(slots=True)
class _ConnectionInfo:
    spec: ConnectionSpec
    dst_full_name: str
    latency_budget_s: Optional[float]


@dataclass(order=True, slots=True)
class _PendingDelivery:
    due_time: float
    sequence: int
    send_time: float = field(compare=False)
    src_full_name: str = field(compare=False)
    info: _ConnectionInfo = field(compare=False)
    payload: Any = field(compare=False)


@dataclass(slots=True)
class ConnectionDelivery:
    """Delivery record made available to destination components."""

    connection: ConnectionSpec
    payload: Any
    send_time: float
    delivery_time: float
    src: str

    @property
    def latency_s(self) -> float:
        return self.delivery_time - self.send_time


class ConnectionManager:
    """Manage logical message passing between component behaviours."""

    def __init__(self, scenario: ScenarioSpec) -> None:
        self._scenario = scenario
        self._by_src: Dict[str, List[_ConnectionInfo]] = {}
        self._inboxes: Dict[str, List[ConnectionDelivery]] = {}
        self._pending: List[_PendingDelivery] = []
        self._sequence = 0
        self._build_index()

    def _build_index(self) -> None:
        for connection in getattr(self._scenario, "connections", []):
            if not isinstance(connection, ConnectionSpec):
                continue
            latency_budget_s = _latency_budget_seconds(connection)
            info = _ConnectionInfo(
                spec=connection,
                dst_full_name=connection.dst,
                latency_budget_s=latency_budget_s,
            )
            self._by_src.setdefault(connection.src, []).append(info)

    def send(
        self,
        component: ComponentSpec,
        payload: Any,
        sim_time: float,
        connection_name: str | None = None,
    ) -> None:
        src_full_name = _component_full_name(component)
        destinations = self._by_src.get(src_full_name)
        if not destinations:
            LOGGER.debug(
                "Component '%s' attempted to emit on connection '%s' but has no declared outputs",
                src_full_name,
                connection_name or "<all>",
            )
            return

        dispatched = False
        for info in destinations:
            if connection_name is not None and info.spec.name != connection_name:
                continue
            due_time = sim_time + (info.latency_budget_s or 0.0)
            heapq.heappush(
                self._pending,
                _PendingDelivery(
                    due_time=due_time,
                    sequence=self._sequence,
                    send_time=sim_time,
                    src_full_name=src_full_name,
                    info=info,
                    payload=payload,
                ),
            )
            self._sequence += 1
            dispatched = True

        if not dispatched:
            LOGGER.debug(
                "Component '%s' has no connection named '%s' for emission",
                src_full_name,
                connection_name,
            )

    def advance(self, sim_time: float) -> None:
        """Deliver all pending messages whose budgets have elapsed."""

        while self._pending and self._pending[0].due_time <= sim_time + 1e-9:
            pending = heapq.heappop(self._pending)
            delivery = ConnectionDelivery(
                connection=pending.info.spec,
                payload=pending.payload,
                send_time=pending.send_time,
                delivery_time=sim_time,
                src=pending.src_full_name,
            )
            inbox = self._inboxes.setdefault(pending.info.dst_full_name, [])
            inbox.append(delivery)

            budget = pending.info.latency_budget_s
            if budget is not None:
                latency = delivery.latency_s
                if latency > budget + 1e-9:
                    LOGGER.warning(
                        "Delivery on connection '%s' exceeded latency budget by %.6fs",
                        pending.info.spec.name,
                        latency - budget,
                    )

    def consume(
        self,
        component: ComponentSpec,
        connection_name: str | None = None,
        *,
        flush: bool = True,
    ) -> List[ConnectionDelivery]:
        dest_full_name = _component_full_name(component)
        deliveries = self._inboxes.get(dest_full_name)
        if not deliveries:
            return []

        if connection_name is None and flush:
            self._inboxes.pop(dest_full_name, None)
            return list(deliveries)

        selected: List[ConnectionDelivery] = []
        remaining: List[ConnectionDelivery] = []
        for delivery in deliveries:
            if connection_name is None or delivery.connection.name == connection_name:
                selected.append(delivery)
                if not flush:
                    remaining.append(delivery)
            else:
                remaining.append(delivery)

        if flush:
            if remaining:
                self._inboxes[dest_full_name] = remaining
            else:
                self._inboxes.pop(dest_full_name, None)
        elif remaining or connection_name is None:
            # When not flushing, keep the original ordering intact.
            self._inboxes[dest_full_name] = deliveries

        return selected

    def pending_count(self) -> int:
        return len(self._pending)

    def inbox_size(self, component: ComponentSpec) -> int:
        return len(self._inboxes.get(_component_full_name(component), ()))