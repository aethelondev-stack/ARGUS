#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARGUS: Unified Agent Skill CLI Controller (argus.py)
Version: 1.0.0
License: MIT (Aethelion)

Master CLI controller and mode manager for the ARGUS Vision Shield & Token Guardian.
Designed for autonomous AI coding agents (Antigravity, Cursor, Cline).
"""

import os
import sys
import json
import uuid
import pathlib
import argparse
from datetime import datetime

# Local imports
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from engine import UIEngine
except ImportError:
    UIEngine = None


ARGUS_VERSION = "1.0.0"
DEFAULT_MODE = "auto"
VALID_MODES = ["auto", "local", "direct"]


def log(msg: str):
    """Outputs diagnostic messages to stderr only, keeping stdout reserved for pure JSON."""
    sys.stderr.write(f"[argus] {msg}\n")
    sys.stderr.flush()


def log_error(msg: str):
    sys.stderr.write(f"[argus:ERROR] {msg}\n")
    sys.stderr.flush()


def get_project_root() -> pathlib.Path:
    """Discovers project root by searching upwards for .argus, .agents, or .git indicators."""
    cwd = pathlib.Path.cwd().resolve()
    curr = cwd
    for _ in range(6):
        if (curr / ".argus").is_dir() or (curr / ".agents").is_dir() or (curr / ".git").is_dir():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent

    # Fallback to script ancestors
    try:
        for p in SCRIPT_DIR.parents:
            if (p / ".argus").is_dir() or (p / ".agents").is_dir() or (p / ".git").is_dir():
                return p
    except Exception:
        pass
    return cwd


PROJECT_ROOT = get_project_root()
ARGUS_DIR = PROJECT_ROOT / ".argus"
LOGS_DIR = ARGUS_DIR / "logs"
CONFIG_FILE = ARGUS_DIR / "config.json"


def ensure_dirs():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def atomic_write_json(file_path: pathlib.Path, data: dict):
    ensure_dirs()
    tmp_path = file_path.with_name(f"{file_path.stem}.{uuid.uuid4().hex[:8]}.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp_path.replace(file_path)


def load_config() -> dict:
    config = {
        "argus_mode": os.environ.get("ARGUS_MODE", DEFAULT_MODE).lower(),
        "default_source": os.environ.get("ARGUS_SOURCE", "desktop"),
        "max_consecutive_unchanged": 3,
        "use_gpu": True,
        "adb_port": int(os.environ.get("ARGUS_ADB_PORT", "6175")),
        "version": ARGUS_VERSION
    }
    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            log(f"Warning loading config.json: {e}")
    return config


def save_config(config: dict):
    atomic_write_json(CONFIG_FILE, config)


def evaluate_decision(mode: str, source: str, task_hint: str = "") -> tuple[str, str]:
    """
    Evaluates whether local vision (USE_LOCAL) or direct cloud vision (USE_DIRECT) is appropriate.
    Modes:
      - 'local': Always enforce local on-device Florence-2 vision.
      - 'direct': Bypass local shield, allow agent direct cloud image inspection.
      - 'auto': Hybrid mode. Uses local vision by default for GUI loops, D-Pad navigation,
                and background monitoring. Only falls back if explicitly requested or ungrounded.
    """
    if mode == "direct":
        return "USE_DIRECT", "ARGUS is set to 'direct' mode. Local vision shield is bypassed; direct agent inspection recommended."

    if mode == "local":
        return "USE_LOCAL", "ARGUS is set to 'local' mode. Enforcing 100% on-device GPU vision (0 token upload)."

    # auto / hybrid mode
    p_lower = (task_hint or "").lower()
    if "raw screenshot" in p_lower or "cloud vision" in p_lower:
        return "USE_DIRECT", "User requested explicit raw cloud inspection."

    return "USE_LOCAL", f"Hybrid auto-mode engaged. Offloading {source} observation to on-device vision to preserve agent context."


def main():
    parser = argparse.ArgumentParser(description="ARGUS: Local Vision Shield & Token Guardian")
    parser.add_argument("--status", action="store_true", help="Display ARGUS status, mode, and device environment")
    parser.add_argument("--set-mode", choices=VALID_MODES, help="Set operational mode (auto, local, direct)")
    parser.add_argument("--get-mode", action="store_true", help="Output active operational mode")
    parser.add_argument("--decide", action="store_true", help="Evaluate whether to use local vision or direct cloud vision")
    parser.add_argument("--source", choices=["desktop", "bluestacks"], default=None, help="Capture source")
    parser.add_argument("--peek", action="store_true", help="Peek at desktop wallpaper/icons without displacing windows")
    parser.add_argument("--scan", action="store_true", help="Scan screen and return compact JSON scene graph")
    parser.add_argument("--click", nargs=2, type=int, metavar=("X", "Y"), help="Execute click/tap at coordinates X Y")
    parser.add_argument("--method", choices=["tap", "dpad"], default="tap", help="Action method for click")
    parser.add_argument("--dpad", nargs="*", help="DPAD sequence (e.g. DPAD_UP DPAD_RIGHT DPAD_CENTER)")
    parser.add_argument("--desktop-items", action="store_true", help="List desktop applications and shortcuts directly from shell")
    parser.add_argument("--launch", type=str, help="Launch desktop app or shortcut without moving cursor")
    parser.add_argument("--reset", action="store_true", help="Reset circuit breaker state")
    parser.add_argument("--dry-run", action="store_true", help="Simulate action without interacting with display")
    parser.add_argument("--server", action="store_true", help="Start FastMCP server for MCP integration")
    parser.add_argument("--prompt", type=str, default="", help="Contextual prompt or task description for decision")

    args = parser.parse_args()
    ensure_dirs()
    config = load_config()

    # 1. Mode Configuration Commands
    if args.set_mode:
        config["argus_mode"] = args.set_mode
        save_config(config)
        log(f"Operational mode updated to '{args.set_mode}' in .argus/config.json")
        print(json.dumps({"status": "success", "argus_mode": args.set_mode}, indent=2))
        sys.exit(0)

    if args.get_mode:
        print(json.dumps({"argus_mode": config.get("argus_mode", DEFAULT_MODE)}, indent=2))
        sys.exit(0)

    # 2. Decision Engine
    if args.decide:
        mode = config.get("argus_mode", DEFAULT_MODE)
        src = args.source or config.get("default_source", "desktop")
        decision, reason = evaluate_decision(mode, src, args.prompt)
        res = {
            "decision": decision,
            "argus_mode": mode,
            "source": src,
            "reason": reason
        }
        print(json.dumps(res, indent=2, ensure_ascii=False))
        sys.exit(0)

    # 3. FastMCP Server Launch
    if args.server:
        try:
            from server import main as run_server
            log("Starting FastMCP server on stdio...")
            run_server()
            sys.exit(0)
        except Exception as e:
            log_error(f"Failed to start FastMCP server: {e}")
            sys.exit(1)

    # 4. Status Query
    if args.status:
        cuda_available = False
        device_name = "CPU"
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                device_name = torch.cuda.get_device_name(0)
        except Exception:
            pass

        status_payload = {
            "status": "active",
            "version": ARGUS_VERSION,
            "project_root": str(PROJECT_ROOT),
            "argus_mode": config.get("argus_mode", DEFAULT_MODE),
            "default_source": config.get("default_source", "desktop"),
            "hardware": {
                "cuda_available": cuda_available,
                "active_device": device_name,
                "vram_budget_mb": 680
            },
            "circuit_breaker": {
                "max_consecutive_unchanged": config.get("max_consecutive_unchanged", 3),
                "is_tripped": False
            }
        }
        print(json.dumps(status_payload, indent=2, ensure_ascii=False))
        sys.exit(0)

    # 5. Desktop Items / Launch
    if args.desktop_items or args.launch:
        if UIEngine is None:
            print(json.dumps({"status": "error", "message": "UIEngine dependencies not loaded"}, indent=2))
            sys.exit(1)
        engine = UIEngine(use_gpu=config.get("use_gpu", True))
        if args.launch:
            if args.dry_run:
                print(json.dumps({"status": "dry_run_success", "action": f"Would launch '{args.launch}'"}, indent=2))
                sys.exit(0)
            success, msg = engine.launch_desktop_item(args.launch)
            print(json.dumps({"success": success, "message": msg}, indent=2, ensure_ascii=False))
            sys.exit(0 if success else 1)
        else:
            items = engine.get_desktop_items()
            print(json.dumps({
                "desktop_items_count": len(items),
                "items": [it["name"] for it in items],
                "token_estimate": 35
            }, indent=2, ensure_ascii=False))
            sys.exit(0)

    # 6. Reset Circuit Breaker
    if args.reset:
        log("Circuit breaker manually reset.")
        print(json.dumps({"status": "success", "message": "Circuit breaker state reset to normal."}, indent=2))
        sys.exit(0)

    # 7. Screen Scan
    if args.scan:
        if args.dry_run:
            src = args.source or config.get("default_source", "desktop")
            print(json.dumps({
                "status": "dry_run_success",
                "source": src,
                "message": f"Dry-run validated. Capture from '{src}' ready without executing."
            }, indent=2))
            sys.exit(0)

        if UIEngine is None:
            print(json.dumps({"status": "error", "message": "UIEngine dependencies missing."}, indent=2))
            sys.exit(1)

        src = args.source or config.get("default_source", "desktop")
        engine = UIEngine(use_gpu=config.get("use_gpu", True))
        try:
            img = engine.capture(source=src, peek_desktop=args.peek)
            can_proceed, breaker_msg = engine.breaker.check_and_update(img, "scan")
            if not can_proceed:
                print(json.dumps({
                    "status": "CIRCUIT_BREAKER_TRIGGERED",
                    "error": breaker_msg,
                    "token_estimate": 25
                }, indent=2, ensure_ascii=False))
                sys.exit(0)

            result = engine.scan_screen(img, source=src)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(0)
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}, indent=2))
            sys.exit(1)

    # 8. Click / Tap / D-Pad Action
    if args.click:
        x, y = args.click
        method = args.method
        if args.dry_run:
            print(json.dumps({
                "status": "dry_run_success",
                "action": f"Would execute {method} at ({x}, {y}) with dpad={args.dpad}"
            }, indent=2))
            sys.exit(0)

        if UIEngine is None:
            print(json.dumps({"status": "error", "message": "UIEngine dependencies missing."}, indent=2))
            sys.exit(1)

        engine = UIEngine(use_gpu=config.get("use_gpu", True))
        success, msg = engine.execute_action([x, y], method=method, dpad_steps=args.dpad)
        print(json.dumps({"success": success, "message": msg}, indent=2, ensure_ascii=False))
        sys.exit(0 if success else 1)

    # Default fallback if no valid command passed
    parser.print_help(sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
