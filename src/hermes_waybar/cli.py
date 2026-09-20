from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

from .client import HermesApiClient
from .config import default_config_path, load_config
from .notifications import default_state_path, watch
from .pickers import pick


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-waybar")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor = subparsers.add_parser("doctor", help="test the Hermes API Server connection")
    doctor.add_argument("--endpoint", help="override the configured API Server URL")
    doctor.add_argument("--api-key", help="override the configured API Server key")
    doctor.add_argument("--config", type=Path, help="configuration file path")
    doctor.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    status = subparsers.add_parser("status", help="emit current status for Waybar")
    status.add_argument("--endpoint", help="override the configured API Server URL")
    status.add_argument("--api-key", help="override the configured API Server key")
    status.add_argument("--config", type=Path, help="configuration file path")
    status.add_argument("--waybar", action="store_true", help="emit Waybar JSON")
    subparsers.add_parser("open", help="open or focus Hermes Desktop")
    subparsers.add_parser("hud", help="open Hermes Desktop and float it (HUD)")
    subparsers.add_parser("focus", help="focus an existing Hermes Desktop window")
    watch_parser = subparsers.add_parser("watch", help="watch session completion notifications")
    watch_parser.add_argument("--endpoint", help="override the configured API Server URL")
    watch_parser.add_argument("--api-key", help="override the configured API Server key")
    watch_parser.add_argument("--config", type=Path, help="configuration file path")
    watch_parser.add_argument("--interval", type=float, default=10.0)
    watch_parser.add_argument("--state", type=Path, default=default_state_path())
    watch_parser.add_argument("--once", action="store_true")
    sessions_parser = subparsers.add_parser("sessions", help="pick a session and open it")
    sessions_parser.add_argument("--endpoint", help="override the configured API Server URL")
    sessions_parser.add_argument("--api-key", help="override the configured API Server key")
    sessions_parser.add_argument("--config", type=Path, help="configuration file path")
    sessions_parser.add_argument("--theme", help="rofi theme path")
    sessions_parser.add_argument("--limit", type=int, default=10)
    prompt_parser = subparsers.add_parser("prompt", help="pick a session and send a prompt")
    prompt_parser.add_argument("--endpoint", help="override the configured API Server URL")
    prompt_parser.add_argument("--api-key", help="override the configured API Server key")
    prompt_parser.add_argument("--config", type=Path, help="configuration file path")
    prompt_parser.add_argument("--theme", help="rofi theme path")
    prompt_parser.add_argument("--limit", type=int, default=10)
    return parser


def _notify_desktop(title: str, body: str) -> None:
    try:
        subprocess.run(
            ["notify-send", "--app-name=Hermes", title, body],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def _hyprland_window_exists(window_class: str) -> bool:
    try:
        result = subprocess.run(
            ["hyprctl", "clients", "-j"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    try:
        clients = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False
    return any(client.get("class") == window_class for client in clients)


def _open_desktop(*, focus_only: bool, hud: bool = False) -> int:
    window_class = os.environ.get("HERMES_WAYBAR_WINDOW_CLASS", "Hermes")
    command_env = os.environ.get("HERMES_WAYBAR_DESKTOP_COMMAND")
    if focus_only or (not command_env and _hyprland_window_exists(window_class)):
        if _hyprland_window_exists(window_class):
            subprocess.run(
                ["hyprctl", "dispatch", "focuswindow", f"class:^{window_class}$"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if hud:
                subprocess.run(
                    ["hyprctl", "dispatch", "togglefloating", f"class:^{window_class}$"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return 0
        if focus_only:
            print(f"nenhuma janela com class {window_class}", file=sys.stderr)
            return 1
    command = command_env or "hermes desktop --skip-build"
    try:
        subprocess.Popen(shlex.split(command), start_new_session=True)
    except (OSError, ValueError) as exc:
        print(f"não foi possível abrir o Hermes Desktop: {exc}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "open":
        return _open_desktop(focus_only=False)
    if args.command == "hud":
        return _open_desktop(focus_only=False, hud=True)
    if args.command == "focus":
        return _open_desktop(focus_only=True)
    try:
        config = load_config(args.config)
    except ValueError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2
    endpoint = args.endpoint or config.endpoint
    api_key = args.api_key or config.api_key
    client = HermesApiClient(endpoint, api_key, config.timeout)
    if args.command == "status":
        print(client.status().to_waybar_json())
        return 0
    if args.command == "watch":
        if args.interval <= 0:
            print("interval must be greater than zero", file=sys.stderr)
            return 2
        try:
            return watch(client, args.state, args.interval, once=args.once)
        except Exception as exc:
            print(f"notification watch failed: {exc}", file=sys.stderr)
            return 1
    if args.command in {"sessions", "prompt"}:
        rows = client.visible_sessions(args.limit)
        if not rows:
            print("nenhuma sessão encontrada", file=sys.stderr)
            return 1
        entries = []
        for row in rows:
            title = str(row.get("title") or row.get("id") or "sessão").strip()
            model = str(row.get("model") or "").strip()
            entries.append(f"{title}" + (f" [{model}]" if model else ""))
        chosen = pick(entries, "Sessão", args.theme)
        if chosen is None:
            return 0
        index = entries.index(chosen)
        row = rows[index]
        session_id = str(row.get("id") or "")
        title = str(row.get("title") or session_id)
        if args.command == "sessions":
            print(f"sessão selecionada: {title} ({session_id})")
            return 0
        message = pick([], "Prompt", args.theme)
        if message is None:
            print("nenhum prompt fornecido", file=sys.stderr)
            return 1
        try:
            response = client.send_prompt(session_id, message)
        except Exception as exc:
            _notify_desktop("Hermes", f"falha ao enviar prompt: {exc}")
            print(f"falha ao enviar prompt: {exc}", file=sys.stderr)
            return 1
        text = str(response.get("final_response") or response.get("response") or "").strip()
        _notify_desktop("Hermes", text[:500] or "prompt enviado")
        print(text or "prompt enviado")
        return 0
    report = client.doctor()
    print(report.to_json() if args.json else report.to_text())
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
