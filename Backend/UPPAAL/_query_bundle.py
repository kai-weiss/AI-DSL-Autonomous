from __future__ import annotations

from typing import Dict

__all__ = ["QueryBundle"]


class QueryBundle:
    """Holds the path to the generated NTA and the query map for a run."""

    def __init__(self, nta_path: str, queries: Dict[str, str]):
        self.nta_path = nta_path
        self.queries = queries