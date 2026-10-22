"""Characters, hands and vehicles. Faces stay in shadow; light comes from practical sources."""
import math

import cairo

from kit import hx, src, poly, rect, rrect, rrect_path, circle, ellipse, glow, AMBER

SKIN = "#B88C70"
GLOVE = "#3567AE"
JACKET = "#2B2E31"


# ----------------------------------------------------------------- Daniel

def _head_path(ctx):
    ctx.move_to(-62, 10)
    ctx.curve_to(-92, -40, -112, -110, -92, -165)
    ctx.curve_to(-72, -225, 0, -248, 52, -222)
    ctx.curve_to(78, -206, 88, -180, 90, -152)
    ctx.curve_to(92, -140, 93, -134, 96, -128)
    ctx.curve_to(106, -112, 118, -100, 120, -92)
    ctx.curve_to(116, -84, 104, -82, 98, -80)
    ctx.curve_to(102, -72, 104, -66, 100, -60)
    ctx.curve_to(104, -54, 102, -46, 96, -42)
    ctx.curve_to(98, -30, 94, -18, 78, -12)
    ctx.curve_to(60, -6, 50, 0, 46, 22)
    ctx.close_path()


def daniel_profile(ctx, x, y, s, light=AMBER, light_a=0.6, rim=None, blink=False, look=0.0):
    """Daniel in profile facing right; (x, y) = base of the neck. Mostly shadow, lit from the front."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    # jacket and collar
    ctx.move_to(-230, 260)
    ctx.curve_to(-220, 90, -150, 30, -70, 8)
    ctx.line_to(60, 18)
    ctx.curve_to(150, 40, 210, 120, 230, 260)
    ctx.close_path()
    src(ctx, JACKET)
    ctx.fill()
    poly(ctx, [(-70, 8), (-20, 70), (10, 40), (60, 18), (40, 0), (-50, -4)], "#1D2023")
    poly(ctx, [(10, 40), (60, 18), (90, 70), (40, 90)], "#25292C")
    # head
    _head_path(ctx)
    src(ctx, "#3A2A22")
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    g = cairo.LinearGradient(125, 0, 10, 0)
    g.add_color_stop_rgba(0, *hx(light, light_a))
    g.add_color_stop_rgba(0.55, *hx(light, light_a * 0.25))
    g.add_color_stop_rgba(1, *hx(light, 0))
    ctx.rectangle(-200, -300, 400, 400)
    ctx.set_source(g)
    ctx.fill()
    # stubble along the jaw
    ellipse(ctx, 50, -30, 55, 26, "#1C1512", 0.55)
    # ear
    ellipse(ctx, -22, -118, 15, 24, "#2B1F19")
    ctx.restore()
    # hair
    ctx.move_to(-96, -150)
    ctx.curve_to(-96, -215, -20, -252, 40, -230)
    ctx.curve_to(70, -220, 84, -200, 86, -186)
    ctx.curve_to(40, -200, -10, -196, -40, -176)
    ctx.curve_to(-60, -150, -70, -130, -96, -150)
    ctx.close_path()
    src(ctx, "#141110")
    ctx.fill()
    # eye
    ex, ey = 66 + look * 4, -142
    if blink:
        rect(ctx, ex - 9, ey, 18, 3, "#0B0807")
    else:
        ellipse(ctx, ex, ey, 9, 5, "#0B0807")
        circle(ctx, ex + 4, ey - 1, 1.8, "#F3D9B0", 0.9)
    rect(ctx, ex - 14, ey - 16, 30, 5, "#120E0C", 0.9)   # brow
    if rim:  # thin rim on the front edge
        _head_path(ctx)
        ctx.set_line_width(3)
        src(ctx, rim, 0.7)
        ctx.stroke()
    ctx.restore()


def daniel_back(ctx, x, y, s, phase=None):
    """Daniel from behind, walking away; feet at (x, y)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    sw = math.sin(phase) * 0.35 if phase is not None else 0
    for k, sgn in enumerate((-1, 1)):
        ctx.save()
        ctx.translate(sgn * 22, -250)
        ctx.rotate(sw * sgn)
        rrect(ctx, -19, 0, 38, 250, 16, "#1E2530" if k else "#232B37")
        rrect(ctx, -22, 236, 44, 18, 8, "#0B0C0E")
        ctx.restore()
    ctx.move_to(-82, -470)
    ctx.curve_to(-96, -380, -92, -300, -78, -240)
    ctx.line_to(78, -240)
    ctx.curve_to(92, -300, 96, -380, 82, -470)
    ctx.curve_to(40, -492, -40, -492, -82, -470)
    ctx.close_path()
    src(ctx, JACKET)
    ctx.fill()
    for sgn in (-1, 1):
        ctx.save()
        ctx.translate(sgn * 80, -462)
        ctx.rotate(-sw * sgn * 0.8 + sgn * 0.08)
        rrect(ctx, -17, 0, 34, 210, 16, "#25282B")
        circle(ctx, 0, 214, 15, "#6E5546")
        ctx.restore()
    rect(ctx, -16, -510, 32, 30, "#5E4A3E")
    circle(ctx, 0, -548, 50, "#4A3A31")
    ctx.arc(0, -552, 51, math.pi * 0.95, math.pi * 2.05)
    ctx.close_path()
    src(ctx, "#141110")
    ctx.fill()
    ctx.restore()


# ----------------------------------------------------------------- hands

def hand(ctx, x, y, s, angle=0.0, pose="point", color=SKIN, sleeve=JACKET, torn=False, light=AMBER, light_a=0.25):
    """Hand pointing along +x after rotation. (x, y) = wrist. Poses: point, fist, flat, press, open."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(angle)
    ctx.scale(s, s)
    if sleeve:
        rrect(ctx, -210, -46, 200, 92, 30, sleeve)
        rect(ctx, -30, -46, 18, 92, "#1C1F22")
    dark = hx(color)
    dark = (dark[0] * 0.72, dark[1] * 0.72, dark[2] * 0.72, 1)
    rrect(ctx, -14, -38, 96, 76, 26, color)                 # palm / back of hand
    if pose in ("point", "press"):
        rrect(ctx, 60, -34, 100 if pose == "point" else 80, 24, 12, color)     # index
        for k in range(3):
            rrect(ctx, 64, -8 + k * 16, 34, 18, 9, dark)                         # curled fingers
        rrect(ctx, 20, 18, 52, 22, 11, color)                                     # thumb
        if torn:
            ctx.set_line_width(3)
            ctx.move_to(100, -34)
            for j in range(5):
                ctx.line_to(104 + j * 9, -26 + (5 if j % 2 else -6))
            src(ctx, "#1E3E6E")
            ctx.stroke()
            rrect(ctx, 120, -30, 40, 18, 8, "#B99683")
    elif pose == "fist":
        for k in range(4):
            rrect(ctx, 66, -36 + k * 18, 34, 20, 10, color if k % 2 == 0 else dark)
        rrect(ctx, 30, 20, 50, 22, 11, color)
    elif pose in ("flat", "open"):
        spread = 0.12 if pose == "open" else 0.03
        for k in range(4):
            ctx.save()
            ctx.translate(70, -27 + k * 18)
            ctx.rotate((k - 1.5) * spread)
            rrect(ctx, 0, -9, 92 - abs(k - 1.2) * 12, 19, 9, color)
            ctx.restore()
        ctx.save()
        ctx.translate(20, 30)
        ctx.rotate(0.6)
        rrect(ctx, 0, -10, 60, 22, 11, color)
        ctx.restore()
    g = cairo.LinearGradient(0, -40, 0, 40)
    g.add_color_stop_rgba(0, *hx(light, light_a))
    g.add_color_stop_rgba(1, *hx(light, 0))
    rrect_path(ctx, -14, -38, 96, 76, 26)
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()


def glove_hand(ctx, x, y, s, angle=0.0, pose="point", torn=False):
    hand(ctx, x, y, s, angle, pose, color=GLOVE, sleeve="#C9CFCC", torn=torn, light="#DDE8FF", light_a=0.2)


# ----------------------------------------------------------------- the worker

def worker(ctx, x, y, s, arm_up=False, lean=0.0, rim="#FFFFFF", suit="#C9CFCC"):
    """Man in a disposable coverall, hood down, mask and goggles, backlit; feet at (x, y)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(lean)
    ctx.scale(s, s)
    for rimpass in (True, False):
        o = 4 if rimpass else 0
        col = rim if rimpass else suit
        for dx in (-26, 24):
            ctx.move_to(dx - 24 - o, -250)
            ctx.curve_to(dx - 30 - o, -160, dx - 24 - o, -60, dx - 20 - o, -6)
            ctx.line_to(dx + 20 + o, -6)
            ctx.curve_to(dx + 24 + o, -70, dx + 26 + o, -170, dx + 22 + o, -250)
            ctx.close_path()
            src(ctx, col)
            ctx.fill()
        ctx.move_to(-70 - o, -440 - o)
        ctx.curve_to(-88 - o, -380, -80 - o, -300, -62 - o, -236)
        ctx.line_to(62 + o, -236)
        ctx.curve_to(80 + o, -300, 88 + o, -380, 70 + o, -440 - o)
        ctx.curve_to(40, -462 - o, -40, -462 - o, -70 - o, -440 - o)
        ctx.close_path()
        src(ctx, col)
        ctx.fill()
        ctx.move_to(-66 - o, -432)
        ctx.curve_to(-96 - o, -370, -98 - o, -300, -90 - o, -246)
        ctx.line_to(-66 + o, -246)
        ctx.curve_to(-70 + o, -310, -64 + o, -370, -50 + o, -420)
        ctx.close_path()
        src(ctx, col)
        ctx.fill()
        ctx.save()
        ctx.translate(58, -430)
        ctx.rotate(0.35 if arm_up else -0.05 - math.pi)
        rrect(ctx, -20 - o, -190 - o, 40 + 2 * o, 200 + 2 * o, 20, col)
        ctx.restore()
    rect(ctx, -4, -440, 8, 200, "#AEB4B1", 0.6)
    ellipse(ctx, 0, -246, 64, 10, "#8C9390", 0.4)
    circle(ctx, -78, -236, 16, GLOVE)
    if arm_up:
        hx_, hy_ = 58 + 180 * math.sin(0.35), -430 - 180 * math.cos(0.35)
        rrect(ctx, hx_ - 22, hy_ - 40, 44, 50, 14, GLOVE)
        for k in range(4):
            rrect(ctx, hx_ - 20 + k * 11, hy_ - 64, 9, 30, 4, GLOVE)
    else:
        circle(ctx, 66, -238, 16, GLOVE)
    circle(ctx, 0, -500, 46, "#151A1E")
    ctx.arc(0, -500, 46, math.pi * 1.1, math.pi * 1.9)
    ctx.set_line_width(4)
    src(ctx, rim, 0.8)
    ctx.stroke()
    rrect(ctx, -32, -496, 64, 34, 14, "#E6EAE8")
    rrect(ctx, -30, -522, 60, 16, 7, "#6E8494", 0.85)
    rect(ctx, -24, -519, 18, 4, "#FFFFFF", 0.8)
    ctx.restore()


def worker_face(ctx, x, y, s, stage=0, eye_dx=0.0, mask_down=0.0, head_turn=0.0):
    """Close-up of the worker's head and shoulders, seen through glass. stage 0: normal,
    1: stained mask + neck lines, 2: + clouded eyes. mask_down 0..1 slides the mask below the chin."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.translate(head_turn * 30, 0)
    # shoulders / hood
    ctx.move_to(-330, 420)
    ctx.curve_to(-320, 230, -220, 160, -120, 150)
    ctx.line_to(120, 150)
    ctx.curve_to(220, 160, 320, 230, 330, 420)
    ctx.close_path()
    src(ctx, "#C9CFCC")
    ctx.fill()
    ctx.move_to(-170, 170)
    ctx.curve_to(-180, 90, -150, 40, -110, 30)
    ctx.line_to(110, 30)
    ctx.curve_to(150, 40, 180, 90, 170, 170)
    ctx.close_path()
    src(ctx, "#B7BEBB")
    ctx.fill()       # hood bunched behind the neck
    # neck + face
    rrect(ctx, -60, 40, 120, 140, 40, "#8E7464")
    if stage >= 1:
        ctx.set_line_width(3)
        src(ctx, "#2A1E2A", 0.75)
        for k, (sx_, sy_) in enumerate(((-40, 170), (-10, 175), (25, 172), (45, 168))):
            ctx.move_to(sx_, sy_)
            px, py = sx_, sy_
            for j in range(5):
                px += (-1) ** (j + k) * 9
                py -= 18
                ctx.line_to(px, py)
            ctx.stroke()
    ellipse(ctx, 0, -40, 128, 150, "#9A7D6B")
    ctx.save()
    ctx.arc(0, -40, 1, 0, 0)
    ctx.restore()
    g = cairo.LinearGradient(-130, 0, 130, 0)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.45)
    g.add_color_stop_rgba(0.5, 0, 0, 0, 0.0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.35)
    ctx.save()
    ctx.translate(0, -40)
    ctx.scale(128, 150)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source(g)
    ctx.fill()
    ctx.arc(0, -70, 132, math.pi * 1.05, math.pi * 1.95)
    ctx.close_path()
    src(ctx, "#1C1715")
    ctx.fill()                                       # short hair
    # eyes behind goggles
    for sx_ in (-48, 48):
        ellipse(ctx, sx_, -48, 26, 15, "#E9E6E0" if stage >= 2 else "#F2EEE8")
        if stage >= 2:
            circle(ctx, sx_ + eye_dx * 10, -48, 10, "#B9BDC0", 0.8)
            circle(ctx, sx_ + eye_dx * 10, -48, 4, "#7D8488", 0.6)
        else:
            circle(ctx, sx_ + eye_dx * 10, -48, 10, "#3A2C24")
            circle(ctx, sx_ + 3 + eye_dx * 10, -51, 3, "#FFFFFF", 0.8)
    rrect(ctx, -118, -86, 236, 78, 30, "#A9C2D2", 0.28)
    rrect_path(ctx, -118, -86, 236, 78, 30)
    ctx.set_line_width(10)
    src(ctx, "#5F7686")
    ctx.stroke()
    rect(ctx, -100, -80, 60, 8, "#FFFFFF", 0.5)
    rect(ctx, -140, -62, 22, 12, "#3E4B55")
    rect(ctx, 118, -62, 22, 12, "#3E4B55")
    # mouth area / mask
    my = 30 + mask_down * 120
    if mask_down > 0.2:  # jaw hangs crooked; a dark slack mouth, no teeth
        ctx.save()
        ctx.translate(18, 58)
        ctx.rotate(0.28)
        ellipse(ctx, 0, 0, 22, 14 + 10 * mask_down, "#1A0F10")
        ctx.restore()
        ellipse(ctx, 10, 30, 64, 8, "#5E483D", 0.5)
    rrect(ctx, -92, my - 52, 184, 104, 40, "#E6EAE8")
    if stage >= 1 and mask_down < 0.5:  # stain seeping outward from inside the mask
        for k, (dx, dy, rx, ry) in enumerate(((0, 6, 34, 20), (-26, -6, 16, 12), (24, 14, 18, 10), (8, -16, 12, 9),
                                              (-12, 22, 14, 8), (36, -4, 9, 7))):
            ellipse(ctx, dx, my + dy, rx * (0.8 + 0.15 * stage), ry * (0.8 + 0.15 * stage), "#6B5A50", 0.32)
        ellipse(ctx, 2, my + 4, 18, 11, "#4E4038", 0.35)
    rect(ctx, -120, my - 20, 30, 6, "#D8DCDA")
    rect(ctx, 90, my - 20, 30, 6, "#D8DCDA")
    if stage >= 2:  # the face sinks into shadow
        g = cairo.RadialGradient(0, -20, 40, 0, -20, 220)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.15)
        g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
        ctx.save()
        ctx.translate(0, -40)
        ctx.scale(130, 152)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source(g)
        ctx.fill()
    ctx.restore()


# ----------------------------------------------------------------- other people

def woman(ctx, x, y, s, turn=0.0, walk=None):
    """Woman from behind three-quarters; turn 0..1 turns the head toward camera (face stays dark)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    sw = math.sin(walk) * 0.25 if walk is not None else 0.0
    for k, dx in enumerate((-16, 14)):
        ctx.save()
        ctx.translate(dx, -230)
        ctx.rotate(sw * (1 if k else -1))
        ctx.move_to(-13, 0)
        ctx.curve_to(-14, 80, -10, 170, -8, 226)
        ctx.line_to(9, 226)
        ctx.curve_to(10, 160, 13, 80, 13, 0)
        ctx.close_path()
        src(ctx, "#24282C" if k == 0 else "#1E2226")
        ctx.fill()
        rrect(ctx, -12, 220, 26, 12, 5, "#0C0E10")
        ctx.restore()
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
    for sx in (-1, 1):
        ctx.move_to(sx * 56, -396)
        ctx.curve_to(sx * 74, -340, sx * 74, -280, sx * 68, -222)
        ctx.line_to(sx * 50, -222)
        ctx.curve_to(sx * 54, -290, sx * 52, -350, sx * 44, -390)
        ctx.close_path()
        src(ctx, "#716A5D")
        ctx.fill()
        circle(ctx, sx * 59, -214, 9, "#B79A86")
    rect(ctx, -9, -430, 18, 20, "#9C8574")
    hx_ = turn * 14
    circle(ctx, 2 + hx_, -462, 34, "#2B2421")
    if turn > 0.05:  # a sliver of face in deep shadow between wet strands
        ellipse(ctx, 14 + hx_, -456, 16 * turn, 24, "#3D3029")
    ctx.move_to(-34 + hx_ * 0.5, -470)
    ctx.curve_to(-40, -430, -36, -400, -26, -386)
    ctx.line_to(30 - turn * 10, -388)
    ctx.curve_to(40 - turn * 14, -410, 40 - turn * 10, -440, 34 + hx_ * 0.5, -470)
    ctx.close_path()
    src(ctx, "#241E1B")
    ctx.fill()
    ctx.set_line_width(3)
    ctx.arc(2 + hx_, -462, 34, math.pi * 1.05, math.pi * 1.55)
    src(ctx, "#F7D7A6", 0.7)
    ctx.stroke()
    ctx.restore()


def figure(ctx, x, y, s, color="#06090B", turn=0.0, hood=False, a=1.0):
    """Still standing silhouette; turn rotates the head slightly (0 = facing away)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.push_group()
    rrect(ctx, -26, -230, 22, 230, 10, color)
    rrect(ctx, 4, -230, 22, 230, 10, color)
    ctx.move_to(-52, -420)
    ctx.curve_to(-62, -360, -58, -280, -46, -222)
    ctx.line_to(46, -222)
    ctx.curve_to(58, -280, 62, -360, 52, -420)
    ctx.curve_to(24, -436, -24, -436, -52, -420)
    ctx.close_path()
    src(ctx, color)
    ctx.fill()
    rrect(ctx, -66, -410, 18, 170, 9, color)
    rrect(ctx, 48, -410, 18, 170, 9, color)
    ellipse(ctx, turn * 10, -462, 30 - abs(turn) * 4, 34, color)
    if hood:
        ellipse(ctx, 0, -456, 40, 42, color)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


# ----------------------------------------------------------------- vehicles

def truck_side(ctx, x, ground, s=1.0, wheel_rot=0.0, cab_glow=0.35, headlights=True, facing=1):
    """Unbranded white 26-ft box truck in side view; x = rear end at scale 1, facing right if facing=1."""
    ctx.save()
    ctx.translate(x, ground)
    ctx.scale(s * facing, s)
    top = -300
    g = cairo.LinearGradient(0, top, 0, top + 250)
    g.add_color_stop_rgba(0, *hx("#C9D3DA"))
    g.add_color_stop_rgba(1, *hx("#7F8C96"))
    ctx.rectangle(0, top, 690, 250)
    ctx.set_source(g)
    ctx.fill()
    for k in range(1, 6):
        rect(ctx, k * 115, top + 6, 3, 238, "#8C98A1", 0.6)
    rect(ctx, 0, top + 238, 690, 14, "#3E464C")
    for mx in (12, 668):
        circle(ctx, mx, top + 10, 7, "#FFB23A")
        glow(ctx, mx, top + 10, 26, "#FFB23A", 0.6)
    cx0 = 702
    poly(ctx, [(cx0, -70), (cx0, top + 30), (cx0 + 150, top + 30), (cx0 + 200, top + 140), (cx0 + 270, top + 160),
               (cx0 + 285, -70)], "#B9C4CC")
    poly(ctx, [(cx0 + 18, top + 50), (cx0 + 140, top + 50), (cx0 + 180, top + 135), (cx0 + 18, top + 135)], "#111A21")
    glow(ctx, cx0 + 90, top + 120, 90, AMBER, cab_glow)
    circle(ctx, cx0 + 70, top + 92, 26, "#05090C")
    rect(ctx, cx0 + 40, top + 112, 60, 30, "#05090C")
    for k in range(3):
        circle(ctx, cx0 + 30 + k * 40, top + 26, 5, "#FFB23A")
    rect(ctx, cx0 + 150, top + 60, 8, 70, "#0A0D10")
    rrect(ctx, cx0 + 156, top + 60, 22, 60, 4, "#0A0D10")
    rect(ctx, 0, -70, cx0 + 285, 18, "#2A3136")
    for wx in (110, 200, cx0 + 190):
        circle(ctx, wx, -40, 46, "#07090B")
        circle(ctx, wx, -40, 20, "#4C555B")
        for k in range(5):
            a = wheel_rot + k * 2 * math.pi / 5
            rect(ctx, wx + 12 * math.cos(a) - 3, -40 + 12 * math.sin(a) - 3, 6, 6, "#20262A")
    circle(ctx, 4, -90, 9, "#FF2A1F")
    glow(ctx, 4, -90, 40, "#FF2A1F", 0.8)
    if headlights:
        circle(ctx, cx0 + 278, -98, 10, "#FFF6E0")
        glow(ctx, cx0 + 278, -98, 70, "#FFF6E0", 0.9)
    ctx.restore()


def truck_rear(ctx, x, ground, s=1.0, reverse=0.0, brake=0.6):
    """Rear of the box truck; reverse 0..1 = white reverse lights."""
    ctx.save()
    ctx.translate(x, ground)
    ctx.scale(s, s)
    vg = cairo.LinearGradient(0, -560, 0, -120)
    vg.add_color_stop_rgba(0, *hx("#BCC6CD"))
    vg.add_color_stop_rgba(1, *hx("#78848D"))
    ctx.rectangle(-260, -560, 520, 440)
    ctx.set_source(vg)
    ctx.fill()
    for k in range(9):
        rect(ctx, -250, -545 + k * 46, 500, 4, "#8F9AA2", 0.7)
    rect(ctx, -10, -350, 20, 60, "#3E464C")
    rect(ctx, -270, -130, 540, 26, "#2A3136")
    rect(ctx, -90, -112, 180, 46, "#E3E6E2")                  # blank plate
    for sx in (-1, 1):
        rect(ctx, sx * 230 - 22, -210, 44, 70, "#5A1210")
        glow(ctx, sx * 230, -190, 90, "#FF2A1F", brake)
        circle(ctx, sx * 230, -190, 14, "#FF4A3A", 0.5 + brake * 0.5)
        rect(ctx, sx * 230 - 18, -150, 36, 18, "#DADFE3" if reverse > 0.5 else "#3A4045")
        if reverse > 0:
            glow(ctx, sx * 230, -140, 220, "#F4F8FF", 0.85 * reverse)
        rrect(ctx, sx * 200 - 40, -110, 80, 110, 6, "#07090B")
        circle(ctx, sx * 200, -40, 40, "#0B0D0F")
    for k in range(5):
        circle(ctx, -200 + k * 100, -548, 6, "#FFB23A")
        glow(ctx, -200 + k * 100, -548, 22, "#FFB23A", 0.6)
    ctx.restore()


def truck_front(ctx, x, ground, s=1.0, lights=1.0):
    ctx.save()
    ctx.translate(x, ground)
    ctx.scale(s, s)
    poly(ctx, [(-300, -560), (300, -560), (300, -380), (-300, -380)], "#C3CCD2")          # box behind cab
    poly(ctx, [(-220, -480), (220, -480), (250, -330), (-250, -330)], "#B3BEC6")          # cab
    poly(ctx, [(-190, -465), (190, -465), (215, -350), (-215, -350)], "#0E161C")          # windshield
    glow(ctx, -90, -360, 90, AMBER, 0.35)
    poly(ctx, [(-260, -330), (260, -330), (270, -140), (-270, -140)], "#C9D1D6")           # hood / face
    rrect(ctx, -110, -310, 220, 140, 10, "#2A3136")                                          # grille
    for k in range(6):
        rect(ctx, -100, -300 + k * 22, 200, 8, "#3E464C")
    for sx in (-1, 1):
        rrect(ctx, sx * 190 - 50, -290, 100, 50, 12, "#E9EDF0")
        if lights:
            glow(ctx, sx * 190, -265, 260, "#FFF6E0", lights)
    rect(ctx, -280, -150, 560, 40, "#2A3136")
    for sx in (-1, 1):
        rrect(ctx, sx * 205 - 45, -150, 90, 150, 10, "#07090B")
        rect(ctx, sx * 300 - 10, -440, 20, 110, "#0A0D10")
    for k in range(3):
        circle(ctx, -40 + k * 40, -488, 6, "#FFB23A")
    ctx.restore()


def sedan(ctx, x, ground, s=1.0, color="#1C2E52", door_open=True, dome=True, window_down=True, facing=1):
    """Four-door sedan, side view, front to the right (facing=1). x = rear bumper."""
    ctx.save()
    ctx.translate(x, ground)
    ctx.scale(s * facing, s)
    dark = hx(color)
    dark = (dark[0] * 0.6, dark[1] * 0.6, dark[2] * 0.6, 1)
    poly(ctx, [(0, -40), (30, -80), (110, -120), (270, -120), (340, -80), (400, -70), (400, -25), (0, -25)], color)
    poly(ctx, [(125, -112), (260, -112), (320, -80), (120, -80)], "#0B1220")
    rect(ctx, 188, -112, 6, 32, color)
    if dome:
        glow(ctx, 210, -95, 70, "#FFE7B0", 0.7)
    if window_down:
        rect(ctx, 196, -112, 60, 30, "#05080D")
    if door_open:
        poly(ctx, [(196, -80), (262, -80), (300, -140), (300, -25), (262, -22)], dark)
        poly(ctx, [(262, -80), (300, -140), (300, -112), (270, -78)], "#05080D")
    for wx in (80, 320):
        circle(ctx, wx, -22, 30, "#050709")
        circle(ctx, wx, -22, 12, "#3A4246")
    rect(ctx, 392, -60, 10, 10, "#FFE9C0", 0.5)
    rect(ctx, 0, -60, 8, 12, "#7A1410")
    ctx.restore()


def ambulance_front(ctx, x, y, s, flash):
    """Approaching ambulance seen head-on; flash 0..1 alternates the light bar."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rect(ctx, -160, -330, 320, 230, "#D9DDE0")
    poly(ctx, [(-150, -100), (150, -100), (165, -20), (-165, -20)], "#C2C8CC")
    poly(ctx, [(-120, -230), (120, -230), (135, -110), (-135, -110)], "#0E151B")
    rect(ctx, -170, -20, 340, 30, "#2A3136")
    rect(ctx, -140, -350, 280, 22, "#2A3136")
    on = flash > 0.5
    rect(ctx, -130, -348, 120, 16, "#FF3B30" if on else "#5A1512")
    rect(ctx, 10, -348, 120, 16, "#F4F8FF" if not on else "#3A3F44")
    glow(ctx, -70, -340, 380, "#FF3B30", 0.75 if on else 0.15)
    glow(ctx, 70, -340, 380, "#E6F0FF", 0.15 if on else 0.75)
    for sx in (-1, 1):
        glow(ctx, sx * 120, -60, 200, "#FFF6E0", 0.9)
    ctx.restore()


def van_rear(ctx, x, ground, s=1.0, doors=1.0):
    """County health van from behind, rear doors swung open (doors 0..1)."""
    ctx.save()
    ctx.translate(x, ground)
    ctx.scale(s, s)
    rect(ctx, -230, -470, 460, 400, "#D5DADD")
    rect(ctx, -200, -440, 400, 360, "#10161B")                  # dark cargo opening
    for k in range(3):
        rect(ctx, -190, -420 + k * 110, 380, 8, "#2A3238")
    for sx in (-1, 1):
        w = 200 * (1 - doors * 0.8)
        poly(ctx, [(sx * 230, -470), (sx * (230 + 60 * doors), -480), (sx * (230 + 60 * doors), -60), (sx * 230, -70)], "#C2C8CC")
        rect(ctx, sx * 228 - (6 if sx > 0 else 0), -470, 6, 400, "#9AA2A6")
    rect(ctx, -240, -80, 480, 30, "#2A3136")
    for sx in (-1, 1):
        rrect(ctx, sx * 180 - 40, -70, 80, 70, 8, "#07090B")
        circle(ctx, sx * 220, -360, 10, "#FF2A1F", 0.6)
    ctx.restore()
