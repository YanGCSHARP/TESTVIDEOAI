"""Locations. Each function draws a plate in the 1920x1080 design space (rain and moving props are live)."""
import math

import cairo
import numpy as np

from kit import (hx, src, poly, rect, rrect, rrect_path, circle, ellipse, vgrad, hgrad, glow, cone, pines, AMBER, RED)
import chars as C

DW, DH = 1920, 1080


def sky(ctx, horizon=700, top="#070C12", mid="#15222D", low="#2A3B48"):
    vgrad(ctx, -50, -50, DW + 100, horizon + 60, [(0, top, 1), (0.7, mid, 1), (1, low, 1)])


# ----------------------------------------------------------------- road (side view)

def forest_road_side(P, diner=False):
    c = P.bg
    sky(c)
    pines(c, DW, 600, 260, "#22323D", seed=1)
    pines(c, DW, 650, 320, "#18252E", seed=2)
    pines(c, DW, 700, 380, "#0F181F", seed=3)
    if diner:
        rect(c, 980, 520, 520, 190, "#141B21")
        rect(c, 960, 500, 560, 24, "#1C252C")
        for k in range(6):
            rect(c, 1010 + k * 80, 570, 56, 60, "#0A0F13")
        rect(c, 1300, 420, 10, 110, "#151B1F")
        rrect(c, 1240, 380, 130, 50, 6, "#1A2228")       # dark diner sign (blank)
        glow(c, 1170, 470, 120, "#F7C98A", 0.5)
        rect(c, 1165, 400, 10, 90, "#151B1F")
        circle(c, 1170, 400, 8, "#F7C98A")
    vgrad(c, -50, 690, DW + 100, 260, [(0, "#1A2228", 1), (1, "#0C1115", 1)])
    rect(c, -50, 742, DW + 100, 4, "#6E7A82", 0.35)
    rect(c, -50, 905, DW + 100, 4, "#6E7A82", 0.35)
    for x in range(-20, DW + 40, 240):
        rect(c, x, 950, 18, 140, "#05080B")
    rect(c, -50, 960, DW + 100, 22, "#0A0F13")
    pines(c, DW, DH + 40, 70, "#030507", seed=9, jitter=0.6)
    P.meta["road_y"] = 812


# ----------------------------------------------------------------- windshield POV

def road_pov(P, town=False, vp=(960, 520), lamps=True, trees=True, shops=False, signals=False, wide_road=False):
    """View ahead through the windshield. Lane dashes are live (they move)."""
    c = P.bg
    sky(c, horizon=vp[1] + 40, low="#1E2C37" if town else "#22313D")
    vx, vy = vp
    if trees:
        pines(c, DW, vy + 30, 160, "#16222B", seed=11, spacing=0.8)
    if shops:
        for side in (-1, 1):
            for k in range(6):
                d = 0.25 + k * 0.15
                x = vx + side * (180 + 1400 * (1 - d) ** 1.7)
                hgt = 380 * (1 - d) + 60
                wdt = 260 * (1 - d) + 30
                x0 = x if side > 0 else x - wdt
                rect(c, x0, vy + 40 - hgt, wdt, hgt, "#121A20" if k % 2 else "#0F161B")
                if k % 2 == 0:
                    rect(c, x0 + wdt * 0.15, vy + 40 - hgt * 0.45, wdt * 0.7, hgt * 0.25, "#2B3C44" if k != 2 else "#9FC2B8", 0.8)
    road_w = 1500 if wide_road else 1150
    poly(c, [(vx - 8, vy + 40), (vx + 8, vy + 40), (vx + road_w, DH + 60), (vx - road_w, DH + 60)], "#151C21")
    for side in (-1, 1):
        poly(c, [(vx + side * 8, vy + 40), (vx + side * 12, vy + 40), (vx + side * (road_w - 60), DH + 60),
                 (vx + side * (road_w - 90), DH + 60)], "#6C767C", 0.35)
    if lamps:
        for k in range(5):
            d = 0.15 + k * 0.2
            for side in (-1, 1):
                x = vx + side * (130 + 1100 * (1 - d) ** 2)
                yb = vy + 40 + (DH - vy) * (1 - d) ** 2 * 0.95
                hgt = 600 * (1 - d) ** 2 + 40
                rect(c, x - 3 * (1 - d) - 1, yb - hgt, 6 * (1 - d) + 2, hgt, "#151B1F")
                lx = x - side * 60 * (1 - d)
                glow(c, lx, yb - hgt, 160 * (1 - d) + 20, "#F7C98A", 0.9)
                glow(c, lx, yb + 10, 380 * (1 - d) + 30, "#F7C98A", 0.16, sx=1.2, sy=0.3)
    if signals:
        for side in (-1, 1):
            x = vx + side * 230
            rect(c, x, vy - 150, 8, 200, "#151B1F")
            rrect(c, x - 18, vy - 210, 44, 90, 6, "#0A0D10")
            P.meta.setdefault("signals", []).append((x + 4, vy - 196))
    P.meta["vp"] = vp
    P.meta["road_w"] = road_w


def windshield_fg(P, phone=True, gauges=True):
    """Dark cab frame drawn on the foreground layer: A-pillar, roof edge, dash, gauges, phone mount."""
    c = P.fg
    poly(c, [(-60, -60), (200, -60), (40, DH + 60), (-60, DH + 60)], "#040609")
    poly(c, [(DW + 60, -60), (DW - 60, -60), (DW + 40, DH + 60)], "#040609")
    c.move_to(-60, -60)
    c.line_to(DW + 60, -60)
    c.line_to(DW + 60, 40)
    c.curve_to(DW * 0.6, 72, DW * 0.3, 72, -60, 52)
    c.close_path()
    src(c, "#040609")
    c.fill()
    c.move_to(-60, 905)
    c.curve_to(DW * 0.3, 860, DW * 0.7, 850, DW + 60, 880)
    c.line_to(DW + 60, DH + 60)
    c.line_to(-60, DH + 60)
    c.close_path()
    src(c, "#07090C")
    c.fill()
    if gauges:
        for k, x in enumerate((330, 450)):
            circle(c, x, 985, 48, "#120D06")
            glow(c, x, 985, 66, AMBER, 0.35)
            c.set_line_width(4)
            c.move_to(x, 985)
            c.line_to(x + 30 * math.cos(-0.5 - k), 985 + 30 * math.sin(-0.5 - k))
            src(c, "#FFB04A", 0.9)
            c.stroke()
    if phone:
        rrect(c, 1500, 880, 150, 260, 16, "#0B0E12")
        rect(c, 1511, 893, 128, 240, "#0E2A44")
        glow(c, 1575, 960, 150, "#3E8BD6", 0.3)
        P.meta["phone_small"] = (1511, 893, 128, 240)
    P.meta["glass"] = (60, 60, DW - 120, 800)


# ----------------------------------------------------------------- the sign

def sign(P, panel=(720, 260, 760, 470), forest=True):
    c = P.bg
    px, py, pw, ph = panel
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#060A0E", 1), (0.6, "#121C24", 1), (1, "#0B1115", 1)])
    if forest:
        pines(c, DW, 720, 330, "#16222A", seed=4)
        for x, y in ((240, 640), (300, 610), (380, 650), (170, 660)):
            glow(c, x, y, 40, "#F0A24A", 0.8)
    rect(c, -50, 760, DW + 100, 400, "#0C1216")
    glow(c, px + pw / 2 + 120, 840, 520, "#F6E6C4", 0.18, sx=1.3, sy=0.35)
    for lx in (px + pw * 0.18, px + pw * 0.79):
        rect(c, lx, py + ph - 10, 16, 340, "#2B3236")
    rect(c, px + pw / 2 - 6, py - 90, 12, 90, "#2B3236")
    rrect(c, px + pw / 2 - 70, py - 120, 140, 46, 10, "#1E2428")
    cone(c, px + pw / 2, py - 80, [(px - 120, py + ph + 40), (px + pw + 120, py + ph + 40)], "#FFF2D8", 0.18)
    vgrad(c, px, py, pw, ph, [(0, "#F2EEE4", 1), (1, "#C9C6BD", 1)])
    for k in range(3):
        rect(c, px + pw * 0.09, py + ph * 0.7 + k * ph * 0.072, pw * (0.82 - k * 0.12), ph * 0.038, "#9A988F", 0.8)
    r = np.random.default_rng(5)
    c.set_line_width(ph * 0.03)
    for k in range(26):
        yy = py + ph * 0.68 + r.uniform(0, ph * 0.23)
        c.move_to(px + pw * 0.08 + r.uniform(0, 40), yy)
        c.curve_to(px + pw * 0.33, yy + r.uniform(-20, 20), px + pw * 0.6, yy + r.uniform(-20, 20), px + pw * 0.9, yy + r.uniform(-15, 15))
        src(c, "#141414", 0.75)
        c.stroke()
    for tx, ty, tr in ((0.8, 0.26, 26), (0.12, 0.47, 18), (0.68, 0.62, 14)):
        x, y = px + pw * tx, py + ph * ty
        poly(c, [(x, y), (x + tr, y + tr * 0.4), (x + tr * 0.6, y + tr * 1.2), (x - tr * 0.3, y + tr * 0.7)], "#6F6C64")
    glow(c, px + pw / 2, py - 96, 90, "#FFF4DC", 1.0)
    P.meta["panel"] = (px + pw * 0.04, py + ph * 0.05, pw * 0.92, ph * 0.6)
    P.meta["cones"] = [[(px + pw / 2, py - 80), (px - 150, py + ph + 60), (px + pw + 150, py + ph + 60)]]


def printed_sign(P, panel=(560, 180, 800, 560)):
    """County sign: clean printed panel (text is an overlay)."""
    c = P.bg
    px, py, pw, ph = panel
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#05080B", 1), (1, "#0A0F13", 1)])
    rect(c, -50, 800, DW + 100, 300, "#0C1115")
    for lx in (px + pw * 0.18, px + pw * 0.79):
        rect(c, lx, py + ph - 10, 18, 400, "#2B3236")
    vgrad(c, px, py, pw, ph, [(0, "#F4F2EC", 1), (1, "#CFCCC3", 1)])
    rect(c, px, py, pw, 16, "#C0392B")
    rect(c, px, py + ph - 16, pw, 16, "#C0392B")
    P.meta["panel"] = (px + pw * 0.05, py + ph * 0.08, pw * 0.9, ph * 0.84)


# ----------------------------------------------------------------- plant in the distance

def plant(P):
    c = P.bg
    sky(c, horizon=640, low="#2B3A44")
    for k, (x, w, h) in enumerate(((600, 220, 260), (860, 160, 330), (1060, 300, 200), (1400, 140, 280))):
        rect(c, x, 640 - h, w, h, "#16222A")
        for j in range(4):
            glow(c, x + w * (0.2 + 0.2 * j), 640 - h * 0.6, 26, "#F0A24A", 0.8)
    for x in (930, 980, 1460):
        rect(c, x, 220, 22, 200, "#14202A")
        glow(c, x + 11, 230, 30, RED, 0.8)
    c.save()
    c.translate(1250, 470)
    c.scale(1, 0.5)
    circle(c, 0, 0, 120, "#16222A")
    c.restore()
    rect(c, 1130, 470, 240, 170, "#16222A")
    pines(c, DW, 760, 300, "#0E161C", seed=21)
    pines(c, DW, 900, 380, "#080D11", seed=22)
    P.meta["blink"] = [(941, 230), (991, 230), (1471, 230)]


# ----------------------------------------------------------------- gas station

def station(P, truck_parked=False):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#05080C", 1), (0.55, "#0E161C", 1), (1, "#080C10", 1)])
    pines(c, DW, 520, 200, "#0E161C", seed=6)
    poly(c, [(160, 690), (1820, 690), (DW + 50, 900), (-50, 900)], "#1B2328")
    glow(c, 860, 720, 760, "#E9F3F0", 0.30, sx=1.0, sy=0.28)
    rect(c, 1260, 380, 560, 330, "#2A3036")
    vgrad(c, 1290, 430, 500, 230, [(0, "#E7F5F1", 1), (1, "#BFD9D4", 1)])
    for k in range(4):
        rect(c, 1300 + k * 120, 470, 90, 14, "#8AA19C")
        rect(c, 1300 + k * 120, 540, 90, 14, "#8AA19C")
    rect(c, 1520, 430, 6, 230, "#2A3036")
    poly(c, [(240, 330), (1300, 330), (1300, 400), (240, 400)], "#C9CBC6")
    rect(c, 240, 352, 1060, 26, "#9B2F2A")
    rect(c, 250, 400, 1040, 16, "#F4FBFF")
    for k in range(5):
        glow(c, 330 + k * 220, 410, 120, "#F4FBFF", 0.9, sx=1.4, sy=0.5)
    for cx in (360, 1180):
        rect(c, cx, 416, 24, 290, "#B9BDB8")
    for x in (470, 650, 860, 1040):
        rect(c, x, 560, 64, 140, "#D7DAD6")
        rect(c, x + 10, 580, 44, 30, "#6FC3B3")
        rect(c, x - 10, 696, 84, 12, "#7F8580")
    C.sedan(c, 260, 700)
    for x in (330, 550, 770, 990, 1210, 1540):
        glow(c, x, 800, 90, "#E6F2F0", 0.22, sx=0.35, sy=1.4)
    rect(c, -50, 900, DW + 100, 200, "#0A0E11")
    if truck_parked:
        C.truck_side(c, 1560, 860, 0.38, headlights=False, facing=-1, cab_glow=0.2)
    P.meta["cones"] = [[(240, 410), (1300, 410), (1300, 700), (240, 700)]]
    P.meta["entrance"] = (1530, 600)


def station_high(P):
    """High wide of the lot: the truck pulls in at the far edge, facing the exit (truck is live)."""
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#070B0F", 1), (1, "#0D1418", 1)])
    poly(c, [(0, 380), (DW, 380), (DW, DH), (0, DH)], "#1A2126")
    for k in range(8):
        rect(c, 120 + k * 210, 820, 8, 120, "#C9CDC8", 0.25)
    rect(c, 300, 300, 1100, 180, "#C9CBC6")             # canopy roof seen from above
    rect(c, 300, 300, 1100, 26, "#9B2F2A")
    glow(c, 850, 520, 700, "#E9F3F0", 0.32, sx=1.1, sy=0.45)
    for x in (420, 640, 860, 1080):
        rect(c, x, 500, 50, 90, "#D7DAD6")
    rect(c, 1450, 260, 420, 300, "#2A3036")
    vgrad(c, 1470, 420, 380, 120, [(0, "#E7F5F1", 1), (1, "#BFD9D4", 1)])
    C.sedan(c, 330, 640, 0.9)
    P.meta["cones"] = [[(300, 480), (1400, 480), (1500, 780), (200, 780)]]


def sedan_close(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#0A1014", 1), (1, "#141B20", 1)])
    rect(c, -50, 760, DW + 100, 400, "#1B2328")
    glow(c, 900, 120, 900, "#F4FBFF", 0.35, sx=1.4, sy=0.4)
    C.sedan(c, -260, 900, 3.2)
    for x in (300, 700, 1300):
        glow(c, x, 880, 120, "#E6F2F0", 0.18, sx=0.4, sy=1.2)
    P.meta["cones"] = [[(-60, -60), (DW + 60, -60), (DW + 60, 700), (-60, 700)]]
    P.meta["dome"] = (412, 596)


def ignition(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#06080A", 1), (1, "#0E1216", 1)])
    rrect(c, 300, 300, 1400, 420, 60, "#14181C")               # dash
    rrect(c, 760, 500, 420, 600, 60, "#1B2025")                # steering column
    circle(c, 970, 640, 70, "#2B3238")
    circle(c, 970, 640, 34, "#0B0E11")
    rect(c, 955, 600, 30, 80, "#B9C0C5")                       # key
    rrect(c, 930, 670, 80, 120, 30, "#9EA6AB")
    c.set_line_width(8)
    c.arc(990, 820, 50, 0, 2 * math.pi)
    src(c, "#7D858A")
    c.stroke()
    rrect(c, 1010, 840, 60, 90, 10, "#6A3E2A")                 # leather tag
    glow(c, 1300, 420, 260, "#FFE7B0", 0.25)                    # dome light spill
    P.meta["warn"] = (620, 420)


# ----------------------------------------------------------------- store interior

def store_base(c):
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#7F9490", 1), (0.45, "#4E605D", 1), (1, "#1E2827", 1)])
    for k in range(4):
        glow(c, 240 + k * 480, -20, 380, "#E6F5EF", 0.35, sx=1.4, sy=0.5)


def coffee(P):
    c = P.bg
    store_base(c)
    rect(c, -50, 640, DW + 100, 500, "#3A4446")
    rect(c, -50, 630, DW + 100, 20, "#5E6A6C")
    for k in range(3):
        rrect(c, 300 + k * 480, 160, 380, 470, 18, "#1E2326")
        rect(c, 330 + k * 480, 200, 320, 120, "#2C3438")
        circle(c, 490 + k * 480, 380, 40, "#11161A")
        rect(c, 470 + k * 480, 420, 40, 60, "#0E1215")
    x = 1010
    rect(c, x - 70, 590, 140, 30, "#2B3135")                    # drip tray
    rect(c, x - 64, 594, 128, 18, "#2A170D", 0.9)
    poly(c, [(x - 44, 480), (x + 44, 480), (x + 36, 590), (x - 36, 590)], "#ECE6D8")
    ellipse(c, x, 482, 44, 8, "#2A170D")
    poly(c, [(x + 30, 482), (x + 44, 480), (x + 38, 560), (x + 32, 556)], "#3A2416", 0.8)   # overflow run
    for k in range(6):
        rrect(c, 200 + k * 260, 700, 200, 60, 8, "#C9CFCC", 0.3)
    P.meta["drip"] = (x, 470, 590)


def aisle(P):
    c = P.bg
    store_base(c)
    vp = (960, 420)
    poly(c, [(0, 300), (vp[0] - 60, vp[1] - 30), (vp[0] - 60, vp[1] + 60), (0, DH)], "#4E5B5D")
    poly(c, [(DW, 300), (vp[0] + 60, vp[1] - 30), (vp[0] + 60, vp[1] + 60), (DW, DH)], "#48555A")
    for side in (-1, 1):
        for k in range(5):
            y = 360 + k * 130
            x0 = 0 if side < 0 else DW
            poly(c, [(x0, y), (vp[0] + side * 60, vp[1] - 20 + k * 18), (vp[0] + side * 60, vp[1] - 14 + k * 18), (x0, y + 18)],
                 "#C9CFCC", 0.6)
            for j in range(10):
                u = j / 10
                xx = x0 + (vp[0] + side * 60 - x0) * u
                yy = y + (vp[1] - 20 + k * 18 - y) * u
                rect(c, xx - 20 * (1 - u), yy - 40 * (1 - u) - 4, 34 * (1 - u) + 2, 40 * (1 - u) + 3,
                     ("#B23A2E", "#C99A3A", "#3C6E8A", "#5C8A4A")[(j + k) % 4], 0.85)
    poly(c, [(vp[0] - 60, vp[1] + 60), (vp[0] + 60, vp[1] + 60), (DW, DH), (0, DH)], "#7D8987")
    # soup carton
    rect(c, 820, 760, 300, 170, "#B88A55")
    poly(c, [(820, 760), (1120, 760), (1160, 720), (860, 720)], "#C99A62")
    for k in range(4):
        ellipse(c, 870 + k * 66, 750, 28, 10, "#8C2E25")
    for k in range(3):
        rect(c, 760 + k * 60, 880, 40, 56, "#A3392D")
        ellipse(c, 780 + k * 60, 880, 20, 6, "#C9CFCC")


def counter_phone(P):
    c = P.bg
    store_base(c)
    vgrad(c, -50, 380, DW + 100, 760, [(0, "#4A5456", 1), (1, "#2A3234", 1)])
    rrect(c, 760, 430, 400, 560, 40, "#0C0F12")
    rect(c, 784, 460, 352, 500, "#0A1520")
    rrect(c, 300, 500, 300, 220, 20, "#1C2226")                  # register
    rect(c, 1300, 520, 400, 60, "#C9CFCC", 0.4)
    P.meta["phone"] = (784, 460, 352, 500)


def store_door(P, close=False):
    c = P.bg
    store_base(c)
    if close:
        rect(c, 360, -50, 1200, DH + 100, "#3E4849")
        vgrad(c, 420, 0, 1080, DH, [(0, "#66716F", 1), (1, "#3A4443", 1)])
        rect(c, 420, 0, 1080, 40, "#4A5554")
        rrect(c, 1340, 520, 120, 40, 14, "#B9C0C5")
        P.meta["door"] = (420, 0, 1080, DH)
        P.meta["handle"] = (1360, 540)
        return
    vp = (960, 430)
    poly(c, [(0, 250), (vp[0] - 160, vp[1] - 160), (vp[0] - 160, vp[1] + 200), (0, DH)], "#4E5B5D")
    poly(c, [(DW, 250), (vp[0] + 160, vp[1] - 160), (vp[0] + 160, vp[1] + 200), (DW, DH)], "#48555A")
    poly(c, [(vp[0] - 160, vp[1] + 200), (vp[0] + 160, vp[1] + 200), (DW, DH), (0, DH)], "#7D8987")
    rect(c, vp[0] - 160, vp[1] - 160, 320, 360, "#9FAEAC")
    rect(c, vp[0] - 70, vp[1] - 120, 140, 320, "#6D7778")
    rect(c, vp[0] + 40, vp[1] + 40, 22, 10, "#B9C0C5")
    rect(c, vp[0] - 70, vp[1] + 196, 140, 6, "#FFFFFF", 0.7)
    P.meta["door"] = (vp[0] - 70, vp[1] - 120, 140, 320)


def door_gap(P):
    c = P.bg
    rect(c, -50, -50, DW + 100, 760, "#3A4446")
    rect(c, -50, 640, DW + 100, 60, "#30393A")
    rect(c, -50, 700, DW + 100, 18, "#F4FBFF")
    glow(c, 960, 709, 500, "#F4FBFF", 0.5, sx=2.5, sy=0.15)
    vgrad(c, -50, 718, DW + 100, 400, [(0, "#5E6A69", 1), (1, "#222A2A", 1)])
    for k in range(6):
        rect(c, -50, 760 + k * 70, DW + 100, 3, "#6D7776", 0.6)
    for x in (820, 1010):
        rect(c, x, 700, 90, 18, "#1A1E20")
        poly(c, [(x, 718), (x + 90, 718), (x + 200, 1100), (x - 60, 1100)], "#000000", 0.18)


def floor_low(P):
    c = P.bg
    store_base(c)
    vgrad(c, -50, 520, DW + 100, 620, [(0, "#8E9A99", 1), (1, "#5A6566", 1)])
    for k in range(12):
        rect(c, -50, 560 + k * 48, DW + 100, 2, "#6D7776", 0.6)
    for k in range(10):
        c.move_to(k * 220, 520)
        c.line_to(k * 220 - 600 + k * 60, DH + 50)
        c.set_line_width(2)
        src(c, "#6D7776", 0.4)
        c.stroke()
    rect(c, 1500, 300, 500, 400, "#3A4446")                    # counter
    rect(c, 1060, 640, 300, 170, "#B88A55")                    # carton
    poly(c, [(1060, 640), (1360, 640), (1390, 610), (1090, 610)], "#C99A62")


def handle_close(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#4A5557", 1), (1, "#262E2F", 1)])
    glow(c, 1700, 100, 700, "#E6F5EF", 0.25)
    rect(c, 1500, -50, 40, DH + 100, "#30393A")
    rrect(c, 760, 420, 170, 280, 30, "#9DA5AA")                # escutcheon
    circle(c, 845, 520, 40, "#B9C0C5")
    circle(c, 845, 640, 14, "#2B3135")
    P.meta["pivot"] = (845, 520)


# ----------------------------------------------------------------- cab interior (Daniel in profile)

def cab_profile(P, light="#E39A3B", outside="night"):
    """Daniel's seat seen from the passenger side; the windshield is to the right of frame."""
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#06090C", 1), (1, "#0A0E12", 1)])
    # windshield and side window: night outside, softly lit
    poly(c, [(1180, 80), (DW + 50, 40), (DW + 50, 700), (1300, 640)], "#16222D")
    for k in range(5):
        glow(c, 1400 + k * 140, 300 + (k % 2) * 60, 60, "#F7C98A", 0.4)
    poly(c, [(80, 120), (980, 100), (980, 520), (80, 560)], "#111A22")
    glow(c, 500, 330, 300, "#2E4A5E", 0.4)
    c.set_line_width(26)
    src(c, "#05070A")
    c.move_to(1180, 80)
    c.line_to(1300, 640)
    c.stroke()
    rect(c, -50, 600, DW + 100, 500, "#0A0D10")
    # steering wheel rim (side-on) and dash
    poly(c, [(1200, 640), (DW + 50, 600), (DW + 50, 900), (1240, 900)], "#0E1215")
    glow(c, 1500, 700, 260, light, 0.35)
    c.set_line_width(30)
    src(c, "#15191C")
    c.save()
    c.translate(1240, 660)
    c.scale(0.35, 1)
    c.arc(0, 0, 230, 0, 2 * math.pi)
    c.restore()
    c.stroke()
    P.meta["daniel"] = (860, 650, 1.3)


# ----------------------------------------------------------------- phone close-up

def phone_close(P, bg="cab"):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#05080B", 1), (1, "#0A0E12", 1)])
    for k, (x, y, r) in enumerate(((300, 300, 120), (1500, 200, 160), (1700, 600, 90), (220, 760, 80))):
        circle(c, x, y, r, "#F7C98A" if k % 2 else "#9FB3C2", 0.12)
    rrect(c, 640, 120, 640, 900, 40, "#14181C")                # mount arms
    rrect(c, 690, 90, 540, 980, 60, "#0B0E12")
    rect(c, 720, 140, 480, 880, "#0B1B2C")
    P.meta["phone"] = (720, 140, 480, 880)


# ----------------------------------------------------------------- mirrors

def mirror(P, side="left"):
    """Side mirror in the foreground; the reflection (live) is clipped to meta['mirror']."""
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#070B0F", 1), (1, "#0E151A", 1)])
    for k in range(6):
        glow(c, 200 + k * 330, 300 + (k % 3) * 120, 90, "#F7C98A" if k % 2 else "#9FB3C2", 0.18)
    rect(c, -50, 800, DW + 100, 300, "#0C1115")
    f = P.fg
    x, y, w, h = (520, 170, 880, 700)
    rect(f, x + w + 20 if side == "left" else x - 260, y + h / 2 - 20, 240, 40, "#0A0D10")
    rrect_path(f, x - 40, y - 40, w + 80, h + 80, 70)
    rrect_path(f, x, y, w, h, 50)
    f.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    src(f, "#0A0D10")
    f.fill()
    f.set_fill_rule(cairo.FILL_RULE_WINDING)
    rrect_path(f, x, y, w, h, 50)
    f.set_line_width(6)
    src(f, "#2A3036")
    f.stroke()
    g = cairo.LinearGradient(x, y, x + w, y + h)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.10)
    g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
    rrect_path(f, x, y, w, h, 50)
    f.set_source(g)
    f.fill()
    P.meta["mirror"] = (x, y, w, h)


# ----------------------------------------------------------------- abandoned cars, details

def cars_side(P):
    c = P.bg
    sky(c, horizon=520, low="#1E2C37")
    for k in range(5):
        rect(c, k * 420 - 40, 220, 380, 330, "#10181E" if k % 2 else "#0D1419")
        rect(c, k * 420 + 20, 380, 260, 110, "#1B262E")
    rect(c, -50, 540, DW + 100, 70, "#2A3338")                 # sidewalk
    rect(c, -50, 600, DW + 100, 12, "#4A555A")                 # curb
    vgrad(c, -50, 612, DW + 100, 500, [(0, "#161D22", 1), (1, "#0B1014", 1)])
    for x in (300, 900, 1500):
        rect(c, x, 140, 12, 420, "#151B1F")
        glow(c, x + 6, 150, 70, "#F7C98A", 0.9)
        glow(c, x + 6, 700, 300, "#F7C98A", 0.14, sx=1.2, sy=0.4)
    C.sedan(c, 100, 760, 1.6, color="#5A2A28", door_open=False, dome=False, window_down=True)
    C.sedan(c, 1000, 860, 1.8, color="#33424D", door_open=False, dome=False, window_down=True, facing=1)
    for k in range(9):
        circle(c, 620 + k * 26 + (k % 3) * 8, 900 + (k % 2) * 14, 13, "#D9822B")
    poly(c, [(560, 900), (640, 900), (630, 850), (570, 846)], "#B89B6E")
    P.meta["exhaust"] = (1000, 830)


def car_window(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#0A1014", 1), (1, "#11181D", 1)])
    rect(c, -50, 560, DW + 100, 600, "#33424D")                 # door panel
    rect(c, -50, 560, DW + 100, 20, "#4A5A66")
    rect(c, 200, 120, 1400, 440, "#05080B")                     # open window: dark interior
    rect(c, 200, 120, 1400, 30, "#33424D")
    rrect(c, 260, 300, 500, 260, 40, "#141A1F")                 # seat back
    glow(c, 900, 200, 400, "#F7C98A", 0.15)
    rect(c, 1700, 600, 120, 40, "#22292E")
    P.meta["cones"] = [[(200, 150), (1600, 150), (1600, 560), (200, 560)]]


def jacket(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#0A1014", 1), (1, "#11181D", 1)])
    rect(c, -50, 700, DW + 100, 400, "#161D22")
    poly(c, [(300, 200), (1000, 200), (1000, 820), (300, 820)], "#2E3A44")          # car body
    poly(c, [(1000, 200), (1300, 120), (1300, 900), (1000, 820)], "#3A4752")        # open door
    rect(c, 1040, 260, 220, 200, "#05080B")
    glow(c, 650, 300, 260, "#FFE7B0", 0.25)
    P.meta["hook"] = (1180, 250)


# ----------------------------------------------------------------- crosswalk and town

def crosswalk(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#04070A", 1), (0.5, "#0F181F", 1), (1, "#0A0F13", 1)])
    rect(c, -50, 250, 750, 420, "#10181E")
    rect(c, 760, 300, 480, 370, "#131C22")
    rect(c, 1280, 220, 700, 450, "#0E151A")
    vgrad(c, 860, 420, 300, 170, [(0, "#CFE6DD", 1), (1, "#9CC3B7", 1)])
    for k in range(4):
        circle(c, 900 + k * 70, 540, 24, "#7BA59A")
    poly(c, [(-50, 690), (DW + 50, 690), (DW + 50, 880), (-50, 880)], "#141B20")
    for k in range(7):
        x0 = 520 + k * 130
        poly(c, [(x0, 700), (x0 + 70, 700), (x0 + 110 - k * 4, 860), (x0 + 10 - k * 4, 860)], "#9AA3A6", 0.55)
    rect(c, 1560, 160, 14, 540, "#151B1F")
    rect(c, 1490, 150, 90, 16, "#151B1F")
    glow(c, 1500, 172, 70, "#F7C98A", 1.0)
    cone(c, 1500, 172, [(1300, 720), (1720, 720)], "#F7C98A", 0.22)
    glow(c, 1500, 700, 260, "#F7C98A", 0.25, sx=1.3, sy=0.3)
    poly(c, [(1180, 700), (DW + 50, 700), (DW + 50, 740), (1150, 740)], "#2A3338")
    rect(c, 1390, 470, 10, 230, "#151B1F")
    rrect(c, 1370, 430, 54, 60, 6, "#0A0D10")
    circle(c, 1397, 446, 6, "#F4F7F2")
    rect(c, 1393, 452, 8, 20, "#F4F7F2")
    glow(c, 1397, 460, 40, "#F4F7F2", 0.6)
    rect(c, 220, 520, 300, 12, "#2A3238")
    rect(c, 220, 530, 300, 170, "#3E5361", 0.25)
    P.meta["cones"] = [[(1500, 172), (1300, 720), (1720, 720)]]
    P.meta["woman"] = (1470, 728, 1.12)
    P.meta["laundro_fig"] = (1010, 572, 0.28)
    P.meta["shelter_fig"] = (377, 690, 0.3)


def walk_signal(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#05080B", 1), (1, "#0D1418", 1)])
    glow(c, 1500, 200, 400, "#F7C98A", 0.3)
    rect(c, 930, 600, 60, 600, "#151B1F")
    rrect(c, 760, 220, 400, 420, 30, "#0A0D10")
    rrect(c, 800, 260, 320, 340, 20, "#05070A")
    circle(c, 960, 330, 30, "#F4F7F2")
    c.set_line_width(26)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    src(c, "#F4F7F2")
    for a, b in (((960, 370), (960, 470)), ((960, 390), (900, 450)), ((960, 390), (1020, 430)),
                 ((960, 470), (915, 560)), ((960, 470), (1010, 555))):
        c.move_to(*a)
        c.line_to(*b)
        c.stroke()
    glow(c, 960, 420, 260, "#F4F7F2", 0.5)


def wheel(P, center=False):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#05080B", 1), (1, "#0A0D10", 1)])
    poly(c, [(-50, -50), (DW + 50, -50), (DW + 50, 380), (-50, 420)], "#121D27")   # windshield, night
    for k in range(6):
        glow(c, 200 + k * 300, 200 + (k % 2) * 70, 70, "#F7C98A", 0.35)
    rect(c, -50, 420, DW + 100, 700, "#0B0E11")
    glow(c, 600, 640, 380, AMBER, 0.25)
    if center:
        circle(c, 960, 700, 520, "#15191C")
        circle(c, 960, 700, 450, "#0B0E11")
        rrect(c, 760, 560, 400, 300, 80, "#1E2327")                  # horn pad
        for a in (-0.4, math.pi + 0.4, math.pi / 2):
            c.save()
            c.translate(960, 700)
            c.rotate(a)
            rect(c, 0, -30, 460, 60, "#15191C")
            c.restore()
        P.meta["pad"] = (960, 700)
    else:
        c.set_line_width(80)
        src(c, "#15191C")
        c.arc(960, 1300, 900, math.pi * 1.2, math.pi * 1.8)
        c.stroke()
        P.meta["rim"] = (960, 1300, 900)


def laundromat(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#05080B", 1), (1, "#0C1216", 1)])
    rect(c, -50, 100, DW + 100, 860, "#111A20")
    vgrad(c, 260, 220, 1400, 560, [(0, "#CFE6DD", 1), (1, "#9CC3B7", 1)])
    for k in range(6):
        circle(c, 380 + k * 230, 640, 80, "#7BA59A")
        circle(c, 380 + k * 230, 640, 50, "#5C877C")
    rect(c, 260, 480, 1400, 14, "#86A89E")
    rect(c, 940, 220, 14, 560, "#111A20")
    rect(c, -50, 960, DW + 100, 200, "#0A0E11")
    P.meta["fig"] = (1180, 780, 0.95)


def bus_shelter(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#05080B", 1), (1, "#0C1216", 1)])
    rect(c, -50, 760, DW + 100, 400, "#11171B")
    rect(c, 500, 250, 900, 26, "#2A3238")
    rect(c, 500, 270, 900, 470, "#3E5361", 0.22)
    for x in (500, 1380):
        rect(c, x, 250, 20, 510, "#2A3238")
    glow(c, 1600, 150, 300, "#F7C98A", 0.5)
    P.meta["fig"] = (950, 760, 1.0)
    P.meta["cones"] = [[(1600, 150), (1200, 900), (2000, 900)]]


def awning(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#05080B", 1), (1, "#0C1216", 1)])
    rect(c, -50, -50, DW + 100, 900, "#3A2621")
    for k in range(26):
        for j in range(14):
            rect(c, j * 150 - (75 if k % 2 else 0), k * 36, 146, 33, "#4A3029" if (j + k) % 3 else "#432B25")
    poly(c, [(500, 220), (1500, 220), (1580, 340), (420, 340)], "#1E3B33")
    for k in range(10):
        poly(c, [(500 + k * 100, 220), (550 + k * 100, 220), (558 + k * 108, 340), (500 + k * 108, 340)], "#24463D")
    glow(c, 1000, 340, 300, "#F7C98A", 0.35, sx=1.6, sy=0.6)
    rect(c, -50, 850, DW + 100, 300, "#11171B")
    P.meta["figs"] = [(820, 850, 0.95), (1120, 850, 0.98)]


def town_aerial(P):
    c = P.bg
    rect(c, -50, -50, DW + 100, DH + 100, "#161D22")                         # streets
    r = np.random.default_rng(7)
    for i in range(-1, 10):
        for j in range(-1, 7):
            x, y = i * 220 + 25, j * 190 + 25
            rrect(c, x, y, 170, 140, 8, "#0F161B" if (i + j) % 3 else "#121A20")
            for k in range(3):
                rrect(c, x + 12 + k * 52, y + 12 + (k % 2) * 60, 44, 56, 4, "#0B1115")
            if r.random() < 0.12:
                rect(c, x + 40, y + 40, 30, 22, "#F7C98A", 0.55)
    lamps = []
    for i in range(0, 10):
        for j in range(0, 7):
            if r.random() < 0.35:
                x, y = i * 220 + 10, j * 190 + 10
                glow(c, x, y, 70, "#F7C98A", 0.55)
                circle(c, x, y, 4, "#FFE2B0")
                lamps.append((x, y))
    P.meta["lamps"] = lamps


def radio(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#08090B", 1), (1, "#0D1013", 1)])
    rrect(c, 360, 300, 1200, 480, 30, "#15181B")
    rrect(c, 640, 400, 640, 140, 16, "#2A1A08")
    for x in (480, 1440):
        circle(c, x, 470, 70, "#24282C")
        circle(c, x, 470, 50, "#1A1D20")
    for k in range(6):
        rrect(c, 650 + k * 105, 600, 85, 50, 8, "#24282C")
    P.meta["display"] = (640, 400, 640, 140)
    P.meta["knob"] = (480, 470)


# ----------------------------------------------------------------- health van

def van_street(P):
    road_pov(P, town=True, shops=True, lamps=True, trees=False)
    c = P.bg
    C.van_rear(c, 960, 760, 0.62)
    glow(c, 960, 520, 520, "#F4F8FF", 0.3, sx=1, sy=0.5)
    windshield_fg(P)


def van_cargo(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#1A2228", 1), (1, "#0E1317", 1)])
    rect(c, -50, 820, DW + 100, 300, "#22292E")
    for k in range(2):
        rect(c, 100, 300 + k * 260, 900, 14, "#3A444A")
    for k in range(6):
        rrect(c, 130 + k * 140, 190, 110, 110, 30, "#9FB8C4", 0.35)          # face shields
    for k in range(5):
        rrect(c, 130 + k * 170, 440, 150, 116, 10, "#DCE3E6", 0.8)            # suits in plastic
        rect(c, 130 + k * 170, 480, 150, 8, "#AEB8BD")
    c.set_line_width(14)
    src(c, "#3A444A")
    c.move_to(1200, 420)
    c.line_to(1260, 820)
    c.move_to(1380, 420)
    c.line_to(1320, 820)
    c.stroke()
    rect(c, 1180, 400, 220, 30, "#3A444A")
    rect(c, 1190, 600, 200, 24, "#3A444A")
    rrect(c, 1500, 640, 300, 200, 16, "#E8ECEE")
    rect(c, 1500, 680, 300, 10, "#C0392B")
    cx, cy = 1650, 760                                                         # biohazard trefoil
    for k in range(3):
        a = k * 2 * math.pi / 3 - math.pi / 2
        circle(c, cx + 22 * math.cos(a), cy + 22 * math.sin(a), 20, "#C0392B")
        circle(c, cx + 30 * math.cos(a), cy + 30 * math.sin(a), 13, "#E8ECEE")
    circle(c, cx, cy, 9, "#E8ECEE")
    glow(c, 960, -100, 900, "#F4F8FF", 0.35)
    P.meta["pile"] = (420, 520)


def paper(P, sheet="checklist"):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#C2C8CC", 1), (1, "#8E969A", 1)])
    glow(c, 960, 300, 900, "#FFFFFF", 0.4)
    x, y, w, h = (500, 90, 920, 900) if sheet == "checklist" else (420, 40, 1080, 1000)
    rect(c, x + 14, y + 16, w, h, "#000000", 0.25)
    rect(c, x, y, w, h, "#F2F1EC")
    for tx in (x + 20, x + w - 120):
        rect(c, tx, y - 10, 100, 40, "#E6DFC4", 0.85)
    if sheet == "contacts":
        for k in range(22):
            rect(c, x + 40, y + 80 + k * 41, w - 80, 2, "#B9C4CC")
            rect(c, x + 60, y + 92 + k * 41, 260 + (k * 37) % 120, 12, "#9AA4AA")
        P.meta["panel"] = (x + w * 0.55, y + 60, w * 0.42, h - 100)
    else:
        P.meta["panel"] = (x + 40, y + 60, w - 80, h - 120)


# ----------------------------------------------------------------- fence, pharmacy, truck front

def fence(P):
    c = P.bg
    sky(c, horizon=520, low="#1E2C37")
    rect(c, -50, 200, DW + 100, 400, "#10181E")
    vgrad(c, -50, 600, DW + 100, 500, [(0, "#161D22", 1), (1, "#0B1014", 1)])
    glow(c, 1500, 160, 260, "#F7C98A", 0.6)
    P.meta["cones"] = [[(1500, 160), (1100, 1000), (1900, 1000)]]


def pharmacy(P):
    c = P.bg
    sky(c, horizon=300)
    rect(c, 300, 120, 1300, 860, "#1A1F24")
    rect(c, 300, 120, 1300, 30, "#262C32")
    for k in range(4):
        rect(c, 380 + k * 300, 200, 200, 260, "#0B1014")
    rect(c, 360, 600, 1180, 300, "#0E1418")
    rect(c, 360, 600, 1180, 300, "#2E4A5A", 0.25)
    rrect(c, 880, 520, 160, 60, 8, "#2A3E36")                                  # dark cross sign shape
    rect(c, 940, 528, 40, 44, "#3E6656")
    rect(c, 918, 540, 84, 20, "#3E6656")
    glow(c, 200, 400, 200, "#F7C98A", 0.5)
    rect(c, -50, 980, DW + 100, 200, "#0B0F12")
    P.meta["win_fig"] = (680, 460, 0.5)
    P.meta["shop_fig"] = (1180, 900, 0.62)


def street_ahead(P):
    road_pov(P, town=True, shops=True, lamps=True, trees=False, vp=(960, 470))


# ----------------------------------------------------------------- checkpoint

def checkpoint(P, pov=False, far=False, worker_fig=False):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#06090D", 1), (0.6, "#141C22", 1), (1, "#0B0F12", 1)])
    pines(c, DW, 560, 220, "#0F171D", seed=8)
    rect(c, -50, 600, DW + 100, 500, "#11171B")
    if far:
        for x in (-50, DW - 420):
            for k in range(3):
                rect(c, x + k * 160, 520 - k * 30, 140, 300, "#0C1216")
        c.save()
        c.translate(960, 600)
        c.scale(0.42, 0.42)
        c.translate(-960, -600)
    glow(c, 960, 760, 900, "#F4F8FF", 0.22, sx=1.2, sy=0.3)
    rect(c, 1150, 470, 360, 170, "#C5CBCF")
    rect(c, 1150, 470, 70, 170, "#0C1013")
    poly(c, [(1150, 480), (1105, 470), (1105, 640), (1150, 630)], "#AEB5BA")
    poly(c, [(600, 520), (880, 520), (900, 560), (900, 640), (600, 640)], "#14181C")
    poly(c, [(720, 530), (680, 500), (680, 640), (720, 620)], "#1C2126")
    cones = []
    for tx in (470, 1520):
        rect(c, tx - 6, 190, 12, 460, "#20272C")
        rect(c, tx - 80, 175, 160, 50, "#20272C")
        for k in range(4):
            glow(c, tx - 60 + k * 40, 200, 34, "#FFFFFF", 1.0)
        glow(c, tx, 200, 380, "#EAF2FF", 0.55)
        cone(c, tx, 205, [(tx - 520, 900), (tx + 520, 900)], "#EAF2FF", 0.12)
        cones.append([(tx, 205), (tx - 520, 900), (tx + 520, 900)])
    for x in (200, 420, 1460, 1680):
        poly(c, [(x, 720), (x + 200, 720), (x + 180, 660), (x + 20, 660)], "#9DA3A4")
        rect(c, x, 720, 200, 26, "#7E8485")
    for k in range(10):
        rect(c, 640 + k * 72, 640, 72, 26, "#C0392B" if k % 2 == 0 else "#E8E8E2")
    rect(c, 620, 630, 26, 100, "#30363A")
    rect(c, 1700, 560, 160, 10, "#5A6064")                                    # folding table
    for x in (1710, 1840):
        rect(c, x, 570, 6, 90, "#5A6064")
    if worker_fig:
        C.worker(c, 1010, 790, 0.95)
    if far:
        c.restore()
        P.meta["cones"] = [[(960 + (x - 960) * 0.42, 600 + (y - 600) * 0.42) for x, y in cn] for cn in cones]
    else:
        P.meta["cones"] = cones
    if pov:
        windshield_fg(P)


def checkpoint_high(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#0A0F13", 1), (1, "#0E1418", 1)])
    poly(c, [(600, -50), (1320, -50), (1500, DH + 50), (420, DH + 50)], "#1A2126")            # road
    poly(c, [(300, 380), (1650, 380), (1700, 760), (250, 760)], "#2A2E2C")                    # gravel turnout
    r = np.random.default_rng(3)
    for _ in range(500):
        circle(c, r.uniform(260, 1690), r.uniform(385, 755), r.uniform(1, 3), "#3E423F", 0.6)
    for k in range(6):
        rect(c, 560 + k * 140, 200, 120, 40, "#9DA3A4")
    for k in range(8):
        rect(c, 600 + k * 90, 160, 90, 18, "#C0392B" if k % 2 == 0 else "#E8E8E2")
    for tx in (400, 1520):
        circle(c, tx, 150, 24, "#FFFFFF")
        glow(c, tx, 150, 600, "#EAF2FF", 0.35)
    rect(c, 1100, 40, 260, 110, "#C5CBCF")
    rect(c, 650, 50, 200, 90, "#14181C")
    P.meta["cones"] = [[(400, 150), (-50, 900), (900, 900)], [(1520, 150), (1000, 900), (DW + 50, 900)]]


def checkpoint_table(P):
    checkpoint(P)
    c = P.bg
    c.save()
    c.translate(1780, 640)
    c.rotate(1.2)
    rect(c, -40, -60, 80, 10, "#5A6064")                                       # tipped chair
    rect(c, -40, -60, 10, 80, "#5A6064")
    c.restore()
    for k in range(5):
        c.save()
        c.translate(1720 + k * 26, 556)
        c.rotate(0.2 * k - 0.4)
        rect(c, -14, -10, 28, 20, "#E6E6DE")
        c.restore()
    ellipse(c, 300, 700, 120, 40, "#C9CFCC")                                   # crumpled suit by the barrier
    ellipse(c, 360, 690, 70, 30, "#B7BEBB")


def barrier_close(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#0C1217", 1), (1, "#141C22", 1)])
    glow(c, 1500, 100, 700, "#EAF2FF", 0.55)
    poly(c, [(100, 1100), (1820, 1100), (1650, 520), (270, 520)], "#9DA3A4")
    rect(c, 270, 520, 1380, 30, "#B7BDBE")
    for k in range(6):
        rect(c, 300 + k * 230, 600 + (k % 2) * 80, 120, 4, "#7E8485", 0.6)
    P.meta["edge_y"] = 520
    P.meta["cones"] = [[(1500, 100), (700, 1100), (DW + 100, 1100)]]


def van_interior(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#0B1013", 1), (1, "#11171B", 1)])
    rect(c, 200, 80, 1520, 920, "#6E767B")
    rect(c, 260, 140, 1400, 800, "#0C1013")
    glow(c, 1700, 100, 600, "#EAF2FF", 0.25)
    rect(c, 300, 760, 1320, 30, "#2A3238")
    P.meta["fig"] = (960, 780)


def tire(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#0A0E11", 1), (1, "#141A1E", 1)])
    rect(c, -50, 760, DW + 100, 400, "#2A2E2C")
    r = np.random.default_rng(4)
    for _ in range(900):
        circle(c, r.uniform(-50, DW + 50), r.uniform(765, DH + 40), r.uniform(1.5, 5), "#3E423F", 0.7)
    rect(c, -50, 200, DW + 100, 330, "#7F8C96")                                # truck box underside
    rect(c, -50, 500, DW + 100, 40, "#2A3136")
    glow(c, 300, 700, 500, "#F4F8FF", 0.3)
    P.meta["wheel"] = (960, 640, 300)


# ----------------------------------------------------------------- the driver's side window

def side_window(P, outside="checkpoint", blur_bg=True):
    """From inside the cab, looking out of the closed driver window. Outside is out of focus."""
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#0C1218", 1), (1, "#06090C", 1)])
    if outside == "checkpoint":
        glow(c, 1500, 300, 620, "#F1F6FF", 0.9)
        glow(c, 330, 340, 320, "#F1F6FF", 0.45)
        for bx, by, br in ((1400, 260, 60), (1560, 240, 60), (1480, 380, 40), (280, 330, 45)):
            circle(c, bx, by, br, "#FFFFFF", 0.5)
        rect(c, -50, 760, DW + 100, 400, "#1A2026")
    P.meta["glass"] = (0, 230, DW, 650)
    P.meta["cones"] = [[(1500, 300), (900, 1100), (DW + 100, 1100), (DW + 100, 0)]]
    f = P.fg
    rect(f, -50, -50, DW + 100, 230, "#030406")
    rect(f, -50, 180, DW + 100, 50, "#101317")
    f.move_to(-50, 900)
    f.curve_to(DW * 0.4, 870, DW * 0.7, 860, DW + 50, 870)
    f.line_to(DW + 50, DH + 50)
    f.line_to(-50, DH + 50)
    f.close_path()
    src(f, "#0A0C0F")
    f.fill()
    rrect(f, 1240, 925, 230, 74, 18, "#16191D")
    rrect(f, 1272, 940, 64, 42, 9, "#2A2E33")
    glow(f, 1304, 960, 60, AMBER, 0.35)
    glow(f, 280, 940, 520, AMBER, 0.12, sx=1.6, sy=0.5)
    P.meta["switch"] = (1304, 961)
    if blur_bg:
        P.meta["blur_bg"] = True


def switch_close(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#0B0D10", 1), (1, "#07090B", 1)])
    rect(c, -50, -50, DW + 100, 380, "#121A22")                                # window above, night
    glow(c, 1500, 100, 500, "#F1F6FF", 0.35)
    rect(c, -50, 330, DW + 100, 20, "#1C2026")
    rrect(c, 300, 520, 1320, 320, 60, "#16191D")                               # armrest
    rrect(c, 700, 560, 300, 200, 26, "#22262B")
    rrect(c, 760, 590, 180, 140, 18, "#2E3339")                                # window switch
    rect(c, 790, 620, 120, 16, "#3C424A")
    glow(c, 850, 660, 200, AMBER, 0.25)
    P.meta["switch"] = (850, 660)


def shifter(P):
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#08090B", 1), (1, "#0D1013", 1)])
    rrect(c, 200, 300, 1500, 500, 40, "#121518")
    rrect(c, 820, 360, 300, 600, 60, "#1B2025")                                # column
    glow(c, 600, 500, 400, AMBER, 0.25)
    P.meta["pivot"] = (970, 480)


def truck_door_ext(P):
    """Outside the driver door: white cab door, dark window above, floodlit rain."""
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#10171D", 1), (1, "#0A0E12", 1)])
    glow(c, 300, 100, 700, "#EAF2FF", 0.45)
    vgrad(c, 500, 80, 1500, 1100, [(0, "#8E9AA3", 1), (1, "#4F5A62", 1)])
    rect(c, 560, 120, 1200, 440, "#0E161C")                                    # window
    glow(c, 1000, 450, 300, AMBER, 0.2)
    rect(c, 500, 580, 1500, 8, "#5E6A72")
    rrect(c, 1500, 680, 200, 60, 18, "#2A3136")                                # outside handle
    P.meta["handle"] = (1600, 710)
    P.meta["window"] = (560, 120, 1200, 440)
    P.meta["cones"] = [[(300, 100), (-50, 1100), (1200, 1100)]]


def weigh_station(P):
    """Muted daytime memory: Daniel's arm on an open window at a weigh station."""
    c = P.bg
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#8E979B", 1), (1, "#5E676B", 1)])
    rect(c, 1200, 200, 700, 400, "#6E777B")
    rect(c, 1250, 260, 280, 160, "#3E474B")
    rect(c, -50, 700, DW + 100, 400, "#4E575B")
    rect(c, -50, 300, 1150, 800, "#C9D0D4")                                     # truck door
    rect(c, 60, 300, 980, 30, "#9EA6AA")
    rect(c, 60, 330, 980, 290, "#2E363B")
    C.daniel_profile(c, 560, 620, 0.95, light="#FFFFFF", light_a=0.2)
    C.hand(c, 760, 610, 1.0, angle=0.0, pose="flat", light="#FFFFFF", light_a=0.1)


def black(P):
    rect(P.bg, -50, -50, DW + 100, DH + 100, "#000000")


def wheel_grip(P):
    wheel(P, center=False)
