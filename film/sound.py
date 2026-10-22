"""Soundtrack: recorded narration + synthesized music, ambience and SFX, all placed from timeline.json.

usage: sound.py TIMELINE.json VO_CLEAN.wav OUT.wav
"""
import json
import sys

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import signal
from scipy.ndimage import maximum_filter1d, uniform_filter1d

SR = 48000
rng = np.random.default_rng(11)


def db(x):
    return 10 ** (x / 20)


def tt(d):
    return np.arange(int(d * SR)) / SR


def lp(x, f, o=2):
    return signal.sosfilt(signal.butter(o, f, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, f, o=2):
    return signal.sosfilt(signal.butter(o, f, "high", fs=SR, output="sos"), x, axis=0)


def bp(x, lo, hi, o=2):
    return signal.sosfilt(signal.butter(o, [lo, hi], "band", fs=SR, output="sos"), x, axis=0)


def noise(d):
    return rng.standard_normal(int(d * SR))


def env(n, a=0.01, r=0.05):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def norm(x, peak=1.0):
    m = np.abs(x).max()
    return x / m * peak if m > 0 else x


# ================================================================= one-shots

def s_thud(f=70, d=0.5, click=0.4):
    t = tt(d)
    fr = f * (1 + 0.8 * np.exp(-t * 30))
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 9)
    x += lp(noise(d), 2500) * np.exp(-t * 60) * click
    return norm(x)


def s_click(d=0.06, hi=3000):
    t = tt(d)
    return norm(hp(noise(d), hi) * np.exp(-t * 400) + np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 200) * 0.4)


def s_metal(partials, d, decay=4.0):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * p * t + rng.uniform(0, 6)) * np.exp(-t * decay * (1 + i * 0.3)) / (1 + i * 0.4)
            for i, p in enumerate(partials))
    return norm(x)


def truck_door_close():
    x = s_thud(65, 0.7)
    r = bp(noise(0.5), 800, 3000) * np.exp(-tt(0.5) * 18) * 0.3
    x[:len(r)] += r
    return norm(x)


def door_lock_thunk():
    x = np.zeros(int(0.3 * SR))
    c = s_click()
    x[:len(c)] += c * 0.7
    th = s_thud(110, 0.25, 0.2)
    x[int(0.03 * SR):int(0.03 * SR) + len(th)] += th * 0.8
    return norm(x)


def phone_buzz_counter():
    d = 1.4
    t = tt(d)
    gate = ((t % 0.6) < 0.4).astype(float)
    gate = lp(gate, 40)
    x = signal.square(2 * np.pi * 165 * t) * 0.5 + np.sin(2 * np.pi * 330 * t) * 0.3
    x = bp(x * (1 + 0.6 * lp(noise(d), 300)), 120, 2500)
    return norm(x * gate)


def scrape_door(d=1.6):
    t = tt(d)
    am = np.clip(lp(noise(d), 12) * 4 + 0.5, 0, 1)
    x = bp(noise(d), 250, 1400) * am * np.sin(np.pi * t / d) ** 0.6
    return norm(x)


def soup_can_roll():
    d = 2.4
    t = tt(d)
    roll = (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t * np.exp(-t * 0.4))) * np.exp(-t * 0.9)
    x = bp(noise(d), 1100, 1300, 2) * 6 + bp(noise(d), 2200, 2500, 2) * 4
    x = x * roll
    clink = s_metal([1800, 2950, 4100], 0.6, 8)
    s = int(2.0 * SR)
    x[s:s + len(clink)] += clink[:len(x) - s] * 0.6
    return norm(x)


def handle_strain(d):
    t = tt(d)
    f = 95 + 8 * lp(noise(d), 4) * 20
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    am = np.clip(0.4 + lp(noise(d), 8) * 6, 0, 1)
    return norm(bp(x * am, 400, 2200))


def hazard_tick(d):
    x = np.zeros(int(d * SR))
    for k, t0 in enumerate(np.arange(0, d, 0.7)):
        c = s_click(0.03, 1500) * (1 if k % 2 else 0.7)
        i = int(t0 * SR)
        x[i:i + len(c)] += c[:len(x) - i]
    return x


def call_drop_tone():
    out = []
    for f in (950, 750, 560):
        t = tt(0.13)
        out.append(np.sin(2 * np.pi * f * t) * env(len(t), 0.005, 0.02))
        out.append(np.zeros(int(0.05 * SR)))
    return norm(np.concatenate(out))


def horn_tap():
    t = tt(0.45)
    x = signal.square(2 * np.pi * 311 * t) + signal.square(2 * np.pi * 370 * t)
    x = lp(x, 1800, 4) * env(len(t), 0.02, 0.12)
    return norm(x)


def van_door_creak(d):
    return norm(handle_strain(d) * 0.5 + bp(noise(d), 500, 900) * 0.2)


def fence_drag():
    d = 1.8
    t = tt(d)
    fr = 600 + 900 * t / d
    x = bp(noise(d), 700, 5000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * t)))
    x += 0.4 * signal.sawtooth(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-((t - d / 2) ** 2) * 2)
    return norm(x * np.sin(np.pi * t / d) ** 0.4)


def fence_clatter():
    d = 2.6
    x = np.zeros(int(d * SR))
    for k in range(9):
        hit = s_metal([rng.uniform(300, 900), rng.uniform(1300, 2600), rng.uniform(3000, 5200)], 1.4, rng.uniform(3, 7))
        i = int((0.02 + k * rng.uniform(0.04, 0.16)) * SR)
        x[i:i + len(hit)] += hit[:len(x) - i] * rng.uniform(0.3, 1.0)
    x[:int(0.4 * SR)] += lp(noise(0.4), 4000) * np.exp(-tt(0.4) * 12) * 1.5
    return norm(x)


def boxes_shift():
    d = 1.2
    x = np.zeros(int(d * SR))
    for k in range(4):
        th = s_thud(rng.uniform(90, 140), 0.4, 0.5)
        i = int(k * rng.uniform(0.12, 0.25) * SR)
        x[i:i + len(th)] += th[:len(x) - i] * rng.uniform(0.4, 1)
    return norm(x)


def coverall_rustle(d=0.9):
    x = np.zeros(int(d * SR))
    for _ in range(int(d * 140)):
        g = int(rng.uniform(0.002, 0.01) * SR)
        i = rng.integers(0, len(x) - g)
        x[i:i + g] += rng.standard_normal(g) * np.hanning(g) * rng.uniform(0.2, 1)
    return norm(hp(x, 2500) * np.sin(np.pi * np.arange(len(x)) / len(x)) ** 0.5)


def handle_pull():
    x = np.zeros(int(0.6 * SR))
    c = s_click(0.05, 1200)
    x[:len(c)] += c
    r = bp(noise(0.5), 600, 3000) * np.exp(-tt(0.5) * 10) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 28 * tt(0.5))))
    x[int(0.04 * SR):int(0.04 * SR) + len(r)] += r * 0.7
    th = s_thud(140, 0.3, 0.3)
    x[:len(th)] += th * 0.6
    return norm(x)


def palm_hit_glass():
    d = 1.2
    t = tt(d)
    x = s_thud(85, d, 0.9) * 1.0
    x += s_metal([2150, 3370, 4710], d, 6) * 0.25
    x += lp(noise(d), 3000) * np.exp(-t * 45) * 0.8
    return norm(x)


def mirror_rattle():
    d = 0.7
    t = tt(d)
    return norm(bp(noise(d), 1500, 6000) * np.exp(-t * 6) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 35 * t))))


def window_drop_clunk():
    d = 0.8
    t = tt(d)
    x = s_thud(120, d, 0.6)
    slide = bp(noise(0.25), 1500, 5000) * np.linspace(1, 0, int(0.25 * SR))
    x[:len(slide)] += slide * 0.5
    x += s_metal([900, 1650], d, 9) * 0.3
    return norm(x)


def engine_rev():
    d = 2.2
    t = tt(d)
    f = 30 + 30 * np.clip(t / 1.2, 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(ph * k) / k for k in range(1, 8))
    x = lp(x + lp(noise(d), 300) * 0.6, 500) * env(len(t), 0.1, 0.8)
    return norm(x)


# ================================================================= loops (length = cue duration)

def engine_idle(d):
    t = tt(d)
    f = 28 + 0.6 * np.sin(2 * np.pi * 0.3 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(ph * k + k) / k ** 1.2 for k in range(1, 9))
    x = lp(x, 260) + lp(noise(d), 160) * 0.5
    return norm(x)


def tires_wet(d):
    t = tt(d)
    return norm(bp(noise(d), 1200, 7000) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.2 * t)))


def wipers(d, period=1.7):
    x = np.zeros(int(d * SR))
    for k, t0 in enumerate(np.arange(0.0, d, period / 2)):
        sw = bp(noise(0.42), 800, 4000) * np.sin(np.pi * np.arange(int(0.42 * SR)) / int(0.42 * SR)) ** 2
        th = s_thud(140, 0.15, 0.2) * 0.5
        i = int(t0 * SR)
        x[i:i + len(sw)] += sw[:len(x) - i]
        j = i + len(sw)
        x[j:j + len(th)] += th[:max(0, len(x) - j)]
    return norm(x)


def radio_low(d):
    t = tt(d)
    chords = [(50, 53, 57), (46, 50, 53), (53, 57, 60), (48, 52, 55)]
    x = np.zeros(len(t))
    seg = 4.0
    for k in range(int(d / seg) + 1):
        notes = chords[k % 4]
        i0, i1 = int(k * seg * SR), min(len(t), int((k + 1) * seg * SR))
        tt_ = t[i0:i1] - k * seg
        e = np.minimum(1, tt_ / 0.6) * np.minimum(1, (seg - tt_) / 0.6)
        for m in notes:
            fr = 440 * 2 ** ((m - 69) / 12)
            x[i0:i1] += np.sin(2 * np.pi * fr * tt_) * e * 0.3 + np.sin(4 * np.pi * fr * tt_) * e * 0.08
    return norm(bp(x + noise(d) * 0.01, 300, 3200))


def door_chime(d):
    x = np.zeros(int(d * SR))
    for t0 in np.arange(0, d, 1.0):
        t = tt(0.5)
        c = (np.sin(2 * np.pi * 1047 * t) + 0.3 * np.sin(2 * np.pi * 2094 * t)) * np.exp(-t * 7)
        i = int(t0 * SR)
        x[i:i + len(c)] += c[:len(x) - i]
    return norm(x)


def canopy_hum(d):
    t = tt(d)
    x = np.sin(2 * np.pi * 60 * t) * 0.5 + np.sin(2 * np.pi * 120 * t) * 0.4 + np.sin(2 * np.pi * 180 * t) * 0.15
    x += bp(signal.square(2 * np.pi * 120 * t), 2000, 6000) * 0.05
    return norm(x)


def store_fridges(d):
    t = tt(d)
    x = np.sin(2 * np.pi * 100 * t) * 0.3 + lp(noise(d), 400) * 0.6 + np.sin(2 * np.pi * 50 * t) * 0.2
    return norm(x)


def generator_hum(d):
    t = tt(d)
    f = 30
    ph = 2 * np.pi * f * t
    x = sum(np.sin(ph * k) / k for k in range(1, 10)) * (1 + 0.15 * np.sin(2 * np.pi * 7.5 * t))
    x = lp(x, 700) + lp(noise(d), 900) * 0.4
    return norm(x)


def phone_ring(d):
    x = np.zeros(int(d * SR))
    pat = [(0.0, 1319), (0.15, 1568), (0.3, 1319), (0.45, 1976)]
    for t0 in np.arange(0, d, 1.4):
        for dt, fr in pat:
            t = tt(0.22)
            n = (np.sin(2 * np.pi * fr * t) + 0.4 * np.sin(2 * np.pi * fr * 2 * t)) * np.exp(-t * 10)
            i = int((t0 + dt) * SR)
            x[i:i + len(n)] += n[:max(0, len(x) - i)]
    return norm(x)


def backup_alarm(d):
    t = tt(d)
    gate = ((t % 1.0) < 0.5).astype(float)
    gate = lp(gate, 200)
    x = (np.sin(2 * np.pi * 1050 * t) + 0.3 * signal.square(2 * np.pi * 1050 * t)) * gate
    return norm(lp(x, 5000))


def rain_gust(d):
    t = tt(d)
    x = bp(noise(d), 300, 9000) + lp(noise(d), 400) * 0.5
    return norm(x * np.minimum(1, t / 0.08))


def window_motor(d):
    t = tt(d)
    f = 175 - 25 * np.clip(t / d, 0, 1) + 6 * np.sin(2 * np.pi * 9 * t)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    return norm(bp(x, 150, 3000) * env(len(t), 0.05, 0.1))


ONESHOT = {"truck_door_close": truck_door_close, "door_lock_thunk": door_lock_thunk,
           "phone_buzz_counter": phone_buzz_counter, "scrape_door": scrape_door, "soup_can_roll": soup_can_roll,
           "call_drop_tone": call_drop_tone, "horn_tap": horn_tap, "radio_click_off": lambda: s_click(0.05, 1500),
           "fence_drag": fence_drag, "fence_clatter": fence_clatter, "boxes_shift": boxes_shift,
           "coverall_rustle": coverall_rustle, "handle_pull": handle_pull, "palm_hit_glass": palm_hit_glass,
           "mirror_rattle": mirror_rattle, "window_drop_clunk": window_drop_clunk, "engine_rev": engine_rev}
LOOP = {"engine_idle_cab": engine_idle, "tires_wet": tires_wet, "wipers": wipers, "radio_low_instrumental": radio_low,
        "door_chime_loop": door_chime, "canopy_hum": canopy_hum, "store_fridges": store_fridges,
        "handle_strain": handle_strain, "hazard_tick": hazard_tick, "van_door_creak": van_door_creak,
        "generator_hum": generator_hum, "phone_ring_mount": phone_ring, "backup_alarm_loop": backup_alarm,
        "rain_gust_inside": rain_gust, "window_motor_whine": window_motor, "rain_outside": rain_gust}
LEVEL = {"engine_idle_cab": -22, "tires_wet": -30, "wipers": -24, "radio_low_instrumental": -26, "door_chime_loop": -24,
         "canopy_hum": -32, "store_fridges": -30, "handle_strain": -18, "hazard_tick": -24, "van_door_creak": -26,
         "generator_hum": -24, "phone_ring_mount": -12, "backup_alarm_loop": -15, "rain_gust_inside": -20,
         "window_motor_whine": -16, "rain_outside": -26, "truck_door_close": -12, "door_lock_thunk": -14,
         "phone_buzz_counter": -14, "scrape_door": -12, "soup_can_roll": -14, "call_drop_tone": -18, "horn_tap": -8,
         "radio_click_off": -16, "fence_drag": -10, "fence_clatter": -6, "boxes_shift": -12, "coverall_rustle": -20,
         "handle_pull": -9, "palm_hit_glass": -4, "mirror_rattle": -14, "window_drop_clunk": -6, "engine_rev": -12}


def place(bus, x, t0, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if i0 >= len(bus) or len(x) == 0:
        return
    if i0 < 0:
        x, i0 = x[-i0:], 0
    n = min(len(x), len(bus) - i0)
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    bus[i0:i0 + n, 0] += x[:n] * gain * l * 1.414
    bus[i0:i0 + n, 1] += x[:n] * gain * r * 1.414


def sfx_bus(tl, N):
    bus = np.zeros((N, 2))
    for cue in tl["sfx"]:
        name, t0 = cue["cue"], cue["in"]
        g = db(LEVEL.get(name, -18) + cue.get("gain_db", 0))
        if "out" in cue and name in LOOP:
            d = max(0.2, cue["out"] - t0)
            x = LOOP[name](d) * env(int(d * SR), 0.3 if name not in ("backup_alarm_loop", "phone_ring_mount") else 0.005, 0.3)
        elif name in ONESHOT:
            x = ONESHOT[name]()
        elif name in LOOP:  # loop cue used as a one-off (e.g. a passing tire swoosh)
            d = 2.0
            x = LOOP[name](d) * np.sin(np.pi * np.arange(int(d * SR)) / int(d * SR)) ** 2
        else:
            print("unknown cue", name)
            continue
        place(bus, x, t0, g, pan=0.0)
    return bus


# ================================================================= ambience + music

def rain_bed(tl, N):
    t = np.arange(N) / SR
    x = np.stack([bp(rng.standard_normal(N), 400, 9000), bp(rng.standard_normal(N), 400, 9000)], axis=1)
    x += np.stack([lp(rng.standard_normal(N), 300)] * 2, axis=1) * 0.4
    gain = np.full(N, db(-27))
    for sc in tl["scenes"]:
        i0, i1 = int(sc["start"] * SR), int(sc["end"] * SR)
        if sc["id"] in ("S04",):
            gain[i0:i1] = db(-40)
    gain = lp(gain, 2)
    fade = np.clip(t / 1.0, 0, 1) * np.clip((tl["duration"] - t) / 3.0, 0, 1)
    return x / np.abs(x).max() * (gain * fade)[:, None]


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


def pad(N, notes, detune=0.003, bright=6):
    t = np.arange(N) / SR
    x = np.zeros(N)
    for m in notes:
        for d in (-detune, 0, detune):
            f = note(m) * (1 + d)
            ph = rng.uniform(0, 6)
            for k in range(1, bright + 1):
                if f * k < 5000:
                    x += np.sin(2 * np.pi * f * k * t + ph * k) / k ** 1.5
    x *= 1 + 0.12 * np.sin(2 * np.pi * 0.17 * t)
    return x / np.abs(x).max()


def pulse(N, bpm=60, offset=0.0):
    x = np.zeros(N)
    period = 60 / bpm
    tp = np.arange(int(0.7 * SR)) / SR
    f = 42 * (1 + 0.7 * np.exp(-tp * 25))
    hit = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tp * 6) * (1 - np.exp(-tp * 300))
    for t0 in np.arange(offset, N / SR, period):
        i = int(t0 * SR)
        x[i:i + len(hit)] += hit[:max(0, N - i)]
    return x / max(1e-9, np.abs(x).max())


STATES = {  # layer gains per music state
    "drone": {"main": 1.0},
    "drone_rising": {"main": 1.0, "cluster": 0.6, "rise": 1.0},
    "pulse": {"main": 0.8, "pulse": 1.0},
    "pulse_rising": {"main": 0.9, "pulse": 1.0, "cluster": 0.5, "rise": 1.0},
    "pulse_fast": {"main": 0.7, "pulse_alarm": 1.0, "cluster": 0.9},
    "relief_thin": {"high": 1.0},
    "drone_low": {"low": 1.0},
    "drone_narrow": {"low": 0.8, "cluster": 0.7},
    "silent_then_pulse": {"main": 0.7, "pulse": 0.9},
}


def music(tl, N):
    layers = {
        "main": pad(N, (38, 45, 50, 53)),
        "low": pad(N, (26, 33, 38), bright=4),
        "high": pad(N, (69, 74), bright=3),
        "cluster": pad(N, (50, 51, 57), bright=4),
        "pulse": pulse(N, 60),
    }
    alarm = [c for c in tl["sfx"] if c["cue"] == "backup_alarm_loop"]
    layers["pulse_alarm"] = pulse(N, 60, offset=alarm[0]["in"] if alarm else 0.0)
    t = np.arange(N) / SR
    rise = np.zeros(N)
    gains = {k: np.zeros(N) for k in layers}
    for m in tl["music"]:
        i0, i1 = int(m["start"] * SR), int(m["end"] * SR)
        st = STATES.get(m.get("state"), {"main": 1.0})
        inten = m.get("intensity", 0.3)
        seg = np.ones(i1 - i0)
        if st.get("rise"):
            seg = np.linspace(0.6, 1.4, i1 - i0)
        if m["state"] == "silent_then_pulse" and "back_in_at" in m:
            seg[: max(0, int((m["back_in_at"] - m["start"]) * SR))] = 0
        if "drop_out_at" in m:
            seg[max(0, int((m["drop_out_at"] - m["start"]) * SR)):] = 0
        if "out_at" in m:
            seg[max(0, int((m["out_at"] - m["start"]) * SR)):] = 0
        for k, g in st.items():
            if k in gains:
                gains[k][i0:i1] = g * inten * seg
    out = np.zeros(N)
    for k, x in layers.items():
        g = lp(gains[k], 1.2)          # ~1 s crossfades between states
        out += x * np.clip(g, 0, None)
    out = lp(out, 2500)
    st = np.stack([out, np.roll(out, int(0.011 * SR))], axis=1)
    return st * db(-14)


def reverb(x, seconds=2.4, wet=0.25):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-2.6 * t)[:, None]
    ir = lp(ir, 5000)
    ir /= np.sqrt((ir ** 2).sum(axis=0))
    wetx = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], axis=1)
    return x + wet * wetx


# ================================================================= mix

def duck(vo, depth_db):
    e = np.sqrt(np.maximum(uniform_filter1d(vo ** 2, int(0.01 * SR)), 0))
    act = maximum_filter1d((e > 0.01).astype(float), int(0.35 * SR))
    target = np.where(act > 0, db(depth_db), 1.0)
    out = np.empty(len(vo))
    g = 1.0
    a_att, a_rel = np.exp(-48 / (0.08 * SR)), np.exp(-48 / (0.5 * SR))
    for i in range(0, len(vo), 48):
        tg = target[i]
        g = tg + (g - tg) * (a_att if tg < g else a_rel)
        out[i:i + 48] = g
    return out


def limiter(x, ceiling_db):
    c = db(ceiling_db)
    up = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    tp = up[:4 * len(x)].reshape(-1, 4).max(axis=1)
    peak = maximum_filter1d(tp, size=int(0.01 * SR) + 1)
    g = np.minimum(1.0, c / np.maximum(peak, 1e-9))
    rel = np.exp(-1 / (0.08 * SR))
    gs = np.minimum(signal.lfilter([1 - rel], [1, -rel], g), g)
    return x * gs[:, None]


def main():
    tl = json.load(open(sys.argv[1]))
    vo, sr = sf.read(sys.argv[2])
    assert sr == SR
    if vo.ndim > 1:
        vo = vo.mean(axis=1)
    N = int(tl["duration"] * SR) + SR
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
    vo = hp(vo, 70)
    meter = pyln.Meter(SR)
    vo *= db(-16 - meter.integrated_loudness(vo))
    mus = music(tl, N) * duck(vo, -10)[:, None]
    fx = sfx_bus(tl, N) * duck(vo, -3)[:, None]
    amb = rain_bed(tl, N) * duck(vo, -4)[:, None]
    mix = np.stack([vo, vo], axis=1) + reverb(mus, wet=0.35) + reverb(fx, 1.6, 0.18) + amb
    t = np.arange(N) / SR
    mix *= (np.clip(t / 0.5, 0, 1) * np.clip((tl["duration"] - t) / 2.0, 0, 1))[:, None]
    for _ in range(3):
        mix = limiter(mix, -2.0)
        mix *= db(-14.0 - meter.integrated_loudness(mix))
    mix = limiter(mix, -1.6)
    print(f"loudness {meter.integrated_loudness(mix):.2f} LUFS")
    sf.write(sys.argv[3], mix.astype(np.float32), SR, subtype="PCM_24")


if __name__ == "__main__":
    main()
