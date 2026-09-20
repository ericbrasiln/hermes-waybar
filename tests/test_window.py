import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from hermes_waybar.cli import _hyprland_window_exists


class FakeResult:
    def __init__(self, stdout, returncode=0):
        self.stdout = stdout
        self.returncode = returncode


class WindowTests(unittest.TestCase):
    def test_detects_window_class_in_hyprctl_clients(self):
        payload = json.dumps([
            {"class": "Alacritty"},
            {"class": "Hermes", "title": "Hermes Desktop"},
        ])
        with patch("subprocess.run", return_value=FakeResult(payload)):
            self.assertTrue(_hyprland_window_exists("Hermes"))

    def test_returns_false_when_class_absent(self):
        payload = json.dumps([{"class": "Alacritty"}])
        with patch("subprocess.run", return_value=FakeResult(payload)):
            self.assertFalse(_hyprland_window_exists("Hermes"))

    def test_returns_false_when_hyprctl_missing(self):
        from subprocess import TimeoutExpired

        def raise_timeout(*args, **kwargs):
            raise TimeoutExpired("hyprctl", 5)

        with patch("subprocess.run", side_effect=raise_timeout):
            self.assertFalse(_hyprland_window_exists("Hermes"))


if __name__ == "__main__":
    unittest.main()