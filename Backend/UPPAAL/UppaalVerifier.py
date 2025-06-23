from __future__ import annotations

import datetime as _dt
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from textwrap import dedent
from typing import Dict, List, Tuple, Any
from pathlib import Path
from DSL.metamodel import Model, Component, Connection  # type: ignore

__all__ = [
    "UppaalVerifier",
]

# ---------------------------------------------------------------------------
# Helper conversion ---------------------------------------------------------
# ---------------------------------------------------------------------------

_RE_MS = re.compile(r"^\s*(?P<num>[0-9]+(?:\.[0-9]+)?)\s*ms\s*$", re.I)


def _get_latency_budget(conn) -> Any | None:
    """Return the raw value of *latency_budget* if present, else ``None``."""
    for key in (
            "latency_budget_ms",
            "latency_budget",
            "latencyBudgetMs",
            "latencyBudget",
    ):
        if hasattr(conn, key):
            return getattr(conn, key)
    # fall back to the generic attribute bag some parsers use
    return getattr(conn, "attributes", {}).get("latency_budget")


def _to_ms(value: Any | None) -> int | None:
    """Return *value* expressed in **integer milliseconds**.

    Accepts ``int`` (already ms), ``float`` (s), ``str`` such as ``"33ms"``
    or ``"0:00:00.033"``, and ``datetime.timedelta``.  ``None`` is returned
    unchanged so callers can keep optional fields optional.
    """

    if value is None:
        return None

    # Already an int → interpret as milliseconds directly
    if isinstance(value, int):
        return value

    # float → assume seconds
    if isinstance(value, float):
        return int(round(value * 1000))

    # timedelta
    if isinstance(value, _dt.timedelta):
        return int(round(value.total_seconds() * 1000))

    # str with ms
    if isinstance(value, str):
        s = value.strip()
        m = _RE_MS.match(s)
        if m:
            return int(float(m["num"]))
        # Maybe it is the default str(timedelta) → HH:MM:SS.ffffff
        try:
            h, m_, sec = s.split(":")
            seconds = float(sec)
            return int(round((int(h) * 3600 + int(m_) * 60 + seconds) * 1000))
        except Exception:
            pass
    raise TypeError(f"Cannot convert {value!r} to milliseconds – unsupported type")


# ---------------------------------------------------------------------------
# Public facade -------------------------------------------------------------
# ---------------------------------------------------------------------------

class QueryBundle:
    """Holds the path to the generated NTA and the query map for a run."""

    def __init__(self, nta_path: str, queries: Dict[str, str]):
        self.nta_path = nta_path
        self.queries = queries  # maps PROPERTY‑name → UPPAAL query (text)


class UppaalVerifier:
    """Translate a DSL model into UPPAAL, then call *verifyta* per property."""

    #: natural‑language pattern recognised by _emit_e2e_observer
    RESPONSE_RE = re.compile(
        r"^(?P<src>\w+)\s+to\s+(?P<dst>\w+)\s+response\s+within\s+(?P<val>\d+)\s*ms$",
        re.IGNORECASE,
    )

    def __init__(self, verifyta: str = "verifyta"):
        self.verifyta = verifyta

    # .....................................................................
    # Public API
    # .....................................................................

    def check(self, model: Model, props: List[str], xml_out: str = None) -> Dict[str, bool | None]:
        """Generate an NTA + queries and run them through *verifyta*.

        Returns a mapping *property‑name → bool | None* where:
        * ``True``  – property satisfied
        * ``False`` – property violated (counter‑example exists)
        * ``None``  – verifyta unavailable *or* PROPERTY not recognised
        """

        bundle = self._build_model(model)

        # Optional: keep a copy
        if xml_out is not None:
            dest = Path(xml_out)
            dest.unlink(missing_ok=True)
            Path(bundle.nta_path).rename(dest)
            bundle.nta_path = str(dest)

        results: Dict[str, bool | None] = {}

        for prop_name in props:
            query = bundle.queries.get(prop_name)
            if query is None:
                # The PROPERTY either does not exist or is not recognised
                results[prop_name] = None
                continue

            with tempfile.NamedTemporaryFile("w", suffix=".q", delete=False) as qf:
                qf.write(query)
                qfile = qf.name

            try:
                proc = subprocess.run(
                    [self.verifyta,
                     "-t", "0",  # ask for one counter-example
                     "-y",  # print the symbolic states
                     "-u",  # (optional) show a one-line summary at the end
                     bundle.nta_path,
                     qfile],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                out_lower = proc.stdout.lower()
                print(out_lower)
                results[prop_name] = (
                        "formula is satisfied" in out_lower
                        or "pass" in out_lower
                )
            except FileNotFoundError:
                # verifyta not installed or not on PATH
                results[prop_name] = None
            finally:
                os.remove(qfile)

        return results

    # .....................................................................
    # Internal helpers – model generation
    # .....................................................................

    def _build_model(self, model: Model) -> QueryBundle:  # noqa: C901 – long but clear
        """Serialise *model* to flat‑1_5 XML and return *(nta‑path, queries)*."""

        nta = ET.Element("nta")
        global_decl = ET.SubElement(nta, "declaration")

        # Broadcast channels for task lifecycle events
        global_decl.text = "".join(
            f"\n    broadcast chan start_{c.name}, done_{c.name};" for c in model.components.values()
        ) + "\n  "

        sys_inst: List[str] = []  # collects <system> instantiations
        queries: Dict[str, str] = {}

        # ------------------------------------------------------------------
        # Component templates
        # ------------------------------------------------------------------
        for comp in model.components.values():
            self._emit_component_template(nta, comp)
            sys_inst.append(f"P_{comp.name} = {comp.name}();")

        # ------------------------------------------------------------------
        # Connection‑latency observers
        # ------------------------------------------------------------------
        for conn in getattr(model, "connections", []):  # type: ignore[attr-defined]
            lat_raw = _get_latency_budget(conn)
            if lat_raw is None:
                continue
            conn.__dict__["__latency_ms"] = _to_ms(lat_raw)  # cache for observer
            tpl = self._emit_connection_observer(nta, conn)
            inst = f"I_{tpl}"
            sys_inst.append(f"{inst} = {tpl}();")

            src_comp = conn.src.split(".", 1)[0]
            dst_comp = conn.dst.split(".", 1)[0]
            prop_name = f"ConnLat_{src_comp}_{dst_comp}"
            queries[prop_name] = f"A[] not {inst}.bad"
            model.properties[prop_name] = queries[prop_name]  # expose synthetic

        # ------------------------------------------------------------------
        # DSL PROPERTY clauses
        # ------------------------------------------------------------------
        for prop_name, prop_text in model.properties.items():
            if prop_name in queries:
                continue  # already handled (connection observers)

            text = prop_text.strip().strip("\"")
            if text.startswith("E") or text.startswith("A"):
                queries[prop_name] = text  # raw UPPAAL query
                continue

            m = self.RESPONSE_RE.match(text)
            if m:
                src, dst, budget = m["src"], m["dst"], int(m["val"])
                tpl = self._emit_e2e_observer(nta, src, dst, budget, prop_name)
                inst = f"I_{tpl}"
                sys_inst.append(f"{inst} = {tpl}();")
                queries[prop_name] = f"A[] not {inst}.bad"

        # ------------------------------------------------------------------
        # <system> block
        # ------------------------------------------------------------------
        sys_block = ET.SubElement(nta, "system")
        proc_names = ", ".join(i.split(" = ")[0] for i in sys_inst)
        sys_block.text = "\n    " + "\n    ".join(sys_inst + [f"system {proc_names};"]) + "\n  "

        # ------------------------------------------------------------------
        # Persist temporary NTA file
        # ------------------------------------------------------------------
        tree = ET.ElementTree(nta)
        ET.indent(tree, space="  ", level=0)

        with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as xf:
            xf.write(
                "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
                "<!DOCTYPE nta PUBLIC \"-//Uppaal Team//DTD Flat System 1.5//EN\" "
                "\"http://www.it.uu.se/research/group/darts/uppaal/flat-1_5.dtd\">\n"
            )
            xf.write(ET.tostring(nta, encoding="unicode"))
            nta_path = xf.name

        return QueryBundle(nta_path, queries)

    # ------------------------------------------------------------------
    # Template builders
    # ------------------------------------------------------------------

    def _emit_component_template(self, root: ET.Element, comp: Component) -> None:
        period = _to_ms(getattr(comp, "period_ms", None) or getattr(comp, "period", None))
        wcet = _to_ms(getattr(comp, "wcet_ms", None) or getattr(comp, "wcet", None))
        deadline = _to_ms(getattr(comp, "deadline_ms", None) or getattr(comp, "deadline", None))

        tpl = ET.SubElement(root, "template")
        ET.SubElement(tpl, "name").text = comp.name
        decl = ["clock x;"]
        if deadline is not None:
            decl.append("clock d;")
        ET.SubElement(tpl, "declaration").text = "\n".join(decl)

        # Idle location
        idle = ET.SubElement(tpl, "location", id=f"{comp.name}_Idle")
        ET.SubElement(idle, "name").text = "Idle"
        ET.SubElement(idle, "label", kind="invariant").text = f"x <= {period}"

        # Exec location
        exe = ET.SubElement(tpl, "location", id=f"{comp.name}_Exec")
        ET.SubElement(exe, "name").text = "Exec"
        ET.SubElement(exe, "label", kind="invariant").text = f"x <= {wcet}"

        # (optional) Deadline-miss sink
        bad = None
        if deadline is not None:
            bad = ET.SubElement(tpl, "location", id=f"{comp.name}_DeadlineMiss")
            ET.SubElement(bad, "name").text = "bad"

        ET.SubElement(tpl, "init", ref=idle.get("id"))

        # Idle ➜ Exec – must fire exactly at x==period
        t1 = ET.SubElement(tpl, "transition")
        ET.SubElement(t1, "source", ref=idle.get("id"))
        ET.SubElement(t1, "target", ref=exe.get("id"))
        ET.SubElement(t1, "label", kind="guard").text = f"x == {period}"
        ET.SubElement(t1, "label", kind="synchronisation").text = f"start_{comp.name}!"
        ET.SubElement(t1, "label", kind="assignment").text = (
            f"x = 0{', d = ' + str(deadline) if deadline is not None else ''}"
        )

        # Exec ➜ Idle – finishes exactly at WCET
        t2 = ET.SubElement(tpl, "transition")
        ET.SubElement(t2, "source", ref=exe.get("id"))
        ET.SubElement(t2, "target", ref=idle.get("id"))
        ET.SubElement(t2, "label", kind="guard").text = f"x == {wcet}"
        ET.SubElement(t2, "label", kind="synchronisation").text = f"done_{comp.name}!"
        ET.SubElement(t2, "label", kind="assignment").text = "x = 0"

        # Exec ➜ DeadlineMiss (optional)
        if bad is not None:
            t3 = ET.SubElement(tpl, "transition")
            ET.SubElement(t3, "source", ref=exe.get("id"))
            ET.SubElement(t3, "target", ref=bad.get("id"))
            ET.SubElement(t3, "label", kind="guard").text = f"x > {deadline}"

    # .....................................................................
    # Connection latency observer
    # .....................................................................

    def _emit_connection_observer(self, root: ET.Element, conn: Connection) -> str:
        budget = conn.__dict__["__latency_ms"]

        src_comp = conn.src.split(".", 1)[0]
        dst_comp = conn.dst.split(".", 1)[0]

        tpl_name = f"Obs_{src_comp}_{dst_comp}"

        tpl = ET.SubElement(root, "template")
        ET.SubElement(tpl, "name").text = tpl_name
        ET.SubElement(tpl, "declaration").text = "clock t;"

        idle = ET.SubElement(tpl, "location", id=f"{tpl_name}_Idle")
        ET.SubElement(idle, "name").text = "Idle"

        wait = ET.SubElement(tpl, "location", id=f"{tpl_name}_Wait")
        ET.SubElement(wait, "name").text = "Wait"
        wait.set("invariant", f"t <= {budget}")

        bad = ET.SubElement(tpl, "location", id=f"{tpl_name}_Bad")
        ET.SubElement(bad, "name").text = "bad"

        ET.SubElement(tpl, "init", ref=idle.get("id"))

        tr1 = ET.SubElement(tpl, "transition")  # Idle → Wait
        ET.SubElement(tr1, "source", ref=idle.get("id"))
        ET.SubElement(tr1, "target", ref=wait.get("id"))
        ET.SubElement(tr1, "label", kind="synchronisation").text = f"done_{src_comp}?"
        ET.SubElement(tr1, "label", kind="assignment").text = "t = 0"

        tr2 = ET.SubElement(tpl, "transition")  # Wait → Idle
        ET.SubElement(tr2, "source", ref=wait.get("id"))
        ET.SubElement(tr2, "target", ref=idle.get("id"))
        ET.SubElement(tr2, "label", kind="synchronisation").text = f"start_{dst_comp}?"

        tr3 = ET.SubElement(tpl, "transition")  # Wait → Bad
        ET.SubElement(tr3, "source", ref=wait.get("id"))
        ET.SubElement(tr3, "target", ref=bad.get("id"))
        ET.SubElement(tr3, "label", kind="guard").text = f"t > {budget}"

        return tpl_name

    # .....................................................................
    # End‑to‑end response observer
    # .....................................................................

    def _emit_e2e_observer(
            self,
            root: ET.Element,
            src: str,
            dst: str,
            budget_ms: int,
            prop_name: str,
    ) -> str:
        tpl_name = f"Obs_{prop_name}"

        tpl = ET.SubElement(root, "template")
        ET.SubElement(tpl, "name").text = tpl_name
        ET.SubElement(tpl, "declaration").text = "clock t;"

        idle = ET.SubElement(tpl, "location", id=f"{tpl_name}_Idle")
        ET.SubElement(idle, "name").text = "Idle"

        wait = ET.SubElement(tpl, "location", id=f"{tpl_name}_Wait")
        ET.SubElement(wait, "name").text = "Wait"
        wait.set("invariant", f"t <= {budget_ms}")

        bad = ET.SubElement(tpl, "location", id=f"{tpl_name}_Bad")
        ET.SubElement(bad, "name").text = "bad"

        ET.SubElement(tpl, "init", ref=idle.get("id"))

        tr1 = ET.SubElement(tpl, "transition")  # Idle → Wait (src done)
        ET.SubElement(tr1, "source", ref=idle.get("id"))
        ET.SubElement(tr1, "target", ref=wait.get("id"))
        ET.SubElement(tr1, "label", kind="synchronisation").text = f"done_{src}?"
        ET.SubElement(tr1, "label", kind="assignment").text = "t = 0"

        tr2 = ET.SubElement(tpl, "transition")  # Wait → Idle (dst done)
        ET.SubElement(tr2, "source", ref=wait.get("id"))
        ET.SubElement(tr2, "target", ref=idle.get("id"))
        ET.SubElement(tr2, "label", kind="synchronisation").text = f"done_{dst}?"

        tr3 = ET.SubElement(tpl, "transition")  # Wait → Bad (timeout)
        ET.SubElement(tr3, "source", ref=wait.get("id"))
        ET.SubElement(tr3, "target", ref=bad.get("id"))
        ET.SubElement(tr3, "label", kind="guard").text = f"t > {budget_ms}"

        return tpl_name
