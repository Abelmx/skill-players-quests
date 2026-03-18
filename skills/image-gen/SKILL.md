---
name: image-gen
description: Generate images using an OpenAI-compatible image generation API. Use when the user asks to create, generate, or produce images, pictures, or illustrations.
---

# Image Generation

## Instructions

When the user asks to create, generate, or produce an image:

1. Run the image generation script with the user's prompt and desired output path:
   ```bash
   python scripts/generate_image.py --prompt "YOUR_PROMPT" --output "output.png"
   ```

2. The script calls an OpenAI-compatible chat/completions endpoint that returns
   images as data URIs. It requires the following environment variables:
   - `IMAGE_GEN_API_KEY` — API key for the image generation service
   - `IMAGE_GEN_BASE_URL` — Base URL of the service (e.g. `https://api.example.com`)
   - `IMAGE_GEN_MODEL` — Model ID (optional, defaults to `gemini-2.0-flash-exp-image-generation`)

3. The script saves the generated image as PNG to the specified output path.

## Usage Examples

```bash
python scripts/generate_image.py --prompt "A sunset over mountains"

python scripts/generate_image.py --prompt "A cute cat wearing a hat" --output "cat.png"
```

## Notes

- Output defaults to `output.png` when `--output` is omitted.
- The script auto-installs `httpx` and `Pillow` if not found.
- Timeout defaults to 120 seconds (configurable via `IMAGE_GEN_TIMEOUT`).
