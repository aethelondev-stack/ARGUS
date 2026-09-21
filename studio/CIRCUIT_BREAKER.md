# Circuit Breaker & Perceptual Hashing (CIRCUIT_BREAKER.md)

## 1. The Perceptual Difference Hash (dHash) Algorithm

ARGUS implements a high-speed, noise-resilient 64-bit difference hash (dHash) to track UI dynamics:

```text
[Input Image (RGB)] 
        │
        ▼ Grayscale Conversion
   [Image (L)]
        │
        ▼ Downscale to 9x8 pixels (LANCZOS)
   [9 x 8 Pixel Matrix]
        │
        ▼ Row-wise Gradient Evaluation (P[x] > P[x+1])
   [64 Boolean Gradients]
        │
        ▼ Hex Encoding
   64-bit Hex Hash (e.g. "8f9e2b1a4c3d7e5f")
```

### Why dHash Over Cryptographic Hashes (SHA-256 / MD5)?
Cryptographic hashes are avalanche-sensitive: changing a single sub-pixel or minor cursor blink causes 100% hash variation.  
In contrast, dHash evaluates structural luminance gradients, ignoring subtle render variations while reliably detecting genuine UI state changes.

---

## 2. Hamming Distance & Freeze Detection

The difference between consecutive frames is quantified using the Hamming distance:
$$\text{Distance} = \sum_{i=0}^{63} \left( H_{\text{prev}}[i] \neq H_{\text{curr}}[i] \right)$$

- **Distance $\le 2$:** Screen is perceptually identical. Counter increments: `consecutive_unchanged += 1`.
- **Distance $> 2$:** Visual state changed. Counter resets: `consecutive_unchanged = 0`.
- **Threshold Tripping:** When `consecutive_unchanged >= 3`:
  ```json
  {
    "status": "CIRCUIT_BREAKER_TRIGGERED",
    "error": "Display remained unchanged across 3 consecutive actions. Interface freeze detected."
  }
  ```

---

## 3. Agent Recovery Protocol

1. **Hard Cap (2 Retries):** If local grounding fails or an action fails to alter the UI state, the agent is restricted to a maximum of 2 attempts.
2. **Reset Loop Prohibition:** The agent must never autonomously loop on `--reset` or `smart_ui_reset()` to defeat the safety breaker.
3. **Escalation:** After 2 failed attempts, halt autonomous execution, report `BLOCKED: LOCAL_GROUNDING_FAILED`, and request human review.
