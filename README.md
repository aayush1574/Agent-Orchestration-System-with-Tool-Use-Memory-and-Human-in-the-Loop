# AgentOps Control Room

A portfolio-ready multi-agent orchestration system with dependency-aware planning, specialist routing, a permissioned tool registry, persistent memory, human approval gates, complete traces, and replay.

**Live deployment:** [agentops-control-room.aayush-agentops.workers.dev](https://agentops-control-room.aayush-agentops.workers.dev)

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

## Deploy the hosted console to Cloudflare

The production Worker uses Cloudflare D1 through the `DB` binding generated from
`vite.config.ts`. After authenticating Wrangler and applying the SQL migrations,
deploy the console with:

```bash
npx wrangler d1 execute agentops-control-room --remote --file drizzle/0000_good_makkari.sql
npx wrangler d1 execute agentops-control-room --remote --file drizzle/0001_overjoyed_pete_wisdom.sql
npm run deploy:cloudflare
```

## Test

```bash
cd backend
pytest
```

The default implementation uses deterministic specialists so the project works without credentials. Replace handlers in `backend/app/tools.py` with real MCP tools and configure model adapters in the orchestration layer for OpenAI/Anthropic production routing.

## Production notes

- Copy `.env.example` to `.env` and restrict `ALLOWED_ORIGINS` to the deployed console origin before exposing the standalone API.
- The hosted console persists runs and approval decisions in D1 and exposes `/api/health` for readiness monitoring.
- The FastAPI service exposes `/health/live` and `/health/ready`; configure your container platform to use them for liveness and readiness probes.
- Approval policy is enforced for both low-confidence plans and final delivery. Background failures become explicit failed runs with trace events instead of disappearing silently.
- Tool permissions and per-minute limits are enforced at the registry boundary. Replace demo tool handlers with authenticated MCP/API adapters and keep their secrets in your deployment secret manager.
- Run `npm audit --omit=dev`, `npm run lint`, `npm run build`, and `pytest` in CI before deployment.
