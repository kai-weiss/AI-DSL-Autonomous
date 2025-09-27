from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Individual:
    """Represents a candidate solution returned from a multi-objective EA."""

    values: Dict[str, float]
    objectives: List[float]
    rank: int | None = None
    crowding_distance: float = 0.0


__all__ = ["Individual"]
