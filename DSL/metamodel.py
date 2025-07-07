from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class Component:
    name: str
    period: timedelta | None = None
    deadline: timedelta | None = None
    wcet: timedelta | None = None


@dataclass
class Connection:
    src: str
    dst: str
    latency_budget: timedelta | None = None


@dataclass
class Variable:
    """A tunable variable from an Optimisation block"""

    ref: str
    """Textual reference to the attribute (e.g. Camera.period)"""

    lower: timedelta
    upper: timedelta


@dataclass
class OptimisationSpec:
    variables:   list[Variable] = field(default_factory=list)
    objectives:  list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)


@dataclass
class Model:
    components: dict[str, Component] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)
    properties: dict[str, str] = field(default_factory=dict)
    optimisation: list[OptimisationSpec] = field(default_factory=dict)
