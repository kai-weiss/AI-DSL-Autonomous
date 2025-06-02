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


@dataclass
class Model:
    components: dict[str, Component] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)
    properties: dict[str, str] = field(default_factory=dict)
