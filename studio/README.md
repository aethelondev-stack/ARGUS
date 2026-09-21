# ARGUS Studio Documentation Hub

This directory (`studio/`) provides deep technical blueprints, visual scene graph protocols, perceptual hash mathematical models, and token preservation metrics for **ARGUS (On-Device Vision Shield & Token Guardian)**.

---

## 📚 Document Index

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)**:
   - Deep dive into on-device vision offloading, VRAM optimization (~680 MB on NVIDIA RTX GPUs), Windows session isolation bypass (`OpenDesktopW`), and background ADB headless execution.
2. **[CIRCUIT_BREAKER.md](./CIRCUIT_BREAKER.md)**:
   - Mathematical specification of the 64-bit difference hash (dHash), Hamming distance calculation, 3-consecutive unchanged action threshold, and loop recovery protocols.
3. **[PROTOCOL.md](./PROTOCOL.md)**:
   - Detailed schema specification for desktop and Android scene graphs, coordinate normalization across heterogeneous display densities, and token cost analyses.

---

## 🚀 Quick CLI Verification

```powershell
# 1. Check ARGUS status and hardware detection
python .agents/skills/argus/scripts/argus.py --status

# 2. Query or configure mode (auto | local | direct)
python .agents/skills/argus/scripts/argus.py --get-mode
python .agents/skills/argus/scripts/argus.py --set-mode auto

# 3. Non-invasive dry-run verification
python .agents/skills/argus/scripts/argus.py --scan --source desktop --dry-run
```
