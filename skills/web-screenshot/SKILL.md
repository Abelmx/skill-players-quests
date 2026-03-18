---
name: web-screenshot
description: Capture screenshots of web pages. Use when the user asks to take a screenshot, capture, or snapshot a webpage.
---

# Web Screenshot

Capture screenshots of web pages.

## Usage

```bash
python scripts/screenshot.py --url "https://example.com" --output screenshot.png
```

- `--url`: URL to capture (required)
- `--output`: Output file path (default: screenshot.png)

## Notes

- Install playwright if needed: `pip install playwright && playwright install chromium`
- Takes full-page screenshot
