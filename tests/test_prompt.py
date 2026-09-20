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
        import json
        return json.dumps(self.payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class PromptTests(unittest.TestCase):
    def test_send_prompt_posts_message_and_returns_response(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["data"] = request.data
            captured["auth"] = request.headers.get("Authorization")
            return FakeResponse({"final_response": "pronto"})

        with patch("hermes_waybar.client.urlopen", side_effect=fake_urlopen):
            response = HermesApiClient("http://gateway", "secret").send_prompt("s1", "olá")

        self.assertEqual(response["final_response"], "pronto")
        self.assertEqual(captured["url"], "http://gateway/api/sessions/s1/chat")
        self.assertIn(b'"message"', captured["data"])
        self.assertEqual(captured["auth"], "Bearer secret")

    def test_send_prompt_rejects_empty_inputs(self):
        client = HermesApiClient("http://gateway", "secret")
        with self.assertRaises(ValueError):
            client.send_prompt("", "olá")
        with self.assertRaises(ValueError):
            client.send_prompt("s1", "   ")

    def test_visible_sessions_filters_hidden_rows(self):
        def fake_urlopen(request, timeout):
            return FakeResponse({
                "data": [
                    {"id": "a", "title": "visível"},
                    {"id": "b", "title": "oculta", "hidden": True},
                ],
            })

        with patch("hermes_waybar.client.urlopen", side_effect=fake_urlopen):
            rows = HermesApiClient("http://gateway", "secret").visible_sessions()

        self.assertEqual([row["id"] for row in rows], ["a"])


if __name__ == "__main__":
    unittest.main()