# Output Protocol & Schema Specification (PROTOCOL.md)

This document defines the structured JSON schemas emitted by ARGUS to `stdout` for autonomous agent consumption.

---

## 1. Desktop Scene Graph (`source="desktop"`)

```json
{
  "source": "desktop",
  "screen_dimensions": [1920, 1080],
  "active_foreground_window": "Visual Studio Code",
  "visible_windows_count": 5,
  "visible_windows": [
    {
      "title": "Visual Studio Code",
      "bounds": [0, 0, 1920, 1040],
      "center": [960, 520]
    },
    {
      "title": "BlueStacks App Player",
      "bounds": [200, 100, 1480, 820],
      "center": [840, 460]
    }
  ],
  "token_estimate": 45
}
```

---

## 2. Android / BlueStacks Scene Graph (`source="bluestacks"`)

```json
{
  "source": "bluestacks",
  "screen_dimensions": [1920, 1080],
  "active_focus": {
    "box": [120, 450, 420, 900],
    "center": [270, 675],
    "status": "Cyan Highlight Verified"
  },
  "detected_cards_count": 8,
  "cards": [
    {
      "box": [120, 450, 420, 900],
      "center": [270, 675]
    },
    {
      "box": [460, 450, 760, 900],
      "center": [610, 675]
    }
  ],
  "token_estimate": 45
}
```

---

## 3. Desktop Items Protocol (`--desktop-items`)

Direct Windows Shell readout without capturing screenshots:

```json
{
  "desktop_items_count": 18,
  "items": [
    "Google Chrome",
    "BlueStacks 5",
    "Visual Studio Code",
    "Neon Clicker",
    "Notes.txt"
  ],
  "token_estimate": 35
}
```

---

## 4. Resolution Normalization & Auto-Scaling

When physical display resolution differs from the image capture resolution:
$$\text{Scale}_x = \frac{\text{Device Width}}{\text{Capture Width}}, \quad \text{Scale}_y = \frac{\text{Device Height}}{\text{Capture Height}}$$
$$\text{Target}_x = \text{Coord}_x \times \text{Scale}_x, \quad \text{Target}_y = \text{Coord}_y \times \text{Scale}_y$$

Coordinates are normalized automatically in `engine.py` before executing clicks.
