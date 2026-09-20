import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from hermes_waybar.client import HermesApiClient, ProbeResult
from hermes_waybar.config import load_config
from hermes_waybar.models import DoctorReport


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def read(self):
        return json.dumps(self.payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class ClientTests(unittest.TestCase):
    def test_probe_checks_health_capabilities_and_models(self):
        responses = {
            "http://gateway/health": {"status": "ok", "version": "0.21.3"},
            "http://gateway/v1/capabilities": {"object": "capabilities", "features": {"runs": True}},
            "http://gateway/v1/models": {"object": "list", "data": [{"id": "model-a"}]},
        }

        def fake_urlopen(request, timeout):
            return FakeResponse(responses[request.full_url])

        with patch("hermes_waybar.client.urlopen", side_effect=fake_urlopen):
            report = HermesApiClient("http://gateway", "secret").doctor()

        self.assertTrue(report.reachable)
        self.assertTrue(report.authenticated)
        self.assertEqual(report.version, "0.21.3")
        self.assertEqual(report.model_count, 1)
        self.assertEqual(report.capabilities, {"runs": True})
        self.assertEqual(report.errors, [])

    def test_probe_reports_http_auth_failure_without_exposing_key(self):
        from urllib.error import HTTPError

        def fake_urlopen(request, timeout):
            raise HTTPError(request.full_url, 401, "Unauthorized", {}, None)

        with patch("hermes_waybar.client.urlopen", side_effect=fake_urlopen):
            report = HermesApiClient("http://gateway", "secret-value").doctor()

        self.assertTrue(report.reachable)
        self.assertFalse(report.authenticated)
        self.assertIn("401", " ".join(report.errors))
        self.assertNotIn("secret-value", report.to_text())


class ConfigTests(unittest.TestCase):
    def test_load_config_reads_endpoint_and_key_from_env(self):
        with patch.dict("os.environ", {
            "HERMES_WAYBAR_ENDPOINT": "https://gateway.example",
            "HERMES_WAYBAR_API_KEY": "env-secret",
        }, clear=False):
            config = load_config(Path("/nonexistent/hermes-waybar.toml"))

        self.assertEqual(config.endpoint, "https://gateway.example")
        self.assertEqual(config.api_key, "env-secret")


class OutputTests(unittest.TestCase):
    def test_report_json_is_machine_readable(self):
        report = DoctorReport(reachable=True, authenticated=True, version="0.21.3", model_count=2)
        data = json.loads(report.to_json())
        self.assertEqual(data["version"], "0.21.3")
        self.assertEqual(data["model_count"], 2)


if __name__ == "__main__":
    unittest.main()
