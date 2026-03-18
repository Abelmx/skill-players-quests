#!/usr/bin/env bash
# Format or lint a source file using black (Python) or prettier (JS/TS).
set -e

FILE="${1:?Usage: $0 <file>}"

if [[ ! -f "$FILE" ]]; then
    echo "Error: File not found: $FILE"
    exit 1
fi

ext="${FILE##*.}"
case "$ext" in
    py)
        if command -v black &>/dev/null; then
            black "$FILE"
            echo "Formatted $FILE with black"
        else
            echo "black not found. Install with: pip install black"
        fi
        ;;
    js|ts|jsx|tsx|json)
        if command -v prettier &>/dev/null; then
            prettier --write "$FILE"
            echo "Formatted $FILE with prettier"
        else
            echo "prettier not found. Install with: npm install -g prettier"
        fi
        ;;
    *)
        echo "No formatter configured for .$ext files"
        ;;
esac
