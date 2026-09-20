from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    endpoint: str
    api_key: str
    timeout: float = 8.0


def default_config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "hermes-waybar" / "config.toml"


def load_config(path: Path | None = None) -> Config:
    values: dict[str, object] = {}
    config_path = path or default_config_path()
    if config_path.is_file():
        with config_path.open("rb") as handle:
            raw = tomllib.load(handle)
        values = raw.get("hermes", raw) if isinstance(raw, dict) else {}

    endpoint = os.environ.get("HERMES_WAYBAR_ENDPOINT", str(values.get("endpoint", ""))).strip()
    api_key = os.environ.get("HERMES_WAYBAR_API_KEY", str(values.get("api_key", ""))).strip()
    raw_timeout = os.environ.get("HERMES_WAYBAR_TIMEOUT", str(values.get("timeout", "8")))
    try:
        timeout = float(raw_timeout)
    except ValueError as exc:
        raise ValueError("HERMES_WAYBAR_TIMEOUT must be a number") from exc
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    return Config(endpoint=endpoint.rstrip("/"), api_key=api_key, timeout=timeout)
