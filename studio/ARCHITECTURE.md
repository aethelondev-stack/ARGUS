# Architecture Guide: ARGUS On-Device Vision Shield

## 1. Problem Statement: The Token Bleeding Bottleneck

Autonomous GUI agents (such as Claude Computer Use, GPT-4 Vision agents, or native OS automation agents) routinely inspect the user's screen during multi-step tasks. In standard workflows:
- Each screen capture transmits a 1920x1080 or 4K PNG across the internet.
- Each full-resolution screenshot consumes **2,000 to 2,500 tokens** in the multimodal LLM context.
- A 40-step game navigation, web workflow, or OS setting adjustment burns **80,000 to 100,000 tokens** in minutes.
- If the interface freezes or the agent mistargets an element, the agent enters an autonomous retry loop, consuming budget uncontrollably without making progress.

```text
STANDARD WORKFLOW (TOKEN BLEEDING):
[Screen Capture] ──► [2,000-2,500 Tokens] ──► [Cloud LLM ($$$)] ──► [Click] ──► (Repeat endlessly)

ARGUS SHIELDED WORKFLOW (LOCAL VISION):
[Screen Capture] ──► [Local Florence-2 GPU] ──► [pHash Circuit Breaker]
                            │
                            ▼
              [Compact Structured JSON] (<50 Tokens) ──► [Lead Agent]
```

---

## 2. The Solution: Dual-Layer Shielding

ARGUS decouples **raw pixel observation** from **high-level agent reasoning**:

1. **Local Vision Offloading (Florence-2):**
   - Microsoft's Florence-2-base model runs on the local NVIDIA GPU (RTX 2060 or higher).
   - Operates in FP16 precision, consuming only **~680 MB of VRAM**.
   - Zero raw display images leave the user's machine.
   - Extracts coordinates, detected cards, and focused widgets into a text note:
     `{"source": "desktop", "visible_windows": [...], "token_estimate": 45}`
   - **Maliyet ve Context tasarrufu: %97.5 azalma!**

2. **Perceptual Circuit Breaker (Emniyet Şalteri):**
   - After each action, the display's 64-bit difference hash (dHash) is computed.
   - If the screen fails to change for 3 consecutive actions, the circuit breaker triggers immediately, halting execution and preventing runaway loops.

---

## 3. Windows Session Isolation Bypass (`OpenDesktopW`)

Autonomous background agents on Windows frequently fail with `OSError: screen grab failed` because agent sub-processes run in an isolated non-interactive window station.

ARGUS resolves this via direct Win32 C-API integration:
```python
import ctypes
user32 = ctypes.windll.user32
hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)
```
This re-binds the agent worker thread directly to the interactive Windows `Default` desktop, granting access to active top-level windows without disrupting user focus or displacing windows.

---

## 4. Headless Android / BlueStacks Background Automation

When interacting with Android TV or BlueStacks emulators:
- Screen capture is piped via ADB standard stream: `adb exec-out screencap -p`.
- Touch actions are dispatched via `adb shell input tap x y`.
- D-Pad navigation steps (`DPAD_UP`, `DPAD_DOWN`, `DPAD_CENTER`) execute headless without stealing the user's mouse cursor.
- The user can continue working, coding, or browsing on the PC while the agent operates BlueStacks entirely in the background.
