from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    SUPERVISOR = "supervisor"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    WRITER = "writer"
    REVIEWER = "reviewer"


class RunStatus(str, Enum):
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETE = "complete"
    FAILED = "failed"


class ApprovalLevel(str, Enum):
    NOTIFY = "notify"
    APPROVE_ACTION = "approve_action"
    APPROVE_PLAN = "approve_plan"
    TAKE_OVER = "take_over"


class Subtask(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:10])
    description: str
    specialist: AgentRole
    dependencies: list[str] = Field(default_factory=list)
    expected_output: str
    complexity: int = Field(ge=1, le=5, default=2)
    status: str = "queued"
    output: dict[str, Any] | None = None


class ExecutionPlan(BaseModel):
    objective: str
    subtasks: list[Subtask]
    estimated_cost_usd: float = 0.0
    confidence: float = Field(ge=0, le=1)


class TraceEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent: AgentRole
    event: str
    status: str = "ok"
    latency_ms: int = 0
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)


class TaskRequest(BaseModel):
    task: str = Field(min_length=10, max_length=10_000)
    require_final_approval: bool = True
    confidence_threshold: float = Field(default=0.75, ge=0.5, le=1)


class Run(BaseModel):
    id: str = Field(default_factory=lambda: f"AO-{uuid4().hex[:6].upper()}")
    task: str
    status: RunStatus = RunStatus.PLANNING
    plan: ExecutionPlan | None = None
    progress: int = 0
    traces: list[TraceEvent] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    approval_level: ApprovalLevel | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(approve|modify|reject|take_over)$")
    note: str = Field(default="", max_length=2_000)
