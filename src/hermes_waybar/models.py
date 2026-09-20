from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentStatus:
    state: str
    version: str | None = None
    detail: str = ""

    def to_waybar_dict(self) -> dict[str, str]:
        labels = {
            "running": ("☤", "Hermes: disponível"),
            "busy": ("☤", "Hermes: ocupado"),
            "offline": ("☤", "Hermes: indisponível"),
            "error": ("☤", "Hermes: erro"),
        }
        text, label = labels.get(self.state, ("☤", "Hermes: desconhecido"))
        version = f"\nVersão: {self.version}" if self.version else ""
        detail = f"\n{self.detail}" if self.detail else ""
        return {
            "text": text,
            "tooltip": f"{label}{version}{detail}",
            "class": self.state,
            "alt": self.state,
        }

    def to_waybar_json(self) -> str:
        return json.dumps(self.to_waybar_dict(), ensure_ascii=False)


@dataclass
class DoctorReport:
    reachable: bool = False
    authenticated: bool = False
    version: str | None = None
    model_count: int = 0
    capabilities: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.reachable and self.authenticated and not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "ok": self.ok}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)

    def to_text(self) -> str:
        lines = [
            f"reachable: {'yes' if self.reachable else 'no'}",
            f"authenticated: {'yes' if self.authenticated else 'no'}",
            f"version: {self.version or 'unknown'}",
            f"models: {self.model_count}",
        ]
        if self.capabilities:
            lines.append("capabilities: " + ", ".join(sorted(self.capabilities)))
        if self.errors:
            lines.append("errors:")
            lines.extend(f"  - {error}" for error in self.errors)
        return "\n".join(lines)
