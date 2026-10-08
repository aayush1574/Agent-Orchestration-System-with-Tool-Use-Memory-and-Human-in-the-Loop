import os

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import ApprovalDecision, TaskRequest
from .orchestrator import Orchestrator

allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app = FastAPI(title="AgentOps API", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=False, allow_methods=["GET", "POST", "DELETE"], allow_headers=["content-type", "authorization"])
orchestrator = Orchestrator()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def readiness() -> dict[str, str | int]:
    return {"status": "ready", "registered_tools": orchestrator.tools.registered_count}


@app.post("/api/runs", status_code=202)
async def create_run(request: TaskRequest, background: BackgroundTasks):
    run = orchestrator.create_run(request.task, request.require_final_approval, request.confidence_threshold)
    if run.status.value == "running":
        background.add_task(orchestrator.execute_safely, run.id)
    return run


@app.get("/api/runs")
def list_runs():
    return list(orchestrator.runs.values())[-100:]


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    if run_id not in orchestrator.runs:
        raise HTTPException(404, "Run not found")
    return orchestrator.runs[run_id]


@app.post("/api/runs/{run_id}/decision")
def decide(run_id: str, decision: ApprovalDecision, background: BackgroundTasks):
    try:
        run = orchestrator.decide(run_id, decision)
        if decision.decision == "approve" and run.status.value == "running":
            background.add_task(orchestrator.execute_safely, run.id)
        return run
    except KeyError:
        raise HTTPException(404, "Run not found")
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@app.get("/api/memories")
def list_memories():
    return orchestrator.memory.items


@app.delete("/api/memories/{title}")
def delete_memory(title: str):
    if not orchestrator.memory.delete(title):
        raise HTTPException(404, "Memory not found")
    return {"deleted": True}
