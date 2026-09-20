import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from hermes_waybar.notifications import poll_once


class FakeClient:
    def __init__(self, rows):
        self.rows = rows

    def session_rows(self, limit=20):
        return self.rows


class NotificationTests(unittest.TestCase):
    def test_poll_notifies_only_when_session_gets_end_reason(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            events = []
            client = FakeClient([{"id": "s1", "title": "Pesquisa", "end_reason": "completed"}])
            poll_once(client, path, notify_fn=lambda title, body: events.append((title, body)))
            self.assertEqual(len(events), 1)
            poll_once(client, path, notify_fn=lambda title, body: events.append((title, body)))
            self.assertEqual(len(events), 1)
            self.assertEqual(json.loads(path.read_text()), {"s1": "completed"})


if __name__ == "__main__":
    unittest.main()
