"""Bounded, local JSON conversation memory."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import read_json, write_json


class MemoryStore:
    def __init__(self, path: Path, max_items: int = 2_000) -> None:
        self.path = path
        self.max_items = max(1, max_items)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._items: list[dict[str, Any]] = read_json(path, [])
        if not isinstance(self._items, list):
            raise RuntimeError(f"Invalid memory format in {path}; expected a JSON list.")

    def add(self, role: str, content: str) -> None:
        if role not in {"user", "assistant", "system"}:
            raise ValueError("role must be user, assistant, or system")
        item = {
            "role": role,
            "content": content[:8_000],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._items.append(item)
        self._items = self._items[-self.max_items :]
        write_json(self.path, self._items)

    def recent(self, limit: int = 8) -> list[dict[str, Any]]:
        return [dict(item) for item in self._items[-max(0, limit) :]]

    def clear(self) -> None:
        self._items = []
        write_json(self.path, self._items)

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        terms = {term.casefold() for term in query.split() if len(term) > 2}
        if not terms:
            return []
        ranked = []
        for item in self._items:
            content = str(item.get("content", ""))
            words = set(content.casefold().split())
            score = len(terms & words)
            if score:
                ranked.append((score, item))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [dict(item) for _, item in ranked[:limit]]
