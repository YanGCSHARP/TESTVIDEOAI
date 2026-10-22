"""Drawing kit for DO NOT LOWER YOUR WINDOW: colours, primitives, lights, rain, post-processing.

All functions take explicit sizes, so they work on plates of any resolution.
"""
import math

import cairo
import numpy as np
from scipy.ndimage import gaussian_filter, zoom

AMBER = "#E39A3B"
RED = "#C0392B"
NIGHT = "#0B1520"


# ----------------------------------------------------------------- colour / primitives

def hx(c, a=1.0):
    if not isinstance(c, str):
        return (*c[:3], a)
    c = c.lstrip("#")
    return (int(c[0:2], 16) / 255, int(c[2:4], 16) / 255, int(c[4:6], 16) / 255, a)


def mixc(c1, c2, u):
    a, b = hx(c1), hx(c2)
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def src(ctx, c, a=1.0):
    ctx.set_source_rgba(*hx(c, a))


def surface(w, h):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w), int(h))
    ctx = cairo.Context(s)
    ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    return s, ctx


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


def rrect_path(ctx, x, y, w, h, r):
    r = max(0.1, min(r, w / 2, h / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def rrect(ctx, x, y, w, h, r, c, a=1.0):
    rrect_path(ctx, x, y, w, h, r)
    src(ctx, c, a)
    ctx.fill()


def circle(ctx, x, y, r, c, a=1.0):
    ctx.new_sub_path()
    ctx.arc(x, y, max(r, 0.1), 0, 2 * math.pi)
    src(ctx, c, a)
    ctx.fill()


def ellipse(ctx, x, y, rx, ry, c, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(max(rx, 0.1), max(ry, 0.1))
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    src(ctx, c, a)
    ctx.fill()


def vgrad(ctx, x, y, w, h, stops):
    g = cairo.LinearGradient(0, y, 0, y + h)
    for off, c, a in stops:
        g.add_color_stop_rgba(off, *hx(c, a))
    ctx.rectangle(x, y, w, h)
    ctx.set_source(g)
    ctx.fill()


def hgrad(ctx, x, y, w, h, stops):
    g = cairo.LinearGradient(x, 0, x + w, 0)
    for off, c, a in stops:
        g.add_color_stop_rgba(off, *hx(c, a))
    ctx.rectangle(x, y, w, h)
    ctx.set_source(g)
    ctx.fill()


def glow(ctx, x, y, r, c, a=1.0, sx=1.0, sy=1.0):
    if a <= 0.002 or r <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sx, sy)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, r)
    g.add_color_stop_rgba(0, *hx(c, a))
    g.add_color_stop_rgba(0.3, *hx(c, a * 0.38))
    g.add_color_stop_rgba(1, *hx(c, 0))
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()


def cone(ctx, x0, y0, far, c, a):
    fx = sum(p[0] for p in far) / len(far)
    fy = sum(p[1] for p in far) / len(far)
    g = cairo.LinearGradient(x0, y0, fx, fy)
    g.add_color_stop_rgba(0, *hx(c, a))
    g.add_color_stop_rgba(1, *hx(c, 0))
    ctx.move_to(x0, y0)
    for p in far:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source(g)
    ctx.fill()


def pines(ctx, w, base, height, color, seed=0, jitter=0.35, spacing=1.0, bottom=None):
    r = np.random.default_rng(seed)
    src(ctx, color)
    ctx.rectangle(-200, base - 4, w + 400, (bottom or base + 2000) - base + 4)
    ctx.fill()
    x = -100.0
    while x < w + 100:
        h = height * r.uniform(1 - jitter, 1 + jitter)
        tw0 = h * r.uniform(0.32, 0.42)
        for k in range(5):
            tb = base - h * (k / 5) * 0.92
            tw = tw0 * (1 - k / 5 * 0.8) * r.uniform(0.9, 1.1)
            tt = tb - h * 0.34
            ctx.move_to(x - tw / 2, tb)
            ctx.curve_to(x - tw * 0.2, tb - h * 0.08, x - tw * 0.05, tt + h * 0.1, x, tt)
            ctx.curve_to(x + tw * 0.05, tt + h * 0.1, x + tw * 0.2, tb - h * 0.08, x + tw / 2, tb)
            ctx.close_path()
        ctx.fill()
        x += tw0 * r.uniform(0.35, 0.7) * spacing


def text(ctx, s, x, y, size, c, face="Inter", bold=True, a=1.0, align="left"):
    ctx.select_font_face(face, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
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


def text_w(ctx, s, size, face="Inter", bold=True):
    ctx.select_font_face(face, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    return ctx.text_extents(s).x_advance


def marker_text(ctx, s, x, y, size, seed=0, reveal=1.0, color="#101010"):
    """Hand-written marker look; `reveal` (0..1) writes it letter by letter."""
    r = np.random.default_rng(seed)
    ctx.select_font_face("Inter Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx = x
    n_show = reveal * len(s)
    for i, ch in enumerate(s):
        fs = size * r.uniform(0.92, 1.08)
        ctx.set_font_size(fs)
        adv = ctx.text_extents(ch).x_advance
        rot, dy = r.uniform(-0.07, 0.07), r.uniform(-5, 5) * size / 100
        jit = [(r.uniform(-1.5, 1.5), r.uniform(-1.5, 1.5)) for _ in range(3)]
        part = min(1.0, max(0.0, n_show - i))
        if part > 0:
            for k in range(3):
                ctx.save()
                ctx.translate(cx + jit[k][0] * size / 100, y + dy + jit[k][1] * size / 100)
                ctx.rotate(rot)
                ctx.move_to(0, 0)
                src(ctx, color, 0.55 * part)
                ctx.show_text(ch)
                ctx.restore()
        cx += adv * r.uniform(0.9, 1.0) + size * 0.02
    return cx - x


def marker_width(ctx, s, size, seed=0):
    r = np.random.default_rng(seed)
    ctx.select_font_face("Inter Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx = 0.0
    for ch in s:
        ctx.set_font_size(size * r.uniform(0.92, 1.08))
        adv = ctx.text_extents(ch).x_advance
        r.uniform(-0.07, 0.07), r.uniform(-5, 5)
        [(r.uniform(-1.5, 1.5), r.uniform(-1.5, 1.5)) for _ in range(3)]
        cx += adv * r.uniform(0.9, 1.0) + size * 0.02
    return cx


# ----------------------------------------------------------------- rain / glass

class Rain:
    """Deterministic animated rain: streaks fall continuously; drawn in one stroke per pass."""

    def __init__(self, w, h, n, seed, speed=(1900, 2600), length=(22, 52), angle=0.16,
                 alpha=0.16, color="#C9D6E2", width=1.4):
        r = np.random.default_rng(seed)
        self.w, self.h = w, h
        self.x0 = r.uniform(-200, w + 200, n)
        self.y0 = r.uniform(0, h + 200, n)
        self.v = r.uniform(*speed, n)
        self.l = r.uniform(*length, n)
        self.angle, self.alpha, self.color, self.width = angle, alpha, color, width

    def draw(self, ctx, t, clip=None, alpha_mul=1.0, color=None):
        sa, ca = math.sin(self.angle), math.cos(self.angle)
        ctx.save()
        if clip:
            clip(ctx)
            ctx.clip()
        span = self.h + 300
        y = (self.y0 + self.v * t) % span - 150
        x = self.x0 - (y - self.y0) * sa / ca
        x = (x + 200) % (self.w + 400) - 200
        ctx.set_line_width(self.width)
        for xi, yi, li in zip(x, y, self.l):
            ctx.move_to(xi, yi)
            ctx.line_to(xi - li * sa, yi + li * ca)
        src(ctx, color or self.color, self.alpha * alpha_mul)
        ctx.stroke()
        ctx.restore()


class Drops:
    """Raindrops on glass: static beads plus a few running streaks; wipers can clear them."""

    def __init__(self, x, y, w, h, n, seed, rmin=3, rmax=11):
        r = np.random.default_rng(seed)
        self.p = np.stack([x + r.uniform(0, w, n), y + r.uniform(0, h, n), r.uniform(rmin, rmax, n),
                           r.uniform(0, 1, n), r.uniform(0, 1, n)], axis=1)
        self.box = (x, y, w, h)

    def draw(self, ctx, t, wiper_age=None, alpha=1.0):
        """wiper_age(x, y) -> seconds since the wiper last passed that point (None = never)."""
        x0, y0, w, h = self.box
        for x, y, r, born, run in self.p:
            a = alpha
            if wiper_age is not None:
                age = wiper_age(x, y)
                a *= min(1.0, max(0.0, (age - born * 1.6) / 0.6)) if age is not None else 1.0
            if a <= 0.02:
                continue
            yy = y
            if run > 0.88:  # running drop slides down slowly
                yy = y0 + (y - y0 + (t * 40 * (run - 0.8) * 10)) % h
                ctx.set_line_width(r * 0.55)
                ctx.move_to(x, yy - r * 6)
                ctx.line_to(x, yy)
                src(ctx, "#9FB3C2", 0.07 * a)
                ctx.stroke()
            circle(ctx, x, yy, r, "#0A1016", 0.22 * a)
            circle(ctx, x - r * 0.15, yy - r * 0.15, r * 0.8, "#9FB3C2", 0.10 * a)
            circle(ctx, x - r * 0.35, yy - r * 0.4, r * 0.25, "#EAF2F8", 0.55 * a)


# ----------------------------------------------------------------- post-processing (plates only)

def to_np(surf):
    surf.flush()
    w, h = surf.get_width(), surf.get_height()
    a = np.ndarray((h, w, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1))
    return a.astype(np.float32) / 255


def from_np(rgba):
    """Float RGBA (straight or premultiplied as given) -> cairo surface (expects premultiplied BGRA)."""
    h, w, _ = rgba.shape
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    buf = np.ndarray((h, w, 4), np.uint8, s.get_data(), strides=(s.get_stride(), 4, 1))
    buf[:] = np.clip(rgba * 255 + 0.5, 0, 255).astype(np.uint8)
    s.mark_dirty()
    return s


def fog_noise(h, w, seed):
    r = np.random.default_rng(seed)
    n = gaussian_filter(r.standard_normal((h // 8 + 1, w // 8 + 1)), 6)
    n = zoom((n - n.min()) / (np.ptp(n) + 1e-6), 8, order=1)[:h, :w]
    return n


def band(h, w, y0, y1, peak, falloff):
    y = np.arange(h, dtype=np.float32)[:, None]
    m = np.clip(1 - np.abs(y - peak) / falloff, 0, 1) * ((y > y0) & (y < y1))
    return np.repeat(m, w, axis=1)


def finish_plate(surf, bloom=1.0, thresh=0.62, fog=None, lift=NIGHT, desat=0.0, warm=0.0, blur=0.0, seed=0):
    """Bake bloom / fog / colour lift into an opaque plate. Returns a new cairo surface."""
    a = to_np(surf)
    rgb = a[..., [2, 1, 0]]
    h, w = rgb.shape[:2]
    if blur:
        rgb = gaussian_filter(rgb, (blur, blur, 0))
    if fog is not None:
        col, mask = fog
        m = (mask * (0.55 + 0.45 * fog_noise(h, w, seed)))[..., None]
        rgb = rgb * (1 - m) + np.array(hx(col)[:3], np.float32) * m
    if bloom:
        small = zoom(np.maximum(rgb - thresh, 0), (0.25, 0.25, 1), order=1)
        b = gaussian_filter(small, (6, 6, 0)) * 0.6 + gaussian_filter(small, (22, 22, 0)) * 1.4
        b = zoom(b, (h / small.shape[0], w / small.shape[1], 1), order=1)[:h, :w]
        rgb = rgb + bloom * b
    lc = np.array(hx(lift)[:3], np.float32)
    rgb = lc + rgb * (1 - lc)
    if desat:
        g = rgb.mean(axis=2, keepdims=True)
        rgb = rgb * (1 - desat) + g * desat
    if warm:
        rgb[..., 0] *= 1 + warm
        rgb[..., 2] *= 1 - warm * 0.5
    rgb = rgb / (1 + rgb * 0.25) * 1.25
    out = np.concatenate([rgb[..., ::-1], np.ones((h, w, 1), np.float32)], axis=2)
    return from_np(np.clip(out, 0, 1))


def grade_layer(surf, lift=NIGHT, blur=0.0):
    """Light grading for a transparent foreground layer (keeps alpha, premultiplied)."""
    a = to_np(surf)
    alpha = a[..., 3:4]
    rgb = a[..., [2, 1, 0]]
    if blur:
        rgb = gaussian_filter(rgb, (blur, blur, 0))
        alpha = gaussian_filter(alpha, (blur, blur, 0))
    lc = np.array(hx(lift)[:3], np.float32)
    rgb = rgb + lc * (1 - 0) * alpha * 0.6
    out = np.concatenate([rgb[..., ::-1], alpha], axis=2)
    return from_np(np.clip(out, 0, 1))
