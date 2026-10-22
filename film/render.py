"""Render the whole film picture in parallel chunks and join them.

usage: render.py TIMELINE.json OUT.mp4 [workers] [chunks]
"""
import json
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool

from engine import render_range, FPS

if __name__ == "__main__":
    tl_path, out = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else os.cpu_count()
    chunks = int(sys.argv[4]) if len(sys.argv) > 4 else workers * 3
    n = int(math.ceil(json.load(open(tl_path))["duration"] * FPS))
    tmp = os.path.join(os.path.dirname(os.path.abspath(out)), "chunks")
    os.makedirs(tmp, exist_ok=True)
    step = math.ceil(n / chunks)
    jobs = [(tl_path, i, min(n, i + step), os.path.join(tmp, f"part_{k:03d}.mp4"), "shots")
            for k, i in enumerate(range(0, n, step))]
    t0 = time.time()
    with Pool(workers) as pool:
        for k, p in enumerate(pool.imap(render_range, jobs)):
            print(f"chunk {k + 1}/{len(jobs)} done, {time.time() - t0:.0f}s", flush=True)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        for _, _, _, p, _ in jobs:
            f.write("file '" + p.replace("\\", "/") + "'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out],
                   check=True)
    print(f"done: {n} frames in {time.time() - t0:.0f}s -> {out}")
