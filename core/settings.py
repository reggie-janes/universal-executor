"""Persist UI/user preferences to ``settings.json`` in the repo root.

Generic dict-shaped store. Callers own the key names. Reads tolerate a missing
or malformed file by returning ``{}`` so the app can boot from any state.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path(__file__).parent / "settings.json"


def load() -> dict[str, Any]:
    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save(data: dict[str, Any]) -> None:
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update(**changes: Any) -> dict[str, Any]:
    data = load()
    data.update(changes)
    save(data)
    return data
