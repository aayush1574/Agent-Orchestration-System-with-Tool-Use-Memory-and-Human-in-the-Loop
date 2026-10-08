# AgentOps Control Room

A portfolio-ready multi-agent orchestration system with dependency-aware planning, specialist routing, a permissioned tool registry, persistent memory, human approval gates, complete traces, and replay.

## What is included

- **Interactive control room:** start a run, watch the plan progress, approve or revise delivery, inspect memories, explore spans, and replay an execution.
- **Python orchestration API:** typed task plans, parallel-ready subtasks, specialist execution, escalation policy, tool permissions/rate limits, traces, and memory extraction.
- **Persistent hosted state:** D1 schema and API route for runs and approval decisions.
- **Production infrastructure:** Docker Compose services for FastAPI, Redis, PostgreSQL, and ChromaDB.
- **Agent-facing controls:** WebMCP tools for starting a run and approving a pending delivery when the browser supports them.

## Run the web console

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Run the orchestration API

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; OpenAPI docs are at `/docs`.

## Run with infrastructure

```bash
docker compose up --build
```

## Test

```bash
cd backend
pytest
```

The default implementation uses deterministic specialists so the project works without credentials. Replace handlers in `backend/app/tools.py` with real MCP tools and configure model adapters in the orchestration layer for OpenAI/Anthropic production routing.
