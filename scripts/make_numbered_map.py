#!/usr/bin/env python3
"""Draw cell numbers on top of the official example sheet.

Usage:
    python scripts/make_numbered_map.py --base generic.png --out numbered_map.png

Standard library only. A tiny built-in 5x7 bitmap font is used, so no font
file or Pillow is needed. The output is a derived image containing upstream
pixels: keep it local, do not commit it to the repository.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import png  # noqa: E402
from layout import NUMBERED_CELLS, SHEET_H, SHEET_W  # noqa: E402

FONT = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
}

COLORS = {
    "P": (30, 90, 200, 255),    # paws
    "F": (220, 110, 20, 255),   # faces
    "E": (25, 155, 80, 255),    # end screen
    "U": (150, 60, 180, 255),   # UI chrome
    "X": (110, 110, 110, 255),  # reserved empty cells
}
WHITE = (255, 255, 255, 255)

# U04/U05 are two adjacent slivers (8px and 4px wide) at the very bottom of
# the sheet. Their default external labels would overlap, so give each one a
# separate anchor.
SMALL_LABEL_ANCHORS = {
    "U04": (-108, -26),
    "U05": (-44, -26),
}


def fill_rect(img, w, h, x, y, rw, rh, color):
    for yy in range(max(0, y), min(h, y + rh)):
        for xx in range(max(0, x), min(w, x + rw)):
            o = (yy * w + xx) * 4
            img[o:o + 4] = bytes(color)


def stroke_rect(img, w, h, x, y, rw, rh, color, t=2):
    fill_rect(img, w, h, x, y, rw, t, color)
    fill_rect(img, w, h, x, y + rh - t, rw, t, color)
    fill_rect(img, w, h, x, y, t, rh, color)
    fill_rect(img, w, h, x + rw - t, y, t, rh, color)


def draw_label(img, w, h, text, x, y, scale, bg, fg):
    pad = 3
    tw = len(text) * 6 * scale
    th = 7 * scale
    fill_rect(img, w, h, x, y, tw + 2 * pad, th + 2 * pad, bg)
    for ci, ch in enumerate(text):
        glyph = FONT.get(ch)
        if not glyph:
            continue
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    px = x + pad + ci * 6 * scale + gx * scale
                    py = y + pad + gy * scale
                    fill_rect(img, w, h, px, py, scale, scale, fg)


def main():
    ap = argparse.ArgumentParser(description="Number every cell of the example sheet")
    ap.add_argument("--base", required=True, help="official generic.png")
    ap.add_argument("--out", default="numbered_map.png")
    ap.add_argument("--scale", type=int, default=2, help="label font scale")
    args = ap.parse_args()

    w, h, img = png.read_png(args.base)
    if (w, h) != (SHEET_W, SHEET_H):
        raise ValueError("base must be 1024x1024, got %dx%d" % (w, h))

    for label, (x, y, cw, ch, group) in NUMBERED_CELLS.items():
        color = COLORS[group]
        stroke_rect(img, w, h, x, y, cw, ch, color)
        if cw < 50 or ch < 50:
            dx, dy = SMALL_LABEL_ANCHORS.get(label, (-44, -26))
            lx, ly = max(0, x + dx), max(0, y + dy)
            fill_rect(img, w, h, lx + 8, ly + 20, 2, 8, color)
        else:
            lx, ly = x + 4, y + 4
        draw_label(img, w, h, label, lx, ly, args.scale, color, WHITE)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    png.write_png(str(out), w, h, img)
    print("wrote %s (%d numbered cells)" % (out, len(NUMBERED_CELLS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
