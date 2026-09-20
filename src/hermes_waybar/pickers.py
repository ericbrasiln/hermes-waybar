"""Interactive pickers (Rofi/Walker) for hermes-waybar."""
from __future__ import annotations

import shutil
import subprocess
from typing import Sequence


def _run_rofi(entries: Sequence[str], prompt: str, theme: str | None) -> str | None:
    if entries:
        command = ["rofi", "-dmenu", "-i", "-p", prompt]
    else:
        command = ["rofi", "-dmenu", "-p", prompt, "-lines", "0"]
    if theme:
        command += ["-theme", theme]
    result = subprocess.run(
        command,
        input="\n".join(entries),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.strip()


def _run_walker(entries: Sequence[str], prompt: str) -> str | None:
    result = subprocess.run(
        ["walker", "--dmenu"],
        input="\n".join(entries),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.strip()


def pick(entries: Sequence[str], prompt: str, theme: str | None = None) -> str | None:
    """Show a picker with the first available backend. None when cancelled.

    With no entries and rofi available, opens a free-text entry dialog.
    """
    entries = [entry for entry in entries if entry]
    if shutil.which("rofi"):
        return _run_rofi(entries, prompt, theme)
    if shutil.which("walker") and entries:
        return _run_walker(entries, prompt)
    if not entries:
        try:
            return input(f"{prompt}: ").strip() or None
        except EOFError:
            return None
    for index, entry in enumerate(entries, 1):
        print(f"{index}. {entry}")
    try:
        chosen = input(f"{prompt}: ")
    except EOFError:
        return None
    if not chosen.strip():
        return None
    try:
        return entries[int(chosen.strip()) - 1]
    except (ValueError, IndexError):
        matches = [entry for entry in entries if chosen.strip() in entry]
        return matches[0] if matches else None