from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, List

from DSL.metamodel import Component  # type: ignore

from Backend.UPPAAL._conversions import to_ms

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
    wcet_val = getattr(comp, "wcet_ms", None) or getattr(comp, "wcet", None)
    wcet = to_ms(wcet_val) or 0
    deadline_val = getattr(comp, "deadline_ms", None) or getattr(comp, "deadline", None)
    deadline = to_ms(deadline_val) if deadline_val is not None else None

    # fall back to WCET if no explicit deadline is provided
    if deadline is None:
        deadline = wcet

    is_event_driven = period_val is None

    tpl = ET.SubElement(root, "template")
    ET.SubElement(tpl, "name").text = comp.name
    decl = ["clock x;", "clock slice;"]
    ET.SubElement(tpl, "declaration").text = "\n".join(decl)

    ready_arr = f"ready_{sched_prefix}"
    running_var = f"running_{sched_prefix}"
    remaining_arr = f"remaining_{sched_prefix}"
    wcet_arr = f"WCET_{sched_prefix}"
    idx_ref = f"IDX_{comp.name}"

    # Locations --------------------------------------------------
    idle = ET.SubElement(tpl, "location", id=f"{comp.name}_Idle")
    ET.SubElement(idle, "name").text = "Idle"
    if period and not is_event_driven:
        ET.SubElement(idle, "label", kind="invariant").text = f"x <= {period}"

    ready_loc = ET.SubElement(tpl, "location", id=f"{comp.name}_Ready")
    ET.SubElement(ready_loc, "name").text = "Ready"

    exec_loc = ET.SubElement(tpl, "location", id=f"{comp.name}_Exec")
    ET.SubElement(exec_loc, "name").text = "Exec"
    inv_parts = ["slice <= 1"]
    if deadline is not None:
        inv_parts.append(f"x <= {deadline}")
    ET.SubElement(exec_loc, "label", kind="invariant").text = " && ".join(inv_parts)

    bad = None
    if deadline is not None:
        bad = ET.SubElement(tpl, "location", id=f"{comp.name}_DeadlineMiss")
        ET.SubElement(bad, "name").text = "bad"

    ET.SubElement(tpl, "init", ref=idle.get("id"))

    # Idle --release?--> Ready
    tr_rel = ET.SubElement(tpl, "transition")
    ET.SubElement(tr_rel, "source", ref=idle.get("id"))
    ET.SubElement(tr_rel, "target", ref=ready_loc.get("id"))
    ET.SubElement(tr_rel, "label", kind="synchronisation").text = f"release_{comp.name}?"
    ET.SubElement(tr_rel, "label", kind="assignment").text = (
        f"x = 0, slice = 0, {ready_arr}[{idx_ref}] = true, {remaining_arr}[{idx_ref}] = {wcet_arr}[{idx_ref}]"
    )

    # Ready --start?--> Exec
    tr_start = ET.SubElement(tpl, "transition")
    ET.SubElement(tr_start, "source", ref=ready_loc.get("id"))
    ET.SubElement(tr_start, "target", ref=exec_loc.get("id"))
    ET.SubElement(tr_start, "label", kind="synchronisation").text = f"start_{comp.name}?"
    ET.SubElement(tr_start, "label", kind="assignment").text = "slice = 0"

    # Execution progress loop (1ms quanta)
    tr_quantum = ET.SubElement(tpl, "transition")
    ET.SubElement(tr_quantum, "source", ref=exec_loc.get("id"))
    ET.SubElement(tr_quantum, "target", ref=exec_loc.get("id"))
    ET.SubElement(tr_quantum, "label", kind="guard").text = (
        f"{running_var} == {idx_ref} && {remaining_arr}[{idx_ref}] > 0 && slice == 1"
    )
    ET.SubElement(tr_quantum, "label", kind="assignment").text = (
        f"slice = 0, {remaining_arr}[{idx_ref}] = {remaining_arr}[{idx_ref}] - 1"
    )

    # Exec --done!--> Idle
    tr_done = ET.SubElement(tpl, "transition")
    ET.SubElement(tr_done, "source", ref=exec_loc.get("id"))
    ET.SubElement(tr_done, "target", ref=idle.get("id"))
    ET.SubElement(tr_done, "label", kind="guard").text = (
        f"{running_var} == {idx_ref} && {remaining_arr}[{idx_ref}] == 0 && slice == 0"
    )
    ET.SubElement(tr_done, "label", kind="synchronisation").text = f"done_{comp.name}!"
    ET.SubElement(tr_done, "label", kind="assignment").text = "x = 0, slice = 0"

    # Exec --preempt?--> Ready
    tr_preempt = ET.SubElement(tpl, "transition")
    ET.SubElement(tr_preempt, "source", ref=exec_loc.get("id"))
    ET.SubElement(tr_preempt, "target", ref=ready_loc.get("id"))
    ET.SubElement(tr_preempt, "label", kind="guard").text = (
        f"{running_var} == {idx_ref} && {remaining_arr}[{idx_ref}] > 0 && slice == 0"
    )
    ET.SubElement(tr_preempt, "label", kind="synchronisation").text = f"preempt_{comp.name}?"
    ET.SubElement(tr_preempt, "label", kind="assignment").text = (
        f"{ready_arr}[{idx_ref}] = true"
    )

    if bad is not None:
        tr_ready_bad = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_ready_bad, "source", ref=ready_loc.get("id"))
        ET.SubElement(tr_ready_bad, "target", ref=bad.get("id"))
        ET.SubElement(tr_ready_bad, "label", kind="guard").text = f"x > {deadline}"

        tr_exec_bad = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_exec_bad, "source", ref=exec_loc.get("id"))
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


def emit_env_trigger(root: ET.Element, comp: Component) -> str:
    """Environment trigger for components without inputs."""

    tpl_name = f"Env_{comp.name}"
    tpl = ET.SubElement(root, "template")
    ET.SubElement(tpl, "name").text = tpl_name
    ET.SubElement(tpl, "declaration").text = "clock x;"

    idle = ET.SubElement(tpl, "location", id=f"{tpl_name}_Idle")
    ET.SubElement(idle, "name").text = "Idle"

    done = ET.SubElement(tpl, "location", id=f"{tpl_name}_Done")
    ET.SubElement(done, "name").text = "Done"

    ET.SubElement(tpl, "init", ref=idle.get("id"))

    tr = ET.SubElement(tpl, "transition")
    ET.SubElement(tr, "source", ref=idle.get("id"))
    ET.SubElement(tr, "target", ref=done.get("id"))

    guard_parts: list[str] = []

    if getattr(comp, "criticality_class", None) == "SafetyCritical":
        # Allow a SafetyCritical component to be released while other
        # activities execute by introducing a short, non-deterministic
        # offset before the first release.  This creates the interleavings
        # that make preemption observable in the analysis.
        min_delay = 1
        max_delay = (
            to_ms(getattr(comp, "deadline", None))
            or to_ms(getattr(comp, "period", None))
            or to_ms(getattr(comp, "wcet", None))
        )

        if max_delay is None or max_delay < min_delay:
            max_delay = min_delay

        guard_parts.append(f"x >= {min_delay}")
        guard_parts.append(f"x <= {max_delay}")
        ET.SubElement(idle, "label", kind="invariant").text = f"x <= {max_delay}"
    else:
        ET.SubElement(idle, "committed")

    if guard_parts:
        ET.SubElement(tr, "label", kind="guard").text = " && ".join(guard_parts)

    ET.SubElement(tr, "label", kind="synchronisation").text = f"release_{comp.name}!"

    return tpl_name


def emit_scheduler_template(
    root: ET.Element,
    components: List[Component],
    priority_map: Dict[str, int],
    class_map: Dict[str, int],
    threshold_map: Dict[str, int],
    prefix: str,
    mode: str | None = None,
) -> str:
    """Emit a scheduler template according to the configured policy (Limited-preemption FP or preemption FP)."""

    scheduler_mode = (mode or "LIMITED_PREEMPTIVE_FP").upper()
    limited_preemptive = scheduler_mode != "PREEMPTIVE_FP"

    tpl_name = f"Scheduler_{prefix}"
    tpl = ET.SubElement(root, "template")
    ET.SubElement(tpl, "name").text = tpl_name

    idle = ET.SubElement(tpl, "location", id=f"{tpl_name}_Idle")
    ET.SubElement(idle, "name").text = "Idle"

    evaluate = ET.SubElement(tpl, "location", id=f"{tpl_name}_Evaluate")
    ET.SubElement(evaluate, "name").text = "Evaluate"
    ET.SubElement(evaluate, "committed")

    dispatch = ET.SubElement(tpl, "location", id=f"{tpl_name}_Dispatch")
    ET.SubElement(dispatch, "name").text = "Dispatch"
    ET.SubElement(dispatch, "committed")

    preempt = ET.SubElement(tpl, "location", id=f"{tpl_name}_Preempt")
    ET.SubElement(preempt, "name").text = "Preempt"
    ET.SubElement(preempt, "committed")

    busy = ET.SubElement(tpl, "location", id=f"{tpl_name}_Busy")
    ET.SubElement(busy, "name").text = "Busy"

    ET.SubElement(tpl, "init", ref=idle.get("id"))

    ordered = sorted(
        components,
        key=lambda c: (class_map.get(c.name, 0), priority_map.get(c.name, 0), c.name),
    )

    ready_arr = f"ready_{prefix}"
    running_var = f"running_{prefix}"
    next_var = f"next_{prefix}"
    criticality_arr = f"criticality_{prefix}"
    thresholds_arr = f"thresholds_{prefix}"
    priority_arr = f"priorities_{prefix}"

    ready_terms = [f"{ready_arr}[IDX_{c.name}]" for c in components]
    some_ready = " || ".join(ready_terms)

    if limited_preemptive:
        outrank_terms = [
            f"({ready_arr}[IDX_{c.name}] && {criticality_arr}[IDX_{c.name}] < {thresholds_arr}[{running_var}])"
            for c in components
        ]
    else:
        outrank_terms = [
            f"({ready_arr}[IDX_{c.name}] && {priority_arr}[IDX_{c.name}] < {priority_arr}[{running_var}])"
            for c in components
        ]
    outrank_expr = " || ".join(outrank_terms)

    # Idle reacts to releases and queued work
    for comp in components:
        tr_rel = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_rel, "source", ref=idle.get("id"))
        ET.SubElement(tr_rel, "target", ref=evaluate.get("id"))
        ET.SubElement(tr_rel, "label", kind="synchronisation").text = (
            f"release_{comp.name}?"
        )

    if some_ready:
        tr_idle_eval = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_idle_eval, "source", ref=idle.get("id"))
        ET.SubElement(tr_idle_eval, "target", ref=evaluate.get("id"))
        ET.SubElement(tr_idle_eval, "label", kind="guard").text = some_ready

    # Evaluate → Idle (no work)
    if some_ready:
        idle_guard = f"{running_var} == -1 && !({some_ready})"
    else:
        idle_guard = f"{running_var} == -1"
    tr_eval_idle = ET.SubElement(tpl, "transition")
    ET.SubElement(tr_eval_idle, "source", ref=evaluate.get("id"))
    ET.SubElement(tr_eval_idle, "target", ref=idle.get("id"))
    ET.SubElement(tr_eval_idle, "label", kind="guard").text = idle_guard
    ET.SubElement(tr_eval_idle, "label", kind="assignment").text = f"{next_var} = -1"

    # Dispatch highest-ranked ready job when CPU idle
    for i, comp in enumerate(ordered):
        guard_terms = [f"{running_var} == -1", f"{ready_arr}[IDX_{comp.name}]"]
        for prev in ordered[:i]:
            guard_terms.append(f"!{ready_arr}[IDX_{prev.name}]")
        tr = ET.SubElement(tpl, "transition")
        ET.SubElement(tr, "source", ref=evaluate.get("id"))
        ET.SubElement(tr, "target", ref=dispatch.get("id"))
        ET.SubElement(tr, "label", kind="guard").text = " && ".join(guard_terms)
        ET.SubElement(tr, "label", kind="assignment").text = (
            f"{next_var} = IDX_{comp.name}"
        )

    # Preemption when an eligible job outranks the running task
    for i, comp in enumerate(ordered):
        guard_terms = [f"{running_var} != -1", f"{ready_arr}[IDX_{comp.name}]"]
        if limited_preemptive:
            guard_terms.append(
                f"{criticality_arr}[IDX_{comp.name}] < {thresholds_arr}[{running_var}]"
            )
        else:
            guard_terms.append(
                f"{priority_arr}[IDX_{comp.name}] < {priority_arr}[{running_var}]"
            )
        for prev in ordered[:i]:
            guard_terms.append(f"!{ready_arr}[IDX_{prev.name}]")
        tr = ET.SubElement(tpl, "transition")
        ET.SubElement(tr, "source", ref=evaluate.get("id"))
        ET.SubElement(tr, "target", ref=preempt.get("id"))
        ET.SubElement(tr, "label", kind="guard").text = " && ".join(guard_terms)
        ET.SubElement(tr, "label", kind="assignment").text = (
            f"{next_var} = IDX_{comp.name}"
        )

    # Continue running if no preemption candidate exists
    tr_eval_busy = ET.SubElement(tpl, "transition")
    ET.SubElement(tr_eval_busy, "source", ref=evaluate.get("id"))
    ET.SubElement(tr_eval_busy, "target", ref=busy.get("id"))
    guard_terms = [f"{running_var} != -1"]
    if outrank_expr:
        guard_terms.append(f"!({outrank_expr})")
    ET.SubElement(tr_eval_busy, "label", kind="guard").text = " && ".join(guard_terms)
    ET.SubElement(tr_eval_busy, "label", kind="assignment").text = f"{next_var} = -1"

    # Preemption signalling to the current task
    for comp in components:
        tr_pre = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_pre, "source", ref=preempt.get("id"))
        ET.SubElement(tr_pre, "target", ref=dispatch.get("id"))
        ET.SubElement(tr_pre, "label", kind="guard").text = (
            f"{running_var} == IDX_{comp.name}"
        )
        ET.SubElement(tr_pre, "label", kind="synchronisation").text = (
            f"preempt_{comp.name}!"
        )
        ET.SubElement(tr_pre, "label", kind="assignment").text = (
            f"{ready_arr}[IDX_{comp.name}] = true, {running_var} = -1"
        )

    # Dispatch selected job
    for comp in components:
        tr_dispatch = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_dispatch, "source", ref=dispatch.get("id"))
        ET.SubElement(tr_dispatch, "target", ref=busy.get("id"))
        ET.SubElement(tr_dispatch, "label", kind="guard").text = (
            f"{next_var} == IDX_{comp.name}"
        )
        ET.SubElement(tr_dispatch, "label", kind="synchronisation").text = (
            f"start_{comp.name}!"
        )
        ET.SubElement(tr_dispatch, "label", kind="assignment").text = (
            f"{running_var} = IDX_{comp.name}, {ready_arr}[IDX_{comp.name}] = false, {next_var} = -1"
        )

    # Busy state reacts to new releases and completions
    for comp in components:
        tr_busy_rel = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_busy_rel, "source", ref=busy.get("id"))
        ET.SubElement(tr_busy_rel, "target", ref=evaluate.get("id"))
        ET.SubElement(tr_busy_rel, "label", kind="synchronisation").text = (
            f"release_{comp.name}?"
        )

    for comp in components:
        tr_done = ET.SubElement(tpl, "transition")
        ET.SubElement(tr_done, "source", ref=busy.get("id"))
        ET.SubElement(tr_done, "target", ref=evaluate.get("id"))
        ET.SubElement(tr_done, "label", kind="synchronisation").text = (
            f"done_{comp.name}?"
        )
        ET.SubElement(tr_done, "label", kind="guard").text = (
            f"{running_var} == IDX_{comp.name}"
        )
        ET.SubElement(tr_done, "label", kind="assignment").text = (
            f"{running_var} = -1, {next_var} = -1"
        )

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