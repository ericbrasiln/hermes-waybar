from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Callable

from .client import HermesApiClient


def default_state_path() -> Path:
    return Path.home() / ".local" / "state" / "hermes-waybar" / "notifications.json"


def _notify(title: str, body: str, notify_fn: Callable[..., object] | None = None) -> None:
    if notify_fn is not None:
        notify_fn(title, body)
        return
    try:
        subprocess.run(
            ["notify-send", "--app-name=Hermes", title, body],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def poll_once(
    client: HermesApiClient,
    state_path: Path,
    *,
    notify_fn: Callable[..., object] | None = None,
) -> int:
    rows = client.session_rows(limit=20)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    previous = {}
    if state_path.is_file():
        try:
            previous = json.loads(state_path.read_text())
        except (OSError, json.JSONDecodeError):
            previous = {}

    current = {}
    notifications = 0
    for row in rows:
        session_id = str(row.get("id") or "")
        if not session_id:
            continue
        end_reason = str(row.get("end_reason") or "")
        current[session_id] = end_reason
        if end_reason and previous.get(session_id) != end_reason:
            title = str(row.get("title") or session_id)
            _notify("Sessão Hermes concluída", f"{title}: {end_reason}", notify_fn)
            notifications += 1

    state_path.write_text(json.dumps(current, ensure_ascii=False, sort_keys=True))
    return notifications


def watch(
    client: HermesApiClient,
    state_path: Path,
    interval: float = 10.0,
    *,
    once: bool = False,
    notify_fn: Callable[..., object] | None = None,
) -> int:
    while True:
        try:
            poll_once(client, state_path, notify_fn=notify_fn)
        except Exception as exc:
            if once:
                raise
            print(f"hermes-waybar: notification poll failed: {exc}")
        if once:
            return 0
        time.sleep(interval)
