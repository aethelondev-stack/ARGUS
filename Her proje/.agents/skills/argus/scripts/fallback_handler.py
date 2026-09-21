#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARGUS: Circuit Breaker & Fallback Handler (fallback_handler.py)
Version: 1.0.0
License: MIT (Aethelion)

Provides Perceptual Hash (dHash) freeze detection, circuit breaker loop prevention,
bounding box validation, and ADB UI hierarchy extraction.
"""

import re
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image


class CircuitBreaker:
    """
    Perceptual Hash (pHash) based circuit breaker.
    Tracks visual screen state across actions and halts execution
    if the display remains unchanged for N consecutive attempts.
    """
    def __init__(self, max_consecutive_unchanged: int = 3):
        self.max_consecutive_unchanged = max_consecutive_unchanged
        self.consecutive_unchanged = 0
        self.last_hash = None
        self.action_history = []
        self.is_tripped = False

    def compute_phash(self, image_pil: Image.Image) -> str:
        """Computes a 64-bit difference hash (dHash) from a PIL Image."""
        resized = image_pil.convert('L').resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(resized.getdata())
        diff = []
        for row in range(8):
            for col in range(8):
                pixel_left = pixels[row * 9 + col]
                pixel_right = pixels[row * 9 + col + 1]
                diff.append(pixel_left > pixel_right)
        decimal_value = 0
        hex_string = []
        for index, value in enumerate(diff):
            if value:
                decimal_value += 2 ** (index % 4)
            if index % 4 == 3:
                hex_string.append(hex(decimal_value)[2:])
                decimal_value = 0
        return ''.join(hex_string)

    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """Computes Hamming distance between two hex hashes."""
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 999
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    def check_and_update(self, image_pil: Image.Image, action_name: str) -> tuple[bool, str]:
        """
        Updates circuit breaker state against current screen frame.
        Returns: (can_proceed: bool, message: str)
        """
        current_hash = self.compute_phash(image_pil)

        if self.last_hash is not None:
            dist = self.hamming_distance(self.last_hash, current_hash)
            # If distance <= 2, the screen hasn't perceptibly changed
            if dist <= 2:
                self.consecutive_unchanged += 1
            else:
                self.consecutive_unchanged = 0
                self.is_tripped = False
        else:
            self.consecutive_unchanged = 0

        self.last_hash = current_hash
        self.action_history.append((action_name, current_hash))

        if self.consecutive_unchanged >= self.max_consecutive_unchanged:
            self.is_tripped = True
            return False, (
                f"CIRCUIT_BREAKER_TRIGGERED: Display remained unchanged across {self.consecutive_unchanged} "
                f"consecutive actions. Interface freeze detected. Halted to prevent token burnout."
            )

        return True, "OK"

    def reset(self):
        """Resets breaker state to normal."""
        self.consecutive_unchanged = 0
        self.last_hash = None
        self.is_tripped = False


def validate_bounding_box(box: list[int], screen_width: int, screen_height: int, score: float = 1.0, min_score: float = 0.60) -> tuple[bool, str]:
    """
    Validates that a bounding box is geometrically plausible.
    box format: [x1, y1, x2, y2]
    """
    if score < min_score:
        return False, f"Confidence score below minimum threshold ({score:.2f} < {min_score})"

    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1

    if width <= 5 or height <= 5:
        return False, "Bounding box too small (probable noise or artifact)"

    screen_area = screen_width * screen_height
    box_area = width * height

    # If box covers more than 35% of total screen, it is a container/background
    if box_area > (screen_area * 0.35):
        return False, f"Box covers {(box_area / screen_area) * 100:.1f}% of screen; classified as container/background"

    return True, "Valid"


def fallback_adb_dump() -> list[dict]:
    """
    Pulls Android UI view hierarchy via ADB uiautomator without raw image transfer.
    Returns structured list of elements with text and coordinate bounds.
    """
    try:
        cmd = ["adb", "exec-out", "uiautomator", "dump", "/dev/tty"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode != 0 or not result.stdout.strip():
            # Fallback to file dump on SDCard
            subprocess.run(["adb", "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], timeout=5)
            xml_res = subprocess.run(["adb", "exec-out", "cat", "/sdcard/window_dump.xml"], capture_output=True, text=True, timeout=5)
            xml_data = xml_res.stdout
        else:
            xml_data = result.stdout

        elements = []
        root = ET.fromstring(xml_data)
        for node in root.iter('node'):
            text = node.attrib.get('text', '') or node.attrib.get('content-desc', '')
            bounds = node.attrib.get('bounds', '')  # Format: [x1,y1][x2,y2]
            if text and bounds:
                match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                if match:
                    x1, y1, x2, y2 = map(int, match.groups())
                    elements.append({
                        "text": text,
                        "center": [(x1 + x2) // 2, (y1 + y2) // 2],
                        "box": [x1, y1, x2, y2]
                    })
        return elements
    except Exception:
        return []
