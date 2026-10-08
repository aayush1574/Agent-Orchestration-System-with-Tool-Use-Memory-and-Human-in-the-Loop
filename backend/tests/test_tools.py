import asyncio
import pytest

from app.models import AgentRole
from app.tools import ToolDefinition, ToolRegistry, default_registry


def test_tool_registry_enforces_agent_permissions():
    registry = default_registry()
    with pytest.raises(PermissionError):
        asyncio.run(registry.invoke("web_search", AgentRole.WRITER, query="test"))


def test_tool_invocation_is_logged():
    registry = default_registry()
    result = asyncio.run(registry.invoke("calculator", AgentRole.ANALYSIS, values=[1, 2, 3]))
    assert result["sum"] == 6
    assert registry.invocations[0]["success"] is True


def test_tool_registry_enforces_rate_limits():
    registry = ToolRegistry()
    registry.register(ToolDefinition("once", "Single call", frozenset({AgentRole.ANALYSIS}), 1, lambda: {"ok": True}))
    asyncio.run(registry.invoke("once", AgentRole.ANALYSIS))
    with pytest.raises(RuntimeError, match="Rate limit exceeded"):
        asyncio.run(registry.invoke("once", AgentRole.ANALYSIS))
