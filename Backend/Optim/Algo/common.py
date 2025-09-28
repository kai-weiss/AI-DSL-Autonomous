from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Deque, Dict, Iterable, List, Sequence
from collections import deque


def hypervolume_2d(front: Sequence[Sequence[float]], ref: Sequence[float]) -> float:
    """Compute the 2-D hypervolume of front w.r.t. ref for minimisation."""

    pts = [tuple(map(float, point)) for point in front]
    if not pts:
        return 0.0

    ref0, ref1 = float(ref[0]), float(ref[1])
    pts.sort(key=lambda pair: pair[0])

    hv = 0.0
    prev_f1 = ref1
    for f0, f1 in pts:
        hv += max(0.0, ref0 - f0) * max(0.0, prev_f1 - f1)
        prev_f1 = f1
    return hv


class PlateauDetector:
    """Tracks median hypervolume improvements to decide on early stopping."""

    def __init__(
        self,
        *,
        epsilon: float,
        window: int,
        ref_padding: float = 1.0,
    ) -> None:
        if window <= 0:
            raise ValueError("window must be positive")
        if epsilon < 0:
            raise ValueError("epsilon must be non-negative")

        self.epsilon = float(epsilon)
        self.window = int(window)
        self.ref_padding = float(ref_padding)

        self._hv_history: Deque[float] = deque(maxlen=self.window)
        self._best_median = float("-inf")
        self._last_improvement_gen = 0
        self._max_values: List[float] | None = None
        self._stopped = False

    @property
    def stopped(self) -> bool:
        return self._stopped

    def update(self, front: Iterable[Sequence[float]], generation: int) -> bool:
        front_list = [tuple(map(float, point)) for point in front]
        if not front_list:
            return False

        self._update_reference(front_list)
        ref_point = [value + self.ref_padding for value in self._max_values or []]
        hv_value = hypervolume_2d(front_list, ref_point)
        self._hv_history.append(hv_value)

        if self._best_median == float("-inf"):
            self._best_median = hv_value
            self._last_improvement_gen = generation

        if len(self._hv_history) < self.window:
            return False

        current_median = median(self._hv_history)
        if current_median - self._best_median > self.epsilon:
            self._best_median = current_median
            self._last_improvement_gen = generation
            return False

        if generation - self._last_improvement_gen >= self.window:
            self._stopped = True
            return True

        return False

    def _update_reference(self, front: Sequence[Sequence[float]]) -> None:
        if self._max_values is None:
            self._max_values = [float("-inf")] * len(front[0])

        for point in front:
            for idx, value in enumerate(point):
                self._max_values[idx] = max(self._max_values[idx], float(value))


@dataclass
class Individual:
    """Represents a candidate solution returned from a multi-objective EA."""

    values: Dict[str, float]
    objectives: List[float]
    rank: int | None = None
    crowding_distance: float = 0.0


__all__ = ["Individual", "PlateauDetector", "hypervolume_2d"]
