"""
Small checkpoint helpers for recovering automation state across page UI resets.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.conf import settings


CHECKPOINT_KEYS = [
    "target_url",
    "selected_country",
    "chosen_suggestion",
    "chosen_suggestion_index",
    "destination_committed",
    "selected_month",
    "checkin_date",
    "checkout_date",
    "guest_count",
    "guest_breakdown",
    "guest_total_added",
    "listings",
    "selected_listing_title",
    "selected_listing_subtitle",
    "selected_listing_images",
]


def _checkpoint_path() -> Path:
    path = getattr(settings, "RUNTIME_STATE_FILE", None)
    if path:
        return Path(path)
    base_dir = Path(getattr(settings, "BASE_DIR", Path.cwd()))
    return base_dir / "runtime_state.json"


def _is_json_safe(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool, list, dict, type(None)))


def _extract_state(shared_state: dict) -> dict:
    state = {}
    for key in CHECKPOINT_KEYS:
        value = shared_state.get(key)
        if _is_json_safe(value):
            state[key] = value
    return state


def save_checkpoint(shared_state: dict, step_name: str) -> str:
    payload = {
        "step": step_name,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "state": _extract_state(shared_state),
    }
    path = _checkpoint_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def load_checkpoint() -> dict:
    path = _checkpoint_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        state = payload.get("state", {})
        return state if isinstance(state, dict) else {}
    except Exception:
        return {}


def merge_checkpoint(shared_state: dict) -> dict:
    restored = load_checkpoint()
    for key, value in restored.items():
        current = shared_state.get(key)
        if current in (None, "", [], {}):
            shared_state[key] = value
    return restored


def clear_checkpoint() -> None:
    path = _checkpoint_path()
    if path.exists():
        path.unlink()
