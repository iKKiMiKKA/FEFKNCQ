#!/usr/bin/env python3
"""Authoritative sprite layout of the STOMPGAME custom character sheet.

Coordinates come from the game's inline source (stompgame index.html), the
official "HOW TO MAKE A STOMPGAME CHARACTER!.txt" in generic.zip and the
generic.zip/settings.json. All coordinates are (x, y, w, h) in the 1024x1024
"giant" texture, origin at top-left.

IMPORTANT: this table is the contract. Do not let an image model invent a
different arrangement; compose the sheet with build_sheet.py instead.
"""

SHEET_W = 1024
SHEET_H = 1024

BASE_URL = "https://ikkimikka.net/stompgame/generic.png"
BASE_SHA256 = "EF952E7FD566464B54053D1610661C85D34339D5082FB49C2BE73EE5E8050F2D"

# Cells an OC may redraw. Order matters: it is the animation frame order.
CELLS = {
    # front paw, 6 frames: 3 rows in column x=0, then 3 rows in column x=160
    "front_0": (0, 0, 160, 256),
    "front_1": (0, 256, 160, 256),
    "front_2": (0, 512, 160, 256),
    "front_3": (160, 0, 160, 256),
    "front_4": (160, 256, 160, 256),
    "front_5": (160, 512, 160, 256),
    # back paw, 5 frames: 3 rows in column x=320, then 2 rows in column x=480
    "back_0": (320, 0, 160, 256),
    "back_1": (320, 256, 160, 256),
    "back_2": (320, 512, 160, 256),
    "back_3": (480, 0, 160, 256),
    "back_4": (480, 256, 160, 256),
    # normal portraits: ego levels 0..5, downward in column x=768
    "normal_0": (768, 0, 128, 128),
    "normal_1": (768, 128, 128, 128),
    "normal_2": (768, 256, 128, 128),
    "normal_3": (768, 384, 128, 128),
    "normal_4": (768, 512, 128, 128),
    "normal_5": (768, 640, 128, 128),
    # excited portraits: ego levels 0..5, downward in column x=896
    "excite_0": (896, 0, 128, 128),
    "excite_1": (896, 128, 128, 128),
    "excite_2": (896, 256, 128, 128),
    "excite_3": (896, 384, 128, 128),
    "excite_4": (896, 512, 128, 128),
    "excite_5": (896, 640, 128, 128),
    # exhausted ("tired") two-frame alternation
    "tired_0": (768, 896, 128, 128),
    "tired_1": (896, 896, 128, 128),
    # end screen banner
    "endscreen": (0, 768, 256, 128),
}

# Consecutive frames whose continuity must be checked to avoid visual jumps.
GROUPS = [
    "front", "back", "normal", "excite", "tired",
]
GROUP_MEMBERS = {
    "front": ["front_%d" % i for i in range(6)],
    "back": ["back_%d" % i for i in range(5)],
    "normal": ["normal_%d" % i for i in range(6)],
    "excite": ["excite_%d" % i for i in range(6)],
    "tired": ["tired_0", "tired_1"],
    "endscreen": ["endscreen"],
}

# Never redraw these: UI chrome and the paw shadow lattice. Their pixels are
# copied verbatim from the official base image by build_sheet.py.
DECOR = {
    "portrait_frame": (640, 0, 128, 128),
    "portrait_bg": (640, 128, 128, 128),
    "intro_flag": (640, 256, 128, 32),
    "shadow_end": (745, 998, 8, 21),
    "shadow_mid": (751, 998, 4, 21),
}

# Reserved empty cells (game never samples them at default settings).
BLANK_CELLS = {
    "back_5_reserved": (480, 512, 160, 256),
    "normal_6_reserved": (768, 768, 128, 128),
    "excite_6_reserved": (896, 768, 128, 128),
}

BG_KEYS = {
    "white": (255, 255, 255),
    "green": (0, 255, 0),
    "black": (0, 0, 0),
    "magenta": (255, 0, 255),
}

# Fast first pass: 10 generated frames. The paws generate front_0 (raised),
# front_2 (descending / near ground), front_3 (touchdown) and front_5 (max
# pressure) plus back_0, so the front paw fall reads clearly: front_1 reuses
# front_0 for the upper-air hold and front_4 reuses front_5 for the ground
# press. The calm column generates two tiers (normal_0 = calm 1, normal_1 =
# calm 2) and the kill column generates two tiers (excite_0 = excited 1,
# excite_1 = excited 2), so ego 0 -> 1 already shows a clear face change on
# both lines. normal_1/excite_1 are seeded from the highest-tier designs
# (normal_5/excite_5) as a quick placeholder; a later detail pass moves those
# two faces back to normal_5/excite_5 and regenerates proper mid-tier faces for
# normal_1/excite_1. Levels 2-5 reuse normal_1 on the calm column and excite_1
# on the kill column. Everything else is copied by build_sheet.py from the same
# group. Adding a file named <cell>.png later automatically overrides its reuse
# entry, so refining details never requires editing this table.
MUST_GENERATE = [
    "front_0",    # raised paw (paw_state=0)
    "front_2",    # descending, near ground (paw_state=2)
    "front_3",    # touchdown (pressure ~0)
    "front_5",    # maximum pressure
    "back_0",     # far paw baseline
    "normal_0",   # calm tier 1 (ego 0 baseline)
    "normal_1",   # calm tier 2 (seeded from the normal_5 design for now)
    "excite_0",   # kill tier 1 (ego 0)
    "excite_1",   # kill tier 2 (seeded from the excite_5 design for now)
    "endscreen",  # banner
]

REUSE_MAP = {
    "front_1": "front_0", "front_4": "front_5",
    "back_1": "back_0", "back_2": "back_0", "back_3": "back_0", "back_4": "back_0",
    "normal_2": "normal_1", "normal_3": "normal_1",
    "normal_4": "normal_1", "normal_5": "normal_1",
    "excite_2": "excite_1", "excite_3": "excite_1",
    "excite_4": "excite_1", "excite_5": "excite_1",
    "tired_0": "normal_0", "tired_1": "normal_0",
}

# Numbering of every cell on the example sheet, for references/numbering.md
# and scripts/make_numbered_map.py. label -> (x, y, w, h, group)
NUMBERED_CELLS = {
    "P01": (0, 0, 160, 256, "P"), "P02": (160, 0, 160, 256, "P"),
    "P03": (320, 0, 160, 256, "P"), "P04": (480, 0, 160, 256, "P"),
    "P05": (0, 256, 160, 256, "P"), "P06": (160, 256, 160, 256, "P"),
    "P07": (320, 256, 160, 256, "P"), "P08": (480, 256, 160, 256, "P"),
    "P09": (0, 512, 160, 256, "P"), "P10": (160, 512, 160, 256, "P"),
    "P11": (320, 512, 160, 256, "P"), "X01": (480, 512, 160, 256, "X"),
    "F01": (768, 0, 128, 128, "F"), "F02": (896, 0, 128, 128, "F"),
    "F03": (768, 128, 128, 128, "F"), "F04": (896, 128, 128, 128, "F"),
    "F05": (768, 256, 128, 128, "F"), "F06": (896, 256, 128, 128, "F"),
    "F07": (768, 384, 128, 128, "F"), "F08": (896, 384, 128, 128, "F"),
    "F09": (768, 512, 128, 128, "F"), "F10": (896, 512, 128, 128, "F"),
    "F11": (768, 640, 128, 128, "F"), "F12": (896, 640, 128, 128, "F"),
    "X02": (768, 768, 128, 128, "X"), "X03": (896, 768, 128, 128, "X"),
    "F13": (768, 896, 128, 128, "F"), "F14": (896, 896, 128, 128, "F"),
    "E01": (0, 768, 256, 128, "E"),
    "U01": (640, 0, 128, 128, "U"),
    "U02": (640, 128, 128, 128, "U"),
    "U03": (640, 256, 128, 32, "U"),
    "U04": (745, 998, 8, 21, "U"),
    "U05": (751, 998, 4, 21, "U"),
}
