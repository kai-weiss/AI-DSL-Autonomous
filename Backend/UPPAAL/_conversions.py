from __future__ import annotations

import datetime as _dt
import re
from typing import Any

__all__ = ["get_latency_budget", "to_ms"]

_RE_MS = re.compile(r"^\s*(?P<num>[0-9]+(?:\.[0-9]+)?)\s*ms\s*$", re.I)


def get_latency_budget(conn) -> Any | None:
    """Return the raw value of *latency_budget* if present, else ``None``."""

    for key in (
        "latency_budget_ms",
        "latency_budget",
        "latencyBudgetMs",
        "latencyBudget",
    ):
        if hasattr(conn, key):
            return getattr(conn, key)

    return getattr(conn, "attributes", {}).get("latency_budget")


def to_ms(value: Any | None) -> int | None:
    """Return *value* expressed in **integer milliseconds**."""

    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(round(value * 1000))

    if isinstance(value, _dt.timedelta):
        return int(round(value.total_seconds() * 1000))

    if isinstance(value, str):
        s = value.strip()
        m = _RE_MS.match(s)
        if m:
            return int(float(m["num"]))
        try:
            h, m_, sec = s.split(":")
            seconds = float(sec)
            return int(round((int(h) * 3600 + int(m_) * 60 + seconds) * 1000))
        except Exception:
            pass

    raise TypeError(f"Cannot convert {value!r} to milliseconds – unsupported type")