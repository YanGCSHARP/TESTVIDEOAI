"""Drawing helpers: easing, colours, flat shapes, text plates and infographic characters."""
import math
import cairo

# ---------------------------------------------------------------- easing

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def ease_out_back(x, s=1.9):
    x = clamp(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def ease_out_cubic(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_in_cubic(x):
    return clamp(x) ** 3


def ease_in_out(x):
    return 0.5 - 0.5 * math.cos(math.pi * clamp(x))


def pop(t, t_in, t_out=None, d_in=0.45, d_out=0.3):
    """Scale-style presence: 0 -> overshoot -> 1 on entry, ease-in back to 0 on exit."""
    v = ease_out_back(prog(t, t_in, t_in + d_in)) if t >= t_in else 0.0
    if t_out is not None and t >= t_out:
        v *= 1 - ease_in_cubic(prog(t, t_out, t_out + d_out))
    return v


def lerp(a, b, u):
    return a + (b - a) * u


# ---------------------------------------------------------------- colour

def hx(c, a=1.0):
    c = c.lstrip("#")
    return (int(c[0:2], 16) / 255, int(c[2:4], 16) / 255, int(c[4:6], 16) / 255, a)


def shade(c, f=0.78):
    r, g, b, a = hx(c) if isinstance(c, str) else c
    return (r * f, g * f, b * f, a)


def mix(c1, c2, u):
    a = hx(c1) if isinstance(c1, str) else c1
    b = hx(c2) if isinstance(c2, str) else c2
    return tuple(lerp(x, y, u) for x, y in zip(a, b))


def src(ctx, c, alpha=None):
    r, g, b, a = hx(c) if isinstance(c, str) else c
    ctx.set_source_rgba(r, g, b, a if alpha is None else alpha * a)


RED = "#C0392B"
YELLOW = "#F4C20D"
INK = "#121A22"
PAPER = "#EFE9DC"

# ---------------------------------------------------------------- shapes

def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def fill_rrect(ctx, x, y, w, h, r, c, alpha=None):
    rrect(ctx, x, y, w, h, r)
    src(ctx, c, alpha)
    ctx.fill()


def fill_rect(ctx, x, y, w, h, c, alpha=None):
    ctx.rectangle(x, y, w, h)
    src(ctx, c, alpha)
    ctx.fill()


def fill_circle(ctx, x, y, r, c, alpha=None):
    ctx.new_sub_path()
    ctx.arc(x, y, max(r, 0.01), 0, 2 * math.pi)
    src(ctx, c, alpha)
    ctx.fill()


def shaded_rrect(ctx, x, y, w, h, r, c, side=0.32):
    """Flat block with a one-tone-darker shadow band on the right side."""
    fill_rrect(ctx, x, y, w, h, r, c)
    ctx.save()
    rrect(ctx, x, y, w, h, r)
    ctx.clip()
    fill_rect(ctx, x + w * (1 - side), y, w * side + 1, h, shade(c))
    ctx.restore()


def poly(ctx, pts, c, alpha=None):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    src(ctx, c, alpha)
    ctx.fill()


def cloud(ctx, x, y, s, c, alpha=None):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for cx, cy, r in [(-60, 10, 42), (-10, -18, 58), (50, 0, 46), (95, 18, 30)]:
        ctx.new_sub_path()
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
    rrect(ctx, -100, 0, 225, 50, 25)
    src(ctx, c, alpha)
    ctx.fill()
    ctx.restore()


# ---------------------------------------------------------------- text

FONT = "Inter ExtraBold"
FONT_BLACK = "Inter Black"


def set_font(ctx, size, face=FONT):
    ctx.select_font_face(face, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def text_w(ctx, s, size, face=FONT):
    set_font(ctx, size, face)
    return ctx.text_extents(s).x_advance


def draw_text(ctx, s, x, y, size, c, face=FONT, align="left", alpha=None):
    set_font(ctx, size, face)
    w = ctx.text_extents(s).x_advance
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    ctx.move_to(x, y)
    src(ctx, c, alpha)
    ctx.show_text(s)
    return w


def plate(ctx, x, y, shown, full, size, bg, fg, accent=None, presence=1.0, cursor_t=None,
          pad=(30, 18), origin="left"):
    """Info plate. Box size is computed from the full text so it does not jitter while typing."""
    if presence <= 0.001:
        return
    tw = text_w(ctx, full, size)
    w, h = tw + 2 * pad[0] + (14 if accent else 0), size * 1.05 + 2 * pad[1]
    ctx.save()
    ox = x if origin == "left" else x + w / 2
    ctx.translate(ox, y + h / 2)
    ctx.scale(presence, presence)
    ctx.translate(-ox, -(y + h / 2))
    fill_rrect(ctx, x + 8, y + 8, w, h, 6, "#000000", 0.28)
    fill_rrect(ctx, x, y, w, h, 6, bg)
    tx = x + pad[0]
    if accent:
        fill_rect(ctx, x, y, 14, h, accent)
        tx += 14
    draw_text(ctx, shown, tx, y + pad[1] + size * 0.86, size, fg)
    if cursor_t is not None and (len(shown) < len(full) or int(cursor_t * 3) % 2 == 0):
        set_font(ctx, size)
        cx = tx + ctx.text_extents(shown).x_advance + 4
        fill_rect(ctx, cx, y + pad[1] + 2, size * 0.12, size * 0.92, fg, 0.9)
    ctx.restore()
    return w, h


# ---------------------------------------------------------------- characters

def blink(t, seed):
    """True while the eyes are closed. Blinks roughly every 2.7-3.4 s, 0.12 s long."""
    period = 2.7 + (seed % 7) * 0.1
    ph = (t + seed * 0.61) % period
    return ph < 0.12


def head(ctx, x, y, r, skin, hair, t, seed=0, turn=0.0, style="short", silhouette=False):
    bob = math.sin(t * 2.1 + seed) * 3
    y += bob
    if style == "long" and not silhouette:
        fill_rrect(ctx, x - r * 1.08, y - r * 0.4, r * 2.16, r * 1.85, r * 0.7, hair)
    fill_circle(ctx, x, y, r, skin)
    if not silhouette:
        # one-tone darker crescent for volume
        ctx.save()
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.clip()
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.new_sub_path()
        ctx.arc(x - r * 0.28 + turn * r * 0.2, y - r * 0.12, r * 0.98, 0, 2 * math.pi)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        src(ctx, shade(skin, 0.86))
        ctx.fill()
        ctx.restore()
        # hair cap
        ctx.save()
        ctx.arc(x, y, r * 1.02, 0, 2 * math.pi)
        ctx.clip()
        hx_off = turn * r * 0.25
        ctx.new_sub_path()
        ctx.arc(x - hx_off, y - r * 0.55, r * 1.05, math.pi, 2 * math.pi)
        ctx.close_path()
        src(ctx, hair)
        ctx.fill()
        if style == "long":
            fill_circle(ctx, x - r * 0.62 - hx_off, y - r * 0.5, r * 0.4, hair)
        ctx.restore()
        if style == "long":
            fill_circle(ctx, x + r * 0.15 - hx_off, y - r * 1.05, r * 0.38, hair)  # bun
        # eyes
        ex = turn * r * 0.45
        ey = y + r * 0.02
        if blink(t, seed):
            for sx in (-1, 1):
                fill_rrect(ctx, x + ex + sx * r * 0.32 - r * 0.11, ey - 2, r * 0.22, 4, 2, INK)
        else:
            for sx in (-1, 1):
                fill_circle(ctx, x + ex + sx * r * 0.32, ey, r * 0.095, INK)
        fill_rrect(ctx, x + ex - r * 0.14, y + r * 0.42, r * 0.28, 4, 2, shade(skin, 0.6))
    return y


def person(ctx, x, y, s, t, shirt, pants, skin, hair, seed=0, turn=0.0, walk=None,
           hold=None, style="short", silhouette=False, rim=None):
    """Standing infographic character with feet at (x, y). walk = phase (radians) or None."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if silhouette:
        shirt = pants = skin = hair = "#0A0E13"
    swing = math.sin(walk) * 0.42 if walk is not None else 0.0
    lift = abs(math.sin(walk)) * 7 if walk is not None else 0.0
    breathe = math.sin(t * 1.7 + seed) * 2.5
    ctx.translate(0, -lift)

    if rim:  # thin coloured rim behind a silhouette
        ctx.save()
        ctx.translate(-5, 0)
        _body(ctx, swing, breathe, rim, rim, rim, hold, t, seed, rim_only=True)
        fill_circle(ctx, 0, -392 + breathe, 66, rim)
        ctx.restore()
    _body(ctx, swing, breathe, shirt, pants, skin, hold, t, seed)
    head(ctx, 0, -392 + breathe, 62, skin, hair, t, seed, turn, style, silhouette)
    if hold == "box":
        _box(ctx, -78, -305 + breathe, silhouette)
        for sx in (-1, 1):
            fill_rrect(ctx, sx * 70 - 18, -250 + breathe, 36, 30, 14, skin)
    ctx.restore()


def _body(ctx, swing, breathe, shirt, pants, skin, hold, t, seed, rim_only=False):
    # legs
    for sgn in (-1, 1):
        ctx.save()
        ctx.translate(sgn * 24, -150)
        ctx.rotate(swing * sgn)
        fill_rrect(ctx, -18, 0, 36, 152, 16, pants if sgn < 0 else shade(pants, 0.85))
        fill_rrect(ctx, -20, 132, 48, 22, 10, "#1A1F26")
        ctx.restore()
    # back arm
    arm_back = -swing * 0.8
    ctx.save()
    ctx.translate(48, -300 + breathe)
    ctx.rotate(arm_back + (0.2 if hold else 0))
    fill_rrect(ctx, -15, 0, 30, 150, 15, shade(shirt, 0.8))
    ctx.restore()
    # torso
    if rim_only:
        fill_rrect(ctx, -64, -330 + breathe, 128, 186, 44, shirt)
    else:
        shaded_rrect(ctx, -62, -328 + breathe, 124, 184, 44, shirt)
        fill_rrect(ctx, -15, -338 + breathe, 30, 20, 8, shade(skin, 0.85))  # neck
    # front arm
    ctx.save()
    ctx.translate(-48, -300 + breathe)
    if hold == "folder":
        ctx.rotate(0.95)
    elif hold == "box":
        ctx.rotate(0.35)
    else:
        ctx.rotate(swing * 0.8)
    fill_rrect(ctx, -15, 0, 30, 150, 15, shirt)
    if not rim_only:
        fill_circle(ctx, 0, 150, 17, skin)
    ctx.restore()
    if hold == "folder" and not rim_only:
        ctx.save()
        ctx.translate(-205, -262 + breathe)
        ctx.rotate(-0.12)
        fill_rrect(ctx, 0, 0, 92, 118, 5, shade("#D9B26A", 0.8))
        fill_rrect(ctx, 6, -8, 86, 118, 5, "#D9B26A")
        fill_rect(ctx, 18, 22, 58, 7, shade("#D9B26A", 0.65))
        fill_rect(ctx, 18, 40, 46, 5, shade("#D9B26A", 0.72))
        fill_rect(ctx, 18, 54, 52, 5, shade("#D9B26A", 0.72))
        ctx.restore()


def _box(ctx, x, y, dark):
    c = "#3A2A1C" if dark else "#B98A55"
    fill_rrect(ctx, x, y, 156, 112, 6, c)
    fill_rect(ctx, x + 108, y, 48, 112, shade(c, 0.8))
    fill_rect(ctx, x, y + 20, 156, 6, shade(c, 0.7))


def seated_woman(ctx, x, y, s, t, turn=0.0, seed=3):
    """Upper body only (the desk hides the rest). (x, y) = seat height at body centre."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    skin, hair, blouse = "#E2B48F", "#3B2620", "#5E8C8A"
    breathe = math.sin(t * 1.6 + seed) * 2.5
    # arms resting forward on the desk
    for sgn, c in ((1, shade(blouse, 0.8)), (-1, blouse)):
        ctx.save()
        ctx.translate(sgn * 50, -160 + breathe)
        ctx.rotate(sgn * 0.5 - 0.15 * (1 if sgn < 0 else 0) + math.sin(t * 1.3) * 0.03)
        fill_rrect(ctx, -15, 0, 30, 130, 15, c)
        fill_circle(ctx, 0, 132, 16, skin)
        ctx.restore()
    shaded_rrect(ctx, -60, -188 + breathe, 120, 200, 44, blouse)
    fill_rrect(ctx, -14, -198 + breathe, 28, 20, 8, shade(skin, 0.85))
    # small necklace accent
    fill_circle(ctx, 0, -160 + breathe, 6, "#E6C46A")
    head(ctx, 0, -252 + breathe, 60, skin, hair, t, seed, turn, "long")
    ctx.restore()
