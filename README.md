# ARGUS: On-Device Vision Shield & Token Guardian

> **High-Performance, On-Device Vision Middleware for Autonomous AI Coding Agents (Google Antigravity, Cursor, Cline). Slashes Multimodal Token Bleeding by 97.5% and Eliminates Infinite Retry Loops via Perceptual Circuit Breakers.**

---

## 📑 Table of Contents

- [The Crisis: Multimodal Token Bleeding](#-the-crisis-multimodal-token-bleeding)
- [The Solution: ARGUS Shield](#-the-solution-argus-shield)
- [⚡ Quick Start](#-quick-start)
- [🤖 1-Prompt Setup with an AI Coding Agent](#-1-prompt-setup-with-an-ai-coding-agent)
- [🤖 For AI Coding Agents](#-for-ai-coding-agents)
- [⚙️ Operational Modes](#-operational-modes)
- [🏗️ Architectural Highlights](#-architectural-highlights)
  - [1. Low-VRAM On-Device Vision (Florence-2)](#1-low-vram-on-device-vision-florence-2)
  - [2. Perceptual Hash Circuit Breaker (Emniyet Şalteri)](#2-perceptual-hash-circuit-breaker-emniyet-şalteri)
  - [3. Windows Desktop Session Isolation Bypass](#3-windows-desktop-session-isolation-bypass)
  - [4. Silent Headless Android & BlueStacks Automation](#4-silent-headless-android--bluestacks-automation)
- [🗺️ Repository & Documentation Map](#-repository--documentation-map)
- [📄 License & Attribution](#-license--attribution)

---

## 🚨 The Crisis: Multimodal Token Bleeding

When state-of-the-art AI coding agents interact with desktop environments, browsers, or mobile emulators, they routinely capture and upload full-screen screenshots:

1. **Catastrophic Token Bleed:**  
   Every full-resolution image sent to remote multimodal LLMs burns **2,000 to 2,500 tokens** ($$$/credits). A 40-step automation task incinerates **100,000 tokens** within minutes.
2. **The Infinite Freeze Trap:**  
   If an application hangs, crashes, or a button fails to register, the agent remains blind to the freeze. It re-clicks and re-captures endlessly, burning developer credits until manually aborted.

---

## 🛡️ The Solution: ARGUS Shield

ARGUS sits locally between your operating system and your AI coding agent as an intelligent visual shield:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          ARGUS SHIELD ENGINE                           │
│                                                                        │
│  [Windows Desktop / BlueStacks]                                        │
│          │                                                             │
│          ▼                                                             │
│  [Local Florence-2 Model (CUDA RTX ~680MB)]                            │
│          │                                                             │
│          ├── Extracts Focused Cards & Coordinates                      │
│          ├── pHash Circuit Breaker (Halts after 3 static frames)       │
│          └── Bypasses Windows Desktop Isolation (OpenDesktopW)         │
│          │                                                             │
│          ▼                                                             │
│  [Structured JSON Scene Graph] (<50 Tokens) ──► [Lead AI Agent]       │
└────────────────────────────────────────────────────────────────────────┘
```

- **97.5% Token Preservation:** Replaces 2,000+ token raw images with high-density ~40 token JSON scene graphs.
- **100% On-Device Privacy:** Zero pixels leave your hardware. All vision embeddings run locally on your GPU.
- **Automated Safety Breaker:** Trips immediately if the screen fails to change across 3 consecutive actions.
- **Non-Disruptive Background Operation:** Controls Android emulators via ADB without stealing your mouse cursor or closing windows.

---

## ⚡ Quick Start

Get up and running in under 2 minutes:

1. **Copy the Installation Payload:**  
   Copy `.agents/skills/argus/` and `.argus/config.json.example` into your target repository root. *(See [INSTALL.md](INSTALL.md) for full canonical rules).*
2. **Merge `.gitignore` Rules:**  
   Append ARGUS runtime ignore rules to your project's `.gitignore`.
3. **Install Dependencies:**
   ```powershell
   pip install -r .agents/skills/argus/requirements.txt
   ```
4. **Verify Hardware & Status:**
   ```powershell
   python .agents/skills/argus/scripts/argus.py --status
   ```
5. **Run a Dry-Run Screen Scan:**
   ```powershell
   python .agents/skills/argus/scripts/argus.py --scan --source desktop --dry-run
   ```

---

## 🤖 1-Prompt Setup with an AI Coding Agent

If you are using Google Antigravity, Cursor, or Cline, paste this prompt into your conversation once:

```text
Install and verify ARGUS for this project.

First, discover the ARGUS skill (.agents/skills/argus) and inspect project configuration.

If my ARGUS mode preference is not yet saved in .argus/config.json, present me with these choices once:
1. auto (Recommended - Hybrid on-device vision, 97.5% token preservation)
2. local (Pure local GPU Florence-2 - Zero cloud upload)
3. direct (Direct cloud vision / Standard screenshots)

If my preference is already saved, do not ask again.
Verify that the installation and hardware status are functional before executing GUI actions.
```

---

## 🤖 For AI Coding Agents

When operating in an ARGUS-equipped repository:
1. **Never Call Raw Screenshot Tools:** Do not invoke `windows-desktop-control:screenshot` or `view_file` on display images. Always use `argus.py --scan` or `smart_ui_scan`.
2. **Source Disambiguation:**
   - PC / Desktop requests ("ekranım / masaüstüm") $\rightarrow$ `--source desktop`.
   - Android / Game / BlueStacks requests $\rightarrow$ `--source bluestacks`.
3. **Circuit Breaker Discipline:** If `CIRCUIT_BREAKER_TRIGGERED` is returned, stop immediately. Attempt at most 2 retries before escalating to the user (`BLOCKED: LOCAL_GROUNDING_FAILED`).

---

## ⚙️ Operational Modes

Configured in `.argus/config.json`:

| Mode | Visual Engine | Cloud Upload | When to Use |
| :--- | :--- | :---: | :--- |
| **`auto`** *(Default)* | On-Device Florence-2 with intelligent fallback | Zero (unless escalated) | Recommended for all everyday automation and game agent loops. |
| **`local`** | Strictly on-device Florence-2 GPU | **Zero** | High-security or offline environments where no pixels may leave the machine. |
| **`direct`** | Standard Antigravity / Multimodal Cloud Screenshots | Full PNGs | Systems without dedicated GPU / CUDA where cloud vision is required. |

---

## 🏗️ Architectural Highlights

### 1. Low-VRAM On-Device Vision (Florence-2)
ARGUS utilizes Microsoft's **Florence-2-base** foundation vision model in FP16 precision. Optimized on local hardware, it consumes only **~680 MB of VRAM**, coexisting peacefully with active games and IDEs on modern GPUs (e.g. RTX 2060).

### 2. Perceptual Hash Circuit Breaker (Emniyet Şalteri)
ARGUS computes a 64-bit difference hash (dHash) after every GUI action. If the Hamming distance between frames is $\le 2$ across 3 consecutive steps, ARGUS halts execution, completely immunizing users from infinite token burnout.

### 3. Windows Desktop Session Isolation Bypass
Windows background agent processes are restricted by default to isolated desktop stations, causing `OSError: screen grab failed`. ARGUS re-binds calling threads directly to `user32.OpenDesktopW("Default")`, allowing direct inspection of active applications without minimizing or disrupting user windows.

### 4. Silent Headless Android & BlueStacks Automation
Using ADB standard stream pipes (`screencap -p` and `input tap`), ARGUS executes touch interactions, D-Pad navigation, and layout scraping completely in the background without commandeering the physical mouse pointer.

---

## 🗺️ Repository & Documentation Map

```text
ARGUS/
├── README.md                          # Master product overview & quick start
├── LICENSE                            # MIT License (Aethelion)
├── INSTALL.md                         # Canonical installation & payload classification
├── SECURITY.md                        # Threat model & privacy boundaries
├── requirements.txt                   # Python dependencies
├── toggle_shield.bat                  # One-click desktop status inspector
├── .env.example                       # Environment template
├── .gitignore                         # Runtime ignore rules
│
├── .agents/skills/argus/
│   ├── SKILL.md                       # Antigravity skill interface definition
│   └── scripts/
│       ├── argus.py                   # Master CLI controller & mode engine
│       ├── engine.py                  # Florence-2 vision engine & screen grabber
│       ├── fallback_handler.py        # pHash circuit breaker & XML fallback
│       └── server.py                  # FastMCP server implementation
│
├── .argus/
│   ├── config.json.example            # Configuration template
│   └── logs/                          # Runtime breaker logs
│
└── studio/
    ├── README.md                      # Studio index
    ├── ARCHITECTURE.md                # Token preservation & isolation architecture
    ├── CIRCUIT_BREAKER.md             # dHash mathematical model & recovery rules
    └── PROTOCOL.md                    # Structured JSON scene graph contract
```

---

## 📄 License & Attribution

ARGUS is released as open-source software under the **MIT License**.  
Copyright (c) 2026 **Aethelion / aethelondev-stack**. All rights reserved.
