#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARGUS: Local Vision Engine (engine.py)
Version: 1.0.0
License: MIT (Aethelion)

Provides on-device vision inference (Florence-2 via PyTorch CUDA),
Windows desktop interactive session isolation bypass, ADB headless capture,
and coordinate scaling for high-efficiency GUI agents.
"""

import os
import sys
import subprocess
import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

# Local imports
try:
    from .fallback_handler import CircuitBreaker, validate_bounding_box, fallback_adb_dump
except ImportError:
    from fallback_handler import CircuitBreaker, validate_bounding_box, fallback_adb_dump


class UIEngine:
    """
    On-device vision and GUI interaction engine.
    Offloads visual grounding to local Florence-2 (approx 680 MB VRAM)
    and formats findings into compact structured JSON.
    """
    def __init__(self, model_name: str = "microsoft/Florence-2-base", use_gpu: bool = True):
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.breaker = CircuitBreaker(max_consecutive_unchanged=3)
        self.model = None
        self.processor = None
        self._model_loaded = False
        self.device = "cpu"

    def lazy_load_florence(self):
        """Loads Florence-2 on demand with FP16 precision on CUDA if available."""
        if self._model_loaded:
            return
        try:
            import torch
            from transformers import AutoProcessor, AutoModelForCausalLM

            device = "cuda" if (self.use_gpu and torch.cuda.is_available()) else "cpu"
            sys.stderr.write(f"[argus] Initializing Florence-2 on device: {device}...\n")
            sys.stderr.flush()

            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                dtype=torch.float16 if device == "cuda" else torch.float32
            ).to(device)
            self.device = device
            self._model_loaded = True
            sys.stderr.write(f"[argus] Florence-2 ready on {device} (VRAM footprint ~680MB).\n")
            sys.stderr.flush()
        except Exception as e:
            sys.stderr.write(f"[argus:WARNING] Florence-2 initialization deferred: {e}. Active fallback: CV/OCR mode.\n")
            sys.stderr.flush()
            self._model_loaded = False

    def query_florence(self, image_pil: Image.Image, prompt: str = "<OD>", max_tokens: int = 100) -> str | None:
        """Runs inference with Florence-2 on local hardware without sending pixels to cloud."""
        self.lazy_load_florence()
        if not self._model_loaded:
            return None
        import torch
        resized = image_pil.resize((768, 768))
        inputs = self.processor(
            text=prompt,
            images=resized,
            return_tensors="pt"
        ).to(self.device, torch.float16 if self.device == "cuda" else torch.float32)

        with torch.inference_mode():
            generated_ids = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=max_tokens,
                use_cache=False
            )
        text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

        if self.device == "cuda":
            torch.cuda.empty_cache()
        return text

    def get_desktop_items(self) -> list[dict]:
        """
        Reads user and public desktop shortcuts/files directly from Windows Shell.
        Executes without capturing screenshots or disrupting active windows.
        """
        user_dt = os.path.expanduser('~/Desktop')
        pub_dt = r'C:\Users\Public\Desktop'
        items = []

        for folder in [user_dt, pub_dt]:
            if os.path.exists(folder):
                try:
                    for fname in os.listdir(folder):
                        fpath = os.path.join(folder, fname)
                        is_link = fname.lower().endswith(('.lnk', '.url'))
                        items.append({
                            "name": fname.replace('.lnk', '').replace('.url', ''),
                            "filename": fname,
                            "path": fpath,
                            "type": "shortcut" if is_link else "file"
                        })
                except Exception:
                    pass
        return items

    def launch_desktop_item(self, item_name: str) -> tuple[bool, str]:
        """Launches a desktop shortcut or file directly via OS shell."""
        items = self.get_desktop_items()
        matches = [it for it in items if item_name.lower() in it['name'].lower()]
        if matches:
            target = matches[0]['path']
            try:
                os.startfile(target)
                return True, f"Launched: {matches[0]['name']}"
            except Exception as e:
                return False, f"Failed to launch '{matches[0]['name']}': {e}"
        return False, f"Desktop item matching '{item_name}' not found."

    @staticmethod
    def switch_to_user_desktop() -> bool:
        """
        Switches calling thread to interactive Windows 'Default' desktop station.
        Resolves the 'OSError: screen grab failed' error in headless/sub-desktop agent sessions.
        """
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
                return True
        except Exception:
            pass
        return False

    def get_visible_desktop_windows(self) -> list[dict]:
        """Enumerates visible top-level application windows on interactive desktop."""
        self.switch_to_user_desktop()
        try:
            import ctypes
            user32 = ctypes.windll.user32
            windows = []

            def enum_cb(hwnd, lparam):
                if user32.IsWindowVisible(hwnd):
                    buf = ctypes.create_unicode_buffer(256)
                    user32.GetWindowTextW(hwnd, buf, 256)
                    title = buf.value
                    if title and title not in ['Program Manager', 'Default IME', 'MSCTFIME UI']:
                        rect = (ctypes.c_long * 4)()
                        user32.GetWindowRect(hwnd, ctypes.byref(rect))
                        w = rect[2] - rect[0]
                        h = rect[3] - rect[1]
                        if w > 50 and h > 50:
                            windows.append({
                                "title": title,
                                "bounds": [rect[0], rect[1], rect[2], rect[3]],
                                "center": [(rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2]
                            })
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if hdesk:
                user32.EnumDesktopWindows(hdesk, WNDENUMPROC(enum_cb), 0)
            return windows
        except Exception:
            return []

    def peek_desktop(self, restore_after: bool = True) -> Image.Image:
        """
        Minimizes windows momentarily (Win+D) to capture the base desktop,
        then restores open windows immediately so user workflow remains uninterrupted.
        """
        import time
        self.switch_to_user_desktop()
        if not pyautogui:
            return self.capture(source="desktop")

        pyautogui.hotkey('win', 'd')
        time.sleep(0.12)
        img = pyautogui.screenshot().convert('RGB')
        if restore_after:
            pyautogui.hotkey('win', 'd')
        return img

    def capture(self, source: str = "desktop", file_path: str = None, peek_desktop: bool = False) -> Image.Image:
        """
        Captures screen frame from:
        - 'desktop': Windows PC screen
        - 'bluestacks': Android emulator / device via ADB
        - Local file path if specified
        """
        if file_path and os.path.exists(file_path):
            return Image.open(file_path).convert('RGB')

        if source == "bluestacks":
            try:
                cmd = ["adb", "exec-out", "screencap", "-p"]
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode == 0 and len(result.stdout) > 1000:
                    import io
                    return Image.open(io.BytesIO(result.stdout)).convert('RGB')
            except Exception as e:
                sys.stderr.write(f"[argus] ADB capture failed ({e}). Falling back to desktop capture.\n")
                sys.stderr.flush()

        # Desktop capture
        self.switch_to_user_desktop()
        if peek_desktop:
            return self.peek_desktop(restore_after=True)

        if pyautogui:
            try:
                return pyautogui.screenshot().convert('RGB')
            except Exception:
                self.switch_to_user_desktop()
                return pyautogui.screenshot().convert('RGB')

        raise RuntimeError("No screenshot capture method available on this environment.")

    def detect_cyan_focus(self, image_pil: Image.Image) -> list[int] | None:
        """
        Detects focused cards in Android TV / TvBox UIs (Cyan / Bright Blue border).
        Returns: [x1, y1, x2, y2] or None
        """
        if cv2 is None:
            return None
        img_np = np.array(image_pil)
        r = img_np[:, :, 0]
        g = img_np[:, :, 1]
        b = img_np[:, :, 2]

        cyan_mask = ((b > 140) & (g > 140) & (r < 110)).astype(np.uint8) * 255
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cyan_mask)

        lines = []
        for i in range(1, num_labels):
            x, y, w, h, area = stats[i]
            if h > 120 and area > 100:
                lines.append((x, y, w, h))

        if len(lines) >= 2:
            lines.sort(key=lambda l: l[0])
            left_line = lines[0]
            right_line = lines[-1]
            x1 = left_line[0]
            y1 = min(left_line[1], right_line[1])
            x2 = right_line[0] + right_line[2]
            y2 = max(left_line[1] + left_line[3], right_line[1] + right_line[3])
            return [int(x1), int(y1), int(x2), int(y2)]
        elif len(lines) == 1:
            x, y, w, h = lines[0]
            est_w = int(h * 0.7)
            return [int(x), int(y), int(x + est_w), int(y + h)]

        return None

    def detect_card_grid(self, image_pil: Image.Image) -> list[dict]:
        """Detects UI cards in Android TV / mobile layouts using edge and contour analysis."""
        if cv2 is None:
            return []
        img_np = np.array(image_pil)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        screen_area = img_np.shape[0] * img_np.shape[1]

        cards = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            aspect = float(w) / max(1, h)
            if 0.5 <= aspect <= 1.1 and (screen_area * 0.015 < area < screen_area * 0.25):
                center = [x + w // 2, y + h // 2]
                cards.append({
                    "box": [x, y, x + w, y + h],
                    "center": center
                })

        cards.sort(key=lambda c: (c['center'][1] // 100, c['center'][0]))
        return cards

    def calculate_dpad_steps(self, from_center: list[int], to_center: list[int], row_height_est: int = 400, col_width_est: int = 220) -> list[str]:
        """Calculates remote DPAD navigation steps (UP, DOWN, LEFT, RIGHT) from active focus to target."""
        dx = to_center[0] - from_center[0]
        dy = to_center[1] - from_center[1]

        steps = []
        row_diff = round(dy / max(1, row_height_est))
        if row_diff > 0:
            steps.extend(["DPAD_DOWN"] * row_diff)
        elif row_diff < 0:
            steps.extend(["DPAD_UP"] * abs(row_diff))

        col_diff = round(dx / max(1, col_width_est))
        if col_diff > 0:
            steps.extend(["DPAD_RIGHT"] * col_diff)
        elif col_diff < 0:
            steps.extend(["DPAD_LEFT"] * abs(col_diff))

        steps.append("DPAD_CENTER")
        return steps

    def scan_screen(self, image_pil: Image.Image, source: str = "desktop") -> dict:
        """
        Deconstructs screen into minimal structured JSON for either
        Windows Desktop or Android BlueStacks / TvBox.
        """
        width, height = image_pil.size

        if source == "desktop":
            windows = self.get_visible_desktop_windows()
            active_title = ""
            try:
                import ctypes
                user32 = ctypes.windll.user32
                hwnd = user32.GetForegroundWindow()
                buf = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, buf, 256)
                active_title = buf.value
            except Exception:
                pass

            return {
                "source": "desktop",
                "screen_dimensions": [width, height],
                "active_foreground_window": active_title,
                "visible_windows_count": len(windows),
                "visible_windows": windows[:12],
                "token_estimate": 45
            }

        # BlueStacks / Android TV
        focus_box = self.detect_cyan_focus(image_pil)
        cards = self.detect_card_grid(image_pil)

        active_focus = None
        if focus_box:
            fc_x = (focus_box[0] + focus_box[2]) // 2
            fc_y = (focus_box[1] + focus_box[3]) // 2
            active_focus = {
                "box": focus_box,
                "center": [fc_x, fc_y],
                "status": "Cyan Highlight Verified"
            }

        return {
            "source": "bluestacks",
            "screen_dimensions": [width, height],
            "active_focus": active_focus,
            "detected_cards_count": len(cards),
            "cards": cards[:12],
            "token_estimate": 45
        }

    def get_device_resolution(self) -> tuple[int, int]:
        """Queries physical display resolution from Android via ADB."""
        try:
            res = subprocess.run(["adb", "shell", "wm", "size"], capture_output=True, text=True, timeout=2)
            lines = res.stdout.strip().split('\n')
            for line in reversed(lines):
                if ":" in line:
                    parts = line.split(":")[-1].strip().split("x")
                    if len(parts) == 2:
                        return int(parts[0]), int(parts[1])
        except Exception:
            pass
        return 1920, 1080

    def scale_coords(self, coords: list[int], src_size: tuple[int, int], target_size: tuple[int, int]) -> list[int]:
        """Scales coordinates from captured frame resolution to target device native resolution."""
        src_w, src_h = src_size
        target_w, target_h = target_size
        scale_x = target_w / max(1, src_w)
        scale_y = target_h / max(1, src_h)

        if len(coords) == 2:
            return [int(coords[0] * scale_x), int(coords[1] * scale_y)]
        elif len(coords) == 4:
            return [
                int(coords[0] * scale_x), int(coords[1] * scale_y),
                int(coords[2] * scale_x), int(coords[3] * scale_y)
            ]
        return coords

    def execute_action(self, target_coords: list[int], method: str = "tap", dpad_steps: list[str] = None, image_size: tuple[int, int] = None) -> tuple[bool, str]:
        """Executes touch tap, mouse click, or D-Pad action with resolution auto-scaling."""
        if method == "tap":
            x, y = target_coords
            if image_size:
                dev_w, dev_h = self.get_device_resolution()
                if image_size != (dev_w, dev_h):
                    x, y = self.scale_coords([x, y], image_size, (dev_w, dev_h))

            # Attempt ADB first
            cmd = ["adb", "shell", "input", "tap", str(x), str(y)]
            try:
                res = subprocess.run(cmd, capture_output=True, timeout=3)
                if res.returncode == 0:
                    return True, f"Tapped via ADB at ({x}, {y})"
            except Exception:
                pass

            # Desktop fallback via pyautogui
            if pyautogui:
                self.switch_to_user_desktop()
                pyautogui.click(x, y)
                return True, f"Desktop clicked at ({x}, {y})"

            return False, "No execution backend (ADB or pyautogui) responded."

        elif method == "dpad" and dpad_steps:
            key_codes = {
                "DPAD_UP": "19",
                "DPAD_DOWN": "20",
                "DPAD_LEFT": "21",
                "DPAD_RIGHT": "22",
                "DPAD_CENTER": "23"
            }
            for step in dpad_steps:
                code = key_codes.get(step, "23")
                subprocess.run(["adb", "shell", "input", "keyevent", code], timeout=2)
            return True, f"Executed D-Pad sequence: {' -> '.join(dpad_steps)}"

        return False, f"Unknown action method: '{method}'"
