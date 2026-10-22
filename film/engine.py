"""Frame engine: plates + live layers + overlays -> frames -> ffmpeg.

Every shot is authored in a 1920x1080 design space. Its plate is rendered once at 1.12x so the
Ken Burns camera can push in without going soft. Per frame: camera, parallax layers, animated
elements (rain, drops, wipers, lights, props), overlays from the timeline, grain, vignette, dips.
"""
import json
import math
import re
import os
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Optional

import cairo
import numpy as np

from kit import (hx, src, rect, rrect, glow, text, text_w, marker_text, marker_width, surface, finish_plate,
                 grade_layer, Rain, AMBER, RED)

W, H, FPS = 1920, 1080, 30
DW, DH = 1920, 1080
PS = 1.12                      # plate oversampling
PW, PH = int(DW * PS), int(DH * PS)


# ----------------------------------------------------------------- easing

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def ease(x):
    x = clamp(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_in(x):
    return clamp(x) ** 3


def lerp(a, b, u):
    return a + (b - a) * u


def noise1(t, seed=0.0):
    """Smooth pseudo-random value in [-1, 1]."""
    return (math.sin(t * 1.7 + seed) * 0.5 + math.sin(t * 2.9 + seed * 1.3) * 0.3 + math.sin(t * 5.3 + seed * 2.1) * 0.2)


# ----------------------------------------------------------------- shot definition

@dataclass
class Cam:
    z0: float = 1.0
    z1: float = 1.04
    c0: tuple = (960, 540)
    c1: tuple = (960, 540)
    handheld: float = 0.0          # px amplitude of slow handheld drift
    shakes: tuple = ()             # (local_time, amplitude) impacts
    curve: str = "ease"            # ease | linear

    def at(self, t, u):
        k = u if self.curve == "linear" else 0.5 * u + 0.5 * ease(u)
        z = lerp(self.z0, self.z1, k)
        cx, cy = lerp(self.c0[0], self.c1[0], k), lerp(self.c0[1], self.c1[1], k)
        sx = sy = 0.0
        if self.handheld:
            sx += self.handheld * noise1(t * 0.9, 1.0)
            sy += self.handheld * noise1(t * 0.8, 4.0)
        for ts, amp in self.shakes:
            d = t - ts
            if 0 <= d < 0.6:
                e = amp * math.exp(-d * 9)
                sx += e * math.sin(d * 90)
                sy += e * math.cos(d * 77)
        return z, cx, cy, sx, sy


@dataclass
class Shot:
    plate: Callable                         # plate(P) draws into P.bg / P.fg, may fill P.meta
    cam: Cam = field(default_factory=Cam)
    live_bg: Optional[Callable] = None      # live_bg(ctx, f) in design space, under the camera
    live_fg: Optional[Callable] = None      # drawn after the foreground layer
    screen: Optional[Callable] = None       # screen-space extras
    rain: Optional[dict] = None             # {"n":..,"alpha":..,"lit":..} animated rain in the bg layer
    fg_depth: float = 0.35                  # how much the foreground layer follows the camera
    post: dict = field(default_factory=dict)
    fg_post: dict = field(default_factory=dict)


class Plate:
    def __init__(self):
        self.bg_surf, self.bg = surface(PW, PH)
        self.bg.scale(PS, PS)
        self._fg = None
        self.meta = {}

    @property
    def fg(self):
        if self._fg is None:
            self.fg_surf, self._fg = surface(PW, PH)
            self._fg.scale(PS, PS)
        return self._fg


def build_plate(shot, sid):
    P = Plate()
    src(P.bg, "#05080B")
    P.bg.paint()
    shot.plate(P)
    post = {"bloom": 1.0, "thresh": 0.62, "seed": hash(sid) % 1000}
    post.update(shot.post)
    fog = post.pop("fog", None)
    if fog is not None:  # fog given in design-space rows: (colour, y0, y1, peak, falloff, strength)
        from kit import band
        col, y0, y1, pk, fo, st = fog
        post["fog"] = (col, band(PH, PW, y0 * PS, y1 * PS, pk * PS, fo * PS) * st)
    bg = finish_plate(P.bg_surf, **post)
    fg = grade_layer(P.fg_surf, **shot.fg_post) if P._fg is not None else None
    for s in (bg, fg):
        if s is not None:
            s.flush()
    return bg, fg, P.meta


# ----------------------------------------------------------------- per-frame context

class Frame:
    def __init__(self, T, sid, shot_info, meta, scene):
        self.T = T
        self.sid = sid
        self.start, self.end = shot_info["start"], shot_info["end"]
        self.t = T - self.start
        self.dur = self.end - self.start
        self.u = clamp(self.t / self.dur) if self.dur > 0 else 0
        self.meta = meta
        self.scene = scene


class Engine:
    def __init__(self, timeline, shots):
        self.tl = timeline
        self.shots = shots
        self.cache = {}
        self.scene_of = {s["id"]: s for s in timeline["scenes"]}
        self.items = {}
        for v in timeline["vo"]:
            scene, n = v["id"].rsplit("_", 1)
            self.items.setdefault(scene, {})[int(n)] = v["start"]
        self.rain_far = Rain(DW, DH, 520, 1, speed=(1500, 2000), length=(14, 30), alpha=0.11, width=1.0)
        self.rain_near = Rain(DW, DH, 260, 2, speed=(2300, 3000), length=(40, 90), alpha=0.16, width=1.8)
        self.rain_lit = Rain(DW, DH, 520, 3, speed=(1900, 2600), length=(24, 60), alpha=0.32, color="#FFF4E2", width=1.5)
        r = np.random.default_rng(5)
        self.grain = []
        for _ in range(6):
            g = (0.5 + r.normal(0, 0.18, (H // 2, W // 2))).clip(0, 1)
            s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W // 2, H // 2)
            buf = np.ndarray((H // 2, W // 2, 4), np.uint8, s.get_data(), strides=(s.get_stride(), 4, 1))
            v = (g * 255).astype(np.uint8)
            buf[..., 0] = buf[..., 1] = buf[..., 2] = v
            buf[..., 3] = 255
            s.mark_dirty()
            self.grain.append(s)

    def shot_at(self, T):
        shots = self.tl["shots"]
        lo, hi = 0, len(shots) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if shots[mid]["start"] <= T:
                lo = mid
            else:
                hi = mid - 1
        return shots[lo]

    def plate(self, sid):
        if sid not in self.cache:
            shot = self.shots[sid]
            self.cache = {k: v for k, v in self.cache.items() if k in list(self.cache)[-2:]}
            self.cache[sid] = build_plate(shot, sid)
        return self.cache[sid]

    # ------------------------------------------------------------- frame

    def render(self, T):
        info = self.shot_at(T)
        sid = info["id"]
        shot = self.shots[sid]
        bg, fg, meta = self.plate(sid)
        f = Frame(T, sid, info, meta, self.scene_of[info["scene"]])
        f.items = self.items.get(info["scene"], {})
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        ctx.set_antialias(cairo.ANTIALIAS_GOOD)
        src(ctx, "#000000")
        ctx.paint()
        z, cx, cy, sx, sy = shot.cam.at(f.t, f.u)
        f.cam = (z, cx, cy, sx, sy)

        def apply(depth):
            zz = z ** depth if depth != 1 else z
            ccx = DW / 2 + (cx - DW / 2) * depth
            ccy = DH / 2 + (cy - DH / 2) * depth
            sc = (W / DW) * zz
            # keep the view inside the plate
            half_w, half_h = DW / (2 * zz), DH / (2 * zz)
            ccx = clamp(ccx, half_w, DW - half_w)
            ccy = clamp(ccy, half_h, DH - half_h)
            ctx.translate(W / 2 + sx * depth, H / 2 + sy * depth)
            ctx.scale(sc, sc)
            ctx.translate(-ccx, -ccy)

        ctx.save()
        apply(1.0)
        ctx.save()
        ctx.scale(1 / PS, 1 / PS)
        ctx.set_source_surface(bg, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
        ctx.paint()
        ctx.restore()
        if shot.live_bg:
            ctx.save()
            shot.live_bg(ctx, f)
            ctx.restore()
        if shot.rain:
            self.draw_rain(ctx, f, shot.rain)
        self.panel_overlays(ctx, f, "bg")
        ctx.restore()

        if fg is not None or shot.live_fg:
            ctx.save()
            apply(shot.fg_depth)
            if fg is not None:
                ctx.save()
                ctx.scale(1 / PS, 1 / PS)
                ctx.set_source_surface(fg, 0, 0)
                ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
                ctx.paint()
                ctx.restore()
            if shot.live_fg:
                ctx.save()
                shot.live_fg(ctx, f)
                ctx.restore()
            self.panel_overlays(ctx, f, "fg")
            ctx.restore()

        if shot.screen:
            ctx.save()
            ctx.scale(W / DW, H / DH)
            shot.screen(ctx, f)
            ctx.restore()
        ctx.save()
        ctx.scale(W / DW, H / DH)
        self.screen_overlays(ctx, f)
        ctx.restore()
        self.finish(ctx, T)
        surf.flush()
        return surf

    def draw_rain(self, ctx, f, cfg):
        t = f.T
        a = cfg.get("alpha", 1.0)
        self.rain_far.draw(ctx, t, alpha_mul=a)
        if cfg.get("near", True):
            self.rain_near.draw(ctx, t, alpha_mul=a)
        for poly_ in f.meta.get("cones", []):
            def clip(c, p=poly_):
                c.move_to(*p[0])
                for q in p[1:]:
                    c.line_to(*q)
                c.close_path()
            self.rain_lit.draw(ctx, t, clip=clip, alpha_mul=cfg.get("lit", 1.0))

    # ------------------------------------------------------------- overlays

    def overlays_now(self, T):
        return [o for o in self.tl["overlays"] if o["in"] <= T < o["out"]]

    def panel_overlays(self, ctx, f, layer):
        """Text that lives on objects in the shot: phone screens, sign panels, paper."""
        for o in self.overlays_now(f.T):
            if o.get("anchor_shot") and o["anchor_shot"] != f.sid:
                continue
            u_in = prog(f.T, o["in"], o["in"] + 0.35)
            u_out = 1 - prog(f.T, o["out"] - 0.3, o["out"])
            a = min(u_in, u_out)
            if o["style"] == "phone" and "phone" in f.meta and f.meta.get("phone_layer", "bg") == layer:
                x, y, w, h = f.meta["phone"]
                lines = [p for ln in o["text"].split("\n") for p in (ln.split(" · ") if len(ln) > 20 else [ln])]
                size = min(w * 0.085, w * 0.8 / max(text_w(ctx, ln, 100) / 100 * 1.25 for ln in lines))
                rrect(ctx, x + w * 0.06, y + h * 0.36, w * 0.88, size * 1.6 * len(lines) + size, 10, "#0B1A2A", 0.85 * a)
                for i, ln in enumerate(lines):
                    text(ctx, ln, x + w / 2, y + h * 0.36 + size * 1.5 + i * size * 1.6, size * (1.25 if i == 0 else 1.0),
                         "#FFFFFF" if i == 0 else "#A9C4DE", align="center", a=a)
            elif o["style"] in ("marker", "printed") and "panel" in f.meta and f.meta.get("panel_layer", "bg") == layer:
                x, y, w, h = f.meta["panel"]
                lines = o["text"].split("\n")
                rep_m = re.search(r"\s*×(\d+)$", o["text"])
                if rep_m:
                    lines = [o["text"][:rep_m.start()].strip()] * int(rep_m.group(1))
                if o["style"] == "marker":
                    total_chars = sum(len(ln) for ln in lines)
                    reveal = prog(f.T, o["in"], o["in"] + min(3.0, 0.11 * total_chars))
                    n = len(lines)
                    size = min(h / (n * 1.25 + 0.4), max(w / (marker_width(ctx, ln, 100, seed=i) / 100) for i, ln in enumerate(lines)) * 0.86)
                    size = min(size, min(w * 0.86 / (marker_width(ctx, ln, 100, seed=i) / 100) for i, ln in enumerate(lines)))
                    total = total_chars
                    done = 0
                    for i, ln in enumerate(lines):
                        lw = marker_width(ctx, ln, size, seed=i)
                        part = clamp((reveal * total - done) / max(len(ln), 1))
                        marker_text(ctx, ln, x + (w - lw) / 2, y + h / 2 - (n - 1) * size * 0.62 + i * size * 1.24 + size * 0.35,
                                    size, seed=i, reveal=part)
                        done += len(ln)
                else:
                    size = min(h / (len(lines) * 1.5 + 0.6), w * 0.84 / max(text_w(ctx, ln, 100) / 100 for ln in lines))
                    for i, ln in enumerate(lines):
                        text(ctx, ln, x + w / 2, y + h / 2 - (len(lines) - 1) * size * 0.75 + i * size * 1.5 + size * 0.36,
                             size * (1.15 if i == 0 else 1.0), "#141414", align="center", a=a * 0.92)

    def screen_overlays(self, ctx, f):
        T = f.T
        for o in self.overlays_now(T):
            if o["style"] == "rule":
                self.rule_card(ctx, o, T)
            elif o["style"] == "title":
                n = int(max(0, T - o["in"]) / 0.06)
                s = o["text"][:n]
                size = 96
                w = text_w(ctx, o["text"], size, face="Inter Black", bold=False)
                text(ctx, s, DW / 2 - w / 2, DH / 2 + 34, size, "#F2F2F2", face="Inter Black", bold=False)
                if n >= len(o["text"]):
                    rect(ctx, DW / 2 - w / 2, DH / 2 + 70, w * ease_out(prog(T, o["in"] + 0.06 * len(o["text"]), o["in"] + 0.06 * len(o["text"]) + 0.5)), 8, RED)
        hud = f.scene.get("hud")
        if hud:
            a = prog(T, f.scene["start"] + 0.3, f.scene["start"] + 1.0) * (1 - prog(T, f.scene["end"] - 0.6, f.scene["end"] - 0.2))
            if a > 0:
                s = hud["time"] + (f"   ·   {hud['miles_to_exit']} MI TO EXIT" if hud.get("miles_to_exit") is not None else "")
                w = text_w(ctx, s, 30)
                rrect(ctx, DW - w - 110, DH - 112, w + 60, 56, 6, "#05090D", 0.55 * a)
                rect(ctx, DW - w - 110, DH - 112, 5, 56, RED, a)
                text(ctx, s, DW - w - 70, DH - 73, 30, "#DDE6EC", a=a)

    def rule_card(self, ctx, o, T):
        lines = o["text"].split("\n")
        label, line = lines[0], lines[1]
        a = prog(T, o["in"], o["in"] + 0.4) * (1 - prog(T, o["out"] - 0.4, o["out"]))
        slide = (1 - ease_out(prog(T, o["in"], o["in"] + 0.5))) * -40
        x, y = 110 + slide, DH - 300
        w = text_w(ctx, line, 54, face="Inter ExtraBold", bold=False)
        rrect(ctx, x - 30, y - 70, w + 70, 170, 8, "#05090D", 0.62 * a)
        rect(ctx, x - 30, y - 70, 6, 170, RED, a)
        text(ctx, label, x, y - 20, 30, RED, face="Inter ExtraBold", bold=False, a=a)
        n = int(max(0, T - o["in"] - 0.2) / 0.035)
        text(ctx, line[:n], x, y + 50, 54, "#F2F2F2", face="Inter ExtraBold", bold=False, a=a)

    # ------------------------------------------------------------- finish

    def finish(self, ctx, T):
        g = self.grain[int(T * FPS) % len(self.grain)]
        ctx.save()
        ctx.scale(2, 2)
        ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
        ctx.set_source_surface(g, 0, 0)
        ctx.paint_with_alpha(0.22)
        ctx.restore()
        vg = cairo.RadialGradient(W / 2, H / 2, 420, W / 2, H / 2, 1250)
        vg.add_color_stop_rgba(0, 0, 0, 0, 0)
        vg.add_color_stop_rgba(1, 0, 0, 0, 0.5)
        ctx.rectangle(0, 0, W, H)
        ctx.set_source(vg)
        ctx.fill()
        a = self.dip(T)
        if a > 0:
            ctx.rectangle(0, 0, W, H)
            ctx.set_source_rgba(0, 0, 0, a)
            ctx.fill()

    HARD = {"S14", "S15", "S16", "S17"}   # scenes entered with a hard cut (tension)

    def dip(self, T):
        a = 0.0
        sc = self.tl["scenes"]
        for i, s in enumerate(sc):
            if not (s["start"] - 0.5 <= T < s["end"] + 0.5):
                continue
            if i > 0 and s["id"] not in self.HARD and T >= s["start"]:
                a = max(a, 1 - prog(T, s["start"], s["start"] + 0.45))
            if i + 1 < len(sc) and sc[i + 1]["id"] not in self.HARD and T < s["end"]:
                a = max(a, prog(T, s["end"] - 0.45, s["end"]))
        a = max(a, 1 - prog(T, 0, 0.6))
        end = self.tl["duration"]
        a = max(a, prog(T, end - 2.5, end - 0.4))
        return a


# ----------------------------------------------------------------- rendering

def render_range(args):
    timeline_path, i0, i1, out_path, shots_module = args
    import importlib
    tl = json.load(open(timeline_path))
    shots = importlib.import_module(shots_module).SHOTS
    eng = Engine(tl, shots)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-g", "60", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        proc.stdin.write(bytes(eng.render(i / FPS).get_data()))
    proc.stdin.close()
    proc.wait()
    return out_path
