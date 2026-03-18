---
name: qr-code
description: Generate QR code images from URLs or text. Use when the user asks to create QR codes.
---

# QR Code Generation

## Instructions

When the user asks to create a QR code:

1. Run the QR generation script with the data (URL or text) and output path:
   ```bash
   python scripts/generate_qr.py --data "YOUR_URL_OR_TEXT" --output "qr_output.png"
   ```

2. The script auto-installs `qrcode[pil]` via pip if not found.

## Usage Examples

```bash
# Basic usage (saves to qr_output.png by default)
python scripts/generate_qr.py --data "https://example.com"

# Specify output file
python scripts/generate_qr.py --data "Hello World" --output "hello_qr.png"

# Generate QR for a URL
python scripts/generate_qr.py --data "https://github.com/user/repo" --output "repo_qr.png"
```

## Notes

- Output defaults to `qr_output.png` when `--output` is omitted.
- Supports any text or URL as input data.
