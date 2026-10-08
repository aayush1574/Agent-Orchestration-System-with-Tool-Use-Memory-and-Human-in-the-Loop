from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Memory:
    title: str
    content: str
    scope: str
    importance: float
    retrievals: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryStore:
    """Deterministic in-memory adapter; replace with Chroma/pgvector in production."""

    def __init__(self) -> None:
        self.items: list[Memory] = []

    def remember(self, memory: Memory) -> None:
        self.items.append(memory)

    def retrieve(self, query: str, limit: int = 4) -> list[Memory]:
        terms = set(query.lower().split())
        ranked = sorted(self.items, key=lambda item: (len(terms & set(item.content.lower().split())) * 10) + item.importance, reverse=True)
        selected = ranked[:limit]
        for item in selected:
            item.retrievals += 1
        return selected

    def delete(self, title: str) -> bool:
        before = len(self.items)
        self.items = [item for item in self.items if item.title != title]
        return len(self.items) < before
