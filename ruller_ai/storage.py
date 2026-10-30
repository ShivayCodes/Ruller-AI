"""Small JSON persistence helpers with atomic writes."""
import json
import os
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Could not read data file {path}: {exc}") from exc


def write_json(path: Path, value: Any, *, sync: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            if sync:
                os.fsync(handle.fileno())
        temporary.replace(path)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise RuntimeError(f"Could not write data file {path}: {exc}") from exc
