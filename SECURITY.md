# Security Policy & Privacy Guarantees (SECURITY.md)

ARGUS is built with an uncompromising defense-in-depth security architecture designed to guarantee developer privacy, zero credential leakage, and operational safety.

---

## 1. Security Architecture & Boundary Model

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        ARGUS SECURITY BOUNDARY                         │
│                                                                        │
│  [User Host Environment]                                               │
│     ├── Desktop Screen / BlueStacks Emulator                           │
│     │        │                                                         │
│     │        ▼                                                         │
│     ├── [ARGUS Engine (Local GPU / CUDA)]                              │
│     │        ├── Florence-2 Model (On-Device Memory Sandboxing)        │
│     │        ├── Perceptual Hash Circuit Breaker (Freeze Lockout)      │
│     │        └── Windows Desktop Station Binding (OpenDesktopW)        │
│     │                                                                  │
│     ▼ (Zero Pixels Transmitted Outside Local Host)                     │
│  [Compact Scene Graph JSON (<50 Tokens)]                               │
│     │                                                                  │
│     ▼                                                                  │
│  [Lead AI Agent (Antigravity / Cursor / Claude)]                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Privacy & Data Flow Guarantees

1. **Zero Raw Image Exfiltration:**  
   Raw screenshots are never transmitted to external cloud APIs or saved into remote chat context. All vision embeddings and bounding box detections occur strictly on local hardware.
2. **Deterministic VRAM Sandboxing:**  
   Florence-2 runs in FP16 inference mode consuming only ~680 MB of VRAM. Temporary generation buffers are purged via `torch.cuda.empty_cache()` immediately after inference.
3. **Headless Mouse Non-Interference:**  
   Android/BlueStacks actions use direct ADB touch injection (`input tap`), preventing malicious or errant cursor displacements on the host operating system.
4. **Circuit Breaker Loop Prevention:**  
   If an interface freezes or enters an unresponsive state, ARGUS trips after 3 consecutive identical perceptual hashes, preventing financial loss from infinite agent retries.

---

## 3. Reporting a Vulnerability

If you discover an architectural security flaw, coordinate bypass, or unhandled exception vector in ARGUS:
- Please do NOT disclose it publicly on GitHub Issues.
- Submit a detailed report via private disclosure to the project maintainers (`aethelondev-stack`).
- We acknowledge reports within 48 hours and work on prompt remediation.
