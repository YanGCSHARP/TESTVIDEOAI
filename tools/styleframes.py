"""Code-drawn style frames for DO NOT LOWER YOUR WINDOW: composition, palette, light and overlays.

usage: styleframes.py OUT_DIR
These are look-development frames, not final art: the final shots come from an image/video model
driven by the prompts in story.yaml. Everything here is original drawing.
"""
import math
import os
import sys

import cairo
import numpy as np
from scipy.ndimage import gaussian_filter, zoom

W, H = 1920, 1080
rng = np.random.default_rng(11)


# ----------------------------------------------------------------- basics

def hx(c, a=1.0):
    c = c.lstrip("#")
    return (int(c[0:2], 16) / 255, int(c[2:4], 16) / 255, int(c[4:6], 16) / 255, a)


def src(ctx, c, a=1.0):
    ctx.set_source_rgba(*hx(c, a))


def new():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    return surf, ctx


def poly(ctx, pts, c, a=1.0):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    src(ctx, c, a)
    ctx.fill()


def rect(ctx, x, y, w, h, c, a=1.0):
    ctx.rectangle(x, y, w, h)
    src(ctx, c, a)
    ctx.fill()


def rrect(ctx, x, y, w, h, r, c, a=1.0):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()
    src(ctx, c, a)
    ctx.fill()


def circle(ctx, x, y, r, c, a=1.0):
    ctx.new_sub_path()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    src(ctx, c, a)
    ctx.fill()


def vgrad(ctx, x, y, w, h, stops):
    g = cairo.LinearGradient(0, y, 0, y + h)
    for off, c, a in stops:
        g.add_color_stop_rgba(off, *hx(c, a))
    ctx.rectangle(x, y, w, h)
    ctx.set_source(g)
    ctx.fill()


def glow(ctx, x, y, r, c, a=1.0, sx=1.0, sy=1.0):
    """Soft radial light."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sx, sy)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, r)
    g.add_color_stop_rgba(0, *hx(c, a))
    g.add_color_stop_rgba(0.35, *hx(c, a * 0.35))
    g.add_color_stop_rgba(1, *hx(c, 0))
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()


def cone(ctx, x0, y0, pts_far, c, a):
    """Light cone from (x0, y0) to a far edge, fading out."""
    fx = sum(p[0] for p in pts_far) / len(pts_far)
    fy = sum(p[1] for p in pts_far) / len(pts_far)
    g = cairo.LinearGradient(x0, y0, fx, fy)
    g.add_color_stop_rgba(0, *hx(c, a))
    g.add_color_stop_rgba(1, *hx(c, 0))
    ctx.move_to(x0, y0)
    for p in pts_far:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source(g)
    ctx.fill()


def rain(ctx, n, color="#C9D6E2", alpha=(0.06, 0.18), length=(18, 46), angle=0.18, clip=None, width=1.3):
    ctx.save()
    if clip:
        clip(ctx)
        ctx.clip()
    ctx.set_line_width(width)
    for _ in range(n):
        x, y = rng.uniform(-100, W + 100), rng.uniform(-50, H)
        L = rng.uniform(*length)
        ctx.move_to(x, y)
        ctx.line_to(x - L * math.sin(angle), y + L * math.cos(angle))
        src(ctx, color, rng.uniform(*alpha))
        ctx.stroke()
    ctx.restore()


def pines(ctx, base, height, color, density=26, seed=0, jitter=0.35):
    """A ridge of individual spruce silhouettes (tiered triangles) on a solid base."""
    r = np.random.default_rng(seed)
    src(ctx, color)
    ctx.rectangle(-100, base - 4, W + 200, H - base + 104)
    ctx.fill()
    x = -80.0
    while x < W + 80:
        h = height * r.uniform(1 - jitter, 1 + jitter)
        w = h * r.uniform(0.32, 0.42)
        tiers = 5
        for k in range(tiers):
            tb = base - h * (k / tiers) * 0.92
            tw = w * (1 - k / tiers * 0.8) * r.uniform(0.9, 1.1)
            tt = tb - h * 0.34
            ctx.move_to(x - tw / 2, tb)
            ctx.curve_to(x - tw * 0.2, tb - h * 0.08, x - tw * 0.05, tt + h * 0.1, x, tt)
            ctx.curve_to(x + tw * 0.05, tt + h * 0.1, x + tw * 0.2, tb - h * 0.08, x + tw / 2, tb)
            ctx.close_path()
        ctx.fill()
        x += w * r.uniform(0.35, 0.7) * (26 / density)


def drops_on_glass(ctx, n, region=(0, 0, W, H), rmin=3, rmax=11):
    x0, y0, w, h = region
    for _ in range(n):
        x, y, r = x0 + rng.uniform(0, w), y0 + rng.uniform(0, h), rng.uniform(rmin, rmax)
        circle(ctx, x, y, r, "#0A1016", 0.22)
        circle(ctx, x - r * 0.15, y - r * 0.15, r * 0.8, "#9FB3C2", 0.10)
        circle(ctx, x - r * 0.35, y - r * 0.4, r * 0.25, "#EAF2F8", 0.55)
        if rng.random() < 0.18:  # running streak
            ctx.set_line_width(r * 0.6)
            ctx.move_to(x, y)
            ctx.line_to(x + rng.uniform(-6, 6), y + rng.uniform(30, 120))
            src(ctx, "#9FB3C2", 0.08)
            ctx.stroke()


def text(ctx, s, x, y, size, c, face="Inter", weight=cairo.FONT_WEIGHT_BOLD, a=1.0, align="left"):
    ctx.select_font_face(face, cairo.FONT_SLANT_NORMAL, weight)
    ctx.set_font_size(size)
    w = ctx.text_extents(s).x_advance
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    ctx.move_to(x, y)
    src(ctx, c, a)
    ctx.show_text(s)
    return w


def marker_text(ctx, s, x, y, size, seed=0):
    """Hand-written marker look: jittered heavy letters drawn several times."""
    r = np.random.default_rng(seed)
    ctx.select_font_face("Inter Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx = x
    for ch in s:
        ctx.set_font_size(size * r.uniform(0.92, 1.08))
        adv = ctx.text_extents(ch).x_advance
        rot, dy = r.uniform(-0.07, 0.07), r.uniform(-5, 5)
        for k in range(3):
            ctx.save()
            ctx.translate(cx + r.uniform(-1.5, 1.5), y + dy + r.uniform(-1.5, 1.5))
            ctx.rotate(rot)
            ctx.move_to(0, 0)
            src(ctx, "#101010", 0.55)
            ctx.show_text(ch)
            ctx.restore()
        cx += adv * r.uniform(0.9, 1.0) + size * 0.02
    return cx - x


# ----------------------------------------------------------------- overlays

def hud(ctx, time_s, miles=None):
    s = time_s + (f"   ·   {miles} MI TO EXIT" if miles is not None else "")
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(30)
    w = ctx.text_extents(s).x_advance
    rrect(ctx, W - w - 110, H - 112, w + 60, 56, 6, "#05090D", 0.55)
    rect(ctx, W - w - 110, H - 112, 5, 56, "#C0392B")
    text(ctx, s, W - w - 70, H - 73, 30, "#DDE6EC")


def rule_card(ctx, n, line):
    x, y = 110, H - 300
    ctx.select_font_face("Inter ExtraBold", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(54)
    w = ctx.text_extents(line).x_advance
    rrect(ctx, x - 30, y - 70, w + 70, 170, 8, "#05090D", 0.62)
    rect(ctx, x - 30, y - 70, 6, 170, "#C0392B")
    text(ctx, f"RULE {n}", x, y - 20, 30, "#C0392B", face="Inter ExtraBold", weight=cairo.FONT_WEIGHT_NORMAL)
    text(ctx, line, x, y + 50, 54, "#F2F2F2", face="Inter ExtraBold", weight=cairo.FONT_WEIGHT_NORMAL)


# ----------------------------------------------------------------- post

def to_np(surf):
    surf.flush()
    a = np.ndarray((H, W, 4), np.uint8, surf.get_data()).astype(np.float32) / 255
    return a[..., [2, 1, 0]].copy()


def finish(img, bloom=0.9, thresh=0.62, fog=None, grain=0.03, vign=0.55, lift="#0B1520", warm=0.0):
    out = img.copy()
    if fog is not None:  # fog: (color, mask HxW)
        col, mask = fog
        n = gaussian_filter(rng.standard_normal((H // 8, W // 8)), 6)
        n = zoom((n - n.min()) / (np.ptp(n) + 1e-6), 8, order=1)[:H, :W]
        m = (mask * (0.55 + 0.45 * n))[..., None]
        out = out * (1 - m) + np.array(hx(col)[:3]) * m
    if bloom:
        small = zoom(np.maximum(out - thresh, 0), (0.25, 0.25, 1), order=1)
        b1 = gaussian_filter(small, (6, 6, 0))
        b2 = gaussian_filter(small, (22, 22, 0))
        b = zoom(b1 * 0.6 + b2 * 1.4, (H / small.shape[0], W / small.shape[1], 1), order=1)
        out = out + bloom * b[:H, :W]
    lc = np.array(hx(lift)[:3])
    out = lc + out * (1 - lc)  # lifted, tinted shadows
    if warm:
        out[..., 0] *= 1 + warm
        out[..., 2] *= 1 - warm * 0.5
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    out *= (1 - vign * np.clip(d - 0.45, 0, 1) ** 1.6)[..., None]
    out = out / (1 + out * 0.25) * 1.25  # soft shoulder instead of clipping
    out += rng.normal(0, grain, (H, W, 1))
    return np.clip(out, 0, 1)


def overlay(base, draw):
    """Draw crisp UI overlays on top of a finished frame (no bloom/grain)."""
    surf, ctx = new()
    draw(ctx)
    o = to_np(surf)
    surf.flush()
    alpha = np.ndarray((H, W, 4), np.uint8, surf.get_data())[..., 3:4].astype(np.float32) / 255
    # cairo stores premultiplied colour
    return base * (1 - alpha) + o


def save(img, path):
    from PIL import Image
    Image.fromarray((img * 255).astype(np.uint8)).save(path, quality=93)


def ymask(y0, y1, peak, falloff):
    y = np.arange(H, dtype=np.float32)[:, None]
    m = np.clip(1 - np.abs(y - peak) / falloff, 0, 1) * ((y > y0) & (y < y1))
    return np.repeat(m, W, axis=1) * 1.0


# ================================================================= frames

def f1_road():
    """S01_A: the truck alone on a wet two-lane road through the forest."""
    surf, ctx = new()
    vgrad(ctx, 0, 0, W, 700, [(0, "#070C12", 1), (0.7, "#15222D", 1), (1, "#2A3B48", 1)])
    pines(ctx, 600, 260, "#22323D", seed=1)
    pines(ctx, 650, 320, "#18252E", seed=2)
    pines(ctx, 700, 380, "#0F181F", seed=3)
    # road
    vgrad(ctx, 0, 690, W, 260, [(0, "#1A2228", 1), (1, "#0C1115", 1)])
    for x in range(-40, W, 180):
        rect(ctx, x, 812, 100, 7, "#B8962E", 0.55)
    rect(ctx, 0, 742, W, 4, "#6E7A82", 0.35)
    rect(ctx, 0, 905, W, 4, "#6E7A82", 0.35)
    # headlight cone + wet reflections
    cone(ctx, 1440, 660, [(W + 200, 520), (W + 200, 820)], "#FFF1D0", 0.32)
    glow(ctx, 1700, 860, 420, "#FFE9C0", 0.20, sx=1.6, sy=0.25)
    glow(ctx, 470, 860, 160, "#FF3B2F", 0.25, sx=1.4, sy=0.25)
    truck_side(ctx, 470, 720)
    glow(ctx, 1436, 662, 70, "#FFF6E0", 1.0)
    glow(ctx, 474, 690, 40, "#FF2A1F", 0.9)
    rain(ctx, 1600)
    rain(ctx, 900, color="#FFF4DD", alpha=(0.15, 0.4), clip=lambda c: (c.move_to(1440, 660), c.line_to(W + 200, 480),
                                                                       c.line_to(W + 200, 860), c.close_path()))
    # foreground guardrail and grass
    for x in range(-20, W, 240):
        rect(ctx, x, 950, 18, 130, "#05080B")
    rect(ctx, 0, 960, W, 22, "#0A0F13")
    pines(ctx, H + 40, 70, "#030507", seed=9, jitter=0.6)
    img = to_np(surf)
    fog = ("#3A4C5A", ymask(450, 760, 650, 160) * 0.55)
    img = finish(img, bloom=1.1, fog=fog)
    return overlay(img, lambda c: hud(c, "2:01 AM"))


def truck_side(ctx, x, ground):
    """Side view of the unbranded white box truck, front to the right."""
    bx0, bx1, top = x, x + 690, ground - 300
    vgrad(ctx, bx0, top, bx1 - bx0, 250, [(0, "#C9D3DA", 1), (1, "#7F8C96", 1)])
    for k in range(1, 6):
        rect(ctx, bx0 + k * 115, top + 6, 3, 238, "#8C98A1", 0.6)
    rect(ctx, bx0, top + 238, bx1 - bx0, 14, "#3E464C")
    for mx in (bx0 + 12, bx1 - 22):
        circle(ctx, mx, top + 10, 7, "#FFB23A")
    # cab
    cx0 = bx1 + 12
    poly(ctx, [(cx0, ground - 70), (cx0, top + 30), (cx0 + 150, top + 30), (cx0 + 200, top + 140),
               (cx0 + 270, top + 160), (cx0 + 285, ground - 70)], "#B9C4CC")
    poly(ctx, [(cx0 + 18, top + 50), (cx0 + 140, top + 50), (cx0 + 180, top + 135), (cx0 + 18, top + 135)], "#111A21")
    glow(ctx, cx0 + 90, top + 120, 90, "#E39A3B", 0.35)
    circle(ctx, cx0 + 70, top + 92, 26, "#05090C")      # driver silhouette (far side)
    rect(ctx, cx0 + 40, top + 112, 60, 30, "#05090C")
    for k in range(3):
        circle(ctx, cx0 + 30 + k * 40, top + 26, 5, "#FFB23A")
    rect(ctx, cx0 + 150, top + 60, 8, 70, "#0A0D10")   # mirror arm
    rrect(ctx, cx0 + 156, top + 60, 22, 60, 4, "#0A0D10")
    rect(ctx, bx0, ground - 70, cx0 + 285 - bx0, 18, "#2A3136")
    for wx in (bx0 + 110, bx0 + 200, cx0 + 190):
        circle(ctx, wx, ground - 40, 46, "#07090B")
        circle(ctx, wx, ground - 40, 20, "#4C555B")


def f2_sign():
    """S02_B: the temporary sign at the town limit, rewritten in marker."""
    surf, ctx = new()
    vgrad(ctx, 0, 0, W, H, [(0, "#060A0E", 1), (0.6, "#121C24", 1), (1, "#0B1115", 1)])
    pines(ctx, 720, 330, "#16222A", seed=4)
    for x, y in ((240, 640), (300, 610), (380, 650), (170, 660)):   # distant plant lights
        glow(ctx, x, y, 40, "#F0A24A", 0.8)
    rect(ctx, 0, 760, W, 320, "#0C1216")
    glow(ctx, 1080, 840, 520, "#F6E6C4", 0.18, sx=1.3, sy=0.35)
    # sign
    px, py, pw, ph = 720, 260, 760, 470
    for lx in (px + 140, px + pw - 160):
        rect(ctx, lx, py + ph - 10, 16, 330, "#2B3236")
    rect(ctx, px + pw / 2 - 6, py - 90, 12, 90, "#2B3236")
    rrect(ctx, px + pw / 2 - 70, py - 120, 140, 46, 10, "#1E2428")
    cone(ctx, px + pw / 2, py - 80, [(px - 120, py + ph + 40), (px + pw + 120, py + ph + 40)], "#FFF2D8", 0.18)
    vgrad(ctx, px, py, pw, ph, [(0, "#F2EEE4", 1), (1, "#C9C6BD", 1)])
    rect(ctx, px, py, pw, ph, "#000000", 0.0)
    # blacked-out printed message at the bottom
    for k in range(3):
        rect(ctx, px + 70, py + 330 + k * 34, pw - 140 - k * 90, 18, "#9A988F", 0.8)
    ctx.set_line_width(14)
    r = np.random.default_rng(5)
    for k in range(26):
        y = py + 320 + r.uniform(0, 110)
        ctx.move_to(px + 60 + r.uniform(0, 40), y)
        ctx.curve_to(px + 250, y + r.uniform(-20, 20), px + 450, y + r.uniform(-20, 20), px + pw - 80, y + r.uniform(-15, 15))
        src(ctx, "#141414", 0.75)
        ctx.stroke()
    for tx, ty, tr in ((px + 610, py + 120, 26), (px + 90, py + 220, 18), (px + 520, py + 290, 14)):  # tears
        poly(ctx, [(tx, ty), (tx + tr, ty + tr * 0.4), (tx + tr * 0.6, ty + tr * 1.2), (tx - tr * 0.3, ty + tr * 0.7)], "#6F6C64")
    marker_text(ctx, "KEEP VEHICLE", px + 95, py + 150, 82, seed=1)
    marker_text(ctx, "WINDOWS CLOSED", px + 55, py + 268, 80, seed=2)
    glow(ctx, px + pw / 2, py - 96, 90, "#FFF4DC", 1.0)
    rain(ctx, 1200)
    rain(ctx, 900, color="#FFF6E6", alpha=(0.2, 0.45), clip=lambda c: (c.move_to(px + pw / 2, py - 80),
         c.line_to(px - 150, py + ph + 60), c.line_to(px + pw + 150, py + ph + 60), c.close_path()))
    img = finish(to_np(surf), bloom=0.8, thresh=0.75, fog=("#2E3D49", ymask(500, 800, 690, 140) * 0.5))
    return overlay(img, lambda c: hud(c, "2:05 AM"))


def f3_station():
    """S05_F: the lit, empty gas station from the dark road, with the RULE 1 card."""
    surf, ctx = new()
    vgrad(ctx, 0, 0, W, H, [(0, "#05080C", 1), (0.55, "#0E161C", 1), (1, "#080C10", 1)])
    pines(ctx, 520, 200, "#0E161C", seed=6)
    # apron + light pool
    poly(ctx, [(160, 690), (1820, 690), (W, 900), (0, 900)], "#1B2328")
    glow(ctx, 860, 720, 760, "#E9F3F0", 0.30, sx=1.0, sy=0.28)
    # store
    rect(ctx, 1260, 380, 560, 330, "#2A3036")
    vgrad(ctx, 1290, 430, 500, 230, [(0, "#E7F5F1", 1), (1, "#BFD9D4", 1)])
    for k in range(4):
        rect(ctx, 1300 + k * 120, 470, 90, 14, "#8AA19C")
        rect(ctx, 1300 + k * 120, 540, 90, 14, "#8AA19C")
    rect(ctx, 1520, 430, 6, 230, "#2A3036")
    # canopy
    poly(ctx, [(240, 330), (1300, 330), (1300, 400), (240, 400)], "#C9CBC6")
    rect(ctx, 240, 352, 1060, 26, "#9B2F2A")
    rect(ctx, 250, 400, 1040, 16, "#F4FBFF")
    for k in range(5):
        glow(ctx, 330 + k * 220, 410, 120, "#F4FBFF", 0.9, sx=1.4, sy=0.5)
    for cx in (360, 1180):
        rect(ctx, cx, 416, 24, 290, "#B9BDB8")
    # pumps
    for k, x in enumerate((470, 650, 860, 1040)):
        rect(ctx, x, 560, 64, 140, "#D7DAD6")
        rect(ctx, x + 10, 580, 44, 30, "#6FC3B3")
        rect(ctx, x - 10, 696, 84, 12, "#7F8580")
    # blue sedan, driver door open, at the first pump
    sx, sy = 260, 700
    poly(ctx, [(sx, sy - 40), (sx + 30, sy - 80), (sx + 110, sy - 120), (sx + 270, sy - 120), (sx + 340, sy - 80),
               (sx + 400, sy - 70), (sx + 400, sy - 25), (sx, sy - 25)], "#1C2E52")
    poly(ctx, [(sx + 125, sy - 112), (sx + 260, sy - 112), (sx + 320, sy - 80), (sx + 120, sy - 80)], "#0B1220")
    glow(ctx, sx + 210, sy - 95, 70, "#FFE7B0", 0.7)
    poly(ctx, [(sx + 120, sy - 80), (sx + 205, sy - 80), (sx + 245, sy - 135), (sx + 245, sy - 30), (sx + 205, sy - 25)],
         "#243A66")   # open door
    for wx in (sx + 80, sx + 320):
        circle(ctx, wx, sy - 22, 30, "#050709")
    # reflections on wet apron
    for x in (330, 550, 770, 990, 1210, 1540):
        glow(ctx, x, 800, 90, "#E6F2F0", 0.22, sx=0.35, sy=1.4)
    # road + tail lights leaving
    rect(ctx, 0, 900, W, 180, "#0A0E11")
    glow(ctx, 120, 960, 60, "#FF2A1F", 0.9, sx=1.4, sy=0.6)
    glow(ctx, 230, 960, 60, "#FF2A1F", 0.9, sx=1.4, sy=0.6)
    rain(ctx, 1500)
    rain(ctx, 900, color="#F2FAFF", alpha=(0.15, 0.35), clip=lambda c: c.rectangle(240, 410, 1060, 300))
    img = finish(to_np(surf), bloom=1.0, thresh=0.7, fog=("#26333C", ymask(300, 760, 560, 260) * 0.35))
    return overlay(img, lambda c: (rule_card(c, 1, "A lit building is not an open building."), hud(c, "2:13 AM")))


def windshield_frame(ctx):
    """Driver's view: left A-pillar, roof edge, curved dashboard, gauges and phone mount."""
    poly(ctx, [(0, 0), (190, 0), (40, H), (0, H)], "#040609")
    ctx.move_to(0, 0)
    ctx.line_to(W, 0)
    ctx.line_to(W, 40)
    ctx.curve_to(W * 0.6, 70, W * 0.3, 70, 0, 50)
    ctx.close_path()
    src(ctx, "#040609")
    ctx.fill()
    ctx.move_to(0, 905)
    ctx.curve_to(W * 0.3, 860, W * 0.7, 850, W, 880)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    src(ctx, "#07090C")
    ctx.fill()
    for k, x in enumerate((330, 450)):
        circle(ctx, x, 985, 48, "#120D06")
        glow(ctx, x, 985, 66, "#E39A3B", 0.35)
        ctx.set_line_width(4)
        ctx.move_to(x, 985)
        ctx.line_to(x + 30 * math.cos(-0.5 - k), 985 + 30 * math.sin(-0.5 - k))
        src(ctx, "#FFB04A", 0.9)
        ctx.stroke()
    rrect(ctx, 1500, 880, 150, 260, 16, "#0B0E12")
    rect(ctx, 1511, 893, 128, 240, "#0E2A44")
    glow(ctx, 1575, 960, 150, "#3E8BD6", 0.3)
    ctx.set_line_width(6)
    ctx.move_to(1530, 1080)
    ctx.curve_to(1550, 1000, 1600, 985, 1590, 910)
    src(ctx, "#5DB2FF", 0.9)
    ctx.stroke()


def woman(ctx, x, y, s):
    """Standing woman seen from behind three-quarters, wet sweater, arms straight; feet at (x, y)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    # legs
    for dx, c in ((-16, "#24282C"), (14, "#1E2226")):
        ctx.move_to(dx - 13, -230)
        ctx.curve_to(dx - 14, -150, dx - 10, -60, dx - 8, -4)
        ctx.line_to(dx + 9, -4)
        ctx.curve_to(dx + 10, -70, dx + 13, -150, dx + 13, -230)
        ctx.close_path()
        src(ctx, c)
        ctx.fill()
        rrect(ctx, dx - 12, -10, 26, 12, 5, "#0C0E10")
    # rim light (lamp above-left): offset copy of the torso
    for off, col in (((-3, -3), "#F7D7A6"), ((0, 0), "#7E7668")):
        ox, oy = off
        ctx.move_to(-58 + ox, -400 + oy)
        ctx.curve_to(-70 + ox, -340 + oy, -62 + ox, -280 + oy, -50 + ox, -220 + oy)
        ctx.line_to(50 + ox, -220 + oy)
        ctx.curve_to(60 + ox, -290 + oy, 66 + ox, -350 + oy, 56 + ox, -400 + oy)
        ctx.curve_to(30 + ox, -418 + oy, -30 + ox, -418 + oy, -58 + ox, -400 + oy)
        ctx.close_path()
        src(ctx, col)
        ctx.fill()
    # wet patches, darker toward the hem and shoulders
    vgrad(ctx, -60, -410, 125, 190, [(0, "#5A5348", 0.85), (0.4, "#7E7668", 0.0), (1, "#4E483F", 0.7)])
    # arms hanging straight
    for sx in (-1, 1):
        ctx.move_to(sx * 56, -396)
        ctx.curve_to(sx * 74, -340, sx * 74, -280, sx * 68, -222)
        ctx.line_to(sx * 50, -222)
        ctx.curve_to(sx * 54, -290, sx * 52, -350, sx * 44, -390)
        ctx.close_path()
        src(ctx, "#716A5D")
        ctx.fill()
        circle(ctx, sx * 59, -214, 9, "#B79A86")
    # neck, head and wet hair hanging over the face
    rect(ctx, -9, -430, 18, 20, "#9C8574")
    circle(ctx, 2, -462, 34, "#2B2421")
    ctx.move_to(-34, -470)
    ctx.curve_to(-40, -430, -36, -400, -26, -386)
    ctx.line_to(30, -388)
    ctx.curve_to(40, -410, 40, -440, 34, -470)
    ctx.close_path()
    src(ctx, "#241E1B")
    ctx.fill()
    ctx.set_line_width(3)
    ctx.arc(2, -462, 34, math.pi * 1.05, math.pi * 1.55)
    src(ctx, "#F7D7A6", 0.7)
    ctx.stroke()
    ctx.restore()


def worker(ctx, x, y, s, arm_up=True):
    """Backlit man in a disposable coverall, hood down, mask and goggles; feet at (x, y)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    suit, shade_ = "#C9CFCC", "#8F9693"
    for rimpass in (True, False):
        o = 4 if rimpass else 0
        col = "#FFFFFF" if rimpass else suit
        # legs (baggy coverall)
        for dx in (-26, 24):
            ctx.move_to(dx - 24 - o, -250)
            ctx.curve_to(dx - 30 - o, -160, dx - 24 - o, -60, dx - 20 - o, -6)
            ctx.line_to(dx + 20 + o, -6)
            ctx.curve_to(dx + 24 + o, -70, dx + 26 + o, -170, dx + 22 + o, -250)
            ctx.close_path()
            src(ctx, col)
            ctx.fill()
        # torso
        ctx.move_to(-70 - o, -440 - o)
        ctx.curve_to(-88 - o, -380, -80 - o, -300, -62 - o, -236)
        ctx.line_to(62 + o, -236)
        ctx.curve_to(80 + o, -300, 88 + o, -380, 70 + o, -440 - o)
        ctx.curve_to(40, -462 - o, -40, -462 - o, -70 - o, -440 - o)
        ctx.close_path()
        src(ctx, col)
        ctx.fill()
        # down arm (left of frame)
        ctx.move_to(-66 - o, -432)
        ctx.curve_to(-96 - o, -370, -98 - o, -300, -90 - o, -246)
        ctx.line_to(-66 + o, -246)
        ctx.curve_to(-70 + o, -310, -64 + o, -370, -50 + o, -420)
        ctx.close_path()
        src(ctx, col)
        ctx.fill()
        # raised arm: shoulder -> elbow -> hand, palm out
        if arm_up:
            ctx.save()
            ctx.translate(58, -430)
            ctx.rotate(0.35)
            rrect(ctx, -20 - o, -190 - o, 40 + 2 * o, 200 + 2 * o, 20, col)
            ctx.restore()
    rect(ctx, -4, -440, 8, 200, "#AEB4B1", 0.6)                     # zip line
    # gloves
    circle(ctx, -78, -236, 16, "#3D6FB5")
    if arm_up:
        hx_, hy_ = 58 + 180 * math.sin(0.35), -430 - 180 * math.cos(0.35)
        rrect(ctx, hx_ - 22, hy_ - 40, 44, 50, 14, "#3D6FB5")
        for k in range(4):
            rrect(ctx, hx_ - 20 + k * 11, hy_ - 64, 9, 30, 4, "#3D6FB5")
    # head: face in shadow, white mask, goggles catching the floodlight
    circle(ctx, 0, -500, 46, "#151A1E")
    ctx.arc(0, -500, 46, math.pi * 1.1, math.pi * 1.9)
    ctx.set_line_width(4)
    src(ctx, "#FFFFFF", 0.8)
    ctx.stroke()
    rrect(ctx, -32, -496, 64, 34, 14, "#E6EAE8")
    rrect(ctx, -30, -522, 60, 16, 7, "#6E8494", 0.85)
    rect(ctx, -24, -519, 18, 4, "#FFFFFF", 0.8)
    ctx.restore()


def f4_crosswalk():
    """S08_A: the woman at the crosswalk, seen through the wet windshield."""
    surf, ctx = new()
    vgrad(ctx, 0, 0, W, H, [(0, "#04070A", 1), (0.5, "#0F181F", 1), (1, "#0A0F13", 1)])
    # buildings
    rect(ctx, 0, 250, 700, 420, "#10181E")
    rect(ctx, 760, 300, 480, 370, "#131C22")
    rect(ctx, 1280, 220, 700, 450, "#0E151A")
    vgrad(ctx, 860, 420, 300, 170, [(0, "#CFE6DD", 1), (1, "#9CC3B7", 1)])     # laundromat
    for k in range(4):
        circle(ctx, 900 + k * 70, 540, 24, "#7BA59A")
    rect(ctx, 990, 450, 40, 120, "#0B1013")                                    # silhouette inside
    circle(ctx, 1010, 445, 20, "#0B1013")
    # street + crosswalk
    poly(ctx, [(0, 690), (W, 690), (W, 880), (0, 880)], "#141B20")
    for k in range(7):
        x0 = 520 + k * 130
        poly(ctx, [(x0, 700), (x0 + 70, 700), (x0 + 110 - k * 4, 860), (x0 + 10 - k * 4, 860)], "#9AA3A6", 0.55)
    # streetlight + woman on right curb
    rect(ctx, 1560, 160, 14, 540, "#151B1F")
    rect(ctx, 1490, 150, 90, 16, "#151B1F")
    glow(ctx, 1500, 172, 70, "#F7C98A", 1.0)
    cone(ctx, 1500, 172, [(1300, 720), (1720, 720)], "#F7C98A", 0.22)
    glow(ctx, 1500, 700, 260, "#F7C98A", 0.25, sx=1.3, sy=0.3)
    poly(ctx, [(1180, 700), (W, 700), (W, 740), (1150, 740)], "#2A3338")      # curb
    woman(ctx, 1470, 728, 1.12)
    # walk signal
    rect(ctx, 1390, 470, 10, 230, "#151B1F")
    rrect(ctx, 1370, 430, 54, 60, 6, "#0A0D10")
    circle(ctx, 1397, 446, 6, "#F4F7F2")
    rect(ctx, 1393, 452, 8, 20, "#F4F7F2")
    glow(ctx, 1397, 460, 40, "#F4F7F2", 0.6)
    # bus shelter with a figure
    rect(ctx, 220, 520, 300, 12, "#2A3238")
    rect(ctx, 220, 530, 300, 170, "#3E5361", 0.25)
    rect(ctx, 360, 570, 34, 120, "#06090B")
    circle(ctx, 377, 560, 17, "#06090B")
    rain(ctx, 1300)
    windshield_frame(ctx)
    drops_on_glass(ctx, 260, (80, 60, W - 160, 800))
    ctx.set_line_width(14)                                                   # wiper at rest
    ctx.move_to(300, 870)
    ctx.line_to(1100, 830)
    src(ctx, "#030405")
    ctx.stroke()
    img = finish(to_np(surf), bloom=1.0, thresh=0.65, fog=("#22303A", ymask(200, 720, 560, 260) * 0.3))
    return overlay(img, lambda c: hud(c, "2:23 AM", 2.9))


def f5_checkpoint():
    """S12_C: floodlit checkpoint, the suited worker raising one arm."""
    surf, ctx = new()
    vgrad(ctx, 0, 0, W, H, [(0, "#06090D", 1), (0.6, "#141C22", 1), (1, "#0B0F12", 1)])
    pines(ctx, 560, 220, "#0F171D", seed=8)
    rect(ctx, 0, 600, W, 480, "#11171B")
    glow(ctx, 960, 760, 900, "#F4F8FF", 0.22, sx=1.2, sy=0.3)
    # vehicles behind the gate, doors open
    rect(ctx, 1150, 470, 360, 170, "#C5CBCF")                  # utility van
    rect(ctx, 1150, 470, 70, 170, "#0C1013")
    poly(ctx, [(1150, 480), (1105, 470), (1105, 640), (1150, 630)], "#AEB5BA")
    poly(ctx, [(600, 520), (880, 520), (900, 560), (900, 640), (600, 640)], "#14181C")   # SUV
    poly(ctx, [(720, 530), (680, 500), (680, 640), (720, 620)], "#1C2126")
    # light towers
    for tx in (470, 1520):
        rect(ctx, tx - 6, 190, 12, 460, "#20272C")
        rect(ctx, tx - 80, 175, 160, 50, "#20272C")
        for k in range(4):
            glow(ctx, tx - 60 + k * 40, 200, 34, "#FFFFFF", 1.0)
        glow(ctx, tx, 200, 380, "#EAF2FF", 0.55)
        cone(ctx, tx, 205, [(tx - 520, 900), (tx + 520, 900)], "#EAF2FF", 0.12)
    # barriers and gate arm
    for k, x in enumerate((200, 420, 1460, 1680)):
        poly(ctx, [(x, 720), (x + 200, 720), (x + 180, 660), (x + 20, 660)], "#9DA3A4")
        rect(ctx, x, 720, 200, 26, "#7E8485")
    for k in range(10):
        rect(ctx, 640 + k * 72, 640, 72, 26, "#C0392B" if k % 2 == 0 else "#E8E8E2")
    rect(ctx, 620, 630, 26, 100, "#30363A")
    worker(ctx, 1010, 790, 0.95)
    rain(ctx, 1200)
    for tx in (470, 1520):
        rain(ctx, 700, color="#FFFFFF", alpha=(0.2, 0.5), clip=lambda c, tx=tx: (
            c.move_to(tx, 205), c.line_to(tx - 520, 900), c.line_to(tx + 520, 900), c.close_path()))
    windshield_frame(ctx)
    drops_on_glass(ctx, 220, (80, 60, W - 160, 800))
    img = finish(to_np(surf), bloom=1.3, thresh=0.6, fog=("#2C3944", ymask(150, 760, 420, 380) * 0.35))
    return overlay(img, lambda c: hud(c, "2:38 AM", 0.4))


def gloved_finger(ctx, x, top, length, width, torn=False, curl=0.0, flat=None):
    """A fingertip hooked over the glass edge, seen from inside: knuckle at top, tip pointing down."""
    ctx.save()
    ctx.translate(x, top)
    ctx.rotate(curl)
    base, dark, light = "#3567AE", "#244C86", "#7FA6DE"
    ctx.move_to(-width / 2, -26)
    ctx.curve_to(-width / 2 - 2, length * 0.5, -width / 2 + 2, length - width * 0.3, 0, length)
    ctx.curve_to(width / 2 - 2, length - width * 0.3, width / 2 + 2, length * 0.5, width / 2, -26)
    ctx.curve_to(width / 4, -40, -width / 4, -40, -width / 2, -26)
    ctx.close_path()
    if flat:
        src(ctx, flat, 0.45)
        ctx.fill()
        ctx.restore()
        return
    src(ctx, base)
    ctx.fill_preserve()
    g = cairo.LinearGradient(-width / 2, 0, width / 2, 0)
    g.add_color_stop_rgba(0, *hx(light, 0.55))
    g.add_color_stop_rgba(0.35, *hx(base, 0.0))
    g.add_color_stop_rgba(1, *hx(dark, 0.85))
    ctx.set_source(g)
    ctx.fill()
    for k in range(3):  # glove wrinkles at the knuckle
        ctx.move_to(-width * 0.35, 6 + k * 9)
        ctx.curve_to(-width * 0.1, 10 + k * 9, width * 0.1, 10 + k * 9, width * 0.35, 6 + k * 9)
        ctx.set_line_width(2)
        src(ctx, dark, 0.7)
        ctx.stroke()
    if torn:  # nitrile split open, skin showing, finger bent at the joint
        ctx.move_to(-width * 0.42, length * 0.45)
        for j in range(7):
            ctx.line_to(-width * 0.42 + j * width * 0.14, length * 0.45 + (7 if j % 2 else -5))
        ctx.line_to(width * 0.36, length * 0.78)
        ctx.curve_to(width * 0.1, length * 0.9, -width * 0.2, length * 0.9, -width * 0.4, length * 0.75)
        ctx.close_path()
        src(ctx, "#B99683")
        ctx.fill()
    ctx.restore()


def f6_gap():
    """S16_G: one inch of open window and four gloved fingertips."""
    gy = 300
    # background: outside, through the glass, heavily out of focus
    surf, ctx = new()
    vgrad(ctx, 0, 0, W, H, [(0, "#101820", 1), (1, "#06090C", 1)])
    glow(ctx, 1500, 340, 520, "#F1F6FF", 0.9)
    glow(ctx, 330, 380, 300, "#F1F6FF", 0.45)
    for bx, by, br in ((1400, 300, 60), (1560, 280, 60), (1480, 420, 40), (280, 360, 45)):
        circle(ctx, bx, by, br, "#FFFFFF", 0.5)
    worker(ctx, 760, 1350, 2.1, arm_up=False)
    bg = to_np(surf) * 0.42
    lights, lctx = new()
    glow(lctx, 1500, 340, 520, "#F1F6FF", 0.9)
    for bx, by, br in ((1400, 300, 60), (1560, 280, 60), (1480, 420, 40)):
        circle(lctx, bx, by, br, "#FFFFFF", 0.5)
    bg = comp(bg, lights)
    bg = gaussian_filter(bg, (16, 16, 0))
    rain_s, rctx = new()
    rain(rctx, 1400, color="#FFFFFF", alpha=(0.12, 0.35), length=(20, 60))
    bg = comp(bg, rain_s)
    # foreground: frame, gap, fingers, glass, door
    fg, ctx = new()
    rect(ctx, 0, 0, W, 205, "#030406")
    rect(ctx, 0, 205, W, 34, "#101317")
    rect(ctx, 0, 236, W, 3, "#2A2F35")
    rect(ctx, 0, 239, W, gy - 239, "#020203", 0.92)
    rain(ctx, 220, color="#DDE8F2", alpha=(0.35, 0.7), length=(8, 24), clip=lambda c: c.rectangle(0, 239, W, gy - 239))
    # glass tint and top edge
    rect(ctx, 0, gy, W, H - gy, "#9DB3C4", 0.06)
    rect(ctx, 0, gy, W, 7, "#C9D8E4", 0.75)
    rect(ctx, 0, gy + 7, W, 3, "#5E7384", 0.6)
    # back of the hand, barely lit, filling the gap above the glass
    ctx.move_to(740, gy + 6)
    ctx.curve_to(760, 250, 800, 236, 900, 236)
    ctx.curve_to(1000, 236, 1060, 246, 1090, gy + 6)
    ctx.close_path()
    src(ctx, "#1C3A63")
    ctx.fill()
    for k, (fx, l, wdt, c) in enumerate(((800, 150, 62, -0.06), (874, 168, 64, -0.01), (948, 160, 62, 0.03), (1020, 128, 56, 0.08))):
        ctx.save()
        ctx.translate(10, 14)
        gloved_finger(ctx, fx, gy + 4, l, wdt, curl=c, flat="#000000")   # contact shadow on the glass
        ctx.restore()
        gloved_finger(ctx, fx, gy + 4, l, wdt, torn=(k == 0), curl=c)
    drops_on_glass(ctx, 260, (0, gy + 20, W, 600), rmin=4, rmax=14)
    glow(ctx, 280, 940, 520, "#E39A3B", 0.16, sx=1.6, sy=0.5)
    ctx.move_to(0, 900)
    ctx.curve_to(W * 0.4, 870, W * 0.7, 860, W, 870)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    src(ctx, "#0A0C0F")
    ctx.fill()
    rrect(ctx, 1240, 925, 230, 74, 18, "#16191D")
    rrect(ctx, 1272, 940, 64, 42, 9, "#2A2E33")
    glow(ctx, 1304, 960, 60, "#E39A3B", 0.35)
    img = comp(bg, fg)
    img = finish(img, bloom=1.0, thresh=0.62, vign=0.7)
    return overlay(img, lambda c: hud(c, "2:43 AM", 0.4))


def comp(base, surf):
    surf.flush()
    a = np.ndarray((H, W, 4), np.uint8, surf.get_data()).astype(np.float32) / 255
    return base * (1 - a[..., 3:4]) + a[..., [2, 1, 0]]


FRAMES = [("01_S01_road", f1_road), ("02_S02_sign", f2_sign), ("03_S05_station_rule1", f3_station),
          ("04_S08_crosswalk", f4_crosswalk), ("05_S12_checkpoint", f5_checkpoint), ("06_S16_one_inch", f6_gap)]

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, fn in FRAMES:
        save(fn(), os.path.join(out, name + ".jpg"))
        print("saved", name)
