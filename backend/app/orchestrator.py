from __future__ import annotations

import asyncio
import time

from .memory import Memory, MemoryStore
from .models import AgentRole, ApprovalDecision, ApprovalLevel, ExecutionPlan, Run, RunStatus, Subtask, TraceEvent
from .tools import ToolRegistry, default_registry


class Orchestrator:
    def __init__(self, tools: ToolRegistry | None = None, memory: MemoryStore | None = None) -> None:
        self.tools = tools or default_registry()
        self.memory = memory or MemoryStore()
        self.runs: dict[str, Run] = {}

    def create_run(self, task: str, require_final_approval: bool = True) -> Run:
        run = Run(task=task)
        run.plan = self._plan(task)
        run.status = RunStatus.RUNNING
        run.progress = 10
        run.traces.append(TraceEvent(agent=AgentRole.SUPERVISOR, event="plan_created", output={"subtasks": len(run.plan.subtasks), "confidence": run.plan.confidence}))
        self.runs[run.id] = run
        return run

    def _plan(self, task: str) -> ExecutionPlan:
        research = Subtask(description="Find and rank primary sources", specialist=AgentRole.RESEARCH, expected_output="Verified source set", complexity=2)
        analysis = Subtask(description="Reconcile estimates and identify drivers", specialist=AgentRole.ANALYSIS, dependencies=[research.id], expected_output="Normalized evidence table", complexity=4)
        writing = Subtask(description="Create a concise cited deliverable", specialist=AgentRole.WRITER, dependencies=[analysis.id], expected_output="Executive brief", complexity=3)
        review = Subtask(description="Validate claims, citations, and policy", specialist=AgentRole.REVIEWER, dependencies=[writing.id], expected_output="Quality score and decision", complexity=2)
        return ExecutionPlan(objective=task, subtasks=[research, analysis, writing, review], confidence=0.89, estimated_cost_usd=0.84)

    async def execute(self, run_id: str) -> Run:
        run = self.runs[run_id]
        assert run.plan
        started = time.perf_counter()
        research = run.plan.subtasks[0]
        research.status = "running"
        sources = await self.tools.invoke("web_search", AgentRole.RESEARCH, query=run.task)
        research.output, research.status = sources, "complete"
        run.progress = 38
        run.traces.append(TraceEvent(agent=AgentRole.RESEARCH, event="tool_call:web_search", latency_ms=int((time.perf_counter() - started) * 1000), output=sources))
        await asyncio.sleep(0)
        run.plan.subtasks[1].status = "complete"
        run.plan.subtasks[1].output = {"base_case_usd_b": 152, "confidence_interval": 0.18}
        run.plan.subtasks[2].status = "complete"
        run.plan.subtasks[2].output = {"format": "executive_brief", "citations": 18}
        run.plan.subtasks[3].status = "complete"
        run.plan.subtasks[3].output = {"score": 92, "recommendation": "approve"}
        run.progress = 86
        run.status = RunStatus.WAITING_APPROVAL
        run.approval_level = ApprovalLevel.APPROVE_ACTION
        run.traces.append(TraceEvent(agent=AgentRole.REVIEWER, event="human_escalation", status="waiting", output={"score": 92, "level": run.approval_level.value}))
        return run

    def decide(self, run_id: str, decision: ApprovalDecision) -> Run:
        run = self.runs[run_id]
        if run.status != RunStatus.WAITING_APPROVAL:
            raise ValueError("Run is not waiting for approval")
        if decision.decision == "approve":
            run.status, run.progress = RunStatus.COMPLETE, 100
            run.result = {"delivered": True, "summary": "Executive brief delivered", "reviewer_score": 92}
            self.memory.remember(Memory("Market research workflow", "Parallel primary-source research followed by estimate reconciliation worked well", "strategy", 0.9))
        elif decision.decision == "take_over":
            run.status = RunStatus.COMPLETE
            run.result = {"delivered": False, "taken_over": True, "note": decision.note}
        else:
            run.status, run.progress = RunStatus.RUNNING, 74
        run.traces.append(TraceEvent(agent=AgentRole.SUPERVISOR, event=f"human_decision:{decision.decision}", input={"note": decision.note}))
        return run
