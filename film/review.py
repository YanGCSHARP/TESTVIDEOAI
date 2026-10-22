"""Render one frame per shot (at a chosen fraction of the shot) into contact sheets for review.

usage: review.py TIMELINE.json OUT_DIR [fraction] [shot_id ...]
"""
import json
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

from engine import Engine
from shots import SHOTS

tl = json.load(open(sys.argv[1]))
out = sys.argv[2]
frac = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
only = set(sys.argv[4:])
os.makedirs(out, exist_ok=True)
eng = Engine(tl, SHOTS)
tiles, t0 = [], time.time()
for s in tl["shots"]:
    if only and s["id"] not in only:
        continue
    T = s["start"] + (s["end"] - s["start"]) * frac
    surf = eng.render(T)
    a = np.ndarray((1080, 1920, 4), np.uint8, surf.get_data())[..., [2, 1, 0]]
    im = Image.fromarray(a.copy())
    if only:
        im.save(f"{out}/{s['id']}.jpg", quality=90)
    t = im.resize((480, 270))
    ImageDraw.Draw(t).text((8, 6), s["id"], fill=(255, 255, 0))
    tiles.append(t)
print(f"{len(tiles)} frames, {(time.time() - t0) / max(1, len(tiles)):.2f}s/frame incl. plates")
for k in range(0, len(tiles), 12):
    sheet = Image.new("RGB", (1440, 1080))
    for i, t in enumerate(tiles[k:k + 12]):
        sheet.paste(t, ((i % 3) * 480, (i // 3) * 270))
    sheet.save(f"{out}/sheet_{k // 12:02d}.jpg", quality=88)
