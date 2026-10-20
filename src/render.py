"""Render the picture: frames -> raw BGRA -> ffmpeg (H.264).

usage: render.py video OUT.mp4 [workers]      render the whole timeline
       render.py stills OUTDIR t1 t2 ...       write PNG stills at the given times
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cairo
import numpy as np
from scipy.ndimage import uniform_filter1d

import timeline as tl
from gfx import RED, YELLOW, INK, ease_in_out, prog, fill_rect, src, hx
from scenes import SCENE_FUNCS

W, H, FPS = tl.W, tl.H, tl.FPS
HALF = tl.TRANS_FRAMES / 2 / FPS


def scene_at(t):
    for name, a, b in tl.SCENES:
        if a <= t < b:
            return name, a, b
    return tl.SCENES[-1]


def draw_scene(ctx, name, t):
    ctx.save()
    SCENE_FUNCS[name](ctx, t)
    ctx.restore()


def draw_clipped(ctx, name, t, clip):
    ctx.save()
    clip(ctx)
    ctx.clip()
    draw_scene(ctx, name, t)
    ctx.restore()


def motion_blur(surface, radius):
    if radius < 2:
        return
    surface.flush()
    buf = np.ndarray((H, W, 4), dtype=np.uint8, buffer=surface.get_data())
    blurred = uniform_filter1d(buf.astype(np.float32), size=int(radius) * 2 + 1, axis=1, mode="nearest")
    buf[:] = np.clip(blurred, 0, 255).astype(np.uint8)
    surface.mark_dirty()


def active_cut(t):
    for c, kind in tl.CUTS.items():
        if kind != "smash" and c - HALF <= t < c + HALF:
            return c, kind
    return None, None


def stripes(ctx, x0, x1, skew, base, stripe):
    """Diagonal hazard-stripe band between x0 and x1 (at the top edge)."""
    ctx.save()
    ctx.move_to(x0, 0)
    ctx.line_to(x1, 0)
    ctx.line_to(x1 - skew, H)
    ctx.line_to(x0 - skew, H)
    ctx.close_path()
    ctx.clip()
    fill_rect(ctx, -W, 0, 3 * W, H, base)
    if stripe:
        ctx.set_line_width(46)
        src(ctx, stripe)
        for k in range(-40, 80):
            x = x0 - skew + k * 110
            ctx.move_to(x, H + 50)
            ctx.line_to(x + 600, -550)
            ctx.stroke()
    ctx.restore()


def render_frame(t):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    fill_rect(ctx, 0, 0, W, H, "#000000")
    c, kind = active_cut(t)
    if c is None:
        draw_scene(ctx, scene_at(t)[0], t)
    else:
        a_name = scene_at(c - 1e-3)[0]
        b_name = scene_at(c)[0]
        ta, tb = min(t, c - 1e-3), max(t, c)
        p = (t - (c - HALF)) / (2 * HALF)
        if kind == "whip":
            off = -W * ease_in_out(p)
            for name, tt, ox in ((a_name, ta, off), (b_name, tb, off + W)):
                ctx.save()
                ctx.translate(ox, 0)
                draw_clipped(ctx, name, tt, lambda cc: cc.rectangle(0, 0, W, H))
                ctx.restore()
            speed = math.sin(math.pi * p)  # peaks mid-transition
            motion_blur(surf, 160 * speed)
        else:  # plate wipe: a band sweeps left -> right revealing the next scene
            skew = 260
            bx = -500 + (W + 1100) * ease_in_out(p)
            band = 340
            draw_clipped(ctx, a_name, ta, lambda cc: _quad(cc, bx, W + skew + 10, skew))
            draw_clipped(ctx, b_name, tb, lambda cc: _quad(cc, -skew - 10, bx - band, skew))
            if kind == "wipe":
                stripes(ctx, bx - band, bx, skew, YELLOW, INK)
            else:
                stripes(ctx, bx - band, bx - band * 0.25, skew, RED, None)
                stripes(ctx, bx - band * 0.25, bx, skew, "#1B2631", None)
    vignette(ctx)
    fade = prog(t, *tl.FADE_OUT)
    if fade > 0:
        fill_rect(ctx, 0, 0, W, H, "#000000", fade)
    fade_in = 1 - prog(t, 0.0, 0.4)
    if fade_in > 0:
        fill_rect(ctx, 0, 0, W, H, "#000000", fade_in)
    surf.flush()
    return surf


def _quad(ctx, x0, x1, skew):
    ctx.move_to(x0, 0)
    ctx.line_to(x1, 0)
    ctx.line_to(x1 - skew, H)
    ctx.line_to(x0 - skew, H)
    ctx.close_path()


def vignette(ctx):
    g = cairo.RadialGradient(W / 2, H / 2, 450, W / 2, H / 2, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.42)
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(g)
    ctx.fill()


def render_chunk(args):
    i0, i1, path = args
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
           "-pix_fmt", "yuv420p", "-g", "60", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        surf = render_frame(i / FPS)
        proc.stdin.write(bytes(surf.get_data()))
    proc.stdin.close()
    proc.wait()
    return path


def main():
    mode = sys.argv[1]
    if mode == "stills":
        out = sys.argv[2]
        os.makedirs(out, exist_ok=True)
        for s in sys.argv[3:]:
            t = float(s)
            render_frame(t).write_to_png(os.path.join(out, f"still_{t:05.2f}.png"))
        return
    out = sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else os.cpu_count()
    tmp = os.path.join(os.path.dirname(out) or ".", "chunks")
    os.makedirs(tmp, exist_ok=True)
    n = tl.NFRAMES
    step = math.ceil(n / workers)
    jobs = [(i, min(n, i + step), os.path.join(tmp, f"chunk_{k:02d}.mp4")) for k, i in enumerate(range(0, n, step))]
    with Pool(workers) as pool:
        parts = pool.map(render_chunk, jobs)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", out], check=True)


if __name__ == "__main__":
    main()
