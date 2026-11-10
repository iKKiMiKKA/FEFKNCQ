#!/usr/bin/env python3
"""Compose a STOMPGAME custom.png from per-cell images.

Usage:
  python scripts/build_sheet.py --frames frames/ --base generic.png --out custom.png

Frame files are named <cell>.png (see layout.py). Alternatively pass
--manifest frames.json, a mapping of cell name -> image path.

The official base image supplies all UI chrome (portrait frame/background,
intro flag, shadow lattice) and reserved blank cells. Only the character
cells are cleared and replaced, which keeps every coordinate exact.

Unless the user chose an output location (--no-desktop), the finished sheet is
also copied to the desktop so it can be uploaded manually.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import png  # noqa: E402
from layout import (BG_KEYS, BASE_SHA256, CELLS, GROUP_MEMBERS,  # noqa: E402
                    MUST_GENERATE, REUSE_MAP, SHEET_H, SHEET_W)


def desktop_dir():
    """Locate the desktop with the standard library only.

    On Windows the shell API is asked first so OneDrive-redirected desktops
    resolve correctly. STOMP_DESKTOP_DIR overrides detection for sandboxed
    agents that expose a different desktop path.
    """
    override = os.environ.get("STOMP_DESKTOP_DIR")
    if override:
        p = Path(override).expanduser()
        if p.is_dir():
            return p
    if os.name == "nt":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(1024)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 0, None, 0, buf) == 0 and buf.value:
                p = Path(buf.value)
                if p.is_dir():
                    return p
        except Exception:
            pass
    home = Path.home()
    candidates = [home / "Desktop", home / "\u684c\u9762"]
    candidates += sorted(home.glob("OneDrive*/Desktop"))
    for p in candidates:
        if p.is_dir():
            return p
    return None


def copy_to_desktop(out, target):
    """Copy the finished sheet to the desktop without overwriting anything."""
    dest = target / "custom.png"
    if dest.exists():
        stamp = time.strftime("%Y%m%d_%H%M%S")
        dest = target / ("custom_%s.png" % stamp)
        n = 1
        while dest.exists():
            dest = target / ("custom_%s_%d.png" % (stamp, n))
            n += 1
    shutil.copy2(str(out), str(dest))
    return dest


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest().upper()


def resolve_frames(frames_dir, manifest):
    mapping = {}
    if manifest:
        data = json.loads(Path(manifest).read_text(encoding="utf-8"))
        root = Path(manifest).resolve().parent
        for name, rel in data.items():
            if name not in CELLS:
                raise ValueError("unknown cell in manifest: %s" % name)
            p = Path(rel)
            mapping[name] = str(p if p.is_absolute() else (root / p))
    else:
        if not frames_dir:
            raise ValueError("--frames is required when --manifest is absent")
        for name in CELLS:
            mapping[name] = str(Path(frames_dir) / (name + ".png"))
    return mapping


def prepare_cell(path, w, h, bg, tol, flood, margin):
    sw, sh, rgba = png.read_png(path)
    if bg != "none":
        key = BG_KEYS.get(bg) if bg != "auto" else None
        png.remove_background(rgba, sw, sh, key=key, tol=tol, flood=flood)
    return png.fit(rgba, sw, sh, w, h, margin=margin)


def group_baseline(name, mapping):
    for group, members in GROUP_MEMBERS.items():
        if name in members:
            for candidate in members:
                p = mapping.get(candidate)
                if p and Path(p).is_file():
                    return candidate, p
            return None, None
    return None, None


def find_source(name, mapping):
    """Resolve a cell to a real image file.

    A file present for the cell itself always wins. Otherwise REUSE_MAP is
    followed until a generated frame is found. This is what makes the fast
    first pass work, and lets later detail passes override any reused cell
    simply by dropping a new <cell>.png into frames/.
    Returns (root_name, root_path, reused_flag, terminal_name). terminal_name
    is the last cell reached on the reuse chain; when nothing on the chain has
    a file it identifies the correct group to take a baseline from (e.g. an
    excite cell chained to a missing normal frame falls back to the normal
    group instead of the empty excite group).
    """
    cur = name
    seen = set()
    while cur not in seen:
        seen.add(cur)
        path = mapping.get(cur)
        if path and Path(path).is_file():
            return cur, path, cur != name, cur
        nxt = REUSE_MAP.get(cur)
        if not nxt:
            break
        cur = nxt
    return None, None, False, cur


def main():
    ap = argparse.ArgumentParser(description="Build a STOMPGAME custom sheet")
    ap.add_argument("--frames", help="directory containing <cell>.png files")
    ap.add_argument("--manifest", help="JSON mapping of cell name -> image path")
    ap.add_argument("--base", required=True, help="official generic.png base")
    ap.add_argument("--out", default="custom.png")
    ap.add_argument("--report", default=None)
    ap.add_argument("--bg", default="auto", choices=["auto", "none", "white", "green", "black", "magenta"])
    ap.add_argument("--tol", type=int, default=38, help="background color tolerance")
    ap.add_argument("--no-flood", action="store_true", help="remove matching color globally instead of border-connected only")
    ap.add_argument("--margin", type=int, default=2, help="transparent padding inside each cell")
    ap.add_argument("--missing", default="baseline", choices=["error", "baseline", "blank"],
                    help="what to do when a frame file is absent")
    desktop = ap.add_mutually_exclusive_group()
    desktop.add_argument("--desktop", dest="desktop", action="store_true",
                         help="also copy the finished sheet to the desktop (default)")
    desktop.add_argument("--no-desktop", dest="desktop", action="store_false",
                         help="skip the desktop copy when the user chose an output location")
    ap.add_argument("--desktop-dir", default=None,
                    help="override the detected desktop directory")
    ap.set_defaults(desktop=True)
    args = ap.parse_args()

    mapping = resolve_frames(args.frames, args.manifest)
    bw, bh, base_rgba = png.read_png(args.base)
    if (bw, bh) != (SHEET_W, SHEET_H):
        raise ValueError("base must be 1024x1024, got %dx%d" % (bw, bh))
    base_hash = file_sha256(args.base)
    sheet = bytearray(base_rgba)

    report = {
        "base": {"path": str(args.base), "sha256": base_hash,
                 "matches_known": base_hash == BASE_SHA256},
        "options": {"bg": args.bg, "tol": args.tol, "flood": not args.no_flood,
                    "margin": args.margin, "missing": args.missing},
        "cells": {}, "warnings": [], "errors": [],
    }
    if not report["base"]["matches_known"]:
        report["warnings"].append(
            "base image hash differs from the recorded one; the upstream sheet may have changed. "
            "Re-check references/layout.md before using the result.")

    report["must_generate"] = {
        n: bool(mapping.get(n) and Path(mapping[n]).is_file()) for n in MUST_GENERATE
    }

    for name, (x, y, w, h) in CELLS.items():
        png.clear_rect(sheet, SHEET_W, SHEET_H, x, y, w, h)
        root, used, reused, terminal = find_source(name, mapping)
        status = None
        if used is None:
            if args.missing == "error":
                report["errors"].append("no frame and no reuse source for %s" % name)
                report["cells"][name] = {"rect": [x, y, w, h], "status": "missing"}
                continue
            if args.missing == "baseline":
                baseline, used = group_baseline(terminal, mapping)
                if used is None:
                    report["errors"].append("no frame and no baseline for %s" % name)
                    report["cells"][name] = {"rect": [x, y, w, h], "status": "missing"}
                    continue
                status = "baseline:%s" % baseline
                report["warnings"].append("%s filled with baseline %s" % (name, baseline))
            else:
                report["cells"][name] = {"rect": [x, y, w, h], "status": "blank"}
                report["warnings"].append("%s left blank" % name)
                continue
        if status is None:
            status = ("reused:%s" % root) if reused else "generated"
        try:
            cell = prepare_cell(used, w, h, args.bg, args.tol, not args.no_flood, args.margin)
        except Exception as exc:
            report["errors"].append("cannot read %s (%s): %s" % (name, used, exc))
            report["cells"][name] = {"rect": [x, y, w, h], "status": "error", "source": used}
            continue
        png.paste(sheet, SHEET_W, SHEET_H, cell, w, h, x, y)
        cov, mean, centroid = png.cell_stats(cell, w, h)
        report["cells"][name] = {
            "rect": [x, y, w, h], "status": status, "source": used,
            "coverage": round(cov, 4), "mean_rgb": list(mean),
            "centroid": [round(centroid[0], 1), round(centroid[1], 1)],
            "corner_opacity": round(png.corner_opacity(cell, w, h), 4),
        }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    png.write_png(str(out), SHEET_W, SHEET_H, sheet)

    if args.desktop:
        ddir = Path(args.desktop_dir).expanduser() if args.desktop_dir else desktop_dir()
        if ddir is None or not ddir.is_dir():
            report["warnings"].append(
                "desktop directory not found; skipped desktop copy "
                "(pass --desktop-dir or set STOMP_DESKTOP_DIR)")
        elif out.resolve().parent == ddir.resolve():
            report["desktop_copy"] = None  # output is already on the desktop
        else:
            try:
                report["desktop_copy"] = str(copy_to_desktop(out, ddir))
            except Exception as exc:
                report["warnings"].append("desktop copy failed: %s" % exc)

    report_path = Path(args.report) if args.report else out.with_suffix(".report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    gen = sum(1 for c in report["cells"].values() if c["status"] == "generated")
    reused = sum(1 for c in report["cells"].values()
                 if str(c["status"]).startswith("reused:"))
    baseline = sum(1 for c in report["cells"].values()
                   if str(c["status"]).startswith("baseline:"))
    print("wrote %s (%d generated, %d reused, %d baseline, %d/%d cells filled)" %
          (out, gen, reused, baseline, gen + reused + baseline, len(CELLS)))
    missing_must = [n for n, present in report["must_generate"].items() if not present]
    if missing_must:
        print("WARN  must-generate frames not supplied: %s" % ", ".join(missing_must))
    print("report: %s" % report_path)
    if report.get("desktop_copy"):
        print("desktop copy: %s" % report["desktop_copy"])
    for msg in report["warnings"]:
        print("WARN  %s" % msg)
    for msg in report["errors"]:
        print("ERROR %s" % msg)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
