---
name: argus
description: >-
  Universal On-Device Vision Shield & Token Guardian for Autonomous Coding Agents.
  Eliminates context window token bleeding by offloading GUI inspection, Windows
  desktop navigation, and Android emulator interaction to local vision models (Florence-2)
  and perceptual hashing circuit breakers.
---

# ARGUS: On-Device Vision Shield & Token Guardian

ARGUS is a modular, high-performance skill that protects AI coding agents (Antigravity, Cursor, Cline) from **multimodal context bloat** and **infinite UI retry loops**.

Instead of capturing and transmitting full-resolution 2,000–2,500 token screenshots to remote cloud LLMs for every click or step, ARGUS runs on-device computer vision (Microsoft Florence-2, ~680 MB VRAM) directly on the user's local GPU. It extracts active cards, focused elements, and bounding boxes, returning a compact (<50 tokens) structured JSON scene graph.

---

## 1. Core Operating Directives

> **Directive 1: Never Upload Raw Screenshots into Multimodal Context.**  
> Do NOT call raw image capture tools (`windows-desktop-control:screenshot`, `adb screencap`, or `view_file` on image paths) during routine GUI navigation. Always query ARGUS first.

> **Directive 2: Source Disambiguation.**  
> - When the user refers to their PC, computer screen, desktop, or Windows ("bilgisayarım / ekranım / masaüstüm"), pass `--source desktop`. Never substitute BlueStacks or ADB when the user requests their PC screen.
> - When the user refers to BlueStacks, Android, TvBox, or mobile games, pass `--source bluestacks`.

> **Directive 3: Loop Prevention & Circuit Breaker Respect.**  
> ARGUS continuously hashes screen frames using a 64-bit perceptual hash (dHash). If the display remains unchanged for 3 consecutive actions, ARGUS trips the circuit breaker (`CIRCUIT_BREAKER_TRIGGERED`).
> - **Max 2 Retries:** If local grounding fails or coordinates do not change the UI state, attempt at most 2 times. Never loop autonomously.
> - **No Automated Reset Loops:** Never call `--reset` or `smart_ui_reset()` in an autonomous loop to circumvent the breaker.
> - **Graceful Escalation:** After 2 failed attempts, HALT immediately, set status to `BLOCKED: LOCAL_GROUNDING_FAILED`, and ask the user for manual guidance.

---

## 2. Operational Modes & First-Run Setup

ARGUS supports three project-level modes configured in `.argus/config.json`:

1. **`auto` (Default & Recommended - Hybrid Mode):**
   - Engages on-device Florence-2 vision for all GUI tasks, loops, and background navigation (0 tokens).
   - Automatically recommends direct cloud vision only if explicitly instructed by the user or if local grounding fails after 2 attempts.
2. **`local` (Pure Local GPU Shield):**
   - Strictly enforces on-device vision. Never allows raw screen upload.
3. **`direct` (Direct Cloud Vision):**
   - Bypasses the local shield. Antigravity inspects displays directly using standard multimodal screenshot tools.

### Querying or Changing Modes:
```powershell
# Check status, device hardware, and active mode
python .agents/skills/argus/scripts/argus.py --status

# Query active mode
python .agents/skills/argus/scripts/argus.py --get-mode

# Configure mode
python .agents/skills/argus/scripts/argus.py --set-mode auto
```

### Initial Project Setup Prompt:
If `.argus/config.json` does not exist in a new project, present the user with these choices once:
```text
ARGUS (Local Vision Shield & Token Guardian) bu projede kullanılabilir.
Tercihiniz:
1. auto (Akıllı Hibrit - Önerilen: Yerel vizyon öncelikli, %97.5 token tasarrufu)
2. local (Sadece Yerel GPU - Sıfır bulut yüklemesi, tam gizlilik)
3. direct (Doğrudan Bulut - Standart ekran görüntüsü araçları)
```
Save the selection via `--set-mode` so subsequent sessions never prompt again.

---

## 3. CLI Command Reference

Execute commands via `run_command`:

### 1. Screen Observation (`--scan`):
```powershell
# Scan Windows desktop
python .agents/skills/argus/scripts/argus.py --scan --source desktop

# Scan Android / BlueStacks / TvBox
python .agents/skills/argus/scripts/argus.py --scan --source bluestacks

# Peek at desktop icons without displacing active application windows
python .agents/skills/argus/scripts/argus.py --scan --source desktop --peek
```

### 2. Desktop Items & Direct Launch:
```powershell
# List desktop files and shortcuts (0 tokens, reads directly from shell)
python .agents/skills/argus/scripts/argus.py --desktop-items

# Launch desktop app directly without moving mouse or touching windows
python .agents/skills/argus/scripts/argus.py --launch "Neon Clicker"
```

### 3. Click / Tap / D-Pad Actions (`--click`):
```powershell
# Mouse / Touch tap at coordinate (X, Y)
python .agents/skills/argus/scripts/argus.py --click 450 320 --method tap

# Android TV / TvBox remote control D-Pad sequence
python .agents/skills/argus/scripts/argus.py --click 0 0 --method dpad --dpad DPAD_RIGHT DPAD_RIGHT DPAD_CENTER
```

### 4. Evaluate Decision Engine (`--decide`):
```powershell
python .agents/skills/argus/scripts/argus.py --decide --source desktop --prompt "Click start button"
```

### 5. Reset Circuit Breaker (`--reset`):
```powershell
python .agents/skills/argus/scripts/argus.py --reset
```

---

## 4. Structured Output Format

When calling `--scan`, ARGUS emits clean JSON to `stdout`:

```json
{
  "source": "desktop",
  "screen_dimensions": [1920, 1080],
  "active_foreground_window": "Opera GX",
  "visible_windows_count": 6,
  "visible_windows": [
    {
      "title": "Opera GX",
      "bounds": [0, 0, 1920, 1040],
      "center": [960, 520]
    }
  ],
  "token_estimate": 45
}
```

If the display is frozen or unresponsive across 3 consecutive actions:
```json
{
  "status": "CIRCUIT_BREAKER_TRIGGERED",
  "error": "Display remained unchanged across 3 consecutive actions. Interface freeze detected.",
  "token_estimate": 25
}
```

---

## 5. Dual MCP Server Integration

If preferred, ARGUS can also run as an MCP server:
```powershell
python .agents/skills/argus/scripts/argus.py --server
```
Exposing tools: `smart_ui_scan`, `smart_ui_click`, `smart_ui_desktop_items`, and `smart_ui_reset`.
