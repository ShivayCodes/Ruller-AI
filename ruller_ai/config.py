"""Configuration and workspace-safe paths."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings. All persistent data stays in the selected data directory."""

    data_dir: Path = Path.home() / ".ruller_ai"
    max_input_chars: int = 8_000
    max_memory_items: int = 2_000
    max_knowledge_items: int = 5_000
    provider: str | None = None
    model: str | None = None
    api_base: str | None = None
    api_key: str | None = None

    @property
    def memory_file(self) -> Path:
        return self.data_dir / "memory.json"

    @property
    def knowledge_file(self) -> Path:
        return self.data_dir / "knowledge.json"

    @property
    def feedback_file(self) -> Path:
        return self.data_dir / "feedback.jsonl"
