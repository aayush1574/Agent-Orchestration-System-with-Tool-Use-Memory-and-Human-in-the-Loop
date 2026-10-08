from __future__ import annotations

import asyncio
import inspect
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from .models import AgentRole

ToolHandler = Callable[..., Awaitable[dict[str, Any]] | dict[str, Any]]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    allowed_agents: frozenset[AgentRole]
    rate_limit_per_minute: int
    handler: ToolHandler


class ToolRegistry:
    """Validated tool boundary with agent permissions, rate limits, and invocation logs."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._calls: dict[str, deque[float]] = defaultdict(deque)
        self.invocations: list[dict[str, Any]] = []

    def register(self, definition: ToolDefinition) -> None:
        if definition.name in self._tools:
            raise ValueError(f"Tool already registered: {definition.name}")
        self._tools[definition.name] = definition

    async def invoke(self, name: str, agent: AgentRole, **inputs: Any) -> dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        tool = self._tools[name]
        if agent not in tool.allowed_agents:
            raise PermissionError(f"{agent.value} cannot use {name}")
        now = time.monotonic()
        calls = self._calls[name]
        while calls and now - calls[0] > 60:
            calls.popleft()
        if len(calls) >= tool.rate_limit_per_minute:
            raise RuntimeError(f"Rate limit exceeded for {name}")
        calls.append(now)
        started = time.perf_counter()
        try:
            value = tool.handler(**inputs)
            output = await value if inspect.isawaitable(value) else value
            self.invocations.append({"tool": name, "agent": agent.value, "inputs": inputs, "output": output, "latency_ms": int((time.perf_counter() - started) * 1000), "success": True})
            return output
        except Exception as exc:
            self.invocations.append({"tool": name, "agent": agent.value, "inputs": inputs, "error": str(exc), "latency_ms": int((time.perf_counter() - started) * 1000), "success": False})
            raise


async def demo_web_search(query: str) -> dict[str, Any]:
    await asyncio.sleep(0.04)
    return {"query": query, "results": [{"title": "Primary market source", "authority": 0.96}, {"title": "Company filing", "authority": 0.94}], "source_count": 2}


def default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ToolDefinition("web_search", "Search and rank authoritative web sources.", frozenset({AgentRole.RESEARCH}), 30, demo_web_search))
    registry.register(ToolDefinition("calculator", "Perform deterministic analysis over numeric inputs.", frozenset({AgentRole.ANALYSIS}), 60, lambda values: {"sum": sum(values), "count": len(values)}))
    return registry
