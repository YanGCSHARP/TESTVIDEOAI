"""Shared timeline: every timing used by both the picture and the sound lives here."""
import math

W, H, FPS = 1920, 1080, 30
DURATION = 30.0
NFRAMES = int(DURATION * FPS)

# Voice-over clip start times (seconds); clip lengths come from build/vo.json.
VO_START = [0.6, 10.45, 16.4, 21.7]

# Scene boundaries. A transition of TRANS_FRAMES frames is centred on each cut.
SCENES = [
    ("concord", 0.0, 5.0),
    ("office", 5.0, 10.0),
    ("aftermath", 10.0, 15.7),
    ("coldcase", 15.7, 21.3),
    ("lab", 21.3, 24.0),
    ("map", 24.0, 27.2),
    ("final", 27.2, 30.0),
]
# How each cut is made: whip pan, plate wipe or a hard "smash" cut.
CUTS = {5.0: "whip", 10.0: "smash", 15.7: "whip", 21.3: "whip", 24.0: "wipe", 27.2: "wipe_red"}
TRANS_FRAMES = 7

IMPACT_T = 10.0
TICKS = [5.5 + i for i in range(5)]          # wall clock, stops at the impact
POSTER_TIMES = [16.05, 16.3, 16.55, 16.8]     # posters slap onto the wall
TAPE_T = 15.85                                # police tape snaps taut
STAMP_T = 18.15                               # "COLD CASE" stamp (on "went cold")
FLIP_START, FLIP_END = 18.9, 20.9             # calendar 2008 -> 2025
YEARS = list(range(2008, 2026))
BEEPS = [21.75, 22.35, 22.95]
MATCH_T = 23.3
MAP_LINE = (24.5, 26.3)
FINAL_TEXT_T = 27.55
FADE_OUT = (29.1, 30.0)
RISERS = [(8.0, 10.0), (19.3, 21.3)]


def flip_times():
    """Times at which the calendar shows each next year (ease-in-out spacing)."""
    n = len(YEARS) - 1
    out = []
    for i in range(1, n + 1):
        u = i / n
        u = 0.5 - 0.5 * math.cos(math.pi * u)
        out.append(FLIP_START + u * (FLIP_END - FLIP_START))
    return out


# Typewriter texts: (key, text, start, seconds per char). Clicks are generated from these.
TYPEWRITER = [
    ("city", "CONCORD, NORTH CAROLINA", 1.05, 0.045),
    ("date", "JUNE 13, 2008", 2.45, 0.055),
    ("final", "17 YEARS LATER…", FINAL_TEXT_T, 0.085),
]


def typed(key, t):
    """(visible text, full text) for a typewriter key at time t."""
    for k, text, t0, cps in TYPEWRITER:
        if k == key:
            n = int(max(0.0, t - t0) / cps) + (1 if t >= t0 else 0)
            return text[: max(0, min(len(text), n))], text
    raise KeyError(key)


def type_click_times():
    out = []
    for _, text, t0, cps in TYPEWRITER:
        for i, ch in enumerate(text):
            if ch != " ":
                out.append(t0 + i * cps)
    return out


def whoosh_times():
    return [t for t, kind in CUTS.items() if kind != "smash"]
