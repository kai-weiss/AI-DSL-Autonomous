from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, List

from .behaviour import BehaviourRegistry, ComponentBehaviour, ComponentContext
from .model import ComponentSpec, ScenarioSpec, VehicleSpec

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class _ComponentRuntime:
    component: ComponentSpec
    vehicle: VehicleSpec
    behaviour: ComponentBehaviour
    period_s: float | None
    deadline_s: float | None
    wcet_s: float | None
    next_activation: float | None = None
    last_release: float | None = None
    next_deadline: float | None = None
    activation_count: int = 0
    actor: Any = None
    setup_complete: bool = False

    def ensure_setup(self, scenario: ScenarioSpec, world: Any) -> None:
        if self.setup_complete:
            return
        context = ComponentContext(
            scenario=scenario,
            world=world,
            vehicle_spec=self.vehicle,
            component_spec=self.component,
            actor=self.actor,
        )
        self.behaviour.setup(context)
        self.setup_complete = True

    def step(self, scenario: ScenarioSpec, world: Any, sim_time: float, dt: float) -> None:
        self.ensure_setup(scenario, world)
        context = ComponentContext(
            scenario=scenario,
            world=world,
            vehicle_spec=self.vehicle,
            component_spec=self.component,
            actor=self.actor,
        )
        if self.period_s is None:
            self.behaviour.tick(context, dt)
            return

        if self.next_activation is None:
            self.next_activation = 0.0

        # Trigger the behaviour for every elapsed period
        while self.next_activation is not None and sim_time + 1e-9 >= self.next_activation:
            activation_time = self.next_activation
            self.last_release = activation_time
            if self.deadline_s is not None:
                self.next_deadline = activation_time + self.deadline_s
            else:
                self.next_deadline = None
            self.behaviour.tick(context, self.period_s)
            self.activation_count += 1
            self.next_activation += self.period_s
    def teardown(self, scenario: ScenarioSpec, world: Any) -> None:
        context = ComponentContext(
            scenario=scenario,
            world=world,
            vehicle_spec=self.vehicle,
            component_spec=self.component,
            actor=self.actor,
        )
        self.behaviour.teardown(context)


@dataclass
class Scheduler:
    """Co-ordinates component behaviours during the simulation."""

    scenario: ScenarioSpec
    registry: BehaviourRegistry = field(default_factory=BehaviourRegistry.with_default_behaviours)
    _components: List[_ComponentRuntime] = field(default_factory=list)

    def bind_vehicle(self, vehicle: VehicleSpec, actor: Any) -> None:
        for component in vehicle.components:
            behaviour_name = component.behaviour
            if behaviour_name is None and vehicle.autopilot:
                behaviour_name = "autopilot"
            try:
                behaviour = self.registry.create(behaviour_name, component, vehicle)
            except KeyError:
                LOGGER.warning(
                    "Component '%s' on vehicle '%s' requested unknown behaviour '%s'",
                    component.name,
                    vehicle.name,
                    behaviour_name,
                )
                behaviour = self.registry.create("noop", component, vehicle)
            except ValueError as exc:
                LOGGER.warning("%s", exc)
                behaviour = self.registry.create("noop", component, vehicle)

            period_s = None
            if component.period is not None:
                seconds = component.period.total_seconds()
                if seconds <= 0:
                    LOGGER.warning(
                        "Component '%s' on vehicle '%s' declared non-positive period %.3fs; treated as event-driven",
                        component.name,
                        vehicle.name,
                        seconds,
                    )
                else:
                    period_s = seconds

            deadline_s = None
            if component.deadline is not None:
                seconds = component.deadline.total_seconds()
                if seconds <= 0:
                    LOGGER.warning(
                        "Component '%s' on vehicle '%s' declared non-positive deadline %.3fs; deadline ignored",
                        component.name,
                        vehicle.name,
                        seconds,
                    )
                else:
                    deadline_s = seconds

            wcet_s = None
            if component.wcet is not None:
                seconds = component.wcet.total_seconds()
                if seconds <= 0:
                    LOGGER.warning(
                        "Component '%s' on vehicle '%s' declared non-positive WCET %.3fs; WCET ignored",
                        component.name,
                        vehicle.name,
                        seconds,
                    )
                else:
                    wcet_s = seconds

            runtime = _ComponentRuntime(
                component=component,
                vehicle=vehicle,
                behaviour=behaviour,
                period_s=period_s,
                deadline_s=deadline_s,
                wcet_s=wcet_s,
                actor=actor,
            )
            self._components.append(runtime)

    def step(self, world: Any, sim_time: float, dt: float) -> None:
        for runtime in self._components:
            runtime.step(self.scenario, world, sim_time, dt)

    def teardown(self, world: Any) -> None:
        for runtime in self._components:
            runtime.teardown(self.scenario, world)

    def components(self) -> Iterable[_ComponentRuntime]:
        return tuple(self._components)