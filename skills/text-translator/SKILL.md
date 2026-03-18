---
name: text-translator
description: Translate text between languages using translation APIs. Use when the user asks to translate text, documents, or content to another language.
---

# Text Translator

## Instructions

When the user asks to translate text:

1. Run the translator script:
   ```bash
   python scripts/translate.py --text "Hello world" --target-lang "es"
   ```

2. The script attempts to use a free translation API or prints a placeholder.

3. Common target languages: es (Spanish), fr (French), de (German), zh (Chinese).

## Notes

- Requires network access for API calls.
- Falls back to placeholder output if API is unavailable.
