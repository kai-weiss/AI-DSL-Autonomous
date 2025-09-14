from __future__ import annotations

import copy
import re
from datetime import timedelta
from typing import Dict, Iterable
from collections import defaultdict
from itertools import chain as it_chain

from DSL.metamodel import Model, Variable

CONN_RE = re.compile(
    r"""^
        (?P<src>[^.]+(?:\.[^.]+)*)     # A.AckHandler_A
        \.(?P<src_port>\w+)            # output
        \s*->\s*
        (?P<dst>[^.]+(?:\.[^.]+)*)     # B.PermissionAckRx_B
        \.(?P<dst_port>\w+)            # input
        \.(?P<attr>\w+)$               # latency_budget
    """,
    re.X,
)
CONN_ATTRS = {"latency_budget"}


def apply_values(model, assignments: Dict[str, timedelta]):
    """Return a new model with variable assignments applied"""
    new_model = copy.deepcopy(model)

    for ref, value in assignments.items():
        obj, attr = ref.rsplit(".", 1)  # always two parts
        # print(obj)
        # CONNECTION attributes
        if attr in CONN_ATTRS:
            conn = next(
                (c for c in new_model.connections if c.name == obj),
                None
            )
            if conn is None:
                raise KeyError(f"Connection '{obj}' not found")
            setattr(conn, attr, value)
            continue

        # component attributes
        else:
            comp_key = obj.split(".", 1)[-1]
            comp = new_model.components.get(comp_key)
            if comp is None:
                raise KeyError(f"Component '{comp_key}' not found")

            target = attr if hasattr(comp, attr) else attr.lower()
            setattr(comp, target, value)

    return new_model


def variable_bounds(spec: Iterable[Variable]) -> Dict[str, tuple[float, float]]:
    bounds = {}
    for var in spec:
        low = var.lower.total_seconds() * 1000.0
        high = var.upper.total_seconds() * 1000.0
        bounds[var.ref] = (low, high)
    return bounds


def _graph(model):
    """adjacency list"""
    g = defaultdict(list)
    for c in model.connections:
        g[c.src].append((c.dst, c))
    return g


def _sources_and_sinks(model):
    all_src = {c.src for c in model.connections}
    all_dst = {c.dst for c in model.connections}
    sources = all_src - all_dst or set(model.components)  # fall-back: every node
    sinks = all_dst - all_src or set(model.components)
    return sources, sinks


def _enumerate_chains(model, max_len=10):
    """yield (comp_names, conn_objs) for each simple path source→sink"""
    g = _graph(model)
    srcs, sinks = _sources_and_sinks(model)

    def dfs(node, comps, conns):
        if node in sinks:
            yield comps[:], conns[:]
        if len(comps) >= max_len:
            return
        for dst, conn in g.get(node, []):
            comps.append(dst);
            conns.append(conn)
            yield from dfs(dst, comps, conns)
            comps.pop();
            conns.pop()

    for s in srcs:
        yield from dfs(s, [s], [])
