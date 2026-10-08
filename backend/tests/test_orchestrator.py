import asyncio

from app.models import AgentRole, ApprovalDecision, ApprovalLevel, RunStatus
from app.orchestrator import Orchestrator
from app.tools import ToolDefinition, ToolRegistry


def test_plan_has_valid_dependency_order():
    orchestrator = Orchestrator()
    run = orchestrator.create_run("Research an emerging market and create a cited executive brief")
    assert run.plan is not None
    ids = [subtask.id for subtask in run.plan.subtasks]
    for index, subtask in enumerate(run.plan.subtasks):
        assert all(dependency in ids[:index] for dependency in subtask.dependencies)


def test_execution_escalates_and_approval_completes():
    orchestrator = Orchestrator()
    run = orchestrator.create_run("Research an emerging market and create a cited executive brief")
    asyncio.run(orchestrator.execute(run.id))
    assert run.status == RunStatus.WAITING_APPROVAL
    completed = orchestrator.decide(run.id, ApprovalDecision(decision="approve"))
    assert completed.status == RunStatus.COMPLETE
    assert completed.progress == 100
    assert len(orchestrator.memory.items) == 1


def test_rejection_routes_back_to_specialist():
    orchestrator = Orchestrator()
    run = orchestrator.create_run("Research an emerging market and create a cited executive brief")
    asyncio.run(orchestrator.execute(run.id))
    revised = orchestrator.decide(run.id, ApprovalDecision(decision="modify", note="Add downside case"))
    assert revised.status == RunStatus.RUNNING
    assert revised.progress == 74


def test_run_can_complete_without_final_approval():
    orchestrator = Orchestrator()
    run = orchestrator.create_run(
        "Research an emerging market and create a cited executive brief",
        require_final_approval=False,
    )
    asyncio.run(orchestrator.execute(run.id))
    assert run.status == RunStatus.COMPLETE
    assert run.progress == 100
    assert run.result and run.result["delivered"] is True


def test_low_confidence_plan_pauses_before_execution():
    orchestrator = Orchestrator()
    run = orchestrator.create_run(
        "Research an emerging market and create a cited executive brief",
        confidence_threshold=0.95,
    )
    assert run.status == RunStatus.WAITING_APPROVAL
    assert run.approval_level == ApprovalLevel.APPROVE_PLAN
    resumed = orchestrator.decide(run.id, ApprovalDecision(decision="approve"))
    assert resumed.status == RunStatus.RUNNING
    asyncio.run(orchestrator.execute(run.id))
    assert run.status == RunStatus.WAITING_APPROVAL
    assert run.approval_level == ApprovalLevel.APPROVE_ACTION


def test_execution_failure_becomes_visible_run_state():
    async def fail_search(query: str):
        raise RuntimeError(f"search unavailable for {query[:8]}")

    tools = ToolRegistry()
    tools.register(ToolDefinition("web_search", "Failing search", frozenset({AgentRole.RESEARCH}), 10, fail_search))
    orchestrator = Orchestrator(tools=tools)
    run = orchestrator.create_run("Research an emerging market and create a cited executive brief")
    asyncio.run(orchestrator.execute_safely(run.id))
    assert run.status == RunStatus.FAILED
    assert run.error and "search unavailable" in run.error
    assert run.traces[-1].event == "execution_failed"
