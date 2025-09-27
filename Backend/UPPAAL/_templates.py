from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, List

from DSL.metamodel import Component  # type: ignore

from _conversions import to_ms

__all__ = [
    "emit_component_template",
    "emit_connection_driver",
    "emit_env_trigger",
    "emit_periodic_timer",
    "emit_scheduler_template",
]


def emit_component_template(
    root: ET.Element, comp: Component, idx: int, sched_prefix: str
) -> None:
    period_val = getattr(comp, "period_ms", None) or getattr(comp, "period", None)
    period = to_ms(period_val or 0)
    wcet = to_ms(getattr(comp, "wcet_ms", None) or getattr(comp, "wcet", None) or 0)
    deadline = to_ms(
        getattr(comp, "deadline_ms", None) or getattr(comp, "deadline", None)
    )
    # fall back to WCET if no explicit deadline is provided
    if deadline is None:
        deadline = wcet

    is_event_driven = period_val is None

    tpl = ET.SubElement(root, "template")
    ET.SubElement(tpl, "name").text = comp.name
    decl = ["clock x;", "clock e;"]
    ET.SubElement(tpl, "declaration").text = "\n".join(decl)

    # Locations --------------------------------------------------
    idle = ET.SubElement(tpl, "location", id=f"{comp.name}_Idle")
    ET.SubElement(idle, "name").text = "Idle"
    if period and not is_event_driven:
        ET.SubElement(idle, "label", kind="invariant").text = f"x <= {period}"

    ready_loc = ET.SubElement(tpl, "location", id=f"{comp.name}_Ready")
    ET.SubElement(ready_loc, "name").text = "Ready"

    exe = ET.SubElement(tpl, "location", id=f"{comp.name}_Exec")
    ET.SubElement(exe, "name").text = "Exec"
    exe_inv = [f"e <= {wcet}"]
    if deadline is not None:
        exe_inv.append(f"x <= {deadline}")
    ET.SubElement(exe, "label", kind="invariant").text = " && ".join(exe_inv)

    bad = None
    if deadline is not None:
        bad = ET.SubElement(tpl, "location", id=f"{comp.name}_DeadlineMiss")
        ET.SubElement(bad, "name").text = "bad"

    ET.SubElement(tpl, "init", ref=idle.get("id"))

    # Idle --release?--> Ready (job released)
    tr_rel = ET.SubElement(tpl, "transition")
    ET.SubElement(tr_rel, "source", ref=idle.get("id"))
    ET.SubElement(tr_rel, "target", ref=ready_loc.get("id"))
    ET.SubElement(tr_rel, "label", kind="synchronisation").text = f"release_{comp.name}?"
    ready_arr = f"ready_{sched_prefix}"
    ET.SubElement(tr_rel, "label", kind="assignment").text = (
        f"x = 0, {ready_arr}[{idx}] = true"
    )

    # Ready --start?--> Exec (dispatched by scheduler)
    tr_start = ET.SubElement(tpl, "transition")
    ET.SubElement(tr_start, "source", ref=ready_loc.get("id"))
    ET.SubElement(tr_start, "target", ref=exe.get("id"))
    ET.SubElement(tr_start, "label", kind="synchronisation").text = f"start_{comp.name}?"
    ET.SubElement(tr_start, "label", kind="assignment").text = "e = 0"

    # Exec --done!--> Idle
    tr_done = ET.SubElement(tpl, "transition")
    ET.SubElement(tr_done, "source", ref=exe.get("id"))
    ET.SubElement(tr_done, "target", ref=idle.get("id"))
    ET.SubElement(tr_done, "label", kind="guard").text = f"e == {wcet}"
    ET.SubElement(tr_done, "label", kind="synchronisation").text = f"done_{comp.name}!"
    ET.SubElement(tr_done, "label", kind="assignment").text = "x = 0"

    # Deadline violations (if specified)
    if bad is not None:
        tr_ready_bad = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_ready_bad, "source", ref=ready_loc.get("id"))
        ET.SubElement(tr_ready_bad, "target", ref=bad.get("id"))
        ET.SubElement(tr_ready_bad, "label", kind="guard").text = f"x > {deadline}"

        tr_exec_bad = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_exec_bad, "source", ref=exe.get("id"))
        ET.SubElement(tr_exec_bad, "target", ref=bad.get("id"))
        ET.SubElement(tr_exec_bad, "label", kind="guard").text = f"x > {deadline}"


def emit_periodic_timer(root: ET.Element, comp_name: str, period_ms: int) -> str:
    """Periodic timer to trigger releases"""
    tpl_name = f"Timer_{comp_name}"
    tpl = ET.SubElement(root, "template")
    ET.SubElement(tpl, "name").text = tpl_name
    ET.SubElement(tpl, "declaration").text = "clock t;"

    wait = ET.SubElement(tpl, "location", id=f"{tpl_name}_Wait")
    ET.SubElement(wait, "name").text = "Wait"
    ET.SubElement(wait, "label", kind="invariant").text = f"t <= {period_ms}"

    ET.SubElement(tpl, "init", ref=wait.get("id"))

    tr = ET.SubElement(tpl, "transition")
    ET.SubElement(tr, "source", ref=wait.get("id"))
    ET.SubElement(tr, "target", ref=wait.get("id"))
    ET.SubElement(tr, "label", kind="guard").text = f"t == {period_ms}"
    ET.SubElement(tr, "label", kind="synchronisation").text = f"release_{comp_name}!"
    ET.SubElement(tr, "label", kind="assignment").text = "t = 0"

    return tpl_name


def emit_env_trigger(root: ET.Element, comp_name: str) -> str:
    """
    Environment trigger for components without inputs.
    Emit a one-shot release at time t = 0.
    """
    tpl_name = f"Env_{comp_name}"
    tpl = ET.SubElement(root, "template")
    ET.SubElement(tpl, "name").text = tpl_name
    ET.SubElement(tpl, "declaration").text = "clock x;"

    idle = ET.SubElement(tpl, "location", id=f"{tpl_name}_Idle")
    ET.SubElement(idle, "name").text = "Idle"
    ET.SubElement(idle, "committed")

    done = ET.SubElement(tpl, "location", id=f"{tpl_name}_Done")
    ET.SubElement(done, "name").text = "Done"

    ET.SubElement(tpl, "init", ref=idle.get("id"))

    tr = ET.SubElement(tpl, "transition")
    ET.SubElement(tr, "source", ref=idle.get("id"))
    ET.SubElement(tr, "target", ref=done.get("id"))
    ET.SubElement(tr, "label", kind="synchronisation").text = f"release_{comp_name}!"

    return tpl_name


def emit_scheduler_template(
    root: ET.Element,
    components: List[Component],
    priority_map: Dict[str, int],
    prefix: str,
) -> str:
    """Fixed-priority scheduler"""
    tpl_name = f"Scheduler_{prefix}"
    tpl = ET.SubElement(root, "template")
    ET.SubElement(tpl, "name").text = tpl_name

    idle = ET.SubElement(tpl, "location", id=f"{tpl_name}_Idle")
    ET.SubElement(idle, "name").text = "Idle"

    dispatch = ET.SubElement(tpl, "location", id=f"{tpl_name}_Dispatch")
    ET.SubElement(dispatch, "name").text = "Dispatch"
    ET.SubElement(dispatch, "committed")

    post = ET.SubElement(tpl, "location", id=f"{tpl_name}_Post")
    ET.SubElement(post, "name").text = "Post"
    ET.SubElement(post, "committed")

    busy = ET.SubElement(tpl, "location", id=f"{tpl_name}_Busy")
    ET.SubElement(busy, "name").text = "Busy"

    ET.SubElement(tpl, "init", ref=idle.get("id"))

    ordered = sorted(
        components, key=lambda c: (priority_map[c.name], c.name)
    )

    ready_terms = [f"ready_{prefix}[IDX_{c.name}]" for c in components]
    some_ready = " || ".join(ready_terms)
    running_var = f"running_{prefix}"

    # Wake the dispatcher whenever a job is released while the CPU is idle
    for comp in components:
        tr_rel = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_rel, "source", ref=idle.get("id"))
        ET.SubElement(tr_rel, "target", ref=dispatch.get("id"))
        ET.SubElement(tr_rel, "label", kind="synchronisation").text = (
            f"release_{comp.name}?"
        )

    # Dispatch transitions (committed – pick highest-priority ready job)
    for i, comp in enumerate(ordered):
        guard_terms = [f"{running_var} == -1", f"ready_{prefix}[IDX_{comp.name}]"]
        for prev in ordered[:i]:
            guard_terms.append(f"!ready_{prefix}[IDX_{prev.name}]")

        tr = ET.SubElement(tpl, "transition")
        ET.SubElement(tr, "source", ref=dispatch.get("id"))
        ET.SubElement(tr, "target", ref=busy.get("id"))
        ET.SubElement(tr, "label", kind="guard").text = " && ".join(guard_terms)
        ET.SubElement(tr, "label", kind="synchronisation").text = f"start_{comp.name}!"
        ET.SubElement(tr, "label", kind="assignment").text = (
            f"{running_var} = IDX_{comp.name}, ready_{prefix}[IDX_{comp.name}] = false"
        )

    if some_ready:
        # If somehow the dispatcher wakes without a pending job, fall back to idle
        tr_disp_idle = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_disp_idle, "source", ref=dispatch.get("id"))
        ET.SubElement(tr_disp_idle, "target", ref=idle.get("id"))
        ET.SubElement(tr_disp_idle, "label", kind="guard").text = f"!({some_ready})"

    # Completion transitions (Busy → committed post-processing
    for comp in components:
        tr_done = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_done, "source", ref=busy.get("id"))
        ET.SubElement(tr_done, "target", ref=post.get("id"))
        ET.SubElement(tr_done, "label", kind="synchronisation").text = (
            f"done_{comp.name}?"
        )
        ET.SubElement(tr_done, "label", kind="guard").text = (
            f"{running_var} == IDX_{comp.name}"
        )
        ET.SubElement(tr_done, "label", kind="assignment").text = (
            f"{running_var} = -1"
        )

    if some_ready:
        tr_post_dispatch = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_post_dispatch, "source", ref=post.get("id"))
        ET.SubElement(tr_post_dispatch, "target", ref=dispatch.get("id"))
        ET.SubElement(tr_post_dispatch, "label", kind="guard").text = some_ready

        tr_post_idle = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_post_idle, "source", ref=post.get("id"))
        ET.SubElement(tr_post_idle, "target", ref=idle.get("id"))
        ET.SubElement(tr_post_idle, "label", kind="guard").text = f"!({some_ready})"
    else:
        # no components – treat post as empty and drop to idle
        tr_post_idle = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_post_idle, "source", ref=post.get("id"))
        ET.SubElement(tr_post_idle, "target", ref=idle.get("id"))

    return tpl_name


def emit_connection_driver(root: ET.Element, src_comp: str, dst_comp: str) -> str:
    """
    Connection driver: propagates done->release
    A committed intermediate state ensures
    that the release is triggered immediately after the completion
    notification
    """
    tpl_name = f"Conn_{src_comp}_to_{dst_comp}"

    tpl = ET.SubElement(root, "template")
    ET.SubElement(tpl, "name").text = tpl_name

    # States
    idle = ET.SubElement(tpl, "location", id=f"{tpl_name}_Idle")
    ET.SubElement(idle, "name").text = "Idle"

    trig = ET.SubElement(tpl, "location", id=f"{tpl_name}_Trig")
    ET.SubElement(trig, "name").text = "Trig"
    ET.SubElement(trig, "committed")

    ET.SubElement(tpl, "init", ref=idle.get("id"))

    # 1. warten auf done_src?
    t1 = ET.SubElement(tpl, "transition")
    ET.SubElement(t1, "source", ref=idle.get("id"))
    ET.SubElement(t1, "target", ref=trig.get("id"))
    ET.SubElement(t1, "label", kind="synchronisation").text = f"done_{src_comp}?"

    # 2. sofort release_dst! senden
    t2 = ET.SubElement(tpl, "transition")
    ET.SubElement(t2, "source", ref=trig.get("id"))
    ET.SubElement(t2, "target", ref=idle.get("id"))
    ET.SubElement(t2, "label", kind="synchronisation").text = f"release_{dst_comp}!"

    return tpl_name