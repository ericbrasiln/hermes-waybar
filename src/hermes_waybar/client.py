from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import DoctorReport


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
