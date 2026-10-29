"""Simple offline document store and transparent lexical retrieval."""
import re
from pathlib import Path
from typing import Any

from .storage import read_json, write_json

TOKEN_RE = re.compile(r"[a-zA-Z0-9_'-]+")


def tokens(text: str) -> set[str]:
    return {token.casefold() for token in TOKEN_RE.findall(text) if len(token) > 1}


class KnowledgeBase:
    SUPPORTED = {".txt", ".md", ".rst", ".py", ".json", ".csv", ".html", ".xml"}

    def __init__(self, path: Path, max_items: int = 5_000) -> None:
        self.path = path
        self.max_items = max(1, max_items)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._items: list[dict[str, Any]] = read_json(path, [])
        if not isinstance(self._items, list):
            raise RuntimeError(f"Invalid knowledge format in {path}; expected a JSON list.")

    @property
    def count(self) -> int:
        return len(self._items)

    def add_text(self, text: str, source: str = "manual") -> bool:
        cleaned = text.strip()
        if not cleaned:
            return False
        record = {"text": cleaned[:20_000], "source": source[:500]}
        fingerprint = (record["source"], record["text"])
        if any((item.get("source"), item.get("text")) == fingerprint for item in self._items):
            return False
        self._items.append(record)
        self._items = self._items[-self.max_items :]
        write_json(self.path, self._items)
        return True

    def ingest_file(self, path: Path) -> int:
        if path.suffix.casefold() not in self.SUPPORTED:
            raise ValueError(f"Unsupported file type: {path.suffix or '(no extension)'}")
        if not path.is_file():
            raise FileNotFoundError(f"Not a file: {path}")
        if path.stat().st_size > 1_000_000:
            raise ValueError("Files larger than 1 MB are not accepted.")
        content = path.read_text(encoding="utf-8", errors="replace")
        chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", content) if chunk.strip()]
        added = sum(self.add_text(chunk, str(path)) for chunk in chunks)
        return added

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_tokens = tokens(query)
        if not query_tokens:
            return []
        scored = []
        for item in self._items:
            text = str(item.get("text", ""))
            doc_tokens = tokens(text)
            if not doc_tokens:
                continue
            overlap = len(query_tokens & doc_tokens)
            if not overlap:
                continue
            # Overlap normalized by query size; intentionally simple and explainable.
            score = overlap / len(query_tokens)
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            {"score": round(score, 3), "text": item["text"], "source": item.get("source", "unknown")}
            for score, item in scored[:max(0, limit)]
        ]
