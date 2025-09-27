from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

from DSL.metamodel import Model  # type: ignore

from ._model_builder import ModelBuilder
from ._query_bundle import QueryBundle

__all__ = ["UppaalVerifier"]


class UppaalVerifier:
    """Translate a DSL model into UPPAAL XML format, then call verifyta per property."""

    RESPONSE_RE = re.compile(
        r"^(?P<src>\w+)\s+to\s+(?P<dst>\w+)\s+response\s+within\s+(?P<val>\d+)\s*ms$",
        re.IGNORECASE,
    )

    PIPELINE_RE = re.compile(
        r"^\s*PIPELINE\s+(?P<seq>.+?)\s+WITHIN\s+(?P<val>\d+)\s*ms\s*$",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(self, verifyta: str = "verifyta"):
        self.verifyta = verifyta
        self._builder = ModelBuilder(self.PIPELINE_RE)

    def check(self, model: Model, props: List[str], xml_out: str | None = None) -> Dict[str, bool | None]:
        """Generate an NTA + queries and run them through verifyta.
        Returns a mapping where:
        - True: property satisfied
        - False: property violated (counter-example exists)
        - None: verifyta unavailable or PROPERTY not recognised
        """

        bundle = self._builder.build(model)

        if xml_out is not None:
            dest = Path(xml_out)
            dest.unlink(missing_ok=True)
            Path(bundle.nta_path).rename(dest)
            bundle = QueryBundle(str(dest), bundle.queries)

        results: Dict[str, bool | None] = {}

        for prop_name in props:
            query = bundle.queries.get(prop_name)
            if query is None:
                raw = prop_name.strip()
                query = raw if raw.startswith("A") or raw.startswith("E") else f"A[] {raw}"

            with tempfile.NamedTemporaryFile("w", suffix=".q", delete=False) as qf:
                qf.write(query)
                qfile = qf.name

            try:
                proc = subprocess.run(
                    [
                        self.verifyta,
                        "-t",
                        "0",
                        "-y",
                        "-u",
                        bundle.nta_path,
                        qfile,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                out_lower = proc.stdout.lower()
                results[prop_name] = (
                    "formula is satisfied" in out_lower or "pass" in out_lower
                )
            except FileNotFoundError:
                results[prop_name] = None
            finally:
                os.remove(qfile)

        return results
