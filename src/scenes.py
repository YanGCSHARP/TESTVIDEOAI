"""Scene drawing. Every scene is a pure function of global time t."""
import math
from contextlib import contextmanager

import cairo

import timeline as tl
from gfx import (RED, YELLOW, INK, PAPER, clamp, prog, lerp, pop, ease_out_back, ease_out_cubic,
                 ease_in_cubic, ease_in_out, hx, shade, mix, src, rrect, fill_rrect, fill_rect,
                 fill_circle, shaded_rrect, poly, cloud, draw_text, text_w, set_font, plate, person,
                 seated_woman, FONT_BLACK)

W, H = tl.W, tl.H


# ---------------------------------------------------------------- camera / parallax

class Cam:
    """Ken Burns camera. Layers with larger depth move and zoom more (parallax)."""

    def __init__(self, zoom=1.0, px=0.0, py=0.0, sx=0.0, sy=0.0):
        self.zoom, self.px, self.py, self.sx, self.sy = zoom, px, py, sx, sy

    @contextmanager
    def layer(self, ctx, depth):
        ctx.save()
        z = 1 + (self.zoom - 1) * depth
        ctx.translate(W / 2 + self.px * depth + self.sx * depth, H / 2 + self.py * depth + self.sy * depth)
        ctx.scale(z, z)
        ctx.translate(-W / 2, -H / 2)
        yield
        ctx.restore()


def kb(t, a, b, z0, z1, p0, p1):
    # half linear, half eased: smooth, but the camera never comes to a full stop
    x = prog(t, a - 0.3, b + 0.3)
    u = 0.5 * x + 0.5 * ease_in_out(x)
    return Cam(lerp(z0, z1, u), lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u))


def vgrad(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, c in stops:
        g.add_color_stop_rgba(off, *(hx(c) if isinstance(c, str) else c))
    return g


OVER = 260  # overscan for backgrounds


def bg_fill(ctx, c):
    fill_rect(ctx, -OVER, -OVER, W + 2 * OVER, H + 2 * OVER, c)


# ================================================================= 1. CONCORD

def concord(ctx, t):
    a, b = 0.0, 5.0
    cam = kb(t, a, b, 1.0, 1.09, (0, 12), (-70, -14))
    lt = t - a

    with cam.layer(ctx, 0.05):
        ctx.rectangle(-OVER, -OVER, W + 2 * OVER, H + 2 * OVER)
        ctx.set_source(vgrad(ctx, 0, -OVER, 0, 760, [(0, "#16283A"), (0.5, "#3C5D77"), (0.85, "#8C7F86"), (1, "#C98F70")]))
        ctx.fill()

    with cam.layer(ctx, 0.15):  # rising sun
        sy = lerp(820, 330, ease_out_cubic(lt / 5.0))
        for r, al in ((260, 0.06), (190, 0.09), (140, 0.14)):
            fill_circle(ctx, 1130, sy, r, "#F6C98A", al)
        fill_circle(ctx, 1130, sy, 96, "#F3C27E")
        fill_circle(ctx, 1148, sy - 12, 70, "#F7D39C")

    with cam.layer(ctx, 0.28):  # clouds drift
        for x0, y0, s, sp, c in ((-150, 170, 1.2, 38, "#5E7A90"), (700, 120, 0.9, 26, "#6E879A"),
                                 (1400, 230, 1.0, 34, "#7E8E9C"), (380, 300, 0.7, 48, "#8D97A3")):
            x = (x0 + sp * t) % (W + 600) - 300
            cloud(ctx, x + 8, y0 + 10, s, shade(c, 0.8), 0.6)
            cloud(ctx, x, y0, s, c, 0.95)

    with cam.layer(ctx, 0.42):  # distant tree line
        ctx.move_to(-OVER, 760)
        for i in range(0, W + 2 * OVER + 40, 40):
            x = -OVER + i
            ctx.line_to(x, 690 - 26 * math.sin(i * 0.013) - 18 * abs(math.sin(i * 0.071)))
        ctx.line_to(W + OVER, 1100)
        ctx.line_to(-OVER, 1100)
        ctx.close_path()
        src(ctx, "#25424E")
        ctx.fill()

    with cam.layer(ctx, 0.7):
        factory(ctx, t)

    with cam.layer(ctx, 1.3):  # foreground fence, lamp, bushes
        fill_rect(ctx, -OVER, 965, W + 2 * OVER, 300, "#1C2B33")
        for i in range(-4, 30):
            x = i * 90
            fill_rect(ctx, x, 880, 12, 120, "#2A3A44")
        fill_rect(ctx, -OVER, 900, W + 2 * OVER, 8, "#2A3A44")
        fill_rect(ctx, -OVER, 945, W + 2 * OVER, 8, "#2A3A44")
        fill_rect(ctx, 150, 420, 18, 600, "#18242C")
        fill_rrect(ctx, 120, 405, 110, 26, 12, "#18242C")
        fill_circle(ctx, 210, 436, 14, "#F6D9A0", 0.75)
        for x, y, r in ((-40, 980, 120), (90, 1010, 100), (1830, 990, 130), (1960, 960, 120)):
            fill_circle(ctx, x, y, r, "#1E3B3A")
            fill_circle(ctx, x - r * 0.25, y - r * 0.25, r * 0.6, "#264A47")

    # location / date plates (screen space, not affected by camera)
    city_s, city_full = tl.typed("city", t)
    plate(ctx, 110, 800, city_s, city_full, 54, "#1B2631", "#FFFFFF", accent=YELLOW,
          presence=pop(t, 0.9, 4.45), cursor_t=t if t < 2.4 else None)
    date_s, date_full = tl.typed("date", t)
    plate(ctx, 110, 905, date_s, date_full, 40, RED, "#FFFFFF",
          presence=pop(t, 2.3, 4.35), cursor_t=t if t < 3.4 else None)


def factory(ctx, t):
    brick, brick_d = "#8A4E3C", "#6F3D30"
    # parking lot
    fill_rect(ctx, -OVER, 860, W + 2 * OVER, 300, "#34444E")
    for i in range(10):
        fill_rect(ctx, 380 + i * 150, 900, 80, 8, "#56656E")
    # low sawtooth wing
    fill_rect(ctx, 250, 600, 330, 260, brick_d)
    for i in range(4):
        poly(ctx, [(250 + i * 82, 600), (250 + i * 82, 545), (332 + i * 82, 600)], "#5B3328")
        poly(ctx, [(258 + i * 82, 596), (258 + i * 82, 560), (300 + i * 82, 588)], "#8FB0BE", 0.55)
    for i in range(3):
        fill_rrect(ctx, 285 + i * 100, 680, 60, 80, 4, "#22313B")
    # smokestack + smoke
    fill_rect(ctx, 1385, 230, 64, 260, brick_d)
    fill_rect(ctx, 1425, 230, 24, 260, shade(brick_d, 0.82))
    fill_rect(ctx, 1375, 222, 84, 20, "#4A2A22")
    fill_rect(ctx, 1385, 300, 64, 10, "#C9C1B5")
    for k in range(7):
        ph = (t * 0.22 + k / 7) % 1.0
        fill_circle(ctx, 1417 + ph * 160 + math.sin(k * 2.1 + t) * 10, 205 - ph * 230,
                    20 + ph * 55, "#B8BFC6", 0.55 * (1 - ph))
    # main building
    x0, y0, x1, y1 = 560, 450, 1500, 860
    fill_rect(ctx, x0, y0, x1 - x0, y1 - y0, brick)
    fill_rect(ctx, x1 - 150, y0, 150, y1 - y0, brick_d)
    ctx.save()
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.clip()
    for r, y in enumerate(range(y0 + 18, y1, 22)):
        fill_rect(ctx, x0, y, x1 - x0, 3, "#000000", 0.08)
        off = 0 if r % 2 else 30
        for x in range(x0 + off, x1, 60):
            fill_rect(ctx, x, y - 19, 3, 19, "#000000", 0.05)
    ctx.restore()
    fill_rect(ctx, x0 - 14, y0 - 26, x1 - x0 + 28, 30, "#5B3328")
    # windows
    for row, wy in enumerate((520, 650)):
        for i in range(8):
            wx = 610 + i * 98
            if row == 1 and 4 <= i <= 6:
                continue
            fill_rrect(ctx, wx - 6, wy - 6, 74, 102, 4, "#C9B9A3")
            fill_rect(ctx, wx, wy, 62, 90, "#22313B")
            poly(ctx, [(wx, wy + 60), (wx + 40, wy), (wx + 62, wy), (wx, wy + 90)], "#9FB4C0", 0.22)
            fill_rect(ctx, wx + 29, wy, 4, 90, "#C9B9A3")
    # loading dock door
    fill_rect(ctx, 1010, 690, 230, 170, "#4F5D66")
    for y in range(698, 860, 18):
        fill_rect(ctx, 1010, y, 230, 4, "#3E4A52")
    # sign (generic, no real branding)
    fill_rrect(ctx, 720, 468, 440, 44, 6, "#E8DCC3")
    draw_text(ctx, "BOTTLING CO.", 940, 503, 32, "#5B3328", align="center")
    # water tower
    for lx in (1590, 1690):
        fill_rect(ctx, lx, 520, 14, 340, "#3A4A55")
    fill_rect(ctx, 1590, 680, 114, 8, "#3A4A55")
    fill_rrect(ctx, 1555, 400, 185, 135, 30, "#6C7D88")
    fill_rect(ctx, 1680, 400, 60, 135, "#5A6A75")
    poly(ctx, [(1550, 405), (1647, 345), (1745, 405)], "#4E5D68")


# ================================================================= 2-3. OFFICE / AFTERMATH

def office_room(ctx, t, cam, dark=False):
    with cam.layer(ctx, 0.55):
        bg_fill(ctx, "#4E6E74")
        fill_rect(ctx, -OVER, 620, W + 2 * OVER, 400, "#44625F")
        fill_rect(ctx, -OVER, 612, W + 2 * OVER, 12, "#3A5552")
        # window with blinds
        fill_rrect(ctx, 170, 150, 470, 420, 6, "#2F4448")
        fill_rect(ctx, 190, 170, 430, 380, "#A9C6CB")
        for i in range(13):
            y = 172 + i * 29
            fill_rect(ctx, 190, y, 430, 17, "#D7E2DF")
            fill_rect(ctx, 190, y + 15, 430, 3, "#B7C7C5")
        if not dark:
            poly(ctx, [(620, 170), (900, 640), (1150, 640), (620, 550)], "#FFF4D6", 0.07)
        # certificate
        fill_rrect(ctx, 1130, 170, 190, 140, 4, "#2C3E50")
        fill_rect(ctx, 1142, 182, 166, 116, "#EDE6D6")
        fill_rect(ctx, 1165, 205, 120, 10, "#A39782")
        for i in range(3):
            fill_rect(ctx, 1165, 230 + i * 18, 120 - i * 25, 6, "#C6BBA6")
        fill_circle(ctx, 1280, 278, 12, "#C9A44C")
        wall_clock(ctx, 940, 230, t)
        # door
        door(ctx, t)

    with cam.layer(ctx, 0.75):  # floor
        fill_rect(ctx, -OVER, 860, W + 2 * OVER, 400, "#2E4046")
        for i in range(-3, 24):
            fill_rect(ctx, i * 110, 860, 4, 400, "#283840")


def door(ctx, t):
    fx, fy, fw, fh = 1470, 230, 250, 630
    fill_rect(ctx, fx - 18, fy - 18, fw + 36, fh + 18, "#33494D")
    fill_rect(ctx, fx, fy, fw, fh, "#1F2D33")          # dark hallway
    poly(ctx, [(fx, fy + fh), (fx + fw, fy + fh), (fx + fw - 40, fy + fh - 120), (fx + 40, fy + fh - 120)],
         "#2B3B41")
    openu = ease_out_back(prog(t, 6.0, 6.45), 1.4)
    dw = lerp(fw, 46, openu)
    fill_rect(ctx, fx + fw - dw, fy, dw, fh, "#7B5A44")
    fill_rect(ctx, fx + fw - dw, fy, dw * 0.25, fh, "#654936")
    fill_circle(ctx, fx + fw - dw + dw * 0.18 if openu < 0.5 else fx + fw - dw * 0.4, fy + fh * 0.52, 9,
                "#D4B86A")


def wall_clock(ctx, x, y, t):
    fill_circle(ctx, x + 6, y + 8, 78, "#000000", 0.18)
    fill_circle(ctx, x, y, 78, "#2C3E50")
    fill_circle(ctx, x, y, 66, "#ECE6D8")
    for i in range(12):
        a = i * math.pi / 6
        r0 = 52 if i % 3 else 46
        ctx.move_to(x + r0 * math.sin(a), y - r0 * math.cos(a))
        ctx.line_to(x + 60 * math.sin(a), y - 60 * math.cos(a))
        ctx.set_line_width(5 if i % 3 == 0 else 3)
        src(ctx, "#2C3E50")
        ctx.stroke()
    # stepping second hand, synced to the tick sounds, frozen after the impact
    n = sum(1 for tk in tl.TICKS if tk <= t)
    frac = 0.0
    for tk in tl.TICKS:
        if tk <= t < tk + 0.18:
            frac = ease_out_back(prog(t, tk, tk + 0.18), 2.4) - 1
    sec = 12 + n + frac
    hand(ctx, x, y, (9 + 41 / 60) / 12 * 2 * math.pi, 34, 8, "#2C3E50")
    hand(ctx, x, y, 41 / 60 * 2 * math.pi, 52, 6, "#2C3E50")
    hand(ctx, x, y, sec / 60 * 2 * math.pi, 58, 3, RED)
    fill_circle(ctx, x, y, 7, RED)


def hand(ctx, x, y, a, length, w, c):
    ctx.move_to(x - 8 * math.sin(a), y + 8 * math.cos(a))
    ctx.line_to(x + length * math.sin(a), y - length * math.cos(a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    src(ctx, c)
    ctx.stroke()


def desk(ctx, t, empty=False):
    # chair (behind desk)
    if empty:
        ctx.save()
        ctx.translate(1000, 650)
        ctx.rotate(0.3)
        fill_rrect(ctx, -80, -250, 160, 200, 30, "#26343B")
        fill_rect(ctx, -12, -60, 24, 70, "#1D292F")
        fill_rrect(ctx, -95, -70, 190, 34, 14, "#2E3E46")
        ctx.restore()
    else:
        fill_rrect(ctx, 735, 400, 170, 260, 34, "#26343B")
    if not empty:
        turn = lerp(0.0, 0.75, ease_out_back(prog(t, 6.75, 7.15), 2.2))
        turn = lerp(turn, 0.25, ease_in_out(prog(t, 8.6, 9.2)))
        seated_woman(ctx, 820, 640, 1.0, t, turn=turn)
    # desk top & front
    fill_rect(ctx, 380, 640, 880, 34, "#8B6A50")
    fill_rect(ctx, 380, 666, 880, 8, "#6F533F")
    fill_rect(ctx, 410, 674, 820, 230, "#6C4F3C")
    fill_rect(ctx, 1110, 674, 120, 230, "#5A4232")
    fill_rect(ctx, 440, 700, 300, 6, "#5A4232")
    # beach bag + towel + sunglasses
    poly(ctx, [(400, 640), (560, 640), (545, 530), (415, 530)], "#D8B46A")
    poly(ctx, [(500, 640), (560, 640), (545, 530), (505, 530)], shade("#D8B46A", 0.85))
    for k in range(3):
        fill_rect(ctx, 412 + k * 0, 552 + k * 30, 140, 9, "#4F8FA0")
    ctx.new_sub_path()
    ctx.arc(480, 532, 45, math.pi, 2 * math.pi)
    ctx.set_line_width(8)
    src(ctx, "#B08F4E")
    ctx.stroke()
    fill_rrect(ctx, 432, 500, 54, 42, 10, "#F2D7A0")
    fill_rect(ctx, 432, 512, 54, 9, "#E0866A")
    fill_rrect(ctx, 488, 552, 30, 16, 7, INK)
    fill_rrect(ctx, 522, 552, 30, 16, 7, INK)
    # family photo with the sea
    ctx.save()
    ctx.translate(605, 640)
    ctx.rotate(-0.06)
    fill_rect(ctx, -2, -128, 112, 128, "#2C3E50")
    fill_rect(ctx, 8, -118, 92, 108, "#A8D0DC")
    fill_rect(ctx, 8, -62, 92, 22, "#3F87A0")
    fill_rect(ctx, 8, -40, 92, 30, "#E9D3A4")
    for k, (px, ph) in enumerate(((30, 46), (54, 54), (76, 36))):
        fill_rrect(ctx, px - 8, -10 - ph * 0.55, 16, ph * 0.55, 6, ("#C0392B", "#2E6E73", "#D8B46A")[k])
        fill_circle(ctx, px, -16 - ph * 0.55, 8, "#E2B48F")
    fill_circle(ctx, 86, -102, 9, "#F6D07A")
    ctx.restore()
    # mug
    fill_rrect(ctx, 960, 590, 46, 52, 8, "#ECE6D8")
    ctx.new_sub_path()
    ctx.arc(1008, 614, 14, -math.pi / 2, math.pi / 2)
    ctx.set_line_width(6)
    src(ctx, "#ECE6D8")
    ctx.stroke()
    # cash register
    open_u = 1.0 if empty else 0.0
    rx = 1060
    fill_rrect(ctx, rx, 520, 170, 120, 10, "#5D6D7E")
    fill_rect(ctx, rx + 120, 520, 50, 120, "#4D5B69")
    fill_rrect(ctx, rx + 40, 470, 90, 50, 6, "#3B4955")
    fill_rect(ctx, rx + 52, 480, 66, 26, "#7FD1B9" if not empty else "#2E5048")
    for i in range(3):
        for j in range(4):
            fill_rrect(ctx, rx + 18 + j * 26, 540 + i * 22, 20, 15, 3, "#ECE6D8")
    if empty:  # drawer pulled out, empty compartments
        fill_rect(ctx, rx - 20, 636, 210, 44, "#4D5B69")
        for j in range(4):
            fill_rect(ctx, rx - 10 + j * 50, 642, 42, 30, "#1E2830")
    # scattered papers
    if empty:
        for px, py, a in ((560, 950, 0.3), (720, 980, -0.4), (900, 945, 0.15), (1300, 990, -0.2)):
            ctx.save()
            ctx.translate(px, py)
            ctx.rotate(a)
            fill_rect(ctx, -50, -30, 100, 64, "#D9D3C4")
            fill_rect(ctx, -36, -16, 60, 6, "#A49C8C")
            ctx.restore()


def office(ctx, t):
    a, b = 5.0, 10.0
    cam = kb(t, a, b, 1.04, 1.14, (40, 10), (-40, -18))
    office_room(ctx, t, cam)
    with cam.layer(ctx, 0.92):
        # man walks in through the door with his folder (resume)
        if t >= 6.15:
            u = ease_out_cubic(prog(t, 6.3, 7.7))
            x = lerp(1600, 1370, u)
            walking = 6.3 <= t < 7.7
            desk(ctx, t)
            person(ctx, x, 905, 0.95, t, "#5F6B5A", "#2F3B4A", "#C99B7A", "#2A211D", seed=5,
                   turn=-0.7, walk=(t - 6.3) * 9.0 if walking else None, hold="folder")
        else:
            desk(ctx, t)
    with cam.layer(ctx, 1.35):
        plant(ctx, 110, 1040)


def plant(ctx, x, y):
    for k, (dx, a, l) in enumerate(((-40, -0.5, 230), (0, -0.1, 270), (40, 0.4, 220), (-15, -0.25, 200),
                                     (25, 0.15, 250))):
        ctx.save()
        ctx.translate(x + dx * 0.3, y - 120)
        ctx.rotate(a)
        fill_rrect(ctx, -26, -l, 52, l, 26, "#2F5D50" if k % 2 else "#3B6E5F")
        ctx.restore()
    fill_rrect(ctx, x - 80, y - 140, 160, 160, 14, "#7A5A44")
    fill_rect(ctx, x + 30, y - 140, 50, 160, "#654936")


def aftermath(ctx, t):
    a, b = 10.0, 15.7
    lt = t - a
    cam = kb(t, a, b, 1.2, 1.1, (-30, -20), (20, 0))
    amp = 34 * math.exp(-lt * 3.2) + 4 * math.exp(-lt * 0.6)
    cam.sx = amp * (math.sin(t * 91) + 0.5 * math.sin(t * 57 + 1))
    cam.sy = amp * (math.cos(t * 83) + 0.5 * math.sin(t * 41 + 2))
    office_room(ctx, max(t, 6.5), cam, dark=True)
    with cam.layer(ctx, 0.92):
        desk(ctx, t, empty=True)
    with cam.layer(ctx, 1.35):
        plant(ctx, 110, 1040)
    # darkness
    fill_rect(ctx, 0, 0, W, H, "#06101A", 0.62)
    # silhouette leaving with a box, through the door
    with cam.layer(ctx, 0.92):
        if 10.6 <= t <= 14.6:
            u = prog(t, 10.6, 14.2)
            x = lerp(1180, 1650, ease_in_out(u))
            alpha = 1 - prog(x, 1530, 1650)
            ctx.push_group()
            person(ctx, x, 905, 0.97, t, "", "", "", "", seed=8, turn=0.8, walk=(t - 10.6) * 7.5,
                   hold="box", silhouette=True, rim=hx(RED, 0.85))
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(alpha)
    # red vignette flash + slow pulse (heartbeat-ish at 70 bpm)
    flash = math.exp(-lt * 5.0)
    beat = 0.5 + 0.5 * math.cos(2 * math.pi * lt * 70 / 60)
    strength = 0.25 + 0.55 * flash + 0.08 * beat
    g = cairo.RadialGradient(W / 2, H / 2, 260, W / 2, H / 2, 1150)
    g.add_color_stop_rgba(0, *hx(RED, 0.0))
    g.add_color_stop_rgba(1, *hx(RED, min(1.0, strength)))
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(g)
    ctx.fill()
    if lt < 0.12:
        fill_rect(ctx, 0, 0, W, H, RED, 0.45 * (1 - lt / 0.12))


# ================================================================= 4. COLD CASE

def year_progress(t):
    ft = tl.flip_times()
    return sum(1 for x in ft if x <= t) / len(ft)


def poster(ctx, x, y, kind, t, t_in, age, seed):
    s = pop(t, t_in, d_in=0.4)
    if s <= 0.001:
        return
    ctx.save()
    ctx.translate(x + 115, y)
    rot = (-0.05, 0.04, -0.02, 0.06)[seed] + 0.2 * math.exp(-max(0, t - t_in) * 6) * math.sin((t - t_in) * 30)
    ctx.rotate(rot)
    ctx.scale(s, s)
    w, h = 230, 310
    paper = mix(mix(PAPER, "#D9C07E", min(1, age * 1.3)), "#9C9077", max(0, age - 0.6) * 0.9)
    ink = mix(INK, "#6B6252", age * 0.8)
    fill_rect(ctx, -w / 2 + 8, 10, w, h, "#000000", 0.25)
    fill_rect(ctx, -w / 2, 0, w, h, paper)
    # curled faded corner
    if age > 0.35:
        cu = prog(age, 0.35, 1.0) * 46
        poly(ctx, [(w / 2 - cu, h), (w / 2, h - cu), (w / 2, h)], "#5B4A3A")
        poly(ctx, [(w / 2 - cu, h), (w / 2, h - cu), (w / 2 - cu, h - cu)], shade(paper, 0.82))
    title = {"wanted": "WANTED", "reward": "REWARD", "seen": "SEEN HIM?", "info": "ANY INFO?"}[kind]
    draw_text(ctx, title, 0, 50, 36 if len(title) < 8 else 30, RED if kind != "info" else ink,
              align="center", alpha=1 - age * 0.55)
    if kind in ("wanted", "seen"):
        fill_circle(ctx, 0, 125, 42, ink)
        fill_rrect(ctx, -60, 165, 120, 70, 30, ink)
        draw_text(ctx, "?", 0, 142, 50, paper, align="center")
    else:
        draw_text(ctx, "$", 0, 150, 90, ink, align="center")
        fill_rect(ctx, -70, 180, 140, 10, ink)
    for i in range(3):
        fill_rect(ctx, -80, 250 + i * 16, 160 - i * 30, 7, ink, 0.8)
    fill_circle(ctx, 0, 14, 10, RED)
    fill_circle(ctx, -3, 11, 4, "#F09A8E")
    ctx.restore()


def coldcase(ctx, t):
    a, b = 15.7, 21.3
    cam = kb(t, a, b, 1.05, 1.15, (-50, 10), (40, -10))
    age = year_progress(t)
    with cam.layer(ctx, 0.5):
        bg_fill(ctx, "#2B3D4E")
        for i in range(-3, 26):
            fill_rect(ctx, i * 96, -OVER, 4, H + 2 * OVER, "#263747")
    with cam.layer(ctx, 0.7):
        # cork board
        fill_rrect(ctx, 200, 140, 1170, 690, 10, "#4F3D2E")
        fill_rect(ctx, 222, 162, 1126, 646, "#8C6E4F")
        for i in range(60):
            fill_circle(ctx, 240 + (i * 197) % 1100, 180 + (i * 131) % 610, 3, "#7A5E43")
        pins = [(375, 170), (665, 195), (955, 160), (1205, 205)]
        board_extras(ctx, t, age)
        for (px, py), kind, tin, sd in zip(pins, ("wanted", "reward", "seen", "info"), tl.POSTER_TIMES, range(4)):
            poster(ctx, px - 115, py + 10, kind, t, tin, age, sd)
        # red yarn connecting pins
        ys = prog(t, 16.95, 17.7)
        if ys > 0:
            ctx.set_line_width(4)
            src(ctx, "#B03A2E", 0.9 - age * 0.3)
            pts = [(px, py + 24) for px, py in pins]
            total = ys * (len(pts) - 1)
            ctx.move_to(*pts[0])
            for i in range(1, len(pts)):
                f = clamp(total - (i - 1))
                if f <= 0:
                    break
                x0, y0 = pts[i - 1]
                x1, y1 = pts[i]
                ctx.line_to(lerp(x0, x1, f), lerp(y0, y1, f) + 26 * math.sin(math.pi * f) * (1 if f < 1 else 0))
            ctx.stroke()
        # COLD CASE stamp
        if t >= tl.STAMP_T:
            u = prog(t, tl.STAMP_T, tl.STAMP_T + 0.22)
            sc = lerp(2.4, 1.0, ease_out_cubic(u)) if u < 1 else 1.0 + 0.04 * math.exp(-(t - tl.STAMP_T - 0.22) * 9)
            ctx.save()
            ctx.translate(745, 615)
            ctx.rotate(-0.13)
            ctx.scale(sc, sc)
            al = min(1, u * 2) * 0.92
            w = text_w(ctx, "COLD CASE", 92, FONT_BLACK)
            rrect(ctx, -w / 2 - 34, -78, w + 68, 112, 10)
            ctx.set_line_width(10)
            src(ctx, RED, al)
            ctx.stroke()
            draw_text(ctx, "COLD CASE", 0, 10, 92, RED, face=FONT_BLACK, align="center", alpha=al)
            ctx.restore()
        calendar(ctx, 1490, 210, t)
    with cam.layer(ctx, 1.35):
        police_tape(ctx, 960, 900, -0.07, tl.TAPE_T, t)
        police_tape(ctx, 960, 975, 0.05, tl.TAPE_T + 0.16, t)


def calendar(ctx, x, y, t):
    ft = tl.flip_times()
    idx = sum(1 for f in ft if f <= t)
    w, h = 300, 330
    fill_rect(ctx, x + 10, y + 12, w, h, "#000000", 0.25)
    fill_rect(ctx, x, y, w, h, "#ECE6D8")
    fill_rect(ctx, x, y, w, 70, RED)
    draw_text(ctx, "JUNE 13", x + w / 2, y + 50, 36, "#FFFFFF", align="center")
    for i in range(5):
        fill_circle(ctx, x + 40 + i * 55, y + 6, 9, "#2C3E50")
    year = tl.YEARS[idx]
    draw_text(ctx, str(year), x + w / 2, y + 230, 104, INK, face=FONT_BLACK, align="center")
    fill_rect(ctx, x + 40, y + 268, w - 80, 6, "#BDB4A2")
    # previous page flipping up and away
    if idx > 0:
        u = prog(t, ft[idx - 1], ft[idx - 1] + 0.1)
        if u < 1:
            ph = (1 - ease_in_cubic(u)) * (h - 70)
            fill_rect(ctx, x, y + 70, w, ph, "#F4EFE4")
            ctx.save()
            ctx.rectangle(x, y + 70, w, ph)
            ctx.clip()
            draw_text(ctx, str(tl.YEARS[idx - 1]), x + w / 2, y + 230, 104, INK, face=FONT_BLACK,
                      align="center")
            ctx.restore()
            fill_rect(ctx, x, y + 70 + ph - 6, w, 6, "#000000", 0.2)


def police_tape(ctx, cx, cy, ang, t0, t):
    u = ease_out_back(prog(t, t0 - 0.22, t0 + 0.12), 1.3)
    if u <= 0:
        return
    wob = 0.035 * math.exp(-max(0, t - t0) * 5) * math.sin(max(0, t - t0) * 32)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(ang + wob)
    L = 2700
    x0 = -L / 2
    ctx.rectangle(x0, -40, L * u, 80)
    ctx.clip()
    fill_rect(ctx, x0, -36 + 7, L, 80, "#000000", 0.3)
    fill_rect(ctx, x0, -36, L, 72, YELLOW)
    fill_rect(ctx, x0, -36, L, 6, INK)
    fill_rect(ctx, x0, 30, L, 6, INK)
    msg = "POLICE LINE  •  DO NOT CROSS  •  "
    w = text_w(ctx, msg, 34)
    x = x0 + 20
    while x < x0 + L:
        draw_text(ctx, msg, x, 13, 34, INK)
        x += w
    ctx.restore()


# ================================================================= 5. LAB

def lab(ctx, t):
    a, b = 21.3, 24.0
    cam = kb(t, a, b, 1.06, 1.16, (40, 8), (-40, -10))
    with cam.layer(ctx, 0.35):
        ctx.rectangle(-OVER, -OVER, W + 2 * OVER, H + 2 * OVER)
        ctx.set_source(vgrad(ctx, 0, 0, 0, H, [(0, "#14363C"), (1, "#0E2429")]))
        ctx.fill()
        for i in range(-3, 24):
            fill_rect(ctx, i * 100, -OVER, 2, H + 2 * OVER, "#18404A")
        for sy in (300, 560):
            fill_rect(ctx, 900, sy, 1300, 14, "#1F4C52")
            for k in range(7):
                fx = 940 + k * 170
                fill_rrect(ctx, fx, sy - 90, 50, 90, 10, "#21535A")
                fill_rect(ctx, fx + 15, sy - 120, 20, 40, "#21535A")
    with cam.layer(ctx, 0.7):
        monitor(ctx, 180, 200, t)
    with cam.layer(ctx, 0.85):
        tube_rack(ctx, 760, 860, t)
    with cam.layer(ctx, 0.95):
        helix(ctx, 1380, 540, t, pop(t, 21.35, d_in=0.55))
    s = pop(t, tl.MATCH_T, 23.75, d_in=0.4, d_out=0.2)
    plate(ctx, 220, 640, "DNA MATCH", "DNA MATCH", 64, RED, "#FFFFFF", accent=YELLOW, presence=s)


def monitor(ctx, x, y, t):
    w, h = 560, 380
    fill_rrect(ctx, x + 10, y + 12, w, h, 18, "#000000", 0.3)
    fill_rrect(ctx, x, y, w, h, 18, "#2C3E50")
    fill_rect(ctx, x + 22, y + 22, w - 44, h - 70, "#0B2227")
    fill_rect(ctx, x + w / 2 - 40, y + h, 80, 60, "#22313B")
    fill_rrect(ctx, x + w / 2 - 120, y + h + 56, 240, 18, 8, "#22313B")
    # gel lanes
    matched = t >= tl.MATCH_T
    import random
    for lane in range(4):
        rnd = random.Random(lane if lane != 3 else 1)
        lx = x + 70 + lane * 115
        draw_text(ctx, ("A", "B", "C", "D")[lane], lx + 35, y + 60, 22, "#6FA8A0", align="center")
        for k in range(7):
            by = y + 80 + rnd.random() * 220
            col = RED if matched and lane in (1, 3) else "#7FD1B9"
            fill_rrect(ctx, lx, by, 70, 9, 4, col, 0.9)
    scan = x + 22 + ((t - 21.3) * 380) % (w - 44)
    if not matched:
        fill_rect(ctx, scan, y + 22, 6, h - 70, "#7FD1B9", 0.45)
    lit = any(bt <= t < bt + 0.15 for bt in tl.BEEPS) or (matched and int(t * 6) % 2 == 0)
    fill_circle(ctx, x + w - 40, y + h - 24, 9, RED if lit else "#4A5A63")


def tube_rack(ctx, x, y, t):
    fill_rrect(ctx, x, y - 20, 360, 40, 8, "#5D6D7E")
    fill_rect(ctx, x + 20, y + 20, 22, 100, "#4D5B69")
    fill_rect(ctx, x + 318, y + 20, 22, 100, "#4D5B69")
    for k, (tx, liq, hgt) in enumerate(((60, "#5DADE2", 0.4), (160, RED, 0.62), (260, "#7FD1B9", 0.35))):
        top, bot = y - 300, y + 10
        fill_rrect(ctx, x + tx, top, 52, bot - top, 26, "#D6EAF0", 0.35)
        lv = bot - (bot - top) * hgt
        ctx.save()
        rrect(ctx, x + tx, top, 52, bot - top, 26)
        ctx.clip()
        fill_rect(ctx, x + tx, lv, 52, bot - lv, liq, 0.9)
        for i in range(4):
            ph = (t * 0.9 + i * 0.25 + k * 0.13) % 1.0
            fill_circle(ctx, x + tx + 16 + (i * 11) % 22, bot - 20 - ph * (bot - lv - 20), 4 + i % 3, "#FFFFFF",
                        0.5 * (1 - ph))
        ctx.restore()
        fill_rect(ctx, x + tx + 8, top + 20, 8, bot - top - 60, "#FFFFFF", 0.25)
        fill_rrect(ctx, x + tx - 6, top - 14, 64, 22, 6, "#ECE6D8")


def helix(ctx, cx, cy, t, s):
    if s <= 0.001:
        return
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(s, s)
    ctx.rotate(0.18)
    n, dy, A = 26, 32, 120
    phase = t * 2.6
    items = []
    for i in range(n):
        yy = (i - n / 2) * dy
        ang = phase + i * 0.42
        for strand in (0, 1):
            a2 = ang + strand * math.pi
            xx = A * math.sin(a2)
            z = math.cos(a2)
            items.append((z, "node", xx, yy, strand))
        items.append((-0.01, "rung", A * math.sin(ang), yy, i))
        if i < n - 1:
            for strand in (0, 1):
                a1, a2 = ang + strand * math.pi, ang + 0.42 + strand * math.pi
                zz = (math.cos(a1) + math.cos(a2)) / 2
                items.append((zz - 0.001, "bone", (A * math.sin(a1), A * math.sin(a2)), yy, strand))
    items.sort(key=lambda it: it[0])
    for z, kind, xx, yy, k in items:
        if kind == "rung":
            ctx.set_line_width(7)
            ctx.move_to(xx, yy)
            ctx.line_to(0, yy)
            src(ctx, (RED, YELLOW, "#7FD1B9", "#5DADE2")[k % 4], 0.85)
            ctx.stroke()
            ctx.move_to(0, yy)
            ctx.line_to(-xx, yy)
            src(ctx, ("#7FD1B9", "#5DADE2", RED, YELLOW)[k % 4], 0.85)
            ctx.stroke()
        elif kind == "bone":
            depth = 0.5 + 0.5 * z
            base = "#48C9B0" if k == 0 else "#E8EEF0"
            ctx.set_line_width(10)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(xx[0], yy)
            ctx.line_to(xx[1], yy + dy)
            src(ctx, mix(shade(base, 0.45), hx(base), depth))
            ctx.stroke()
        else:
            depth = 0.5 + 0.5 * z
            base = "#48C9B0" if k == 0 else "#E8EEF0"
            c = mix(shade(base, 0.45), hx(base), depth)
            fill_circle(ctx, xx, yy, 11 + 7 * depth, c)
    ctx.restore()


# ================================================================= 6. MAP

US = [(-124.7, 48.4), (-123.4, 48.15), (-122.9, 48.05), (-122.4, 47.4), (-122.5, 48.3), (-122.75, 49.0),
      (-95.15, 49.0), (-95.15, 49.38), (-94.8, 48.8), (-89.6, 48.0), (-84.8, 46.9), (-84.4, 46.0),
      (-83.5, 46.0), (-82.5, 45.3), (-82.4, 43.0), (-83.1, 42.0), (-82.5, 41.7), (-79.0, 42.8),
      (-79.2, 43.4), (-76.2, 43.6), (-75.0, 44.8), (-71.5, 45.0), (-70.0, 46.7), (-69.2, 47.45),
      (-67.8, 47.1), (-67.8, 45.7), (-67.0, 44.8), (-68.8, 44.3), (-70.2, 43.6), (-70.8, 42.8),
      (-70.0, 41.7), (-71.4, 41.4), (-73.7, 40.9), (-74.0, 40.5), (-74.0, 39.6), (-74.9, 38.9),
      (-75.1, 38.4), (-75.9, 37.5), (-76.0, 36.9), (-75.5, 35.6), (-76.5, 34.7), (-77.9, 33.9),
      (-79.2, 33.2), (-80.8, 32.1), (-81.4, 30.7), (-81.0, 29.5), (-80.1, 26.9), (-80.4, 25.2),
      (-81.1, 25.1), (-81.8, 26.1), (-82.7, 27.8), (-82.8, 29.2), (-84.0, 30.1), (-85.4, 29.7),
      (-86.5, 30.4), (-88.0, 30.4), (-89.6, 30.2), (-89.4, 29.2), (-90.5, 29.1), (-92.0, 29.6),
      (-93.8, 29.7), (-95.0, 29.2), (-96.8, 28.2), (-97.4, 27.0), (-97.2, 25.9), (-99.1, 26.4),
      (-100.3, 28.0), (-101.4, 29.8), (-102.4, 29.8), (-103.1, 29.0), (-104.5, 29.6), (-106.5, 31.8),
      (-108.2, 31.8), (-108.2, 31.3), (-111.1, 31.3), (-114.8, 32.5), (-117.1, 32.5), (-117.3, 33.2),
      (-118.4, 34.0), (-120.6, 34.5), (-121.9, 36.3), (-122.5, 37.5), (-123.0, 38.0), (-123.7, 39.0),
      (-124.2, 40.4), (-124.2, 41.9), (-124.5, 42.8), (-124.0, 44.6), (-123.9, 46.2), (-124.1, 46.9)]
CONCORD = (-80.58, 35.41)
PORT_ANGELES = (-123.43, 48.12)


def albers(lon, lat):
    p1, p2, p0, l0 = map(math.radians, (29.5, 45.5, 37.5, -96.0))
    n = (math.sin(p1) + math.sin(p2)) / 2
    C = math.cos(p1) ** 2 + 2 * n * math.sin(p1)
    rho0 = math.sqrt(C - 2 * n * math.sin(p0)) / n
    phi, lam = math.radians(lat), math.radians(lon)
    rho = math.sqrt(C - 2 * n * math.sin(phi)) / n
    th = n * (lam - l0)
    return rho * math.sin(th), rho0 - rho * math.cos(th)


def _map_fit():
    pts = [albers(*p) for p in US]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    sc = 1380 / (max(xs) - min(xs))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return lambda lon, lat: (W / 2 + (albers(lon, lat)[0] - cx) * sc, 560 - (albers(lon, lat)[1] - cy) * sc)


PROJ = _map_fit()


def route_points(n=160):
    (x0, y0), (x1, y1) = PROJ(*CONCORD), PROJ(*PORT_ANGELES)
    cxp, cyp = (x0 + x1) / 2 + 60, min(y0, y1) - 40
    return [((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cxp + u * u * x1,
             (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cyp + u * u * y1) for u in (i / (n - 1) for i in range(n))]


ROUTE = route_points()


def map_scene(ctx, t):
    a, b = 24.0, 27.2
    cam = kb(t, a, b, 1.14, 1.04, (-170, 20), (150, 10))
    with cam.layer(ctx, 0.3):
        bg_fill(ctx, "#122230")
        for i in range(-4, 30):
            fill_rect(ctx, i * 80, -OVER, 2, H + 2 * OVER, "#182C3B")
        for j in range(-4, 20):
            fill_rect(ctx, -OVER, j * 80, W + 2 * OVER, 2, "#182C3B")
    with cam.layer(ctx, 0.8):
        pts = [PROJ(*p) for p in US]
        poly(ctx, [(x + 10, y + 14) for x, y in pts], "#0A141C", 0.8)
        poly(ctx, pts, "#2E4A5A")
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.close_path()
        ctx.set_line_width(3)
        src(ctx, "#4B6E80")
        ctx.stroke()
        # route
        u = ease_in_out(prog(t, *tl.MAP_LINE))
        m = max(2, int(u * len(ROUTE)))
        if u > 0:
            ctx.move_to(*ROUTE[0])
            for p in ROUTE[1:m]:
                ctx.line_to(*p)
            ctx.set_line_width(9)
            ctx.set_dash([24, 16])
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            src(ctx, RED)
            ctx.stroke()
            ctx.set_dash([])
            if u < 1:
                hx_, hy_ = ROUTE[m - 1]
                fill_circle(ctx, hx_, hy_, 14, RED)
                fill_circle(ctx, hx_, hy_, 6, "#FFFFFF")
        pin(ctx, *PROJ(*CONCORD), t, 24.2)
        pin(ctx, *PROJ(*PORT_ANGELES), t, tl.MAP_LINE[1])
        x, y = PROJ(*CONCORD)
        plate(ctx, x + 40, y + 10, "CONCORD, NC", "CONCORD, NC", 34, "#1B2631", "#FFFFFF", accent=RED,
              presence=pop(t, 24.3, 26.9))
        x, y = PROJ(*PORT_ANGELES)
        plate(ctx, x + 40, y - 20, "PORT ANGELES, WA", "PORT ANGELES, WA", 34, "#1B2631", "#FFFFFF",
              accent=RED, presence=pop(t, tl.MAP_LINE[1] + 0.05, 26.9))
    # mileage counter (screen space)
    u = prog(t, *tl.MAP_LINE)
    miles = int(round(3000 * ease_out_cubic(u) / 10) * 10)
    plus = "+" if u >= 1 else ""
    label = f"{miles:,}{plus} MILES"
    plate(ctx, 150, 900, label, "3,000+ MILES", 60, YELLOW, INK, presence=pop(t, 24.6, 26.95))


def pin(ctx, x, y, t, t_in):
    s = pop(t, t_in, 26.9)
    if s <= 0:
        return
    ph = ((t - t_in) * 1.2) % 1.0
    ctx.set_line_width(4)
    ctx.new_sub_path()
    ctx.arc(x, y, 18 + ph * 50, 0, 2 * math.pi)
    src(ctx, RED, (1 - ph) * 0.8 * min(1, s))
    ctx.stroke()
    fill_circle(ctx, x, y, 17 * s, RED)
    fill_circle(ctx, x, y, 7 * s, "#FFFFFF")


# ================================================================= 7. FINAL CARD

def final(ctx, t):
    a, b = 27.2, 30.0
    cam = kb(t, a, b, 1.0, 1.07, (0, 0), (-20, -8))
    with cam.layer(ctx, 0.3):
        g = cairo.RadialGradient(W / 2, H / 2, 50, W / 2, H / 2, 1200)
        g.add_color_stop_rgba(0, *hx("#1C2A36"))
        g.add_color_stop_rgba(1, *hx("#05080B"))
        ctx.rectangle(-OVER, -OVER, W + 2 * OVER, H + 2 * OVER)
        ctx.set_source(g)
        ctx.fill()
    for depth, n, sz in ((0.6, 40, 3), (1.2, 18, 5)):
        with cam.layer(ctx, depth):
            for i in range(n):
                x = (i * 389 + t * 14 * depth) % (W + 200) - 100
                y = (i * 211 - t * 9 * depth) % (H + 200) - 100
                fill_circle(ctx, x, y, sz, "#C9D6DF", 0.12)
    with cam.layer(ctx, 1.0):
        shown, full = tl.typed("final", t)
        size = 132
        w = text_w(ctx, full, size, FONT_BLACK)
        x0 = W / 2 - w / 2
        draw_text(ctx, shown, x0 + 6, 600 + 6, size, "#000000", face=FONT_BLACK, alpha=0.5)
        draw_text(ctx, shown, x0, 600, size, "#F2F2F2", face=FONT_BLACK)
        sw = text_w(ctx, shown, size, FONT_BLACK)
        if t >= tl.FINAL_TEXT_T and (len(shown) < len(full) or int(t * 3) % 2 == 0):
            fill_rect(ctx, x0 + sw + 8, 600 - size * 0.74, 14, size * 0.78, RED)
        bar = ease_out_back(prog(t, 28.85, 29.25))
        if bar > 0:
            fill_rect(ctx, W / 2 - (w / 2) * bar, 650, w * bar, 12, RED)


SCENE_FUNCS = {"concord": concord, "office": office, "aftermath": aftermath, "coldcase": coldcase,
               "lab": lab, "map": map_scene, "final": final}


def board_extras(ctx, t, age):
    """Polaroid of the plant and a newspaper clipping on the lower half of the cork board."""
    s = pop(t, 16.95, d_in=0.4)
    if s > 0:
        ctx.save()
        ctx.translate(360, 650)
        ctx.rotate(0.07)
        ctx.scale(s, s)
        fill_rect(ctx, -110 + 8, -95 + 10, 220, 200, "#000000", 0.25)
        fill_rect(ctx, -110, -95, 220, 200, mix(PAPER, "#D9C07E", age))
        fill_rect(ctx, -95, -80, 190, 140, mix("#5E7A90", "#8C8574", age))
        fill_rect(ctx, -70, -20, 140, 80, mix("#8A4E3C", "#8C7462", age))
        for i in range(4):
            fill_rect(ctx, -58 + i * 34, 0, 20, 24, "#22313B")
        fill_rect(ctx, 40, -60, 14, 40, mix("#6F3D30", "#7C6658", age))
        fill_circle(ctx, 0, -84, 9, RED)
        ctx.restore()
    s = pop(t, 17.2, d_in=0.4)
    if s > 0:
        ctx.save()
        ctx.translate(1238, 665)
        ctx.rotate(-0.05)
        ctx.scale(s, s)
        paper = mix("#E4E0D6", "#D2BE8A", age)
        fill_rect(ctx, -120 + 8, -100 + 10, 240, 210, "#000000", 0.25)
        fill_rect(ctx, -120, -100, 240, 210, paper)
        draw_text(ctx, "UNSOLVED", 0, -52, 36, INK, face=FONT_BLACK, align="center", alpha=1 - age * 0.5)
        fill_rect(ctx, -100, -38, 200, 4, INK, 0.7)
        for i in range(6):
            fill_rect(ctx, -100 + (i % 2) * 105, -22 + (i // 2) * 34, 95, 8, "#8A8577")
            fill_rect(ctx, -100 + (i % 2) * 105, -8 + (i // 2) * 34, 75, 8, "#8A8577")
        fill_circle(ctx, 0, -88, 9, RED)
        ctx.restore()
