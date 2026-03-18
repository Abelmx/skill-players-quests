---
name: file-compressor
description: Compress and decompress files and directories. Use when the user asks to zip, compress, extract, or archive files.
---

# File Compressor

## Instructions

When the user asks to compress or decompress files:

1. Compress:
   ```bash
   ./scripts/compress.sh --action compress --input path/to/dir --output archive.tar.gz
   ```

2. Decompress:
   ```bash
   ./scripts/compress.sh --action decompress --input archive.tar.gz --output path/to/output
   ```

3. Uses tar/gzip for compression.

## Notes

- Compress: input can be file or directory.
- Decompress: output is the destination directory.
