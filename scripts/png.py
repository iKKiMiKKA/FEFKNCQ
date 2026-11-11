#!/usr/bin/env python3
"""Minimal PNG reader/writer and image helpers, standard library only.

Supports 8-bit, non-interlaced PNG (color types 0/2/3/4/6). Images are kept
as flat bytearrays of RGBA pixels, width*height*4 bytes.

No Pillow / numpy dependency: the skill must run inside arbitrary AI agents.
"""

import math
import struct
import zlib
from collections import deque

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def read_png(path):
    """Return (width, height, rgba bytearray)."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG file: %s" % path)
    pos = 8
    idat = bytearray()
    plte = b""
    trns = b""
    w = h = bitdepth = colortype = interlace = None
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if tag == b"IHDR":
            w, h, bitdepth, colortype, _comp, _filt, interlace = struct.unpack(">IIBBBBB", body)
        elif tag == b"PLTE":
            plte = body
        elif tag == b"tRNS":
            trns = body
        elif tag == b"IDAT":
            idat += body
        elif tag == b"IEND":
            break
    if w is None or h is None:
        raise ValueError("missing IHDR: %s" % path)
    if bitdepth != 8:
        raise ValueError("only 8-bit PNG is supported (got %s): %s" % (bitdepth, path))
    if interlace != 0:
        raise ValueError("interlaced PNG is not supported: %s" % path)
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(colortype)
    if channels is None:
        raise ValueError("unsupported PNG color type %s: %s" % (colortype, path))

    raw = zlib.decompress(bytes(idat))
    stride = w * channels
    expected = (stride + 1) * h
    if len(raw) < expected:
        raise ValueError("truncated IDAT: %s" % path)
    out = bytearray(w * h * 4)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ftype = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ftype == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 255
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                c = prev[i - channels] if i >= channels else 0
                line[i] = (line[i] + _paeth(a, prev[i], c)) & 255
        elif ftype != 0:
            raise ValueError("unknown PNG filter %s: %s" % (ftype, path))

        base = y * w * 4
        for x in range(w):
            q = x * channels
            if colortype == 6:
                r, g, b, a = line[q], line[q + 1], line[q + 2], line[q + 3]
            elif colortype == 2:
                r, g, b, a = line[q], line[q + 1], line[q + 2], 255
            elif colortype == 0:
                r = g = b = line[q]
                a = 255
            elif colortype == 4:
                r = g = b = line[q]
                a = line[q + 1]
            else:
                idx = line[q]
                if idx * 3 + 3 > len(plte):
                    raise ValueError("bad palette index: %s" % path)
                r, g, b = plte[idx * 3], plte[idx * 3 + 1], plte[idx * 3 + 2]
                a = trns[idx] if idx < len(trns) else 255
            o = base + x * 4
            out[o] = r
            out[o + 1] = g
            out[o + 2] = b
            out[o + 3] = a
        prev = line
    return w, h, out


def write_png(path, w, h, rgba):
    """Write an 8-bit RGBA PNG (filter type 0 on every row)."""
    if len(rgba) != w * h * 4:
        raise ValueError("rgba buffer size mismatch")
    stride = w * 4
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgba[y * stride:(y + 1) * stride]
    png = PNG_SIGNATURE
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def blank(w, h):
    return bytearray(w * h * 4)


def clear_rect(dst, dw, _dh, x, y, w, h):
    """Set a rectangle to fully transparent."""
    row = bytearray(w * 4)
    for yy in range(y, y + h):
        if 0 <= yy < _dh:
            o = (yy * dw + x) * 4
            dst[o:o + w * 4] = row


def paste(dst, dw, dh, src, sw, sh, x, y):
    """Copy src RGBA into dst at (x, y), clipping to dst bounds."""
    for sy in range(sh):
        dy = y + sy
        if dy < 0 or dy >= dh:
            continue
        sx0 = max(0, -x)
        sx1 = min(sw, dw - x)
        if sx1 <= sx0:
            continue
        o = (dy * dw + x + sx0) * 4
        i = (sy * sw + sx0) * 4
        dst[o:o + (sx1 - sx0) * 4] = src[i:i + (sx1 - sx0) * 4]


def crop(src, sw, sh, x, y, w, h):
    out = blank(w, h)
    for sy in range(h):
        yy = y + sy
        if yy < 0 or yy >= sh:
            continue
        for sx in range(w):
            xx = x + sx
            if xx < 0 or xx >= sw:
                continue
            o = (sy * w + sx) * 4
            i = (yy * sw + xx) * 4
            out[o:o + 4] = src[i:i + 4]
    return out


def estimate_bg(rgba, w, h):
    """Estimate a flat background color from the four corners."""
    pts = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
           (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    acc = [0, 0, 0]
    n = 0
    for x, y in pts:
        o = (y * w + x) * 4
        if rgba[o + 3] < 8:
            continue
        acc[0] += rgba[o]
        acc[1] += rgba[o + 1]
        acc[2] += rgba[o + 2]
        n += 1
    if n == 0:
        return None
    return tuple(v // n for v in acc)


def remove_background(rgba, w, h, key=None, tol=38, flood=True):
    """Remove a flat background.

    When flood is True, only pixels connected to the image border and close to
    the key color are removed, so same-colored parts inside the character are
    kept. Returns the number of pixels made transparent.
    """
    if key is None:
        key = estimate_bg(rgba, w, h)
    if key is None:
        return 0
    kr, kg, kb = key[:3]
    d2 = tol * tol * 3

    def close(x, y):
        o = (y * w + x) * 4
        dr = rgba[o] - kr
        dg = rgba[o + 1] - kg
        db = rgba[o + 2] - kb
        return dr * dr + dg * dg + db * db <= d2

    removed = 0
    if not flood:
        for y in range(h):
            for x in range(w):
                o = (y * w + x) * 4
                if rgba[o + 3] > 0 and close(x, y):
                    rgba[o + 3] = 0
                    removed += 1
        return removed

    seen = bytearray(w * h)
    queue = deque()
    for x in range(w):
        queue.append((x, 0))
        queue.append((x, h - 1))
    for y in range(h):
        queue.append((0, y))
        queue.append((w - 1, y))
    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        idx = y * w + x
        if seen[idx]:
            continue
        seen[idx] = 1
        if not close(x, y):
            continue
        o = idx * 4
        if rgba[o + 3] > 0:
            rgba[o + 3] = 0
            removed += 1
        queue.append((x - 1, y))
        queue.append((x + 1, y))
        queue.append((x, y - 1))
        queue.append((x, y + 1))
    return removed


def resize(rgba, sw, sh, tw, th):
    """Bilinear resize to exactly (tw, th)."""
    if (sw, sh) == (tw, th):
        return bytearray(rgba)
    out = blank(tw, th)
    xr = sw / float(tw)
    yr = sh / float(th)
    for y in range(th):
        sy = min(sh - 1, max(0.0, (y + 0.5) * yr - 0.5))
        y0 = int(math.floor(sy))
        y1 = min(sh - 1, y0 + 1)
        fy = sy - y0
        for x in range(tw):
            sx = min(sw - 1, max(0.0, (x + 0.5) * xr - 0.5))
            x0 = int(math.floor(sx))
            x1 = min(sw - 1, x0 + 1)
            fx = sx - x0
            o = (y * tw + x) * 4
            for c in range(4):
                p00 = rgba[(y0 * sw + x0) * 4 + c]
                p10 = rgba[(y0 * sw + x1) * 4 + c]
                p01 = rgba[(y1 * sw + x0) * 4 + c]
                p11 = rgba[(y1 * sw + x1) * 4 + c]
                top = p00 + (p10 - p00) * fx
                bot = p01 + (p11 - p01) * fx
                out[o + c] = int(max(0, min(255, top + (bot - top) * fy + 0.5)))
    return out


def fit(rgba, sw, sh, tw, th, margin=0, anchor="center", max_scale=None):
    """Fit into a (tw, th) transparent canvas, preserving aspect ratio.

    anchor="bottom" puts the subject's bottom edge on the cell's bottom edge.
    The game aligns paws by that edge (see references/layout.md), so a centered
    paw would look like it never reaches the ground.

    max_scale caps the upscale factor (default None = no cap). The back-paw
    cells must stay smaller than the front paw as a far/background foot (C5),
    so they are fit with max_scale=1: a smaller source is kept small instead of
    being blown up to fill the cell, which would erase the 10-15% far-foot
    shrink the artist drew.
    """
    avail_w = max(1, tw - 2 * margin)
    avail_h = max(1, th - 2 * margin)
    scale = min(avail_w / float(sw), avail_h / float(sh))
    if max_scale is not None:
        scale = min(scale, max_scale)
    nw = max(1, int(round(sw * scale)))
    nh = max(1, int(round(sh * scale)))
    small = resize(rgba, sw, sh, nw, nh)
    out = blank(tw, th)
    oy = (th - margin - nh) if anchor == "bottom" else (th - nh) // 2
    paste(out, tw, th, small, nw, nh, (tw - nw) // 2, oy)
    return out


def trim(rgba, w, h, thresh=12):
    """Crop to the visible-pixel bounding box.

    Image models usually center the paw in a square canvas. Trimming first lets
    fit(anchor="bottom") place the actual sole on the cell bottom instead of
    placing the model's empty margin there. Returns (nw, nh, cropped).
    """
    min_x, min_y, max_x, max_y = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if rgba[(y * w + x) * 4 + 3] > thresh:
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
    if max_x < 0:
        return w, h, bytearray(rgba)
    nw, nh = max_x - min_x + 1, max_y - min_y + 1
    return nw, nh, crop(rgba, w, h, min_x, min_y, nw, nh)


def bottom_gap(rgba, w, h, thresh=12):
    """Distance from the last visible row to the bottom edge of the cell."""
    for y in range(h - 1, -1, -1):
        if any(rgba[(y * w + x) * 4 + 3] > thresh for x in range(w)):
            return h - 1 - y
    return h


def bbox_fill(rgba, w, h, thresh=12):
    """Fraction of the visible bounding box that is opaque.

    A cut-out paw/face has transparent holes inside its bounding box (toe gaps,
    outline curves). A flat background plate left behind by a failed background
    removal fills its bounding box almost completely, even after fit() shrinks
    it enough that corner/border heuristics no longer fire.
    """
    min_x, min_y, max_x, max_y = w, h, -1, -1
    opaque = 0
    for y in range(h):
        for x in range(w):
            if rgba[(y * w + x) * 4 + 3] > thresh:
                opaque += 1
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
    if max_x < 0:
        return 0.0
    area = (max_x - min_x + 1) * (max_y - min_y + 1)
    return opaque / float(area)


def cell_stats(rgba, w, h):
    """Return (alpha coverage, mean RGB of opaque pixels, centroid x/y)."""
    n = w * h
    opaque = 0
    sr = sg = sb = 0
    cx = cy = 0
    for i in range(n):
        o = i * 4
        a = rgba[o + 3]
        if a > 12:
            opaque += 1
            sr += rgba[o]
            sg += rgba[o + 1]
            sb += rgba[o + 2]
            x = i % w
            y = i // w
            cx += x
            cy += y
    if opaque == 0:
        return 0.0, (0, 0, 0), (w / 2.0, h / 2.0)
    return (opaque / float(n),
            (sr // opaque, sg // opaque, sb // opaque),
            (cx / float(opaque), cy / float(opaque)))


def corner_opacity(rgba, w, h, k=4):
    """Fraction of opaque pixels in the four k*k corners."""
    pts = []
    for oy in (0, h - k):
        for ox in (0, w - k):
            for y in range(oy, oy + k):
                for x in range(ox, ox + k):
                    pts.append(rgba[(y * w + x) * 4 + 3] > 12)
    return sum(1 for v in pts if v) / float(len(pts)) if pts else 0.0


def border_opacity(rgba, w, h, k=6):
    """Fraction of opaque pixels in the outer k-pixel ring.

    A correctly cut-out subject sits inside the cell with transparent margins.
    A flat background plate (even one with a 2px transparent margin from fit())
    shows up as an opaque ring and is rejected.
    """
    total = 0
    opaque = 0
    for y in range(h):
        for x in range(w):
            if x < k or y < k or x >= w - k or y >= h - k:
                total += 1
                if rgba[(y * w + x) * 4 + 3] > 12:
                    opaque += 1
    return opaque / float(total) if total else 0.0


def color_distance(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))
