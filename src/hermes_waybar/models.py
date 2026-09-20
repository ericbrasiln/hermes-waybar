from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


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
