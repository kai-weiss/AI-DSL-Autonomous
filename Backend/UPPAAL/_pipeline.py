from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, Tuple

__all__ = ["emit_pipeline_observer", "find_predecessor"]


def find_predecessor(strip, comp_name: str, connections: Iterable) -> str | None:
    """
    Liefert den Namen der Komponente, die über eine DSL‑Connection als
    unmittelbarer Vorgänger von *comp_name* fungiert, oder None falls
    kein eindeutiger Vorgänger existiert.
    """
    preds = {
        strip(c.src.split(".")[-2])
        for c in connections
        if strip(c.dst.split(".")[-2]) == comp_name
    }
    return next(iter(preds)) if len(preds) == 1 else None


def emit_pipeline_observer(
    root: ET.Element,
    prop_name: str,
    seq: list[str],
    bound_ms: int,
    start_sync: str,
    conn_budget: Dict[Tuple[str, str], int],
) -> str:
    base = re.sub(r"\W+", "_", prop_name)
    tpl_name = f"PipeObs_{base}"

    first = seq[0]

    entry_budget = 0
    if start_sync.strip().startswith("done_"):
        try:
            _pred = start_sync.strip()[len("done_") : -1]
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
        loc = ET.SubElement(tpl, "location", id=f"{tpl_name}_{comp}")
        ET.SubElement(loc, "name").text = f"Wait_{comp}"
        ET.SubElement(loc, "label", kind="invariant").text = f"t <= {eff_bound}"
        wait_loc[comp] = loc
        time_guard_locs.append(loc)

    # For each pipeline edge create an intermediate wait location
    # this integrates periods and connection latency budgets
    conn_loc: dict[tuple[str, str], ET.Element] = {}
    for i in range(len(seq) - 1):
        curr, nxt = seq[i], seq[i + 1]
        conn = ET.SubElement(
            tpl, "location", id=f"{tpl_name}_Conn_{curr}_to_{nxt}"
        )
        ET.SubElement(conn, "name").text = f"Conn_{curr}_to_{nxt}"
        budget = conn_budget.get((curr, nxt), 0)
        inv_terms = [f"t <= {eff_bound}"]
        if budget > 0:
            inv_terms.append(f"e <= {budget}")
        ET.SubElement(conn, "label", kind="invariant").text = " && ".join(inv_terms)
        conn_loc[(curr, nxt)] = conn
        time_guard_locs.append(conn)

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
            ET.SubElement(tr0b_violate, "label", kind="guard").text = (
                f"e == {entry_budget}"
            )
        ET.SubElement(entry_conn, "label", kind="invariant").text = " && ".join(
            entry_inv_terms
        )
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

        # Only once the next component starts may we begin waiting for its completion
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