from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, List

from .behaviour import BehaviourRegistry, ComponentBehaviour, ComponentContext
from .behaviour.common import OVERTAKE_REQUEST_KEY, OVERTAKE_STATE_KEY
from .connections import ConnectionManager
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
    deadline_misses: int = 0
    wcet_overruns: int = 0
    total_execution_time_s: float = 0.0
    last_execution_time_s: float | None = None
    timing_armed: bool = False


    def _component_key(self) -> str:
        return f"{self.vehicle.name}:{self.component.name}"

    def _timing_active(self, scenario: ScenarioSpec) -> bool:
        state = scenario.properties.get(OVERTAKE_STATE_KEY)
        if isinstance(state, dict):
            phase = state.get("phase")
            if phase == "idle" or phase is None:
                self.timing_armed = False
            else:
                self.timing_armed = True
        elif scenario.properties.get(OVERTAKE_REQUEST_KEY):
            # Fall back to the legacy flag while the overtake state registry is initialised.
            self.timing_armed = True
        else:
            self.timing_armed = False
        return self.timing_armed

    def _run_tick(
        self,
        context: ComponentContext,
        duration_s: float | None,
        *,
        collect_timing: bool,
    ) -> tuple[float, bool]:
        start_wall = time.perf_counter()
        self.behaviour.tick(context, duration_s)
        elapsed = time.perf_counter() - start_wall
        if collect_timing:
            self.last_execution_time_s = elapsed
            self.total_execution_time_s += elapsed
        wcet_overrun = False
        if collect_timing and self.wcet_s is not None and elapsed > self.wcet_s + 1e-9:
            self.wcet_overruns += 1
            wcet_overrun = True
            LOGGER.warning(
                "Component '%s' on vehicle '%s' exceeded WCET (%.6fs > %.6fs)",
                self.component.name,
                self.vehicle.name,
                elapsed,
                self.wcet_s,
            )
        return elapsed, wcet_overrun

    def _record_metrics(
        self,
        scenario: ScenarioSpec,
        sim_time: float,
        activation_start: float,
        elapsed: float,
        wcet_overrun: bool,
        *,
        collect_timing: bool,
    ) -> None:
        if not collect_timing:
            return
        deadline_missed = False
        if self.next_deadline is not None:
            if sim_time > self.next_deadline + 1e-9:
                self.deadline_misses += 1
                deadline_missed = True
                LOGGER.warning(
                    "Component '%s' on vehicle '%s' missed deadline by %.6fs",
                    self.component.name,
                    self.vehicle.name,
                    sim_time - self.next_deadline,
                )
            self.next_deadline = None

        stats_registry = scenario.properties.setdefault("_component_timing", {})
        component_stats = stats_registry.setdefault(self._component_key(), {})
        component_stats.update(
            {
                "activation_count": self.activation_count,
                "last_release": self.last_release,
                "last_activation_start": activation_start,
                "last_completion_sim_time": sim_time,
                "last_execution_time_s": self.last_execution_time_s,
                "total_execution_time_s": self.total_execution_time_s,
                "deadline_misses": self.deadline_misses,
                "wcet_overruns": self.wcet_overruns,
                "deadline_missed_last": deadline_missed,
                "wcet_overrun_last": wcet_overrun,
                "elapsed_time_s": elapsed,
            }
        )

    def ensure_setup(
            self,
            scenario: ScenarioSpec,
            world: Any,
            connection_manager: ConnectionManager,
    ) -> None:
        if self.setup_complete:
            return
        context = ComponentContext(
            scenario=scenario,
            world=world,
            vehicle_spec=self.vehicle,
            component_spec=self.component,
            actor=self.actor,
            connection_manager=connection_manager,
        )
        self.behaviour.setup(context)
        self.setup_complete = True

    def step(
        self,
        scenario: ScenarioSpec,
        world: Any,
        sim_time: float,
        dt: float,
        connection_manager: ConnectionManager,
    ) -> None:
        self.ensure_setup(scenario, world, connection_manager)
        context = ComponentContext(
            scenario=scenario,
            world=world,
            vehicle_spec=self.vehicle,
            component_spec=self.component,
            actor=self.actor,
            connection_manager=connection_manager,
            sim_time=sim_time,
        )
        collect_timing = self._timing_active(scenario)
        if self.period_s is None:
            activation_start = sim_time
            self.last_release = activation_start
            if collect_timing and self.deadline_s is not None:
                self.next_deadline = self.last_release + self.deadline_s
            else:
                self.next_deadline = None
            elapsed, wcet_overrun = self._run_tick(
                context,
                dt,
                collect_timing=collect_timing,
            )
            if collect_timing:
                self.activation_count += 1
            self._record_metrics(
                scenario,
                sim_time,
                activation_start,
                elapsed,
                wcet_overrun,
                collect_timing=collect_timing,
            )
            connection_manager.advance(sim_time)
            return

        if self.next_activation is None:
            self.next_activation = max(sim_time, 0.0)

        # Trigger the behaviour for every elapsed period
        while self.next_activation is not None and sim_time + 1e-9 >= self.next_activation:
            activation_time = self.next_activation
            self.last_release = activation_time
            if collect_timing and self.deadline_s is not None:
                self.next_deadline = self.last_release + self.deadline_s
            else:
                self.next_deadline = None
            activation_start = sim_time
            elapsed, wcet_overrun = self._run_tick(
                context,
                self.period_s,
                collect_timing=collect_timing,
            )
            if collect_timing:
                self.activation_count += 1
            self._record_metrics(
                scenario,
                sim_time,
                activation_start,
                elapsed,
                wcet_overrun,
                collect_timing=collect_timing,
            )
            self.next_activation += self.period_s
            connection_manager.advance(sim_time)

    def teardown(
        self,
        scenario: ScenarioSpec,
        world: Any,
        connection_manager: ConnectionManager,
    ) -> None:
        context = ComponentContext(
            scenario=scenario,
            world=world,
            vehicle_spec=self.vehicle,
            component_spec=self.component,
            actor=self.actor,
            connection_manager=connection_manager,
        )
        self.behaviour.teardown(context)
        timing_registry = scenario.properties.get("_component_timing")
        if isinstance(timing_registry, dict):
            timing_registry.pop(self._component_key(), None)
            if not timing_registry:
                scenario.properties.pop("_component_timing", None)
        self.next_activation = None
        self.last_release = None
        self.next_deadline = None
        self.activation_count = 0
        self.deadline_misses = 0
        self.wcet_overruns = 0
        self.total_execution_time_s = 0.0
        self.last_execution_time_s = None


@dataclass
class Scheduler:
    """Co-ordinates component behaviours during the simulation."""

    scenario: ScenarioSpec
    registry: BehaviourRegistry = field(default_factory=BehaviourRegistry.with_default_behaviours)
    _components: List[_ComponentRuntime] = field(default_factory=list)
    _connection_manager: ConnectionManager = field(init=False)

    def __post_init__(self) -> None:
        self._connection_manager = ConnectionManager(self.scenario)

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
        self._connection_manager.advance(sim_time)
        for runtime in self._components:
            runtime.step(self.scenario, world, sim_time, dt, self._connection_manager)

    def teardown(self, world: Any) -> None:
        for runtime in self._components:
            runtime.teardown(self.scenario, world, self._connection_manager)

    def components(self) -> Iterable[_ComponentRuntime]:
        return tuple(self._components)