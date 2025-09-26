from __future__ import annotations

import datetime as _dt
import os
import re
import itertools
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
    """Return the raw value of *latency_budget* if present, else None"""
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
    """Holds the path to the generated NTA and the query map for a run"""

    def __init__(self, nta_path: str, queries: Dict[str, str]):
        self.nta_path = nta_path
        self.queries = queries  # maps PROPERTY‑name → UPPAAL query (text)


class UppaalVerifier:
    """Translate a DSL model into UPPAAL XML format, then call verifyta per property"""

    #: natural‑language pattern recognised by _emit_e2e_observer
    RESPONSE_RE = re.compile(
        r"^(?P<src>\w+)\s+to\s+(?P<dst>\w+)\s+response\s+within\s+(?P<val>\d+)\s*ms$",
        re.IGNORECASE,
    )

    PIPELINE_RE = re.compile(
        r"^\s*PIPELINE\s+(?P<seq>.+?)\s+WITHIN\s+(?P<val>\d+)\s*ms\s*$",
        re.IGNORECASE | re.DOTALL,
    )

    def _strip_qual(self, name: str) -> str:
        """Return the last component of a dotted identifier"""
        return name.split(".")[-1]

    def __init__(self, verifyta: str = "verifyta"):
        self.verifyta = verifyta

    # .....................................................................
    # Public API
    # .....................................................................

    def check(self, model: Model, props: List[str], xml_out: str = None) -> Dict[str, bool | None]:
        """Generate an NTA + queries and run them through verifyta

        Returns a mapping where:
        - True: property satisfied
        - False: property violated (counter-example exists)
        - None: verifyta unavailable or PROPERTY not recognised
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
            # print(prop_name)
            query = bundle.queries.get(prop_name)
            # print(query)
            if query is None:
                raw = prop_name.strip()
                if raw.startswith("A") or raw.startswith("E"):
                    query = raw
                else:
                    query = f"A[] {raw}"

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
                # print(out_lower)
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
    # Internal helpers – model generation
    # .....................................................................
    def _build_model(self, model: Model) -> QueryBundle:
        """Serialise model to XML"""

        nta = ET.Element("nta")
        global_decl = ET.SubElement(nta, "declaration")

        # Broadcast channels for task lifecycle events
        global_decl.text = "".join(
            f"\n    broadcast chan start_{c.name}, done_{c.name};" for c in model.components.values()
        ) + "\n  "

        sys_inst: List[str] = []  # collects system instantiations
        queries: Dict[str, str] = {}

        # ------------------------------------------------------------------
        # Component templates
        # ------------------------------------------------------------------
        deadline_comps: List[str] = []
        for comp in model.components.values():
            self._emit_component_template(nta, comp)
            sys_inst.append(f"P_{comp.name} = {comp.name}();")
            if getattr(comp, "deadline", None) is not None:
                deadline_comps.append(comp.name)

        # Determine which components have incoming connections
        incoming: Dict[str, bool] = {c.name: False for c in model.components.values()}
        for conn in getattr(model, "connections", []):  # type: ignore[attr-defined]
            dst = conn.dst.split(".")[-2]
            dst = self._strip_qual(dst)
            incoming[dst] = True

        # ------------------------------------------------------------------
        # Connection drivers (glue – forward done→start)
        # ------------------------------------------------------------------
        driver_templates: set[str] = set()
        for conn in getattr(model, "connections", []):  # type: ignore[attr-defined]
            # Resolve component identifiers as used in the broadcast channels
            src_comp = self._strip_qual(conn.src.split(".")[-2])
            dst_comp = self._strip_qual(conn.dst.split(".")[-2])
            # Skip connections that refer to unknown components
            if src_comp not in model.components or dst_comp not in model.components:
                continue
            tpl_name = f"Conn_{src_comp}_to_{dst_comp}"
            if tpl_name in driver_templates:
                continue  # template already emitted & instantiated

            tpl = self._emit_connection_driver(nta, src_comp, dst_comp)
            driver_templates.add(tpl_name)
            inst = f"D_{tpl_name}"
            sys_inst.append(f"{inst} = {tpl_name}();")

        # ------------------------------------------------------------------
        # Environment triggers for components without inputs
        # ------------------------------------------------------------------
        for comp in model.components.values():
            period_val = getattr(comp, "period_ms", None) or getattr(comp, "period", None)
            if period_val is None and not incoming.get(comp.name):
                tpl = self._emit_env_trigger(nta, comp.name)
                inst = f"I_{tpl}"
                sys_inst.append(f"{inst} = {tpl}();")

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

            # Pipeline pattern
            m_pl = self.PIPELINE_RE.match(text)
            if m_pl:

                seq_txt = m_pl.group("seq")
                parts = [self._strip_qual(p.strip()) for p in seq_txt.split("->")]
                parts = [p for p in parts if p]  # leere Einträge entfernen

                # print(parts)

                first = parts[0]
                pred = self._find_predecessor(first,
                                              getattr(model, "connections", []))
                start_sync = f"done_{pred}?" if pred else f"start_{first}?"
                # print(start_sync)

                conn_budget: dict[tuple[str, str], int] = {}
                for c in getattr(model, "connections", []):
                    src = self._strip_qual(c.src.split(".")[-2])
                    dst = self._strip_qual(c.dst.split(".")[-2])
                    conn_budget[(src, dst)] = _to_ms(_get_latency_budget(c)) or 0

                # print(conn_budget)

                tpl = self._emit_pipeline_observer(
                    nta, prop_name, parts, int(m_pl.group("val")), start_sync, conn_budget)
                inst = f"I_{tpl}"
                sys_inst.append(f"{inst} = {tpl}();")
                queries[prop_name] = f"A[] not {inst}.bad"
                # print(queries)

            if "=" in text:
                fields = {}
                for part in text.split(";"):
                    part = part.strip()
                    if not part or "=" not in part:
                        continue
                    k, v = part.split("=", 1)
                    fields[k.strip()] = v.strip()

        if "deadline_misses==0" not in queries and deadline_comps:
            locs = [f"P_{n}.bad" for n in deadline_comps]
            if len(locs) == 1:
                expr = locs[0]
            else:
                expr = "(" + " || ".join(locs) + ")"
            queries["deadline_misses==0"] = f"A[] not {expr}"
            model.properties["deadline_misses==0"] = queries["deadline_misses==0"]

        # ------------------------------------------------------------------
        # system block
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
        period_val = getattr(comp, "period_ms", None) or getattr(comp, "period", None)
        period = _to_ms(period_val or 0)
        wcet = _to_ms(getattr(comp, "wcet_ms", None) or getattr(comp, "wcet", None) or 0)
        deadline = _to_ms(getattr(comp, "deadline_ms", None) or getattr(comp, "deadline", None))
        # fall back to WCET if no explicit deadline is provided
        if deadline is None:
            deadline = wcet

        is_event_driven = period_val is None

        tpl = ET.SubElement(root, "template")
        ET.SubElement(tpl, "name").text = comp.name
        decl = ["clock x;"]
        ET.SubElement(tpl, "declaration").text = "\n".join(decl)

        # Idle location
        idle = ET.SubElement(tpl, "location", id=f"{comp.name}_Idle")
        ET.SubElement(idle, "name").text = "Idle"
        if period and not is_event_driven:
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

        # Idle ➜ Exec
        t1 = ET.SubElement(tpl, "transition")
        ET.SubElement(t1, "source", ref=idle.get("id"))
        ET.SubElement(t1, "target", ref=exe.get("id"))

        if is_event_driven:
            ET.SubElement(t1, "label", kind="synchronisation").text = f"start_{comp.name}?"
        else:
            ET.SubElement(t1, "label", kind="guard").text = f"x == {period}"
            ET.SubElement(t1, "label", kind="synchronisation").text = f"start_{comp.name}!"
        ET.SubElement(t1, "label", kind="assignment").text = "x = 0"

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
    # Environment trigger for event‑driven components with no inputs
    # .....................................................................
    def _emit_env_trigger(self, root: ET.Element, comp_name: str) -> str:
        """Emit a simple template that fires ``start_<comp_name>!`` once at t=0."""

        tpl_name = f"Env_{comp_name}"
        tpl = ET.SubElement(root, "template")
        ET.SubElement(tpl, "name").text = tpl_name
        ET.SubElement(tpl, "declaration").text = "clock x;"

        idle = ET.SubElement(tpl, "location", id=f"{tpl_name}_Idle")
        ET.SubElement(idle, "name").text = "Idle"
        ET.SubElement(idle, "label", kind="invariant").text = "x <= 0"

        done = ET.SubElement(tpl, "location", id=f"{tpl_name}_Done")
        ET.SubElement(done, "name").text = "Done"

        ET.SubElement(tpl, "init", ref=idle.get("id"))

        tr = ET.SubElement(tpl, "transition")
        ET.SubElement(tr, "source", ref=idle.get("id"))
        ET.SubElement(tr, "target", ref=done.get("id"))
        ET.SubElement(tr, "label", kind="guard").text = "x == 0"
        ET.SubElement(tr, "label", kind="synchronisation").text = f"start_{comp_name}!"

        return tpl_name

    def _emit_pipeline_observer(
            self,
            root: ET.Element,
            prop_name: str,
            seq: list[str],
            bound_ms: int,
            start_sync: str,
            conn_budget: dict[tuple[str, str], int],
    ) -> str:

        base = re.sub(r"\W+", "_", prop_name)
        tpl_name = f"PipeObs_{base}"

        first = seq[0]

        entry_budget = 0
        if start_sync.strip().startswith("done_"):
            try:
                _pred = start_sync.strip()[len("done_"):-1]
                entry_budget = conn_budget.get((_pred, first), 0)
            except Exception:
                entry_budget = 0

        total_budget = entry_budget
        for i in range(len(seq) - 1):
            curr, nxt = seq[i], seq[i + 1]
            total_budget += conn_budget.get((curr, nxt), 0)

        eff_bound = max(bound_ms - total_budget, 0)

        tpl = ET.SubElement(root, "template")
        ET.SubElement(tpl, "name").text = tpl_name
        ET.SubElement(tpl, "declaration").text = "clock t; clock e;"

        # Locations
        idle = ET.SubElement(tpl, "location", id=f"{tpl_name}_Idle")
        ET.SubElement(idle, "name").text = "Idle"

        # For each component we create a location where we wait
        # for its completion; the adjusted end-to-end bound applies.
        wait_loc: dict[str, ET.Element] = {}
        time_guard_locs: list[ET.Element] = []
        for comp in seq:
            L = ET.SubElement(tpl, "location", id=f"{tpl_name}_{comp}")
            ET.SubElement(L, "name").text = f"Wait_{comp}"
            ET.SubElement(L, "label", kind="invariant").text = f"t <= {eff_bound}"
            wait_loc[comp] = L
            time_guard_locs.append(L)

        # For each pipeline edge create an intermediate wait location
        # this integrates periods and connection latency budgets
        conn_loc: dict[tuple[str, str], ET.Element] = {}
        for i in range(len(seq) - 1):
            curr, nxt = seq[i], seq[i + 1]
            C = ET.SubElement(tpl, "location", id=f"{tpl_name}_Conn_{curr}_to_{nxt}")
            ET.SubElement(C, "name").text = f"Conn_{curr}_to_{nxt}"
            budget = conn_budget.get((curr, nxt), 0)
            inv_terms = [f"t <= {eff_bound}"]
            if budget > 0:
                inv_terms.append(f"e <= {budget}")
            ET.SubElement(C, "label", kind="invariant").text = " && ".join(inv_terms)
            conn_loc[(curr, nxt)] = C
            time_guard_locs.append(C)

        bad = ET.SubElement(tpl, "location", id=f"{tpl_name}_Bad")
        ET.SubElement(bad, "name").text = "bad"

        done = ET.SubElement(tpl, "location", id=f"{tpl_name}_Done")
        ET.SubElement(done, "name").text = "Done"

        ET.SubElement(tpl, "init", ref=idle.get("id"))

        # Transitions

        # If the pipeline starts on a predecessors done, we must first
        # wait for start? before waiting for done?.
        if start_sync.strip().startswith("done_"):
            # reset e
            tr0 = ET.SubElement(tpl, "transition")
            ET.SubElement(tr0, "source", ref=idle.get("id"))
            entry_conn_id = f"{tpl_name}_Conn_ENTRY_to_{first}"
            entry_conn = ET.SubElement(tpl, "location", id=entry_conn_id)
            ET.SubElement(entry_conn, "name").text = f"Conn_ENTRY_to_{first}"
            entry_inv_terms = [f"t <= {eff_bound}"]
            if entry_budget > 0:
                entry_inv_terms.append(f"e <= {entry_budget}")
                tr0b_violate = ET.SubElement(tpl, "transition")
                ET.SubElement(tr0b_violate, "source", ref=entry_conn_id)
                ET.SubElement(tr0b_violate, "target", ref=bad.get("id"))
                ET.SubElement(tr0b_violate, "label", kind="guard").text = f"e == {entry_budget}"
            ET.SubElement(entry_conn, "label", kind="invariant").text = " && ".join(entry_inv_terms)
            time_guard_locs.append(entry_conn)
            ET.SubElement(tr0, "target", ref=entry_conn_id)
            ET.SubElement(tr0, "label", kind="synchronisation").text = start_sync
            ET.SubElement(tr0, "label", kind="assignment").text = "t = 0, e = 0"

            # Conn_ENTRY_to_first --start_first?--> Wait_first
            tr0b = ET.SubElement(tpl, "transition")
            ET.SubElement(tr0b, "source", ref=entry_conn_id)
            ET.SubElement(tr0b, "target", ref=wait_loc[first].get("id"))
            ET.SubElement(tr0b, "label", kind="synchronisation").text = f"start_{first}?"

        else:
            # Idle --start_first?--> Wait_first
            tr_start = ET.SubElement(tpl, "transition")
            ET.SubElement(tr_start, "source", ref=idle.get("id"))
            ET.SubElement(tr_start, "target", ref=wait_loc[first].get("id"))
            ET.SubElement(tr_start, "label", kind="synchronisation").text = start_sync
            ET.SubElement(tr_start, "label", kind="assignment").text = "t = 0"

        # For each internal edge: Wait_curr --done_curr?--> Conn_curr_to_next --start_next?--> Wait_next
        for i in range(len(seq) - 1):
            curr, nxt = seq[i], seq[i + 1]
            # Wait for the current component to finish
            tr1 = ET.SubElement(tpl, "transition")
            ET.SubElement(tr1, "source", ref=wait_loc[curr].get("id"))
            ET.SubElement(tr1, "target", ref=conn_loc[(curr, nxt)].get("id"))
            ET.SubElement(tr1, "label", kind="synchronisation").text = f"done_{curr}?"
            ET.SubElement(tr1, "label", kind="assignment").text = "e = 0"

            # Enforce per‑connection budget on the waiting time until next starts
            budget = conn_budget.get((curr, nxt), 0)
            if budget > 0:
                tr_budget = ET.SubElement(tpl, "transition")
                ET.SubElement(tr_budget, "source", ref=conn_loc[(curr, nxt)].get("id"))
                ET.SubElement(tr_budget, "target", ref=bad.get("id"))
                ET.SubElement(tr_budget, "label", kind="guard").text = f"e == {budget}"

            # Only once the next component *starts* may we begin waiting for its completion
            tr2 = ET.SubElement(tpl, "transition")
            ET.SubElement(tr2, "source", ref=conn_loc[(curr, nxt)].get("id"))
            ET.SubElement(tr2, "target", ref=wait_loc[nxt].get("id"))
            ET.SubElement(tr2, "label", kind="synchronisation").text = f"start_{nxt}?"

        # Last completion closes the pipeline within the E2E bound
        last = seq[-1]
        tr_done = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_done, "source", ref=wait_loc[last].get("id"))
        ET.SubElement(tr_done, "target", ref=done.get("id"))
        ET.SubElement(tr_done, "label", kind="synchronisation").text = f"done_{last}?"
        ET.SubElement(tr_done, "label", kind="guard").text = f"t <= {eff_bound}"

        # Global timeout from every location where time may elapse
        for loc in time_guard_locs:
            tr_to_bad = ET.SubElement(tpl, "transition")
            ET.SubElement(tr_to_bad, "source", ref=loc.get("id"))
            ET.SubElement(tr_to_bad, "target", ref=bad.get("id"))
            ET.SubElement(tr_to_bad, "label", kind="guard").text = f"t == {eff_bound}"

        # Allow re‑use
        tr_reset = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_reset, "source", ref=done.get("id"))
        ET.SubElement(tr_reset, "target", ref=idle.get("id"))

        return tpl_name

    # --------------------------------------------------------------
    # Connection driver: leitet done→start weiter
    # --------------------------------------------------------------
    def _emit_connection_driver(self, root: ET.Element,
                                src_comp: str, dst_comp: str) -> str:
        """
        Erzeugt ein kleines UPPAAL‑Template, das bei
            done_<src_comp>?   ⇒   start_<dst_comp>!
        sofort in derselben Taktung auslöst.

        Wegen der „nur ein Sync‑Label“-Regel werden zwei
        Übergänge verwendet (Idle → Trig → Idle).
        """
        tpl_name = f"Conn_{src_comp}_to_{dst_comp}"

        tpl = ET.SubElement(root, "template")
        ET.SubElement(tpl, "name").text = tpl_name

        # States ----------------------------------------------------
        idle = ET.SubElement(tpl, "location", id=f"{tpl_name}_Idle")
        ET.SubElement(idle, "name").text = "Idle"

        trig = ET.SubElement(tpl, "location", id=f"{tpl_name}_Trig")
        ET.SubElement(trig, "name").text = "Trig"
        ET.SubElement(trig, "committed")  # sofortiger Rücksprung

        ET.SubElement(tpl, "init", ref=idle.get("id"))

        # 1. warten auf done_src?
        t1 = ET.SubElement(tpl, "transition")
        ET.SubElement(t1, "source", ref=idle.get("id"))
        ET.SubElement(t1, "target", ref=trig.get("id"))
        ET.SubElement(t1, "label", kind="synchronisation").text = f"done_{src_comp}?"

        # 2. sofort start_dst! senden
        t2 = ET.SubElement(tpl, "transition")
        ET.SubElement(t2, "source", ref=trig.get("id"))
        ET.SubElement(t2, "target", ref=idle.get("id"))
        ET.SubElement(t2, "label", kind="synchronisation").text = f"start_{dst_comp}!"

        return tpl_name

    def _find_predecessor(self, comp_name: str, connections) -> str | None:
        """
        Liefert den Namen der Komponente, die über eine DSL‑Connection als
        unmittelbarer Vorgänger von *comp_name* fungiert, oder None falls
        kein eindeutiger Vorgänger existiert.
        """
        preds = {
            self._strip_qual(c.src.split(".")[-2])
            for c in connections
            if self._strip_qual(c.dst.split(".")[-2]) == comp_name
        }
        return next(iter(preds)) if len(preds) == 1 else None
