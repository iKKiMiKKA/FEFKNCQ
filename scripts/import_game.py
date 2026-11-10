#!/usr/bin/env python3
"""Reference implementation: upload custom.png and start the game in a browser.

This is a fallback for agents that lack a native browser tool. Prefer the
agent's own browser automation (see references/import.md) so the game window
stays open for the user.

Install the optional dependency first:
    pip install -r requirements-browser.txt
    playwright install chromium
"""

import argparse
import sys
from pathlib import Path

GAME_URL = "https://ikkimikka.net/stompgame/?character=custom"


def main():
    ap = argparse.ArgumentParser(description="Import a sheet into STOMPGAME")
    ap.add_argument("--image", required=True, help="path to custom.png")
    ap.add_argument("--url", default=GAME_URL)
    ap.add_argument("--headless", action="store_true", help="run without a visible window")
    ap.add_argument("--no-wait", action="store_true", help="close the browser immediately after starting")
    ap.add_argument("--no-click", action="store_true", help="do not click CLICK TO BEGIN")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright is not installed.", file=sys.stderr)
        print("Run: pip install -r requirements-browser.txt && playwright install chromium", file=sys.stderr)
        print("Or follow references/import.md with the agent's own browser tool.", file=sys.stderr)
        return 2

    image = Path(args.image).resolve()
    if not image.is_file():
        print("ERROR: image not found: %s" % image, file=sys.stderr)
        return 2

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=args.headless)
        page = browser.new_page(viewport={"width": 1000, "height": 720})
        page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
        # The upload input is injected by the custom-upload panel at runtime.
        page.wait_for_selector("#upload", timeout=60000)
        page.set_input_files("#upload", str(image))
        print("uploaded %s" % image.name)
        # Uploading triggers done_loading() and a fresh game init.
        page.wait_for_timeout(3500)
        if not args.no_click:
            page.locator("#outcanvas").click(position={"x": 400, "y": 240})
            print("clicked CLICK TO BEGIN")
        print("game URL: %s" % args.url)
        if not args.headless and not args.no_wait:
            try:
                input("Game window is open. Press Enter to close the browser...")
            except EOFError:
                pass
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
