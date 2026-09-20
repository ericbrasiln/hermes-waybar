import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from hermes_waybar.client import HermesApiClient
from hermes_waybar.models import AgentStatus


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


class StatusTests(unittest.TestCase):
    def test_status_maps_running_gateway_to_waybar_json(self):
        def fake_urlopen(request, timeout):
            responses = {
                "http://gateway/health/detailed": {
                    "status": "ok",
                    "version": "0.21.3",
                    "gateway_state": "running",
                    "gateway_busy": True,
                    "platforms": {"api_server": {"state": "connected"}},
                },
                "http://gateway/api/sessions?limit=5": {
                    "data": [{"title": "Pesquisa", "model": "gpt-test"}],
                },
                "http://gateway/api/model/options": {
                    "model": "gpt-test",
                    "provider": "test-provider",
                },
            }
            return FakeResponse(responses[request.full_url])

        with patch("hermes_waybar.client.urlopen", side_effect=fake_urlopen):
            status = HermesApiClient("http://gateway", "secret").status()

        self.assertIsInstance(status, AgentStatus)
        self.assertEqual(status.state, "busy")
        self.assertEqual(status.version, "0.21.3")
        data = json.loads(status.to_waybar_json())
        self.assertEqual(data["class"], "busy")
        self.assertIn("ocupado", data["tooltip"])

    def test_status_maps_transport_failure_to_offline(self):
        from urllib.error import URLError

        with patch("hermes_waybar.client.urlopen", side_effect=URLError("offline")):
            status = HermesApiClient("http://gateway", "secret").status()

        self.assertEqual(status.state, "offline")
        self.assertIn("indisponível", status.to_waybar_json())


if __name__ == "__main__":
    unittest.main()
