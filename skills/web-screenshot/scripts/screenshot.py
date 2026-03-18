#!/usr/bin/env python3
"""Capture full-page screenshot of a URL using Playwright."""
import argparse
import subprocess
import sys


def ensure_playwright():
    """Install playwright and chromium if needed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)


def main():
    parser = argparse.ArgumentParser(description="Capture webpage screenshot")
    parser.add_argument("--url", required=True, help="URL to capture")
    parser.add_argument("--output", default="screenshot.png", help="Output file path")
    args = parser.parse_args()

    ensure_playwright()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(args.url, wait_until="networkidle")
        page.screenshot(path=args.output, full_page=True)
        browser.close()

    print(f"Screenshot saved to {args.output}")


if __name__ == "__main__":
    main()
