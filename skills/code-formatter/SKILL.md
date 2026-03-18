---
name: code-formatter
description: Format and lint source code files. Use when the user asks to format, beautify, or lint code in Python, JavaScript, or other languages.
---

# Code Formatter

## Instructions

When the user asks to format or lint code:

1. Run the formatter script on the target file:
   ```bash
   ./scripts/format_code.sh path/to/file.py
   ```

2. The script runs black (Python) or prettier (JS/TS) if available.

3. If no formatter is installed, it echoes a message suggesting installation.

## Notes

- Python: `pip install black`
- JS/TS: `npm install -g prettier`
