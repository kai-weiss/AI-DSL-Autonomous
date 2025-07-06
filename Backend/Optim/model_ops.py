from __future__ import annotations

import copy
import re
from datetime import timedelta
from typing import Dict, Iterable

from DSL.metamodel import Model, Variable


CONN_RE = re.compile(r"\((?P<src>\w+)\.(?P<src_port>\w+)->(?P<dst>\w+)\.(?P<dst_port>\w+)\)\.(?P<attr>\w+)")


def apply_values(model: Model, assignments: Dict[str, timedelta]) -> Model:
    """Return a new model with variable assignments applied"""
    new_model = copy.deepcopy(model)
    for ref, value in assignments.items():
        m = CONN_RE.match(ref)
        if m:
            src = f"{m.group('src')}.{m.group('src_port')}"
            dst = f"{m.group('dst')}.{m.group('dst_port')}"
            attr = m.group('attr')
            for c in new_model.connections:
                if c.src == src and c.dst == dst:
                    setattr(c, attr, value)
                    break
            continue
        comp_name, attr = ref.split('.', 1)
        comp = new_model.components.get(comp_name)
        if comp is not None:
            setattr(comp, attr, value)
    return new_model


def variable_bounds(spec: Iterable[Variable]) -> Dict[str, tuple[float, float]]:
    bounds = {}
    for var in spec:
        low = var.lower.total_seconds() * 1000.0
        high = var.upper.total_seconds() * 1000.0
        bounds[var.ref] = (low, high)
    return bounds
