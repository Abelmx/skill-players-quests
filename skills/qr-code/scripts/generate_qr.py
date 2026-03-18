#!/usr/bin/env python3
"""Generate QR code PNG from URL or text."""

import argparse
import subprocess
import sys


def ensure_qrcode():
    """Install qrcode[pil] if not available."""
    try:
        import qrcode  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode[pil]"])


def main():
    parser = argparse.ArgumentParser(description="Generate QR code PNG")
    parser.add_argument("--data", required=True, help="URL or text to encode")
    parser.add_argument("--output", default="qr_output.png", help="Output file path (default: qr_output.png)")
    args = parser.parse_args()

    ensure_qrcode()

    import qrcode

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(args.data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(args.output)
    print(f"QR code saved to {args.output}")


if __name__ == "__main__":
    main()
