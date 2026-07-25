from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MEMORY_FILE = Path("assistant_memory.json")


def load_memory() -> dict[str, Any]:
    """Load saved assistant memory from disk."""

    if not MEMORY_FILE.exists():
        return {
            "messages": [],
            "user_preferences": {},
        }

    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Memory file must contain a JSON object.")

        return {
            "messages": data.get("messages", []),
            "user_preferences": data.get("user_preferences", {}),
        }

    except (json.JSONDecodeError, OSError, ValueError):
        return {
            "messages": [],
            "user_preferences": {},
        }


def save_memory(memory: dict[str, Any]) -> None:
    """Save assistant memory to disk."""

    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            memory,
            file,
            indent=2,
            ensure_ascii=False,
        )


def clear_memory() -> None:
    """Delete all saved assistant memory."""

    if MEMORY_FILE.exists():
        MEMORY_FILE.unlink()