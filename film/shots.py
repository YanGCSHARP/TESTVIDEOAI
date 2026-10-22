"""All 102 shots of DO NOT LOWER YOUR WINDOW: plate + camera + live animation per shot id."""
import math
from functools import partial

import cairo

import chars as C
import sets as L
from engine import Cam, Shot, clamp, prog, ease, ease_out, ease_in, lerp, noise1, DW, DH
from kit import src, rect, rrect, circle, ellipse, glow, poly, Drops, AMBER, RED, marker_text

WHITE_LIGHT = "#EAF2FF"
_drops = {}


# ----------------------------------------------------------------- live helpers

def drops(ctx, f, n=240, wipe=None, alpha=1.0):
    key = (f.sid, n)
    if key not in _drops:
        x, y, w, h = f.meta.get("glass", (60, 60, DW - 120, 800))
        _drops[key] = Drops(x, y, w, h, n, seed=hash(f.sid) % 9999)
    if wipe:  # drops build up between wiper passes
        alpha *= clamp(((f.T % wipe) / wipe) * 1.4)
    _drops[key].draw(ctx, f.T, alpha=alpha)


def wipers(ctx, f, period=1.7):
    ph = (f.T % period) / period
    a = math.sin(math.pi * ph) ** 0.8
    for px, rng in ((560, 1.25), (1250, 1.25)):
        ang = math.pi + 0.15 + a * rng
        ctx.save()
        ctx.translate(px, 905)
        ctx.rotate(ang)
        ctx.set_line_width(14)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(0, 0)
        ctx.line_to(760, 0)
        src(ctx, "#030405")
        ctx.stroke()
        ctx.restore()


def dashes(ctx, f, speed=0.9, color="#B8962E"):
    vx, vy = f.meta.get("vp", (960, 520))
    for k in range(10):
        d = (k / 10 + f.T * speed * 0.35) % 1.0
        d2 = (d + 0.04) % 1.0
        if d2 < d:
            continue
        y0, y1 = vy + 40 + (DH - vy) * d ** 2.2, vy + 40 + (DH - vy) * d2 ** 2.2
        w0, w1 = 2 + 26 * d ** 2.2, 2 + 26 * d2 ** 2.2
        poly(ctx, [(vx - w0, y0), (vx + w0, y0), (vx + w1, y1), (vx - w1, y1)], color, 0.6)


def item_t(f, n):
    """Local time of narration item n of this scene (None if unknown)."""
    t = f.items.get(n)
    return None if t is None else t - f.start


def cab_daniel(ctx, f, light=AMBER, light_a=0.6, scale=None, rim=None, shake=0.0, breath=False):
    x, y, s = f.meta.get("daniel", (860, 650, 1.3))
    s = scale or s
    bob = math.sin(f.T * 1.3) * 3 + shake * noise1(f.T * 6, 2)
    blink = (f.T % 3.7) < 0.12
    C.daniel_profile(ctx, x, y + bob, s, light=light, light_a=light_a, rim=rim, blink=blink)
    if breath:
        ph = (f.T % 2.6) / 2.6
        if ph < 0.6:
            glow(ctx, x + 150 * s + ph * 160, y - 90 * s - ph * 30, 40 + ph * 120, "#DCE6EE", 0.2 * (1 - ph / 0.6))


def passing_lights(ctx, f, color="#F7C98A", period=3.2):
    ph = (f.T % period) / period
    glow(ctx, lerp(DW + 300, -300, ph), 300, 520, color, 0.18)


def S(plate, cam=None, **kw):
    return Shot(plate=plate, cam=cam or Cam(), **kw)


RAIN = {"alpha": 1.0}
RAIN_SOFT = {"alpha": 0.6, "near": False}


def stack(*fns):
    def run(P):
        for fn in fns:
            fn(P)
    return run


# ----------------------------------------------------------------- S00 cold open

def _glove_rise(ctx, f):
    u = ease_out(prog(f.t, 0.2, f.dur * 0.75))
    C.glove_hand(ctx, 1260, lerp(1250, 560, u), 2.4, angle=-math.pi / 2, pose="flat")


def _point_down(ctx, f):
    bob = math.sin(f.T * 2.2) * 6
    C.glove_hand(ctx, 1000, 260 + bob, 1.9, angle=math.pi / 2 + 0.05, pose="point")


def _outside_worker(P):
    C.worker(P.bg, 900, 1700, 2.6, rim="#FFFFFF")


def _wheel_grip(ctx, f):
    tremble = noise1(f.T * 9, 3) * 2
    C.hand(ctx, 760 + tremble, 520, 2.4, angle=-0.35, pose="fist")
    C.hand(ctx, 1520, 640 + tremble, 1.8, angle=-2.2, pose="flat", light_a=0.15)


def _cold_open_wide(ctx, f):
    C.truck_rear(ctx, 960, 980, 0.62, brake=0.7)
    C.worker(ctx, 720, 990, 0.62)


SHOTS = {
    "S00_A": S(L.truck_door_ext, Cam(1.0, 1.06), live_bg=_glove_rise, rain=RAIN),
    "S00_B": S(stack(L.side_window, _outside_worker), Cam(1.0, 1.03), live_bg=_point_down,
               live_fg=lambda c, f: drops(c, f), post={"blur": 9}, rain=RAIN_SOFT),
    "S00_C": S(L.weigh_station, Cam(1.02, 1.08, (900, 560), (1020, 540)), post={"desat": 0.55, "bloom": 0.3, "lift": "#2A2E30"}),
    "S00_D": S(L.checkpoint, Cam(1.0, 1.05), live_bg=_cold_open_wide, rain=RAIN, post={"fog": ("#2C3944", 150, 760, 420, 380, 0.3)}),
    "S00_E": S(L.wheel_grip, Cam(1.0, 1.03, handheld=2), live_bg=_wheel_grip),
    "S00_F": S(L.black, Cam(1.0, 1.0), post={"bloom": 0}),
}


# ----------------------------------------------------------------- S01

def _road_meta(P):
    L.forest_road_side(P)
    P.meta["cones"] = [[(1440, 660), (DW + 100, 470), (DW + 100, 870)]]


def _truck_on_road(ctx, f):
    for k in range(13):
        x = (k * 180 - f.T * 520) % (DW + 360) - 180
        rect(ctx, x, 812, 100, 7, "#B8962E", 0.55)
    from kit import cone
    cone(ctx, 1440, 660, [(DW + 200, 520), (DW + 200, 820)], "#FFF1D0", 0.3)
    glow(ctx, 1700, 860, 420, "#FFE9C0", 0.18, sx=1.6, sy=0.25)
    C.truck_side(ctx, 470, 720 + math.sin(f.T * 7) * 1.5, wheel_rot=f.T * 9)


def _truck_passing(ctx, f):
    x = lerp(-1100, DW + 200, f.u)
    from kit import cone
    cone(ctx, x + 970, 660, [(x + 1700, 520), (x + 1700, 820)], "#FFF1D0", 0.28)
    C.truck_side(ctx, x, 720, wheel_rot=f.T * 9)


def _cab_drive(ctx, f):
    passing_lights(ctx, f)
    cab_daniel(ctx, f)


def _phone_route(ctx, f, color="#5DB2FF"):
    x, y, w, h = f.meta["phone"]
    ctx.set_line_width(10)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x + w * 0.5, y + h * 0.95)
    ctx.curve_to(x + w * 0.55, y + h * 0.7, x + w * 0.3, y + h * 0.55, x + w * 0.45, y + h * 0.3)
    ctx.curve_to(x + w * 0.55, y + h * 0.18, x + w * 0.62, y + h * 0.12, x + w * 0.6, y + h * 0.04)
    src(ctx, color, 0.9)
    ctx.stroke()
    circle(ctx, x + w * 0.5, y + h * 0.9, 14, "#FFFFFF")
    circle(ctx, x + w * 0.5, y + h * 0.9, 8, color)


def _pov_road(ctx, f):
    dashes(ctx, f)


def _pov_fg(ctx, f, wipe=1.7):
    if wipe:
        drops(ctx, f, wipe=wipe)
        wipers(ctx, f, wipe)
    else:
        drops(ctx, f)


SHOTS.update({
    "S01_A": S(_road_meta, Cam(1.04, 1.08, (900, 560), (1000, 560)), live_bg=_truck_on_road, rain=RAIN,
               post={"fog": ("#3A4C5A", 450, 760, 650, 160, 0.55)}),
    "S01_B": S(L.cab_profile, Cam(1.02, 1.05, handheld=3), live_bg=_cab_drive),
    "S01_C": S(L.phone_close, Cam(1.0, 1.06), live_bg=_phone_route),
    "S01_D": S(stack(partial(L.road_pov, trees=True), L.windshield_fg), Cam(1.0, 1.03), live_bg=_pov_road,
               live_fg=_pov_fg, rain=RAIN, post={"fog": ("#2A3A46", 380, 640, 540, 140, 0.45)}),
    "S01_E": S(partial(L.forest_road_side, diner=True), Cam(1.03, 1.05), live_bg=_truck_passing, rain=RAIN,
               post={"fog": ("#3A4C5A", 450, 760, 650, 160, 0.5)}),
})


# ----------------------------------------------------------------- S02

def _reflection(ctx, f):
    ctx.push_group()
    ctx.translate(DW, 0)
    ctx.scale(-1, 1)
    C.daniel_profile(ctx, 900, 820, 1.5, light=AMBER, light_a=0.5)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(0.22)


def _blink_lights(ctx, f):
    for k, (x, y) in enumerate(f.meta.get("blink", [])):
        on = ((f.T * 0.9 + k * 0.33) % 1.0) < 0.5
        glow(ctx, x, y, 40, RED, 0.9 if on else 0.2)


def _ambulance(ctx, f):
    dashes(ctx, f, speed=0.9)
    u = ease_in(prog(f.t, 0.3, f.dur * 0.8))
    if 0 < u < 1:
        vx, vy = f.meta["vp"]
        x = lerp(vx - 60, -700, u ** 1.4)
        y = lerp(vy + 60, DH + 300, u ** 1.6)
        s = lerp(0.08, 2.6, u ** 1.5)
        flash = (f.T * 3.0) % 1.0
        C.ambulance_front(ctx, x, y, s, flash)
        wash = 0.18 * u
        ctx.rectangle(-60, -60, DW + 120, DH + 120)
        src(ctx, RED if flash > 0.5 else "#E6F0FF", wash)
        ctx.fill()


SHOTS.update({
    "S02_A": S(L.sign, Cam(1.0, 1.12, (1000, 540), (1100, 470)), rain=RAIN,
               post={"fog": ("#2E3D49", 500, 800, 690, 140, 0.5), "bloom": 0.6, "thresh": 0.82}),
    "S02_B": S(partial(L.sign, panel=(260, 120, 1400, 860), forest=False), Cam(1.0, 1.05), rain=RAIN_SOFT, post={"bloom": 0.6, "thresh": 0.8}),
    "S02_C": S(partial(L.side_window, outside="night"), Cam(1.0, 1.03), live_bg=_reflection,
               live_fg=lambda c, f: drops(c, f, n=320), rain=RAIN_SOFT),
    "S02_D": S(L.plant, Cam(1.04, 1.08, (880, 540), (1040, 540)), live_bg=_blink_lights, rain=RAIN,
               post={"fog": ("#3A4A55", 300, 720, 600, 200, 0.55)}),
    "S02_E": S(stack(partial(L.road_pov, trees=True), L.windshield_fg), Cam(1.0, 1.02), live_bg=_ambulance,
               live_fg=_pov_fg, rain=RAIN, post={"fog": ("#2A3A46", 380, 640, 540, 140, 0.45)}),
})


# ----------------------------------------------------------------- S03

def _truck_parks(ctx, f):
    u = ease_out(prog(f.t, 0.0, f.dur * 0.7))
    C.truck_side(ctx, lerp(2300, 1560, u), 880, 0.42, facing=-1, wheel_rot=-u * 30, cab_glow=0.25)


def _dome(ctx, f):
    x, y = f.meta["dome"]
    glow(ctx, x, y, 260, "#FFE7B0", 0.35 + 0.05 * math.sin(f.T * 13))


def _warn(ctx, f):
    x, y = f.meta["warn"]
    on = (f.T % 1.0) < 0.5
    circle(ctx, x, y, 16, "#FF9F2E" if on else "#3A2208")
    glow(ctx, x, y, 90, "#FF9F2E", 0.8 if on else 0.05)


def _walk_to_store(ctx, f):
    u = ease(prog(f.t, 0.2, f.dur))
    C.daniel_back(ctx, lerp(760, 1500, u), lerp(1080, 730, u), lerp(0.95, 0.36, u), phase=f.T * 6.5)


SHOTS.update({
    "S03_A": S(L.station, Cam(1.0, 1.08, (900, 560), (940, 520)), rain=RAIN, post={"fog": ("#26333C", 300, 760, 560, 260, 0.35)}),
    "S03_B": S(L.station_high, Cam(1.02, 1.06), live_bg=_truck_parks, rain=RAIN),
    "S03_C": S(L.sedan_close, Cam(1.0, 1.06, (900, 560), (1000, 520)), live_bg=_dome, rain=RAIN),
    "S03_D": S(L.ignition, Cam(1.0, 1.05), live_bg=_warn),
    "S03_E": S(stack(L.station, L.windshield_fg), Cam(1.0, 1.02), live_fg=lambda c, f: drops(c, f, n=300), rain=RAIN,
               post={"fog": ("#26333C", 300, 760, 560, 260, 0.35)}),
    "S03_F": S(L.station, Cam(1.05, 1.02, (1000, 560), (1100, 560)), live_bg=_walk_to_store, rain=RAIN,
               post={"fog": ("#26333C", 300, 760, 560, 260, 0.35)}),
})


# ----------------------------------------------------------------- S04 / S05 store

INTERIOR = {"bloom": 0.5, "thresh": 0.85, "lift": "#10181C"}


def _drips(ctx, f):
    x, y0, y1 = f.meta["drip"]
    for k in range(3):
        ph = (f.T * 1.4 + k / 3) % 1.0
        y = lerp(y0, y1, ph ** 2)
        ellipse(ctx, x + 4, y, 5, 8, "#2A170D", 0.9)
    r = (f.T * 1.4) % 1.0
    ellipse(ctx, x, 600, 20 + r * 40, 4 + r * 4, "#6A4A30", 0.4 * (1 - r))


def _phone_buzz(ctx, f):
    x, y, w, h = f.meta["phone"]
    on = 0.15 < f.u < 0.6
    if on:
        jit = math.sin(f.T * 90) * 4
        rect(ctx, x + jit, y, w, h, "#E8F2FF")
        glow(ctx, x + w / 2, y + h / 2, 600, "#DDEBFF", 0.35)
        circle(ctx, x + w / 2 + jit, y + h * 0.35, 60, "#9FB3C2")


def _door_flex(ctx, f):
    x, y, w, h = f.meta["door"]
    t8 = item_t(f, 8)
    k = 0.5 + 0.5 * math.sin(f.T * 1.3)
    if t8 is not None and f.t > t8:
        k = 1.0
    glow(ctx, x + w * 0.45, y + h * 0.42, w * 0.35, "#000000", 0.12 + 0.12 * k, sx=1.0, sy=0.45)
    glow(ctx, x + w * 0.45, y + h * 0.36, w * 0.3, "#FFFFFF", 0.04 * k, sx=1.0, sy=0.2)


def _shoulder_fg(ctx, f):
    ctx.move_to(-60, DH + 60)
    ctx.curve_to(0, 600, 200, 420, 420, 400)
    ctx.curve_to(520, 380, 600, 500, 620, DH + 60)
    ctx.close_path()
    src(ctx, "#0A0D10", 0.92)
    ctx.fill()
    circle(ctx, 300, 300, 170, "#0A0D10", 0.92)


def _can_roll(ctx, f):
    u = ease_out(prog(f.t, 0.25 * f.dur, 0.55 * f.dur))
    bx = lerp(980, 760, ease_out(prog(f.t, 0.0, 0.3 * f.dur)))
    rrect(ctx, bx - 160, 840, 260, 120, 50, "#16120F")                      # boot
    rrect(ctx, bx - 40, 640, 120, 230, 30, "#1E2530")                        # jeans
    if u > 0:
        cx = lerp(980, 1500, u)
        rect(ctx, cx - 30, 940, 60, 80, "#A3392D")
        rot = u * 14
        ellipse(ctx, cx + 30 * math.cos(rot) * 0.2, 980, 6, 40, "#C9CFCC", 0.6)


def _handle(ctx, f):
    px, py = f.meta["pivot"]
    u = ease(prog(f.t, 0.2, f.dur * 0.7))
    strain = 0.02 * math.sin(f.T * 40) * prog(f.t, f.dur * 0.7, f.dur)
    ctx.save()
    ctx.translate(px, py)
    ctx.rotate(u * 0.62 + strain)
    rrect(ctx, -20, -26, 420, 52, 26, "#C3C9CD")
    rect(ctx, 0, -26, 400, 10, "#E6EAEC", 0.7)
    ctx.restore()
    circle(ctx, px, py, 34, "#D2D8DB")


def _slam_in(ctx, f):
    cab_daniel(ctx, f, shake=6, breath=True)


def _mirror_clip(ctx, f):
    x, y, w, h = f.meta["mirror"]
    rrect(ctx, x, y, w, h, 50, "#000000", 0.0)
    ctx.new_path()
    from kit import rrect_path
    rrect_path(ctx, x, y, w, h, 50)
    ctx.clip()
    return x, y, w, h


def _mirror_station(ctx, f):
    x, y, w, h = _mirror_clip(ctx, f)
    vg = cairo.LinearGradient(0, y, 0, y + h)
    vg.add_color_stop_rgba(0, 0.03, 0.05, 0.07, 1)
    vg.add_color_stop_rgba(1, 0.06, 0.08, 0.1, 1)
    ctx.rectangle(x, y, w, h)
    ctx.set_source(vg)
    ctx.fill()
    s = lerp(1.0, 0.55, f.u)
    cx, cy = x + w * 0.55, y + h * 0.55
    rect(ctx, cx - 300 * s, cy - 140 * s, 600 * s, 60 * s, "#C9CBC6")
    rect(ctx, cx - 300 * s, cy - 120 * s, 600 * s, 16 * s, "#9B2F2A")
    glow(ctx, cx, cy - 70 * s, 400 * s, "#F4FBFF", 0.5)
    rect(ctx, cx + 120 * s, cy - 40 * s, 260 * s, 170 * s, "#BFD9D4")
    door = ease(prog(f.t, item_t(f, 9) or 0, (item_t(f, 9) or 0) + 1.2))
    rect(ctx, cx + 230 * s, cy - 10 * s, 60 * s * (1 - door * 0.8), 140 * s, "#2A3036")
    glow(ctx, x + w * 0.2, y + h * 0.8, 120, RED, 0.25)


def _taillights_leave(ctx, f):
    u = f.u
    for dx in (0, 110):
        glow(ctx, lerp(260, -200, u) + dx, 960, 60, "#FF2A1F", 0.9 * (1 - u))


SHOTS.update({
    "S04_A": S(L.coffee, Cam(1.0, 1.08, (900, 540), (1000, 540)), live_bg=_drips, post=INTERIOR),
    "S04_B": S(L.aisle, Cam(1.0, 1.07), post=INTERIOR),
    "S04_C": S(L.counter_phone, Cam(1.02, 1.05), live_bg=_phone_buzz, post=INTERIOR),
    "S04_D": S(L.store_door, Cam(1.0, 1.1, (960, 540), (960, 500)), live_fg=_shoulder_fg, fg_depth=1.4,
               post={**INTERIOR, "blur": 0}),
    "S04_E": S(partial(L.store_door, close=True), Cam(1.0, 1.04, handheld=1), live_bg=_door_flex, post=INTERIOR),
    "S05_A": S(L.door_gap, Cam(1.0, 1.05), post=INTERIOR),
    "S05_B": S(L.floor_low, Cam(1.0, 1.03), live_bg=_can_roll, post=INTERIOR),
    "S05_C": S(L.handle_close, Cam(1.0, 1.1), live_bg=_handle, post=INTERIOR),
    "S05_D": S(L.cab_profile, Cam(1.04, 1.06, handheld=7), live_bg=_slam_in),
    "S05_E": S(L.mirror, Cam(1.0, 1.03, handheld=2), live_bg=_mirror_station),
    "S05_F": S(L.station, Cam(1.1, 1.0, (960, 560), (960, 540)), live_bg=_taillights_leave, rain=RAIN,
               post={"fog": ("#26333C", 300, 760, 560, 260, 0.35)}),
})


# ----------------------------------------------------------------- S06 / S07

def _cars_ahead(P):
    L.road_pov(P, town=True, shops=True, trees=False)
    c = P.bg
    for x, y, s, col in ((760, 640, 0.9, "#5A2A28"), (1150, 600, 0.6, "#33424D"), (880, 560, 0.4, "#2B3A48")):
        rrect(c, x - 180 * s, y - 120 * s, 360 * s, 130 * s, 20 * s, col)
        rect(c, x - 140 * s, y - 110 * s, 280 * s, 50 * s, "#0B1220")
        for sx in (-1, 1):
            rect(c, x + sx * 150 * s - 18 * s, y - 50 * s, 36 * s, 16 * s, "#5A1210")
        rect(c, x - 190 * s, y + 8 * s, 380 * s, 22 * s, "#0B0E10")
    L.windshield_fg(P)


def _exhaust(ctx, f):
    x, y = f.meta["exhaust"]
    for k in range(5):
        ph = (f.T * 0.5 + k / 5) % 1.0
        glow(ctx, x - ph * 160, y - ph * 60, 30 + ph * 90, "#C9D6E2", 0.25 * (1 - ph))


def _jacket(ctx, f):
    hx_, hy_ = f.meta["hook"]
    ang = math.sin(f.T * 1.4) * 0.12 + noise1(f.T, 4) * 0.04
    ctx.save()
    ctx.translate(hx_, hy_)
    ctx.rotate(ang)
    poly(ctx, [(-20, 0), (20, 0), (110, 120), (90, 360), (-90, 360), (-110, 120)], "#D9B23A")
    poly(ctx, [(-110, 120), (-160, 300), (-130, 310), (-90, 160)], "#C9A030")
    poly(ctx, [(110, 120), (160, 300), (130, 310), (90, 160)], "#C9A030")
    rect(ctx, -4, 20, 8, 330, "#8C7020")
    ctx.restore()
    rect(ctx, hx_ - 10, hy_ - 14, 20, 20, "#2A3136")


def _mirror_street(ctx, f, woman_walk=False, fog=False):
    x, y, w, h = _mirror_clip(ctx, f)
    vg = cairo.LinearGradient(0, y, 0, y + h)
    vg.add_color_stop_rgba(0, 0.03, 0.05, 0.07, 1)
    vg.add_color_stop_rgba(1, 0.07, 0.09, 0.11, 1)
    ctx.rectangle(x, y, w, h)
    ctx.set_source(vg)
    ctx.fill()
    vx, vy = x + w * 0.5, y + h * 0.45
    poly(ctx, [(vx - 10, vy), (vx + 10, vy), (x + w, y + h), (x, y + h)], "#141B20")
    for k in range(4):
        d = ((k / 4) + f.T * 0.15) % 1
        for side in (-1, 1):
            gx = vx + side * (40 + 500 * d)
            glow(ctx, gx, vy - 120 * d, 30 + 120 * d, "#F7C98A", 0.5)
    if woman_walk:
        s = lerp(0.42, 0.22, f.u)
        C.woman(ctx, vx + 60, vy + 160 * s + 120, s, walk=f.T * 5)
    if fog:
        ctx.rectangle(x, y, w, h)
        src(ctx, "#2A3742", 0.35)
        ctx.fill()


def _tap_phone(ctx, f):
    _phone_route(ctx, f, color="#3E5A75")
    x, y, w, h = f.meta["phone"]
    u = prog(f.t, 0, 0.8)
    C.hand(ctx, lerp(x + w * 1.6, x + w * 0.85, ease_out(u)), y + h * 0.75, 1.9, angle=math.pi + 0.4, pose="point")


def _signals(ctx, f):
    dashes(ctx, f, speed=0.7)
    for x, y in f.meta.get("signals", []):
        circle(ctx, x, y + 58, 11, "#3EE07A")
        glow(ctx, x, y + 58, 70, "#3EE07A", 0.7)


SHOTS.update({
    "S06_A": S(_cars_ahead, Cam(1.0, 1.06), live_fg=lambda c, f: drops(c, f), rain=RAIN),
    "S06_B": S(L.cars_side, Cam(1.08, 1.08, (820, 560), (1120, 560), curve="linear"), live_bg=_exhaust, rain=RAIN),
    "S06_C": S(L.car_window, Cam(1.06, 1.06, (860, 540), (1080, 540), curve="linear"), rain=RAIN),
    "S06_D": S(L.jacket, Cam(1.0, 1.06), live_bg=_jacket, rain=RAIN),
    "S06_E": S(L.mirror, Cam(1.0, 1.02, handheld=2), live_bg=_mirror_street),
    "S07_A": S(L.phone_close, Cam(1.0, 1.04), live_bg=_tap_phone),
    "S07_B": S(L.phone_close, Cam(1.04, 1.1), live_bg=_phone_route),
    "S07_C": S(L.mirror, Cam(1.0, 1.02, handheld=2), live_bg=partial(_mirror_street, fog=True)),
    "S07_D": S(stack(partial(L.road_pov, town=True, shops=True, trees=False, signals=True), L.windshield_fg),
               Cam(1.0, 1.04), live_bg=_signals, live_fg=_pov_fg, rain=RAIN),
    "S07_E": S(partial(L.cab_profile), Cam(1.25, 1.3, (980, 420), (990, 420)),
               live_bg=lambda c, f: cab_daniel(c, f, light_a=0.75)),
})


# ----------------------------------------------------------------- S08 / S09

def _crosswalk_people(ctx, f, turn_from=None):
    x, y, s = f.meta["woman"]
    turn = 0.0
    if turn_from is not None:
        turn = ease_out(prog(f.t, turn_from, turn_from + 0.6))
    C.woman(ctx, x, y, s, turn=turn)
    lx, ly, ls = f.meta["laundro_fig"]
    C.figure(ctx, lx, ly, ls, color="#0B1013")
    sx, sy, ss = f.meta["shelter_fig"]
    C.figure(ctx, sx, sy, ss)


def _crosswalk_pov(P):
    L.crosswalk(P)
    L.windshield_fg(P)


def _horn(ctx, f):
    px, py = f.meta["pad"]
    u = ease_out(prog(f.t, 0.0, f.dur * 0.75))
    press = 1 if f.u > 0.8 else 0
    C.hand(ctx, lerp(px + 900, px + 60, u) - press * 10, py + 30, 2.6, angle=math.pi + 0.15, pose="flat" if press else "point")


def _laundro(ctx, f):
    x, y, s = f.meta["fig"]
    turn = ease(prog(f.t, 0.3, 1.2))
    C.figure(ctx, x, y, s, color="#0E1417", turn=turn)


def _shelter(ctx, f):
    x, y, s = f.meta["fig"]
    C.figure(ctx, x, y, s, turn=lerp(-1, 1, f.u))
    u = prog(f.t, f.dur * 0.25, f.dur * 0.7)
    if 0 < u < 1:
        x = lerp(-2600, DW + 300, u)
        for k in range(5):
            ctx.push_group()
            C.truck_side(ctx, x - k * 70, 1150, 2.2, wheel_rot=f.T * 9)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(0.32)


def _radio(ctx, f):
    x, y, w, h = f.meta["display"]
    kx, ky = f.meta["knob"]
    t_click = f.dur * 0.55
    if f.t < t_click:
        rect(ctx, x + 20, y + 20, w - 40, h - 40, "#FFB04A", 0.85)
        glow(ctx, x + w / 2, y + h / 2, 400, "#FFB04A", 0.3)
    u = ease_out(prog(f.t, 0.0, t_click))
    C.hand(ctx, lerp(kx - 700, kx - 170, u), ky + 10, 1.8, angle=0.0, pose="press")


def _flicker_face(ctx, f):
    on = (f.T * 2.5) % 1.0 < 0.5
    cab_daniel(ctx, f, light=RED if on else "#E6F0FF", light_a=0.45, scale=1.8)


def _awning(ctx, f):
    for x, y, s in f.meta["figs"]:
        C.figure(ctx, x, y, s, color="#090C0E")
    u = prog(f.t, f.dur * 0.35, f.dur * 0.8)
    if 0 < u < 1:
        ctx.rectangle(lerp(-1500, DW + 200, u), 500, 1400, 700)
        src(ctx, "#0A0D10", 0.92)
        ctx.fill()


def _aerial_truck(ctx, f, into_town=False):
    for x, y in f.meta["lamps"]:
        if (int(x) + int(y)) % 3 == 0:
            circle(ctx, x + 8, y + 6, 3, "#020304")
    y = 60 + 190 * 3 - 80 + 25
    x = lerp(-120, DW + 120, f.u) if not into_town else lerp(DW * 0.65, DW * 0.35, f.u)
    rect(ctx, x - 40, y - 12, 80, 24, "#D5DCE1")
    glow(ctx, x + 50 * (1 if not into_town else -1), y, 90, "#FFF6E0", 0.6, sx=1.6, sy=0.5)


SHOTS.update({
    "S08_A": S(_crosswalk_pov, Cam(1.0, 1.1, (1100, 540), (1250, 520)), live_bg=_crosswalk_people,
               live_fg=lambda c, f: drops(c, f), rain=RAIN, post={"fog": ("#22303A", 200, 720, 560, 260, 0.3)}),
    "S08_B": S(L.walk_signal, Cam(1.0, 1.06), rain=RAIN),
    "S08_C": S(partial(L.wheel, center=True), Cam(1.0, 1.04), live_bg=_horn),
    "S08_D": S(L.crosswalk, Cam(1.6, 1.7, (1470, 470), (1470, 460)), live_bg=partial(_crosswalk_people, turn_from=0.25),
               rain=RAIN, post={"fog": ("#22303A", 200, 720, 560, 260, 0.3)}),
    "S08_E": S(L.laundromat, Cam(1.0, 1.08, (1100, 560), (1180, 540)), live_bg=_laundro, rain=RAIN_SOFT),
    "S08_F": S(L.bus_shelter, Cam(1.0, 1.04), live_bg=_shelter, rain=RAIN),
    "S09_A": S(L.mirror, Cam(1.0, 1.03, handheld=2), live_bg=partial(_mirror_street, woman_walk=True)),
    "S09_B": S(L.radio, Cam(1.0, 1.05), live_bg=_radio),
    "S09_C": S(L.cab_profile, Cam(1.2, 1.28, (900, 470), (920, 460)), live_bg=_flicker_face),
    "S09_D": S(L.awning, Cam(1.0, 1.05), live_bg=_awning, rain=RAIN),
    "S09_E": S(L.town_aerial, Cam(1.15, 1.0), live_bg=_aerial_truck, rain=RAIN_SOFT),
})


# ----------------------------------------------------------------- S10 / S11

def _no_response(ctx, f):
    pass


def _eye_close(ctx, f):
    cab_daniel(ctx, f, light="#F4F8FF", light_a=0.4 + 0.2 * math.sin(f.T * 3))


def _fence(ctx, f):
    t_fall = item_t(f, 5) or f.dur * 0.6
    drag = ease(prog(f.t, 0, t_fall))
    fall = ease_in(prog(f.t, t_fall, t_fall + 0.6))
    C.truck_rear(ctx, lerp(-200, 260, drag), 1060, 1.3, brake=0.3)
    ctx.save()
    ctx.translate(lerp(560, 760, drag), 1000)
    ctx.rotate(-fall * 1.45)
    ctx.set_line_width(4)
    src(ctx, "#8E979C")
    for k in range(12):
        ctx.move_to(k * 50, 0)
        ctx.line_to(k * 50, -560)
    for k in range(10):
        ctx.move_to(0, -k * 56)
        ctx.line_to(550, -k * 56)
    ctx.stroke()
    rect(ctx, -10, -570, 20, 580, "#B9C0C5")
    rect(ctx, 540, -570, 20, 580, "#B9C0C5")
    ctx.restore()
    if fall >= 1:
        glow(ctx, 900, 980, 300, "#FFFFFF", 0.15 * max(0, 1 - (f.t - t_fall - 0.6) * 2))


def _pharmacy(ctx, f):
    x, y, s = f.meta["win_fig"]
    C.figure(ctx, x, y, s, color="#04060A", a=prog(f.t, item_t(f, 6) or 0.5, (item_t(f, 6) or 0.5) + 1.0))
    x, y, s = f.meta["shop_fig"]
    C.figure(ctx, x, y, s, color="#04060A", a=prog(f.t, item_t(f, 7) or 2.0, (item_t(f, 7) or 2.0) + 1.0))


def _pile(ctx, f):
    x, y = f.meta["pile"]
    sh = ease(prog(f.t, f.dur * 0.35, f.dur * 0.6)) * 26
    rrect(ctx, x - 160, y - 20 + sh, 330, 120, 30, "#DCE3E6", 0.85)
    rect(ctx, x - 150, y + 20 + sh, 310, 8, "#AEB8BD")


def _truck_charge(ctx, f):
    u = ease_in(f.u)
    C.truck_front(ctx, 960, lerp(700, 1500, u), lerp(0.3, 2.4, u), lights=1.0)


SHOTS.update({
    "S10_A": S(L.van_street, Cam(1.0, 1.08), live_bg=partial(dashes, speed=0.25), live_fg=lambda c, f: drops(c, f), rain=RAIN),
    "S10_B": S(L.van_cargo, Cam(1.08, 1.08, (820, 540), (1100, 540), curve="linear"), post={"bloom": 0.7, "thresh": 0.75}),
    "S10_C": S(partial(L.paper, sheet="checklist"), Cam(1.0, 1.08), post={"bloom": 0.5, "thresh": 0.85, "lift": "#1A2228"}),
    "S10_D": S(partial(L.paper, sheet="contacts"), Cam(1.0, 1.06, (960, 420), (1000, 640)), post={"bloom": 0.5, "thresh": 0.85, "lift": "#1A2228"}),
    "S10_E": S(L.cab_profile, Cam(1.5, 1.6, (990, 400), (1000, 395)), live_bg=_eye_close),
    "S11_A": S(L.mirror, Cam(1.0, 1.02, handheld=2), live_bg=lambda c, f: (_mirror_street(c, f), rect(c, 1150, 150, 300, 800, "#C5CBCF", 0.95))),
    "S11_B": S(L.fence, Cam(1.0, 1.03, handheld=2), live_bg=_fence, rain=RAIN),
    "S11_C": S(L.pharmacy, Cam(1.0, 1.06, (960, 560), (960, 500)), live_bg=_pharmacy, rain=RAIN),
    "S11_D": S(L.van_cargo, Cam(1.15, 1.18, (600, 560), (600, 560), handheld=2), live_bg=_pile, post={"bloom": 0.7, "thresh": 0.75}),
    "S11_E": S(L.street_ahead, Cam(1.0, 1.02), live_bg=_truck_charge, rain=RAIN),
})


# ----------------------------------------------------------------- S12 / S13

def _raise_arm(ctx, f):
    up = f.t > (item_t(f, 5) or f.dur * 0.3)
    C.worker(ctx, 1010, 790, 0.95, arm_up=up)


def _exhale(ctx, f):
    cab_daniel(ctx, f, light="#EAF2FF", light_a=0.55, scale=1.7, breath=True)


def _parked_top(ctx, f, turn=0.0, figs=False):
    x, y = lerp(960, 960, f.u), 620
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-math.pi / 2 + turn * math.pi)
    rect(ctx, -60, -40, 300, 120, "#D5DCE1")
    rect(ctx, 240, -30, 70, 100, "#C3CCD2")
    ctx.restore()
    if not turn:
        from kit import cone
        cone(ctx, x, y - 260, [(x - 200, y - 520), (x + 200, y - 520)], "#FFF6E0", 0.35)
    if figs:
        for k, (fx, fy) in enumerate(((700, 260), (900, 230), (1250, 250))):
            circle(ctx, fx + math.sin(f.T + k) * 10, fy + f.u * 60, 18, "#E6EAE8")


def _worker_walk_in(ctx, f):
    u = ease_out(prog(f.t, 0, f.dur * 0.75))
    C.worker(ctx, lerp(-200, 420, u), 1300, 1.7)


def _switch_hand(ctx, f, approach=True):
    sx, sy = f.meta["switch"]
    if approach:
        u = ease_out(prog(f.t, 0.0, f.dur * 0.9))
        C.hand(ctx, lerp(sx - 900, sx - 230, u), sy + 40, 1.6, angle=0.0, pose="point")
    else:
        C.hand(ctx, sx - 520, sy + 160, 1.6, angle=0.2, pose="fist")
        glow(ctx, lerp(200, 1700, (f.T * 0.2) % 1), 300, 260, WHITE_LIGHT, 0.12)


def _glove_close(ctx, f):
    C.glove_hand(ctx, 520, 760, 4.2, angle=-0.25, pose="point", torn=True)
    ctx.save()
    ctx.translate(520, 760)
    ctx.rotate(-0.25)
    ctx.scale(4.2, 4.2)
    ctx.translate(160, -22)
    ctx.rotate(0.9)                     # bent sideways at the middle joint
    rrect(ctx, -6, -12, 46, 24, 12, "#B99683")
    ctx.restore()


def _two_shot(ctx, f):
    t_point = item_t(f, 8) or 0.0
    t_track = item_t(f, 9) or f.dur * 0.4
    t_down = item_t(f, 10) or f.dur * 0.7
    look = ease(prog(f.t, t_track, t_track + 0.8))
    C.worker_face(ctx, 1250, 610, 1.25, stage=0, eye_dx=-look, head_turn=-look * 0.5)
    if f.t > t_down:
        C.glove_hand(ctx, 1150, 260, 1.4, angle=math.pi / 2 + 0.05, pose="point")


def _two_shot_fg(ctx, f):
    drops(ctx, f)
    t_point = item_t(f, 8) or 0.0
    u = ease_out(prog(f.t, t_point, t_point + 0.7))
    C.hand(ctx, lerp(-200, 260, u), 820 - u * 120, 2.2, angle=-0.35, pose="point")


SHOTS.update({
    "S12_A": S(partial(L.checkpoint, far=True), Cam(1.0, 1.15, (960, 560), (960, 560)), rain=RAIN,
               post={"fog": ("#2C3944", 150, 760, 520, 340, 0.4)}),
    "S12_B": S(partial(L.checkpoint, worker_fig=True), Cam(1.04, 1.06, (900, 540), (1020, 540)), rain=RAIN,
               post={"fog": ("#2C3944", 150, 760, 420, 380, 0.3)}),
    "S12_C": S(partial(L.checkpoint, pov=True), Cam(1.0, 1.03), live_bg=_raise_arm, live_fg=lambda c, f: drops(c, f),
               rain=RAIN, post={"fog": ("#2C3944", 150, 760, 420, 380, 0.35)}),
    "S12_D": S(L.cab_profile, Cam(1.18, 1.22, (900, 480), (900, 470)), live_bg=_exhale),
    "S12_E": S(L.checkpoint_high, Cam(1.1, 1.0), live_bg=_parked_top, rain=RAIN_SOFT),
    "S13_A": S(L.truck_door_ext, Cam(1.0, 1.03), live_bg=_worker_walk_in, rain=RAIN),
    "S13_C": S(L.switch_close, Cam(1.0, 1.08), live_bg=_switch_hand),
    "S13_D": S(L.black, Cam(1.0, 1.06), live_bg=_glove_close, post={"bloom": 0}),
    "S13_E": S(L.side_window, Cam(1.0, 1.02), live_bg=_two_shot, live_fg=_two_shot_fg, post={"blur": 9}, rain=RAIN_SOFT),
    "S13_F": S(L.switch_close, Cam(1.08, 1.12), live_bg=partial(_switch_hand, approach=False)),
})
SHOTS["S13_B"] = SHOTS["S00_B"]
SHOTS["S13_D"].post = {"bloom": 0.4}


def _glove_bg(P):
    c = P.bg
    from kit import vgrad
    vgrad(c, -50, -50, DW + 100, DH + 100, [(0, "#10171D", 1), (1, "#06090C", 1)])
    glow(c, 1500, 260, 700, "#EAF2FF", 0.6)


SHOTS["S13_D"] = S(_glove_bg, Cam(1.0, 1.06), live_bg=_glove_close, post={"blur": 10}, rain=RAIN_SOFT)


# ----------------------------------------------------------------- S14 / S15

def _face(ctx, f, stage=1, scale=1.25, eyes=False, mask_down=0.0):
    edx = math.sin(f.T * 0.8) * 0.6 if eyes else 0.0
    C.worker_face(ctx, 960, 600 if not eyes else 660, scale, stage=stage, eye_dx=edx, mask_down=mask_down)


def _phone_ring(ctx, f):
    x, y, w, h = f.meta["phone"]
    t_off = (item_t(f, 10) or 99) - 0.0
    if f.t < t_off:
        rect(ctx, x, y, w, h, "#F2F7FF")
        glow(ctx, x + w / 2, y + h / 2, 800, "#EAF2FF", 0.45 + 0.1 * math.sin(f.T * 12))
        circle(ctx, x + w * 0.3, y + h * 0.85, 46, "#2ECC71")
        circle(ctx, x + w * 0.7, y + h * 0.85, 46, RED)


def _jab(ctx, f):
    x, y, w, h = f.meta["phone"]
    t_hit = f.dur * 0.25
    if f.t < t_hit:
        rect(ctx, x, y, w, h, "#F2F7FF")
        glow(ctx, x + w / 2, y + h / 2, 800, "#EAF2FF", 0.45)
    u = ease_out(prog(f.t, 0, t_hit))
    C.hand(ctx, lerp(x + w + 600, x + w * 0.62, u), y + h * 0.82, 2.2, angle=math.pi + 0.3, pose="press")


def _yank(ctx, f):
    hx_, hy_ = f.meta["handle"]
    t1 = item_t(f, 9) or f.dur * 0.3
    pulls = (t1 + 0.5, t1 + 2.4)
    off = 0.0
    for p in pulls:
        d = f.t - p
        if 0 <= d < 0.35:
            off = 30 * math.sin(d / 0.35 * math.pi)
    lean = -0.12 if f.t > (item_t(f, 8) or 0) else 0.0
    C.worker(ctx, 900, 1500, 2.1, lean=lean)
    C.glove_hand(ctx, hx_ - 240 - off, hy_ + 10, 1.4, angle=0.0, pose="fist")


def _shoulder_blur(ctx, f):
    u = ease(prog(f.t, 0.3, 1.6))
    a = 0.85 * (1 - 0.3 * u)
    glow(ctx, 260, 760, 700, "#C9CFCC", a, sx=0.8, sy=1.2)
    glow(ctx, 330, 300, 260, "#151A1E", a, sx=0.9, sy=1.1)


def _rear_bg(P):
    L.tire(P)
    c = P.bg
    from kit import vgrad
    vgrad(c, -50, -50, DW + 100, 760, [(0, "#0A0E11", 1), (1, "#141A1E", 1)])
    for tx in (300, 1650):
        circle(c, tx, 140, 40, "#FFFFFF")
        glow(c, tx, 140, 500, "#EAF2FF", 0.5)
    P.meta["cones"] = [[(300, 140), (-50, 1000), (800, 1000)], [(1650, 140), (1100, 1000), (DW + 50, 1000)]]


def _reverse_on(ctx, f):
    on = clamp((f.t - f.dur * 0.25) * 6)
    C.truck_rear(ctx, 960, 1020, 1.25, reverse=on, brake=0.4)


def _rise(ctx, f):
    edge = f.meta["edge_y"]
    hand_u = ease_out(prog(f.t, f.dur * 0.15, f.dur * 0.35))
    head_u = ease(prog(f.t, f.dur * 0.45, f.dur))
    ctx.save()
    ctx.rectangle(-60, -60, DW + 120, edge + 60)
    ctx.clip()
    circle(ctx, 1100, edge + 140 - head_u * 260, 120, "#C9CFCC")
    circle(ctx, 1100, edge + 150 - head_u * 260, 86, "#151A1E")
    ctx.restore()
    if hand_u > 0:
        C.glove_hand(ctx, 700, edge + 60 - hand_u * 40, 1.8, angle=-math.pi / 2 + 0.2, pose="flat")


def _sit_up(ctx, f):
    x, y = f.meta["fig"]
    u = ease(prog(f.t, f.dur * 0.15, f.dur * 0.8))
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-math.pi / 2 * (1 - u))
    ctx.move_to(-110, 0)
    ctx.curve_to(-120, -120, -90, -230, -60, -270)
    ctx.line_to(60, -270)
    ctx.curve_to(90, -230, 120, -120, 110, 0)
    ctx.close_path()
    src(ctx, "#AEB4B1")
    ctx.fill()
    ellipse(ctx, 0, -270, 90, 26, "#9AA19E")
    circle(ctx, 0, -330, 56, "#121619")
    rrect(ctx, -34, -326, 68, 34, 12, "#C9CECB")
    ctx.restore()
    glow(ctx, x, y - 200, 300, "#000000", 0.25)


def _tire(ctx, f):
    x, y, r = f.meta["wheel"]
    spin = -f.T * 14 * prog(f.t, f.dur * 0.2, f.dur * 0.6)
    circle(ctx, x, y, r, "#07090B")
    circle(ctx, x, y, r * 0.45, "#3A4246")
    for k in range(8):
        a = spin + k * math.pi / 4
        rect(ctx, x + r * 0.3 * math.cos(a) - 8, y + r * 0.3 * math.sin(a) - 8, 16, 16, "#1E2326")
    for k in range(18):
        ph = (f.T * 2 + k / 18) % 1
        if f.u > 0.3:
            circle(ctx, x - 200 - ph * 600, y + r - ph * 200 + (k % 5) * 20, 4, "#4A4E4B", 1 - ph)


SHOTS.update({
    "S14_A": S(L.side_window, Cam(1.0, 1.08), live_bg=partial(_face, stage=1), live_fg=lambda c, f: drops(c, f),
               post={"blur": 9}, rain=RAIN_SOFT),
    "S14_B": S(L.side_window, Cam(1.0, 1.04), live_bg=partial(_face, stage=2, scale=2.4, eyes=True),
               live_fg=lambda c, f: drops(c, f), post={"blur": 9}, rain=RAIN_SOFT),
    "S14_C": S(L.phone_close, Cam(1.0, 1.05, handheld=2), live_bg=_phone_ring),
    "S14_D": S(L.truck_door_ext, Cam(1.0, 1.03, handheld=3), live_bg=_yank, rain=RAIN),
    "S14_E": S(L.phone_close, Cam(1.04, 1.06, handheld=3), live_bg=_jab),
    "S14_F": S(L.checkpoint, Cam(1.05, 1.1, (1100, 540), (1150, 540)), live_fg=_shoulder_blur, fg_depth=1.3, rain=RAIN,
               post={"fog": ("#2C3944", 150, 760, 420, 380, 0.3)}),
    "S15_A": S(L.checkpoint_table, Cam(1.1, 1.1, (700, 540), (1250, 540), curve="linear"), rain=RAIN,
               post={"fog": ("#2C3944", 150, 760, 420, 380, 0.3)}),
    "S15_B": S(L.shifter, Cam(1.0, 1.05), live_bg=lambda c, f: _shifter(c, f)),
    "S15_C": S(_rear_bg, Cam(1.0, 1.04), live_bg=_reverse_on, rain=RAIN),
    "S15_D": S(L.barrier_close, Cam(1.0, 1.05), live_bg=_rise, rain=RAIN),
    "S15_E": S(L.van_interior, Cam(1.0, 1.08), live_bg=_sit_up, rain=RAIN_SOFT),
    "S15_F": S(L.tire, Cam(1.0, 1.03, handheld=4), live_bg=_tire, rain=RAIN),
})


def _shifter(ctx, f):
    px, py = f.meta["pivot"]
    u = ease(prog(f.t, f.dur * 0.2, f.dur * 0.6))
    ctx.save()
    ctx.translate(px, py)
    ctx.rotate(0.9 + u * 0.35)
    rrect(ctx, -14, 0, 28, 420, 14, "#2A2F34")
    ctx.restore()
    ex = px + 420 * math.cos(0.9 + u * 0.35 + math.pi / 2) * -1
    ey = py + 420 * math.sin(0.9 + u * 0.35 + math.pi / 2)
    C.hand(ctx, ex - 60, ey - 40, 1.8, angle=0.4, pose="fist")


# ----------------------------------------------------------------- S16 / S17

def _alongside(ctx, f):
    u = f.u
    x = lerp(300, 900, ease(u)) if u < 0.6 else lerp(900, 1100, ease_out((u - 0.6) / 0.4))
    if u > 0.6:
        for k in range(4):
            ctx.push_group()
            C.worker_face(ctx, x - k * 60, 640, 1.1, stage=1)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(0.25 if k else 1.0)
    else:
        C.worker_face(ctx, x, 640 + math.sin(f.T * 6) * 10, 1.1, stage=1)


def _palm(ctx, f, t_hit=0.1, face=True):
    if face:
        C.worker_face(ctx, 1150, 690, 1.0, stage=1)
    d = f.t - t_hit
    s = 3.2 if d < 0 else lerp(2.5, 2.6, clamp(d))
    C.glove_hand(ctx, 700, 520, s, angle=-math.pi / 2 + 0.1, pose="open")
    if 0 <= d < 0.4:
        for k in range(14):
            a = k / 14 * 2 * math.pi
            r = 80 + d * 700
            circle(ctx, 900 + r * math.cos(a), 300 + r * math.sin(a) * 0.6, 5, "#DDE8F2", 0.6 * (1 - d / 0.4))


def _mirror_figs(ctx, f):
    x, y, w, h = _mirror_clip(ctx, f)
    ctx.rectangle(x, y, w, h)
    src(ctx, "#0B1014")
    ctx.fill()
    glow(ctx, x + w * 0.7, y + h * 0.2, 400, "#EAF2FF", 0.6)
    rect(ctx, x, y + h * 0.62, w, h * 0.12, "#9DA3A4")
    for k in range(2):
        u = ease(prog(f.t, 0.2 + k * 0.4, f.dur))
        C.worker(ctx, x + w * (0.25 + 0.25 * k) + u * 80, y + h * 0.9, 0.45 + u * 0.15)


def _glass_drop(ctx, f, fingers=False):
    t_drop = 1.2 if not fingers else -1
    gy = 239 if f.t < t_drop else 300 + 6 * math.exp(-(f.t - t_drop) * 8) * math.sin((f.t - t_drop) * 40)
    rect(ctx, -60, 239, DW + 120, max(0, gy - 239), "#020203", 0.92)
    if gy > 245:
        for k in range(26):
            seed = k * 7919
            xx = (seed % DW + f.T * (500 + seed % 400)) % DW
            ln = 10 + seed % 30
            yy = 240 + ((f.T * 900 + seed) % max(1, gy - 240))
            ctx.set_line_width(1.5)
            ctx.move_to(xx, yy)
            ctx.line_to(xx - 6, yy + ln)
            src(ctx, "#DDE8F2", 0.35)
            ctx.stroke()
    rect(ctx, -60, gy, DW + 120, 7, "#C9D8E4", 0.75)
    rect(ctx, -60, gy + 7, DW + 120, 3, "#5E7384", 0.6)
    if fingers:
        u = ease_out(prog(f.t, 0.2, 1.6))
        ctx.move_to(740, gy + 6)
        ctx.curve_to(760, 250, 800, 236, 900, 236)
        ctx.curve_to(1000, 236, 1060, 246, 1090, gy + 6)
        ctx.close_path()
        src(ctx, "#1C3A63", u)
        ctx.fill()
        for k, (fx, l, wdt, c) in enumerate(((800, 150, 62, -0.06), (874, 168, 64, -0.01), (948, 160, 62, 0.03), (1020, 128, 56, 0.08))):
            _finger(ctx, fx, gy + 4, l * u, wdt, torn=(k == 0), curl=c)


def _finger(ctx, x, top, length, width, torn=False, curl=0.0):
    if length < 4:
        return
    ctx.save()
    ctx.translate(x, top)
    ctx.rotate(curl)
    ctx.move_to(-width / 2, -26)
    ctx.curve_to(-width / 2 - 2, length * 0.5, -width / 2 + 2, length - width * 0.3, 0, length)
    ctx.curve_to(width / 2 - 2, length - width * 0.3, width / 2 + 2, length * 0.5, width / 2, -26)
    ctx.curve_to(width / 4, -40, -width / 4, -40, -width / 2, -26)
    ctx.close_path()
    src(ctx, "#3567AE")
    ctx.fill_preserve()
    g = cairo.LinearGradient(-width / 2, 0, width / 2, 0)
    g.add_color_stop_rgba(0, 0.5, 0.65, 0.87, 0.55)
    g.add_color_stop_rgba(0.35, 0.2, 0.4, 0.68, 0.0)
    g.add_color_stop_rgba(1, 0.14, 0.3, 0.52, 0.85)
    ctx.set_source(g)
    ctx.fill()
    if torn and length > 60:
        rrect(ctx, -width * 0.4, length * 0.5, width * 0.8, length * 0.3, 10, "#B99683")
    ctx.restore()


def _gap_plate(P):
    L.side_window(P)
    f = P.fg
    rect(f, -60, 180, DW + 120, 59, "#101317")


def _turnaround(ctx, f):
    _parked_top(ctx, f, turn=ease(prog(f.t, 0.2, f.dur * 0.8)), figs=True)


def _hold_switch(ctx, f):
    sx, sy = f.meta["switch"]
    C.hand(ctx, sx - 220, sy + 20, 1.5, angle=0.0, pose="press")
    _glass_drop(ctx, type("F", (), {"t": 99, "T": f.T})())


def _headlight_sweep(ctx, f):
    x = lerp(-400, DW + 400, ease(f.u))
    glow(ctx, x, 520, 700, "#FFF6E0", 0.55, sx=0.6, sy=1.0)


def _sign_closing(P):
    L.printed_sign(P, panel=(500, 260, 920, 520))
    c = P.bg
    rect(c, -50, -50, DW + 100, DH + 100, "#000000", 0.55)


def _match_cut(ctx, f):
    t11 = item_t(f, 11)
    if t11 is None or f.t < t11:
        return
    a = ease(prog(f.t, t11, t11 + 0.5))
    ctx.rectangle(-60, -60, DW + 120, DH + 120)
    src(ctx, "#C2C8CC", a)
    ctx.fill()
    rect(ctx, 420, 40, 1080, 1000, "#F2F1EC", a)
    for k in range(22):
        rect(ctx, 460, 120 + k * 41, 1000, 2, "#B9C4CC", a)
        if a > 0.9:
            marker_text(ctx, "NO RESPONSE", 1030, 136 + k * 41, 30, seed=k, reveal=clamp((f.t - t11 - 0.5) * 3 - k * 0.15))


def _rain_in(ctx, f):
    cab_daniel(ctx, f, light=AMBER, light_a=0.5, scale=1.7)
    for k in range(40):
        ph = (f.T * 1.3 + k / 40) % 1
        x = 1500 - ph * 500 + (k % 7) * 20
        y = 120 + ph * 500 + (k % 5) * 30
        rect(ctx, x, y, 3, 18, "#DDE8F2", 0.5 * (1 - ph))


def _town_bokeh(ctx, f):
    pass


SHOTS.update({
    "S16_A": S(L.side_window, Cam(1.0, 1.02, handheld=6), live_bg=_alongside, live_fg=lambda c, f: drops(c, f),
               post={"blur": 9}, rain=RAIN_SOFT),
    "S16_B": S(L.side_window, Cam(1.0, 1.0, shakes=((0.1, 30),)), live_bg=_palm, live_fg=lambda c, f: drops(c, f),
               post={"blur": 9}, rain=RAIN_SOFT),
    "S16_C": S(L.side_window, Cam(1.0, 1.04, handheld=3), live_bg=partial(_face, stage=2, scale=1.6, mask_down=1.0),
               live_fg=lambda c, f: drops(c, f), post={"blur": 9}, rain=RAIN_SOFT),
    "S16_D": S(L.mirror, Cam(1.0, 1.02, handheld=9), live_bg=_mirror_figs),
    "S16_E": S(L.side_window, Cam(1.0, 1.0, shakes=((0.2, 40),)), live_bg=partial(_palm, t_hit=0.2),
               live_fg=lambda c, f: drops(c, f), post={"blur": 9}, rain=RAIN_SOFT),
    "S16_F": S(_gap_plate, Cam(1.0, 1.03, shakes=((1.2, 22),)), live_fg=lambda c, f: (_glass_drop(c, f), drops(c, f)),
               post={"blur": 12}, rain=RAIN_SOFT),
    "S16_G": S(_gap_plate, Cam(1.02, 1.08), live_fg=lambda c, f: (_glass_drop(c, f, fingers=True), drops(c, f)),
               post={"blur": 12}, rain=RAIN_SOFT),
    "S17_A": S(L.checkpoint_high, Cam(1.0, 1.06), live_bg=_turnaround, rain=RAIN_SOFT),
    "S17_B": S(_gap_plate, Cam(1.0, 1.04), live_fg=lambda c, f: (_hold_switch(c, f), drops(c, f)), post={"blur": 12}, rain=RAIN_SOFT),
    "S17_C": S(_sign_closing, Cam(1.0, 1.05), live_bg=_headlight_sweep, rain=RAIN),
    "S17_D": S(partial(L.printed_sign, panel=(300, 120, 1320, 840)), Cam(1.0, 1.06), rain=RAIN_SOFT,
               post={"bloom": 0.5, "thresh": 0.85}),
    "S17_E": S(partial(L.sign, panel=(260, 120, 1400, 860), forest=False), Cam(1.0, 1.06), live_bg=_match_cut,
               rain=RAIN_SOFT, post={"bloom": 0.6, "thresh": 0.8}),
    "S17_F": S(L.cab_profile, Cam(1.18, 1.24, (900, 470), (910, 460)), live_bg=_rain_in),
    "S17_G": S(L.phone_close, Cam(1.0, 1.05), live_bg=_phone_route),
    "S17_H": S(L.town_aerial, Cam(1.0, 1.12), live_bg=partial(_aerial_truck, into_town=True), rain=RAIN_SOFT),
})
