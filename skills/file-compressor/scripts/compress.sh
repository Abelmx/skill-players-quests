#!/usr/bin/env bash
# Compress or decompress files using tar/gzip.
set -e

ACTION=""
INPUT=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --action)
            ACTION="$2"
            shift 2
            ;;
        --input)
            INPUT="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [[ -z "$ACTION" || -z "$INPUT" || -z "$OUTPUT" ]]; then
    echo "Usage: $0 --action compress|decompress --input <path> --output <path>"
    exit 1
fi

case "$ACTION" in
    compress)
        tar -czvf "$OUTPUT" -C "$(dirname "$INPUT")" "$(basename "$INPUT")"
        echo "Compressed $INPUT -> $OUTPUT"
        ;;
    decompress)
        mkdir -p "$OUTPUT"
        tar -xzvf "$INPUT" -C "$OUTPUT"
        echo "Decompressed $INPUT -> $OUTPUT"
        ;;
    *)
        echo "Error: action must be 'compress' or 'decompress'"
        exit 1
        ;;
esac
