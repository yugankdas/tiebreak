"""Dependency graph engine using NetworkX — deterministic, LLM-independent."""
from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx

from app.models.project import Project, Task, TaskStatus


class GraphAnalysis:
    def __init__(self):
        self.cycles: List[List[str]] = []
        self.strongly_connected_components: List[List[str]] = []
        self.tasks_in_cycles: Set[str] = set()
        self.tasks_blocked_by_prerequisites: List[str] = []
        self.tasks_ready: List[str] = []
        self.downstream_map: Dict[str, List[str]] = {}
        self.upstream_map: Dict[str, List[str]] = {}
        self.missing_deps: Dict[str, List[str]] = {}  # task_id -> missing dep ids
        self.graph_data: Dict = {}  # serialised for frontend


class GraphEngine:
    """
    Deterministic dependency graph analysis.

    Edge convention: A → B means "A must be satisfied before B can proceed".
    i.e., A is a prerequisite of B.
    """

    def build_graph(self, project: Project) -> nx.DiGraph:
        G = nx.DiGraph()
        task_ids = {t.task_id for t in project.tasks}

        for task in project.tasks:
            G.add_node(task.task_id, task=task)

        for task in project.tasks:
            for dep_id in task.dependencies:
                if dep_id in task_ids:
                    # edge: dep_id → task.task_id
                    # i.e., dep_id must complete before task
                    G.add_edge(dep_id, task.task_id)

        return G

    def analyse(self, project: Project) -> GraphAnalysis:
        result = GraphAnalysis()
        G = self.build_graph(project)
        task_ids = {t.task_id for t in project.tasks}

        # ── detect missing dependency references ─────────────────────────────
        for task in project.tasks:
            missing = [d for d in task.dependencies if d not in task_ids]
            if missing:
                result.missing_deps[task.task_id] = missing

        # ── detect cycles ─────────────────────────────────────────────────────
        try:
            cycles = list(nx.simple_cycles(G))
            result.cycles = cycles
        except Exception:
            result.cycles = []

        # ── strongly connected components (size > 1 = cycle) ──────────────────
        sccs = [list(c) for c in nx.strongly_connected_components(G) if len(c) > 1]
        result.strongly_connected_components = sccs

        # tasks participating in any cycle
        for cycle in result.cycles:
            for node in cycle:
                result.tasks_in_cycles.add(node)

        # ── upstream / downstream maps ────────────────────────────────────────
        for task in project.tasks:
            # upstream = all tasks that must complete before this one
            try:
                ancestors = list(nx.ancestors(G, task.task_id))
            except Exception:
                ancestors = []
            result.upstream_map[task.task_id] = ancestors

            # downstream = all tasks that depend on this one
            try:
                descendants = list(nx.descendants(G, task.task_id))
            except Exception:
                descendants = []
            result.downstream_map[task.task_id] = descendants

        # ── identify tasks blocked by incomplete prerequisites ─────────────────
        completed = {t.task_id for t in project.tasks if t.status == TaskStatus.COMPLETED}
        for task in project.tasks:
            if task.status == TaskStatus.COMPLETED:
                continue
            unmet = [d for d in task.dependencies if d not in completed]
            if unmet:
                result.tasks_blocked_by_prerequisites.append(task.task_id)

        # ── ready task calculation ────────────────────────────────────────────
        # A task is READY iff:
        # 1. It is not completed
        # 2. It has no unmet prerequisites (all deps completed)
        # 3. It is not in a cycle (cycle tasks can never be ready via normal path)
        for task in project.tasks:
            if task.status == TaskStatus.COMPLETED:
                continue
            if task.task_id in result.tasks_in_cycles:
                continue
            unmet = [d for d in task.dependencies if d not in completed]
            if not unmet:
                result.tasks_ready.append(task.task_id)

        # ── serialise graph for frontend ───────────────────────────────────────
        result.graph_data = self._serialise(project, G, result)
        return result

    def _serialise(self, project: Project, G: nx.DiGraph, analysis: GraphAnalysis) -> Dict:
        task_map = {t.task_id: t for t in project.tasks}
        member_map = {m.member_id: m.name for m in project.team_members}

        nodes = []
        for task in project.tasks:
            in_cycle = task.task_id in analysis.tasks_in_cycles
            is_ready = task.task_id in analysis.tasks_ready
            owner_name = member_map.get(task.owner_id or "", "Unassigned")
            nodes.append({
                "id": task.task_id,
                "label": task.title,
                "status": task.status.value,
                "priority": task.priority,
                "owner": owner_name,
                "in_cycle": in_cycle,
                "is_ready": is_ready,
                "is_protected": task.is_protected,
                "estimated_hours": task.estimated_effort_hours,
                "tags": task.tags,
                "blocker_reason": task.blocker_reason,
            })

        edges = []
        for src, dst in G.edges():
            in_cycle_edge = False
            for cycle in analysis.cycles:
                cycle_set = set(cycle)
                if src in cycle_set and dst in cycle_set:
                    in_cycle_edge = True
                    break
            edges.append({
                "source": src,
                "target": dst,
                "in_cycle": in_cycle_edge,
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "cycles": analysis.cycles,
            "scc": analysis.strongly_connected_components,
            "ready_tasks": analysis.tasks_ready,
            "tasks_in_cycles": list(analysis.tasks_in_cycles),
            "missing_deps": analysis.missing_deps,
        }

    def compute_downstream_impact(self, project: Project, task_id: str) -> List[str]:
        G = self.build_graph(project)
        try:
            return list(nx.descendants(G, task_id))
        except Exception:
            return []

    def tasks_unblocked_by_completing(self, project: Project, completed_task_ids: Set[str]) -> List[str]:
        """Compute which additional tasks would become ready if these tasks were completed."""
        task_ids = {t.task_id for t in project.tasks}
        currently_complete = {t.task_id for t in project.tasks if t.status == TaskStatus.COMPLETED}
        hypothetical_complete = currently_complete | completed_task_ids
        newly_ready = []
        for task in project.tasks:
            if task.task_id in hypothetical_complete:
                continue
            if task.task_id in currently_complete:
                continue
            unmet_now = [d for d in task.dependencies if d not in currently_complete]
            unmet_after = [d for d in task.dependencies if d not in hypothetical_complete]
            if unmet_now and not unmet_after:
                newly_ready.append(task.task_id)
        return newly_ready


_engine = GraphEngine()


def get_graph_engine() -> GraphEngine:
    return _engine
