#!/usr/bin/env python3
"""Validate a composed STOMPGAME sheet before importing it.

Checks: exact size, UI chrome untouched, empty reserved cells, every character
cell non-empty and properly cut out, and frame-to-frame continuity (to catch
broken pose sequences such as a suddenly mirrored foot or a changed character).

Continuity checks are heuristics. They detect abrupt jumps, not anatomical
correctness; the visual review checklist in references/frame-semantics.md is
still required.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import png  # noqa: E402
from layout import (BLANK_CELLS, CELLS, DECOR, GROUPS,  # noqa: E402
                    GROUP_MEMBERS, SHEET_H, SHEET_W)


class Verdict:
    def __init__(self):
        self.rows = []

    def add(self, level, code, msg):
        self.rows.append({"level": level, "code": code, "message": msg})
        print("[%s] %s: %s" % (level, code, msg))

    @property
    def failures(self):
        return [r for r in self.rows if r["level"] == "FAIL"]

    @property
    def warnings(self):
        return [r for r in self.rows if r["level"] == "WARN"]


def main():
    ap = argparse.ArgumentParser(description="Validate a STOMPGAME custom sheet")
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--base", required=True, help="official generic.png for chrome comparison")
    ap.add_argument("--report", default=None, help="build_sheet report JSON, optional")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--max-shift", type=float, default=90.0, help="max centroid jump between adjacent frames, px")
    ap.add_argument("--max-coverage-delta", type=float, default=0.35)
    ap.add_argument("--max-color-delta", type=float, default=95.0)
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args()

    sw, sh, sheet = png.read_png(args.sheet)
    bw, bh, base = png.read_png(args.base)
    v = Verdict()
    if (sw, sh) != (SHEET_W, SHEET_H):
        v.add("FAIL", "size", "sheet is %dx%d, expected %dx%d" % (sw, sh, SHEET_W, SHEET_H))
        return 1
    v.add("PASS", "size", "sheet is 1024x1024")
    if (bw, bh) != (SHEET_W, SHEET_H):
        v.add("FAIL", "base", "base is %dx%d, expected 1024x1024" % (bw, bh))
        return 1

    for name, (x, y, w, h) in DECOR.items():
        a = bytes(png.crop(sheet, sw, sh, x, y, w, h))
        b = bytes(png.crop(base, bw, bh, x, y, w, h))
        if a == b:
            v.add("PASS", "chrome:" + name, "UI pixels unchanged")
        else:
            v.add("FAIL", "chrome:" + name,
                  "UI chrome was modified; never redraw this region")

    for name, (x, y, w, h) in BLANK_CELLS.items():
        cov, _mean, _c = png.cell_stats(png.crop(sheet, sw, sh, x, y, w, h), w, h)
        if cov <= 0.02:
            v.add("PASS", "reserved:" + name, "empty as expected")
        else:
            v.add("WARN", "reserved:" + name,
                  "reserved cell has content (%.3f); harmless at default settings" % cov)

    stats = {}
    for name, (x, y, w, h) in CELLS.items():
        cell = png.crop(sheet, sw, sh, x, y, w, h)
        cov, mean, centroid = png.cell_stats(cell, w, h)
        corner = png.corner_opacity(cell, w, h)
        border = png.border_opacity(cell, w, h, k=6)
        stats[name] = {"coverage": cov, "mean": mean, "centroid": centroid,
                       "corner": corner, "border": border}
        if cov < 0.02:
            v.add("FAIL", "cell:" + name, "cell is empty (coverage %.3f)" % cov)
            continue
        if name != "endscreen" and (corner > 0.45 or (cov > 0.80 and border > 0.50)):
            v.add("FAIL", "cutout:" + name,
                  "opaque background plate detected (coverage %.3f, corners %.2f, border %.2f); "
                  "remove the flat background" % (cov, corner, border))
        elif name != "endscreen" and cov > 0.90:
            v.add("WARN", "cutout:" + name,
                  "cell is almost fully opaque (%.3f); verify transparency" % cov)
        else:
            v.add("PASS", "cell:" + name,
                  "coverage %.3f, corners %.2f, border %.2f" % (cov, corner, border))

    for group in GROUPS:
        members = GROUP_MEMBERS[group]
        for a, b in zip(members, members[1:]):
            sa, sb = stats.get(a), stats.get(b)
            if not sa or not sb:
                continue
            shift = ((sa["centroid"][0] - sb["centroid"][0]) ** 2 +
                     (sa["centroid"][1] - sb["centroid"][1]) ** 2) ** 0.5
            dcov = abs(sa["coverage"] - sb["coverage"])
            dcol = png.color_distance(sa["mean"], sb["mean"])
            code = "continuity:%s->%s" % (a, b)
            if shift > args.max_shift:
                v.add("FAIL", code, "centroid jumps %.1f px; the pose/view/foot side likely changed" % shift)
            elif dcov > args.max_coverage_delta:
                v.add("FAIL", code,
                      "silhouette area jumps %.3f; pose or background changed abruptly" % dcov)
            elif dcol > args.max_color_delta:
                v.add("WARN", code, "average color changes %.1f; check style consistency" % dcol)
            else:
                v.add("PASS", code, "shift %.1f px, coverage delta %.3f, color delta %.1f" % (shift, dcov, dcol))

    if args.report:
        rep = json.loads(Path(args.report).read_text(encoding="utf-8"))
        for name, info in rep.get("cells", {}).items():
            status = str(info.get("status", ""))
            normal = status in ("ok", "generated") or status.startswith("reused:")
            if not normal:
                v.add("WARN", "build:" + name,
                      "frame was neither generated nor reused (%s)" % status)
        missing_must = [n for n, present in rep.get("must_generate", {}).items()
                        if not present]
        if missing_must:
            v.add("WARN", "must_generate",
                  "fast-pass frames missing (reuse fallback used): %s" %
                  ", ".join(missing_must))

    summary = {"checks": v.rows, "failures": len(v.failures), "warnings": len(v.warnings)}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("summary: %d failure(s), %d warning(s)" % (len(v.failures), len(v.warnings)))
    if v.failures:
        return 1
    if args.strict and v.warnings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
