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
