from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import ApprovalDecision, TaskRequest
from .orchestrator import Orchestrator

app = FastAPI(title="AgentOps API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])
orchestrator = Orchestrator()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/runs", status_code=202)
async def create_run(request: TaskRequest, background: BackgroundTasks):
    run = orchestrator.create_run(request.task, request.require_final_approval)
    background.add_task(orchestrator.execute, run.id)
    return run


@app.get("/api/runs")
def list_runs():
    return list(orchestrator.runs.values())


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    if run_id not in orchestrator.runs:
        raise HTTPException(404, "Run not found")
    return orchestrator.runs[run_id]


@app.post("/api/runs/{run_id}/decision")
def decide(run_id: str, decision: ApprovalDecision):
    try:
        return orchestrator.decide(run_id, decision)
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
