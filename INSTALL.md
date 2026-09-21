# ARGUS Installation Guide (INSTALL.md)

This document provides the definitive, canonical procedure for installing **ARGUS (On-Device Vision Shield & Token Guardian)** into any AI agent workspace or global environment.

ARGUS offloads vision inspection, Windows desktop navigation, and Android emulator control to an on-device vision model (Florence-2, ~680 MB VRAM), slashing multimodal agent token consumption by **97.5%** and preventing runaway retry loops via an automated perceptual circuit breaker.

---

## 1. Distribution Repository vs. Target Project

When deploying ARGUS, distinguish between the **ARGUS Distribution Repository** and your **Target Project Workspace**:

```text
ARGUS Distribution Repository                         Your Target Project Root
├── .agents/skills/argus/             ──[COPY]──►  ├── .agents/skills/argus/
│   ├── SKILL.md                                  │   ├── SKILL.md
│   └── scripts/                                  │   └── scripts/
│       ├── argus.py                              │       ├── argus.py
│       ├── engine.py                             │       ├── engine.py
│       ├── fallback_handler.py                   │       ├── fallback_handler.py
│       └── server.py                             │       └── server.py
├── .argus/config.json.example        ──[COPY]──►  ├── .argus/config.json.example
├── studio/ (Reference Docs)          ──[COPY]──►  ├── studio/ (Optional architectural docs)
│                                                 │
│   [DO NOT COPY FROM ARGUS]                      ├── .gitignore (MERGE rules, do NOT overwrite!)
│   ├── .git/                                     ├── README.md (Keep your project's README!)
│   ├── README.md                                 └── [Your project source code...]
│   ├── INSTALL.md
│   ├── SECURITY.md
│   └── LICENSE
```

> [!CAUTION]
> - **DO NOT copy the `.git/` directory** of ARGUS into your project.
> - **DO NOT overwrite your existing `.gitignore`**; append ARGUS's ignore block instead.
> - **DO NOT overwrite your target project's `README.md`** with ARGUS's `README.md`.

---

## 2. Canonical Installation Payload

| Repository Path | Classification | Purpose & Description |
| :--- | :---: | :--- |
| **`.agents/skills/argus/`** | **REQUIRED** | Skill definition (`SKILL.md`), master CLI controller (`argus.py`), vision engine (`engine.py`), circuit breaker (`fallback_handler.py`), and FastMCP server (`server.py`). |
| **`.argus/config.json.example`** | **REQUIRED** | Project configuration template for mode selection (`auto`, `local`, `direct`) and device targets. |
| **`.argus/logs/`** | **AUTO-CREATED** | Runtime diagnostic logs and breaker history. Created automatically by `ensure_dirs()`. |
| **`.argus/config.json`** | **AUTO-CREATED** | Active project configuration file. Created automatically upon `--set-mode`. |
| **`studio/`** | **OPTIONAL** | Technical specifications (`ARCHITECTURE.md`, `CIRCUIT_BREAKER.md`, `PROTOCOL.md`). Recommended for internal documentation. |
| **`requirements.txt`** | **OPTIONAL** | Python package manifest (`torch`, `transformers`, `opencv-python`, `Pillow`, `fastmcp`, `pyautogui`). |
| **`.git/`** | **DISTRIBUTION-ONLY** | ARGUS's Git repository metadata. Never copy to target projects. |
| **`README.md`** | **DISTRIBUTION-ONLY** | Master product documentation for the ARGUS repository. |
| **`INSTALL.md`** | **DISTRIBUTION-ONLY** | This installation guide. |
| **`SECURITY.md`** | **DISTRIBUTION-ONLY** | Threat model and security policy. |
| **`LICENSE`** | **DISTRIBUTION-ONLY** | MIT License file. |
| **`.gitignore`** | **MERGE ONLY** | Must be merged with target project's `.gitignore`. Never overwrite. |

---

## 3. Step-by-Step Installation

### Step 1: Copy Required Files into Your Project Root

#### On Windows (PowerShell):
```powershell
# Navigate to your target project root
cd "C:\path\to\your-project"

# Set path to the ARGUS distribution package
$ARGUS_DIR = "C:\path\to\ARGUS"

# 1. Copy the agent skill directory (Required)
New-Item -ItemType Directory -Force -Path ".agents\skills"
Copy-Item -Recurse -Force "$ARGUS_DIR\.agents\skills\argus" ".agents\skills\"

# 2. Copy the configuration template (Required)
New-Item -ItemType Directory -Force -Path ".argus"
Copy-Item -Force "$ARGUS_DIR\.argus\config.json.example" ".argus\"

# 3. Optional: Copy the studio reference documentation
Copy-Item -Recurse -Force "$ARGUS_DIR\studio" "studio"
```

#### On Linux / macOS (Bash):
```bash
# Navigate to your target project root
cd /path/to/your-project

# Set path to the ARGUS distribution package
ARGUS_DIR="/path/to/ARGUS"

# 1. Copy the agent skill directory (Required)
mkdir -p .agents/skills
cp -r "$ARGUS_DIR/.agents/skills/argus" .agents/skills/

# 2. Copy the configuration template (Required)
mkdir -p .argus
cp "$ARGUS_DIR/.argus/config.json.example" .argus/

# 3. Optional: Copy the studio reference documentation
cp -r "$ARGUS_DIR/studio" ./studio
```

---

### Step 2: Merge `.gitignore` Rules (Do NOT Overwrite)

Append the following block to your target project's existing `.gitignore`:

```gitignore
# ===========================================================================
# ARGUS / Vision Shield Runtime Exclusions
# ===========================================================================
.argus/config.json
.argus/logs/*
!.argus/logs/.gitkeep
__pycache__/
*.py[cod]
*.tmp
*.log
*.png
*.jpg
```

---

### Step 3: Install Python Dependencies

```powershell
pip install -r .agents/skills/argus/requirements.txt
```
*(Or install manually: `pip install torch transformers Pillow opencv-python numpy pyautogui fastmcp`)*.

---

### Step 4: Configure Operational Mode

ARGUS defaults to **`auto`** mode:

```powershell
# Auto Mode (Recommended): Hybrid on-device vision; preserves agent context
python .agents/skills/argus/scripts/argus.py --set-mode auto

# Local Mode: Strictly on-device GPU vision; 0 token upload
python .agents/skills/argus/scripts/argus.py --set-mode local

# Direct Mode: Bypass local shield; standard multimodal cloud screenshots
python .agents/skills/argus/scripts/argus.py --set-mode direct
```

---

### Step 5: Verify the Installation

Execute the status check from your project root:

```powershell
python .agents/skills/argus/scripts/argus.py --status
```

Expected JSON response:
```json
{
  "status": "active",
  "version": "1.0.0",
  "project_root": "C:\\path\\to\\your-project",
  "argus_mode": "auto",
  "default_source": "desktop",
  "hardware": {
    "cuda_available": true,
    "active_device": "NVIDIA GeForce RTX 2060",
    "vram_budget_mb": 680
  },
  "circuit_breaker": {
    "max_consecutive_unchanged": 3,
    "is_tripped": false
  }
}
```

#### Run a Non-Invasive Dry-Run Test:
```powershell
python .agents/skills/argus/scripts/argus.py --scan --source desktop --dry-run
```

---

## 4. Alternative: Global Antigravity Installation

If you want ARGUS available globally across **all** your Antigravity sessions:

1. Copy `.agents/skills/argus/` into Antigravity's global skill directory:
   `C:\Users\<User>\.gemini\antigravity\skills\argus\`
2. To register ARGUS as a persistent MCP server, add this block to `mcp_config.json`:
   ```json
   {
     "mcpServers": {
       "argus": {
         "command": "python",
         "args": [
           "C:\\path\\to\\ARGUS\\.agents\\skills\\argus\\scripts\\server.py"
         ],
         "env": {}
       }
     }
   }
   ```

---

## 5. 1-Prompt Agent Onboarding

When starting a project with an AI coding assistant (Google Antigravity, Cursor, Cline), paste this prompt once:

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
