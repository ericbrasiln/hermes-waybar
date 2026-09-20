from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

from .client import HermesApiClient
from .config import default_config_path, load_config
from .notifications import default_state_path, watch


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
    subparsers.add_parser("open", help="open Hermes Desktop")
    watch_parser = subparsers.add_parser("watch", help="watch session completion notifications")
    watch_parser.add_argument("--endpoint", help="override the configured API Server URL")
    watch_parser.add_argument("--api-key", help="override the configured API Server key")
    watch_parser.add_argument("--config", type=Path, help="configuration file path")
    watch_parser.add_argument("--interval", type=float, default=10.0)
    watch_parser.add_argument("--state", type=Path, default=default_state_path())
    watch_parser.add_argument("--once", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "open":
        command = os.environ.get("HERMES_WAYBAR_DESKTOP_COMMAND", "hermes desktop --skip-build")
        try:
            subprocess.Popen(shlex.split(command), start_new_session=True)
        except (OSError, ValueError) as exc:
            print(f"não foi possível abrir o Hermes Desktop: {exc}", file=sys.stderr)
            return 1
        return 0
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
    report = client.doctor()
    print(report.to_json() if args.json else report.to_text())
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
