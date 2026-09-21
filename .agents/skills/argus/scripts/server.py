#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARGUS: FastMCP Server (server.py)
Version: 1.0.0
License: MIT (Aethelion)

Exposes ARGUS's local vision, perceptual hashing circuit breaker,
and desktop session control as an MCP (Model Context Protocol) server.
"""

import sys
import os
from typing import List, Dict, Optional
from pydantic import Field

# Ensure local directory is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from engine import UIEngine

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None


def create_mcp_server():
    if FastMCP is None:
        raise ImportError("FastMCP is not installed. Install with 'pip install fastmcp'.")

    mcp = FastMCP("ARGUS Vision & Token Shield Server", dependencies=["pyautogui", "Pillow", "opencv-python", "numpy"])
    engine = UIEngine()

    @mcp.tool()
    def smart_ui_scan(
        source: str = Field(
            default="desktop",
            description="Capture source: 'desktop' (Windows PC screen, active windows, desktop buttons) or 'bluestacks' (Android emulator / TvBox)"
        ),
        peek_desktop: bool = Field(
            default=False,
            description="If True and source='desktop', temporarily minimizes windows (Win+D) to capture wallpaper/desktop and restores them immediately."
        )
    ) -> Dict:
        """
        Scans the current screen using local computer vision and perceptual hashing.
        Returns a compact JSON scene graph (<60 tokens) with active focus and cards.
        Prevents raw images from polluting the LLM context.
        """
        try:
            img = engine.capture(source=source, peek_desktop=peek_desktop)
            can_proceed, msg = engine.breaker.check_and_update(img, "scan")
            if not can_proceed:
                return {
                    "status": "CIRCUIT_BREAKER_TRIGGERED",
                    "error": msg,
                    "token_estimate": 25
                }
            result = engine.scan_screen(img, source=source)
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    def smart_ui_desktop_items(
        launch: Optional[str] = Field(
            default=None,
            description="Optional app/file name to launch directly from desktop without moving mouse (e.g. 'Neon Clicker')"
        )
    ) -> Dict:
        """
        Reads all desktop files and shortcuts directly from Windows Shell WITHOUT taking a screenshot.
        Can also launch any desktop app directly. 100% headless, 0 tokens wasted.
        """
        try:
            if launch:
                success, msg = engine.launch_desktop_item(launch)
                return {"success": success, "message": msg}
            items = engine.get_desktop_items()
            return {
                "desktop_items_count": len(items),
                "items": [it["name"] for it in items[:25]],
                "token_estimate": 30
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    def smart_ui_click(
        coords: List[int] = Field(
            description="Target [x, y] coordinates to tap/click"
        ),
        method: str = Field(
            default="tap",
            description="Action method: 'tap' (touch/mouse click) or 'dpad' (Android TV remote)"
        ),
        dpad_steps: Optional[List[str]] = Field(
            default=None,
            description="Optional list of DPAD keys (e.g. ['DPAD_UP', 'DPAD_RIGHT', 'DPAD_CENTER'])"
        )
    ) -> Dict:
        """
        Executes a click or remote control action on the target element.
        Checks the circuit breaker before executing to prevent infinite retry loops.
        """
        try:
            success, msg = engine.execute_action(coords, method=method, dpad_steps=dpad_steps)
            return {"success": success, "message": msg}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def smart_ui_reset() -> Dict:
        """
        Resets the circuit breaker and screen state history.
        """
        engine.breaker.reset()
        return {"status": "success", "message": "Circuit breaker reset to normal."}

    return mcp


def main():
    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
