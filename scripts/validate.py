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
                    GROUP_MEMBERS, MUST_GENERATE, SHEET_H, SHEET_W)


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
    ap.add_argument("--max-ground-gap", type=int, default=6,
                    help="max transparent gap below a paw, px (game aligns paws by the cell bottom edge)")
    ap.add_argument("--min-leg-coverage", type=float, default=0.10,
                    help="min opaque coverage in the top 30%% of a paw cell; 0 disables the hollow-leg check")
    ap.add_argument("--max-top-gap", type=int, default=8,
                    help="max empty space above a paw before the leg starts, px")
    ap.add_argument("--min-pose-diff", type=float, default=0.10,
                    help="min fraction of differing pixels between generated front frames")
    ap.add_argument("--min-back-ratio", type=float, default=0.60,
                    help="min back/front paw coverage ratio (C5 same-foot perspective)")
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
    paw_gaps = {}
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
        if name != "endscreen":
            fill = png.bbox_fill(cell, w, h)
            if fill > 0.92 and cov > 0.20:
                v.add("FAIL", "plate:" + name,
                      "opaque rectangular plate detected (bbox fill %.3f); background removal "
                      "likely failed. Use --bg white/green or supply a transparent PNG" % fill)
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
        if name.startswith(("front_", "back_")):
            paw_gaps[name] = png.bottom_gap(cell, w, h)

    bad_ground = {n: g for n, g in paw_gaps.items() if g > args.max_ground_gap}
    if bad_ground:
        for n, g in bad_ground.items():
            v.add("FAIL", "ground:" + n,
                  "paw bottom is %d px above the cell edge (limit %d); the game aligns paws by "
                  "this edge, so the foot looks airborne when it hits. Rebuild with "
                  "build_sheet.py (it trims and bottom-aligns paws)" % (g, args.max_ground_gap))
    elif paw_gaps:
        v.add("PASS", "ground:paws",
              "all paws touch the cell bottom (max gap %d px)" % max(paw_gaps.values()))

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

    # --- semantic checks: catch "nothing changed" and hollow limbs ---
    # Continuity only detects abrupt jumps. A sheet where the raised paw never
    # shows its sole, the legs are outline-only, or the first three ego levels
    # are one identical face passes every continuity check, so measure those
    # failure modes explicitly.
    def cell_rgba(name):
        x, y, w, h = CELLS[name]
        return bytearray(png.crop(sheet, sw, sh, x, y, w, h)), w, h

    def alpha_diff(a, b):
        if len(a) != len(b):
            return 1.0
        return sum(1 for i in range(3, len(a), 4)
                   if (a[i] >= 12) != (b[i] >= 12)) / float(len(a) // 4)

    def identical(a, b):
        return bytes(png.crop(sheet, sw, sh, *CELLS[a])) == bytes(png.crop(sheet, sw, sh, *CELLS[b]))

    paws = {n: cell_rgba(n) for n in CELLS if n.startswith(("front_", "back_"))}
    hollow, short_top = [], []
    for name, (cell, w, h) in paws.items():
        band = max(1, int(h * 0.3))
        top_cov = png.cell_stats(cell[:w * band * 4], w, band)[0]
        trimmed_h = png.trim(bytearray(cell), w, h)[1]
        top_gap = h - trimmed_h - png.bottom_gap(cell, w, h)
        if args.min_leg_coverage > 0 and top_cov < args.min_leg_coverage:
            hollow.append("%s(%.3f)" % (name, top_cov))
        if top_gap > args.max_top_gap:
            short_top.append("%s(%dpx)" % (name, top_gap))
    if hollow:
        v.add("FAIL", "leg:paws",
              "%d paw cells have hollow/outline-only legs (top 30%% coverage < %.3f): %s. "
              "Draw a solid filled leg/arm reaching the top edge; see prompts.md"
              % (len(hollow), args.min_leg_coverage, ", ".join(hollow)))
    else:
        v.add("PASS", "leg:paws", "all paw legs are solid")
    if short_top:
        v.add("WARN", "top:paws",
              "leg/arm does not reach the cell top in: %s. It will look abruptly shorter "
              "in those frames" % ", ".join(short_top))

    pose_frames = [n for n in MUST_GENERATE if n.startswith("front_")]
    for a, b in zip(pose_frames, pose_frames[1:]):
        if a not in paws or b not in paws:
            continue
        diff = alpha_diff(paws[a][0], paws[b][0])
        if diff < args.min_pose_diff:
            v.add("WARN", "pose:%s->%s" % (a, b),
                  "only %.1f%% of pixels differ; these must be distinct poses "
                  "(raised paw showing the sole -> touchdown -> max pressure)" % (diff * 100))

    if "front_3" in stats and "front_5" in stats:
        c3, c5 = stats["front_3"]["coverage"], stats["front_5"]["coverage"]
        if c5 < c3 * 0.9:
            v.add("WARN", "pressure:front_5",
                  "max-pressure frame is smaller than the touchdown frame (%.3f < %.3f); "
                  "it should look wider/flatter, not thinner" % (c5, c3))

    if "front_0" in stats and "back_0" in stats:
        ratio = stats["back_0"]["coverage"] / max(stats["front_0"]["coverage"], 1e-6)
        if ratio < args.min_back_ratio:
            v.add("WARN", "back:same-foot",
                  "back paw silhouette is only %.0f%% of the front paw; C5 requires the same "
                  "foot slightly smaller/faded, not a different view" % (ratio * 100))

    if identical("normal_0", "normal_1"):
        v.add("WARN", "expression:normal-reuse",
              "normal_0 and normal_1 are the same face: the calm column shows only one tier. "
              "Generate normal_1 as a clearly different second calm face, or accept a single "
              "calm face if that is intended.")
    else:
        v.add("PASS", "expression:early-ego", "normal_0 and normal_1 are two distinct calm faces")

    kill_pairs = (("normal_0", "excite_0"), ("normal_1", "excite_1"),
                  ("normal_0", "excite_1"))
    if any(identical(a, b) for a, b in kill_pairs):
        v.add("FAIL", "expression:kill-ego",
              "excite_0/1 must differ from the calm faces; kills in ego 0/1 are the most "
              "frequent, so reusing a calm face hides the kill reaction. Regenerate "
              "excite_0/1 with an excited open-mouth / bright-eyed expression.")
    else:
        v.add("PASS", "expression:kill-ego", "kill faces differ from the calm faces")

    losses = []
    if all(identical("normal_%d" % i, "normal_1") for i in (2, 3, 4, 5)):
        losses.append("ego 2-5 reuse normal_1 (no further calm expression steps)")
    if all(identical("excite_%d" % i, "excite_1") for i in (2, 3, 4, 5)):
        losses.append("excite 2-5 reuse excite_1 (no further kill feedback)")
    if identical("tired_0", "tired_1"):
        losses.append("tired frames have no blink difference")
    if losses:
        v.add("WARN", "expression:fast-pass",
              "fast-pass reuse losses: " + "; ".join(losses) + ". Tell the user about these; "
              "see prompts.md section 9 for refinement priority")

    if args.report:
        rep = json.loads(Path(args.report).read_text(encoding="utf-8"))
        for name, info in rep.get("cells", {}).items():
            status = str(info.get("status", ""))
            normal = status in ("ok", "generated") or status.startswith("reused:")
            if status == "error":
                v.add("FAIL", "build:" + name,
                      "frame could not be read (%s); check that it is an 8-bit "
                      "non-interlaced PNG" % info.get("source"))
            elif not normal:
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
