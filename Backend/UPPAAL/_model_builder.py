from __future__ import annotations

import re
import tempfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Pattern

from DSL.metamodel import Component, Model

from Backend.UPPAAL._conversions import get_latency_budget, to_ms
from Backend.UPPAAL._pipeline import emit_pipeline_observer, find_predecessor
from Backend.UPPAAL._query_bundle import QueryBundle
from Backend.UPPAAL._templates import (
    emit_component_template,
    emit_connection_driver,
    emit_env_trigger,
    emit_periodic_timer,
    emit_scheduler_template,
)

__all__ = ["ModelBuilder"]


class ModelBuilder:
    def __init__(self, pipeline_re: Pattern[str]):
        self.pipeline_re = pipeline_re

    @staticmethod
    def _strip_qual(name: str) -> str:
        return name.split(".")[-1]

    @staticmethod
    def _sched_prefix(vehicle: str | None) -> str:
        if not vehicle:
            return "GLOBAL"
        return re.sub(r"\W", "_", vehicle)

    def build(self, model: Model) -> QueryBundle:
        nta = ET.Element("nta")
        global_decl = ET.SubElement(nta, "declaration")

        components = list(model.components.values())
        cpu_cfg = getattr(model, "cpu", None)
        configured_order: list[str] = []
        if cpu_cfg and getattr(cpu_cfg, "class_order", None):
            configured_order = [cls for cls in cpu_cfg.class_order if cls]

        seen_classes = set(configured_order)
        for comp in components:
            cls = getattr(comp, "criticality_class", None)
            if cls and cls not in seen_classes:
                configured_order.append(cls)
                seen_classes.add(cls)

        class_rank_map = {cls: idx for idx, cls in enumerate(configured_order)}
        default_class_rank = len(configured_order)
        group_data: Dict[str, Dict[str, object]] = {}
        wcet_lookup: Dict[str, int] = {}
        component_prefix: Dict[str, str] = {}
        component_index: Dict[str, int] = {}

        for comp in components:
            prefix = self._sched_prefix(getattr(comp, "vehicle", None))
            component_prefix[comp.name] = prefix
            data = group_data.setdefault(prefix, {"components": []})
            data["components"].append(comp)  # type: ignore[arg-type]

        for prefix, data in group_data.items():
            comps: List[Component] = data["components"]  # type: ignore[assignment]
            prio_map: Dict[str, int] = {}
            class_map: Dict[str, int] = {}
            threshold_map: Dict[str, int] = {}
            wcet_map: Dict[str, int] = {}
            for idx, comp in enumerate(comps):
                component_index[comp.name] = idx
                prio_map[comp.name] = (
                    comp.priority if comp.priority is not None else 1000 + idx
                )
                cls = getattr(comp, "criticality_class", None)
                rank = class_rank_map.get(cls, default_class_rank)
                class_map[comp.name] = rank

                threshold_label = getattr(comp, "preemption_threshold", None)
                if threshold_label is None:
                    threshold_label = cls
                if threshold_label is not None and threshold_label not in class_rank_map:
                    class_rank_map[threshold_label] = len(class_rank_map)
                    configured_order.append(threshold_label)
                    default_class_rank = len(class_rank_map)
                threshold_rank = class_rank_map.get(threshold_label, rank)
                threshold_map[comp.name] = threshold_rank
                comp.preemption_threshold = threshold_label

                wcet_val = (
                        getattr(comp, "wcet_ms", None) or getattr(comp, "wcet", None)
                )
                wcet_map[comp.name] = to_ms(wcet_val) or 0
                wcet_lookup[comp.name] = wcet_map[comp.name]
            data["prio_map"] = prio_map
            data["class_map"] = class_map
            data["threshold_map"] = threshold_map
            data["wcet_map"] = wcet_map

        if cpu_cfg is not None:
            cpu_cfg.class_order = configured_order


        decl_parts: list[str] = []
        for comp in components:
            decl_parts.append(f"broadcast chan start_{comp.name}, done_{comp.name}, preempt_{comp.name};")
        for comp in components:
            decl_parts.append(f"broadcast chan release_{comp.name};")

        for prefix, data in group_data.items():
            comps: List[Component] = data["components"]  # type: ignore[assignment]
            if not comps:
                continue
            decl_parts.append(
                f"const int NUM_COMPONENTS_{prefix} = {len(comps)};"
            )
            for comp in comps:
                decl_parts.append(
                    f"const int IDX_{comp.name} = {component_index[comp.name]};"
                )
            prio_map: Dict[str, int] = data["prio_map"]  # type: ignore[assignment]
            prio_list = ", ".join(str(prio_map[comp.name]) for comp in comps)
            decl_parts.append(
                f"int priorities_{prefix}[NUM_COMPONENTS_{prefix}] = {{{prio_list}}};"
            )
            decl_parts.append(f"bool ready_{prefix}[NUM_COMPONENTS_{prefix}];")
            decl_parts.append(f"int running_{prefix} = -1;")
            class_map: Dict[str, int] = data["class_map"]  # type: ignore[assignment]
            class_list = ", ".join(str(class_map[comp.name]) for comp in comps)
            decl_parts.append(
                f"int criticality_{prefix}[NUM_COMPONENTS_{prefix}] = {{{class_list}}};"
            )
            threshold_map: Dict[str, int] = data["threshold_map"]  # type: ignore[assignment]
            threshold_list = ", ".join(
                str(threshold_map[comp.name]) for comp in comps
            )
            decl_parts.append(
                f"int thresholds_{prefix}[NUM_COMPONENTS_{prefix}] = {{{threshold_list}}};"
            )
            wcet_map: Dict[str, int] = data["wcet_map"]  # type: ignore[assignment]
            wcet_list = ", ".join(str(wcet_map[comp.name]) for comp in comps)
            decl_parts.append(
                f"const int WCET_{prefix}[NUM_COMPONENTS_{prefix}] = {{{wcet_list}}};"
            )
            decl_parts.append(f"int remaining_{prefix}[NUM_COMPONENTS_{prefix}];")
            decl_parts.append(f"int next_{prefix} = -1;")

        global_decl.text = "\n    " + "\n    ".join(decl_parts) + "\n  " if decl_parts else "\n  "

        sys_inst: List[str] = []
        queries: Dict[str, str] = {}

        # Determine which components have incoming connections.  This needs to
        # happen before we decide whether to emit periodic release timers so
        # that we do not create artificial timers for components that are
        # triggered exclusively via connections.
        incoming: Dict[str, bool] = {c.name: False for c in components}

        for conn in getattr(model, "connections", []):  # type: ignore[attr-defined]
            dst = conn.dst.split(".")[-2]
            dst = self._strip_qual(dst)
            if dst in incoming:
                incoming[dst] = True

        # ------------------------------------------------------------------
        # Component templates
        # ------------------------------------------------------------------
        deadline_comps: List[str] = []
        for comp in components:
            prefix = component_prefix[comp.name]
            emit_component_template(nta, comp, component_index[comp.name], prefix)
            sys_inst.append(f"P_{comp.name} = {comp.name}();")
            if getattr(comp, "deadline", None) is not None:
                deadline_comps.append(comp.name)

        # Periodic release timers
        for comp in components:
            period_val = getattr(comp, "period", None)
            if period_val is not None and not incoming.get(comp.name, False):
                tpl_name = emit_periodic_timer(nta, comp.name, to_ms(period_val))
                sys_inst.append(f"T_{comp.name} = {tpl_name}();")

        # ------------------------------------------------------------------
        # Connection drivers (glue – forward done→start)
        # ------------------------------------------------------------------
        driver_templates: set[str] = set()
        for conn in getattr(model, "connections", []):  # type: ignore[attr-defined]
            src_comp = self._strip_qual(conn.src.split(".")[-2])
            dst_comp = self._strip_qual(conn.dst.split(".")[-2])
            if src_comp not in model.components or dst_comp not in model.components:
                continue
            tpl_name = f"Conn_{src_comp}_to_{dst_comp}"
            if tpl_name in driver_templates:
                continue

            emit_connection_driver(nta, src_comp, dst_comp)
            driver_templates.add(tpl_name)
            inst = f"D_{tpl_name}"
            sys_inst.append(f"{inst} = {tpl_name}();")

        # ------------------------------------------------------------------
        # Environment triggers for components without inputs
        # ------------------------------------------------------------------
        for comp in components:
            period_val = getattr(comp, "period_ms", None) or getattr(comp, "period", None)
            if period_val is None and not incoming.get(comp.name):
                tpl = emit_env_trigger(nta, comp)
                inst = f"I_{tpl}"
                sys_inst.append(f"{inst} = {tpl}();")

        # ------------------------------------------------------------------
        # Scheduler instance (fixed-priority dispatcher)
        # ------------------------------------------------------------------
        scheduler_mode = "LIMITED_PREEMPTIVE_FP"
        if cpu_cfg is not None:
            raw_scheduler = getattr(cpu_cfg, "scheduler", None)
            if raw_scheduler:
                scheduler_mode = str(raw_scheduler).upper()

        for prefix, data in group_data.items():
            comps: List[Component] = data["components"]  # type: ignore[assignment]
            if not comps:
                continue
            prio_map: Dict[str, int] = data["prio_map"]  # type: ignore[assignment]
            class_map: Dict[str, int] = data["class_map"]  # type: ignore[assignment]
            threshold_map: Dict[str, int] = data["threshold_map"]  # type: ignore[assignment]
            sched_tpl = emit_scheduler_template(
                nta,
                comps,
                prio_map,
                class_map,
                threshold_map,
                prefix,
                scheduler_mode,
            )
            sys_inst.append(f"S_{prefix} = {sched_tpl}();")

        # ------------------------------------------------------------------
        # DSL PROPERTY clauses
        # ------------------------------------------------------------------
        for prop_name, prop_text in model.properties.items():
            if prop_name in queries:
                continue # already handled (connection observers)

            text = prop_text.strip().strip("\"")
            if text.startswith("E") or text.startswith("A"):
                queries[prop_name] = text # raw UPPAAL query
                continue

            # Pipeline pattern
            m_pl = self.pipeline_re.match(text)
            if m_pl:
                seq_txt = m_pl.group("seq")
                parts = [self._strip_qual(p.strip()) for p in seq_txt.split("->")]
                parts = [p for p in parts if p] # leere Einträge entfernen

                # print(parts)

                first = parts[0]
                pred = find_predecessor(
                    self._strip_qual, first, getattr(model, "connections", [])
                )
                start_sync = f"done_{pred}?" if pred else f"start_{first}?"
                # print(start_sync)

                conn_budget: dict[tuple[str, str], int] = {}
                for c in getattr(model, "connections", []):
                    src = self._strip_qual(c.src.split(".")[-2])
                    dst = self._strip_qual(c.dst.split(".")[-2])
                    conn_budget[(src, dst)] = to_ms(get_latency_budget(c)) or 0

                # print(conn_budget)

                tpl = emit_pipeline_observer(
                    nta,
                    prop_name,
                    parts,
                    int(m_pl.group("val")),
                    start_sync,
                    conn_budget,
                    wcet_lookup,
                )
                inst = f"I_{tpl}"
                sys_inst.append(f"{inst} = {tpl}();")
                queries[prop_name] = f"A[] not {inst}.bad"
                # print(queries)

        if "deadline_misses==0" not in queries and deadline_comps:
            locs = [f"P_{n}.bad" for n in deadline_comps]
            expr = locs[0] if len(locs) == 1 else "(" + " || ".join(locs) + ")"
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