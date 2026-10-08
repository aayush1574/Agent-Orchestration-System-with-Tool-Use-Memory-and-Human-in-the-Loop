import asyncio

from app.models import ApprovalDecision, RunStatus
from app.orchestrator import Orchestrator


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
