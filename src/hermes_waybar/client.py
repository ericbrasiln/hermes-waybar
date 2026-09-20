from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import AgentStatus, DoctorReport


@dataclass(frozen=True)
class ProbeResult:
    status: int
    payload: dict[str, Any]


class HermesApiClient:
    def __init__(self, endpoint: str, api_key: str, timeout: float = 8.0):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get(self, path: str) -> ProbeResult:
        request = Request(
            f"{self.endpoint}{path}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "hermes-waybar/0.1",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read())
                return ProbeResult(response.status, payload)
        except HTTPError as exc:
            raise HTTPError(exc.url, exc.code, exc.reason, exc.headers, exc.fp) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ConnectionError(str(exc)) from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"invalid JSON from {path}") from exc

    def session_rows(self, limit: int = 5) -> list[dict[str, Any]]:
        result = self._get(f"/api/sessions?limit={max(1, min(limit, 20))}")
        rows = result.payload.get("data", [])
        return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []

    def visible_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        return [row for row in self.session_rows(limit) if not row.get("hidden")]

    def send_prompt(self, session_id: str, message: str) -> dict[str, Any]:
        if not session_id:
            raise ValueError("session id is required")
        if not message.strip():
            raise ValueError("message is required")
        request = Request(
            f"{self.endpoint}/api/sessions/{session_id}/chat",
            data=json.dumps({"message": message}).encode(),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "hermes-waybar/0.1",
            },
            method="POST",
        )
        with urlopen(request, timeout=max(self.timeout, 300.0)) as response:
            return json.loads(response.read())

    def sessions(self, limit: int = 5) -> list[str]:
        rows = self.session_rows(limit)
        labels = []
        for row in rows:
            if not isinstance(row, dict) or row.get("hidden"):
                continue
            title = str(row.get("title") or row.get("id") or "sessão").strip()
            model = str(row.get("model") or "").strip()
            labels.append(f"{title[:56]}" + (f" [{model}]" if model else ""))
        return labels[:limit]

    def current_model(self) -> tuple[str, str]:
        """Return (model, provider) from the API Server model options."""
        try:
            result = self._get("/api/model/options")
        except (HTTPError, ConnectionError, ValueError):
            return "", ""
        model = str(result.payload.get("model") or "").strip()
        provider = str(result.payload.get("provider") or "").strip()
        return model, provider

    def status(self) -> AgentStatus:
        if not self.endpoint or not self.api_key:
            return AgentStatus("offline", detail="configuração ausente")
        try:
            result = self._get("/health/detailed")
        except HTTPError as exc:
            return AgentStatus("error", detail=f"HTTP {exc.code}")
        except (ConnectionError, ValueError) as exc:
            return AgentStatus("offline", detail=str(exc))

        payload = result.payload
        gateway_state = payload.get("gateway_state")
        if gateway_state != "running":
            return AgentStatus(
                "offline",
                version=str(payload.get("version") or "") or None,
                detail=f"gateway: {gateway_state or 'desconhecido'}",
            )
        state = "busy" if payload.get("gateway_busy") else "running"
        try:
            sessions = self.sessions()
        except (HTTPError, ConnectionError, ValueError):
            sessions = []
        model, provider = self.current_model()
        return AgentStatus(
            state,
            version=str(payload.get("version") or "") or None,
            sessions=sessions,
            model=model,
            provider=provider,
        )

    def doctor(self) -> DoctorReport:
        report = DoctorReport()
        if not self.endpoint:
            report.errors.append("endpoint is not configured")
            return report
        if not self.api_key:
            report.errors.append("API key is not configured")
            return report

        try:
            health = self._get("/health")
            report.reachable = True
            report.version = str(health.payload.get("version") or "") or None
        except HTTPError as exc:
            report.reachable = True
            report.errors.append(f"health returned HTTP {exc.code}")
        except (ConnectionError, ValueError) as exc:
            report.errors.append(f"health failed: {exc}")
            return report

        try:
            capabilities = self._get("/v1/capabilities")
            if capabilities.status >= 400:
                report.errors.append(f"capabilities returned HTTP {capabilities.status}")
            else:
                report.authenticated = True
                features = capabilities.payload.get("features", {})
                if isinstance(features, dict):
                    report.capabilities = features
        except HTTPError as exc:
            report.errors.append(f"capabilities returned HTTP {exc.code}")
        except (ConnectionError, ValueError) as exc:
            report.errors.append(f"capabilities failed: {exc}")

        try:
            models = self._get("/v1/models")
            if models.status >= 400:
                report.errors.append(f"models returned HTTP {models.status}")
            else:
                data = models.payload.get("data", [])
                report.model_count = len(data) if isinstance(data, list) else 0
        except HTTPError as exc:
            report.errors.append(f"models returned HTTP {exc.code}")
        except (ConnectionError, ValueError) as exc:
            report.errors.append(f"models failed: {exc}")

        return report
