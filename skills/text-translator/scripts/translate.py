#!/usr/bin/env python3
"""Translate text to a target language using a free API or placeholder."""
import argparse
import json
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Translate text to target language")
    parser.add_argument("--text", "-t", required=True, help="Text to translate")
    parser.add_argument("--target-lang", "-l", default="es", help="Target language code (default: es)")
    args = parser.parse_args()

    # Try libre translate API (free, no key required)
    url = "https://libretranslate.com/translate"
    payload = json.dumps({"q": args.text, "source": "en", "target": args.target_lang})
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", url, "-H", "Content-Type: application/json", "-d", payload],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and "translatedText" in result.stdout:
            data = json.loads(result.stdout)
            print(data.get("translatedText", "[Translation placeholder]"))
        else:
            print(f"[Translation placeholder: {args.text} -> {args.target_lang}]")
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        print(f"[Translation placeholder: {args.text} -> {args.target_lang}]")


if __name__ == "__main__":
    main()
