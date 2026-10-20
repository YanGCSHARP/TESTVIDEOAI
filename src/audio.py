"""Synthesise music + SFX, mix with the voice-over, duck, normalise to -14 LUFS.

usage: audio.py OUT.wav
"""
import json
import sys

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import signal
from scipy.ndimage import maximum_filter1d

import timeline as tl

SR = 48000
N = int(tl.DURATION * SR)
rng = np.random.default_rng(7)
T = np.arange(N) / SR


def db(x):
    return 10 ** (x / 20)


def env_pts(points):
    """Piecewise-linear envelope over the whole timeline from (time, value) pairs."""
    ts, vs = zip(*points)
    return np.interp(T, ts, vs)


def place(bus, clip, t0, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if i0 >= N:
        return
    if i0 < 0:
        clip, i0 = clip[-i0:], 0
    n = min(len(clip), N - i0)
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    bus[i0:i0 + n, 0] += clip[:n] * gain * l * 1.414
    bus[i0:i0 + n, 1] += clip[:n] * gain * r * 1.414


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)


def reverb_ir(seconds=2.2, decay=3.0):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-decay * t)[:, None]
    ir[:, 0] = lp(ir[:, 0], 5000)
    ir[:, 1] = lp(ir[:, 1], 5000)
    return ir / np.sqrt((ir ** 2).sum(axis=0))


IR = reverb_ir()


def reverb(bus, wet):
    out = np.stack([signal.fftconvolve(bus[:, c], IR[:, c])[:N] for c in range(2)], axis=1)
    return bus + wet * out


# ================================================================= music

def note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def pad_voice(freq, amp_env, bright=6, detune=0.0025):
    """Soft saw-ish pad: additive partials, 3 detuned copies, slow tremolo."""
    out = np.zeros(N)
    for d in (-detune, 0.0, detune):
        f = freq * (1 + d)
        ph = rng.uniform(0, 2 * np.pi)
        for k in range(1, bright + 1):
            if f * k > 6000:
                break
            out += np.sin(2 * np.pi * f * k * T + ph * k) / k ** 1.4
    trem = 1 + 0.12 * np.sin(2 * np.pi * 0.21 * T + rng.uniform(0, 6))
    return out * amp_env * trem / 3


def music():
    bus = np.zeros((N, 2))
    # D minor drone pad; chord voices fade in/out to follow the story
    D2, A2, D3, F3, A3, Bb2, G2, Eb3, C3, E3 = (note(m) for m in (38, 45, 50, 53, 57, 46, 43, 51, 48, 52))
    voices = [
        (D2, [(0, 0), (1.5, .55), (10, .7), (10.05, .9), (15.7, .8), (21.3, .8), (27, .7), (30, .3)], 0.0),
        (A2, [(0, 0), (2, .35), (10, .45), (15.7, .25), (21.3, .4), (27.2, .35), (30, .1)], -0.3),
        (D3, [(0, 0), (2.5, .25), (9.9, .3), (10.1, 0), (21.3, 0), (22, .25), (27.2, .25), (30, 0)], 0.3),
        (F3, [(0, 0), (3, .22), (9.9, .26), (10.1, 0), (15.7, 0), (16.5, .22), (27.2, .2), (30, .05)], -0.2),
        # dissonant b2 creeping in before the impact
        (Eb3, [(0, 0), (7.5, 0), (9.95, .3), (10.05, 0), (19.5, 0), (21.25, .28), (21.35, 0), (30, 0)], 0.2),
        # after the impact: Bb / G colour for the cold years
        (Bb2, [(0, 0), (10, 0), (11, .35), (15.7, .3), (21.3, .1), (22, 0), (30, 0)], 0.25),
        (G2, [(0, 0), (15.5, 0), (16.5, .3), (21.3, .3), (22, 0), (30, 0)], -0.25),
        # lab / map: a lift to C and E (hope, discovery) over the D drone
        (C3, [(0, 0), (21.3, 0), (22.2, .22), (27.2, .2), (28, 0), (30, 0)], -0.3),
        (A3, [(0, 0), (22, 0), (23.3, .16), (27.2, .14), (30, 0)], 0.35),
    ]
    for f, pts, pan in voices:
        v = pad_voice(f, env_pts(pts))
        place(bus, v, 0, 0.18, pan)
    # low-pass the pad, opening the filter as tension rises
    cutoff = env_pts([(0, 700), (9.9, 2200), (10.05, 500), (15.7, 900), (21.2, 2400), (21.4, 1200),
                      (27.2, 1500), (30, 500)])
    out = np.zeros_like(bus)
    hop = 2400
    for i in range(0, N, hop):
        fc = cutoff[i]
        sos = signal.butter(2, fc, btype="low", fs=SR, output="sos")
        out[i:i + hop] = signal.sosfilt(sos, bus[max(0, i - 4800):i + hop], axis=0)[-(min(hop, N - i)):]
    bus = out

    # pulse bass at 70 BPM
    beat = 60 / 70
    bass_note = note(26)
    pulse_len = int(0.6 * SR)
    tt = np.arange(pulse_len) / SR
    for seg_a, seg_b, g0, g1 in ((1.0, 9.95, 0.35, 0.8), (15.9, 21.25, 0.45, 0.85), (21.3, 27.1, 0.75, 0.75)):
        t = seg_a
        while t < seg_b:
            u = (t - seg_a) / (seg_b - seg_a)
            f = bass_note * (1 + 0.6 * np.exp(-tt * 30))
            ph = 2 * np.pi * np.cumsum(f) / SR
            p = (np.sin(ph) + 0.35 * np.sin(2 * ph)) * np.exp(-tt * 6.5) * (1 - np.exp(-tt * 400))
            place(bus, p, t, 0.42 * (g0 + (g1 - g0) * u))
            t += beat
    # risers into 0:10 and 0:21
    for a, b in tl.RISERS:
        n = int((b - a) * SR)
        tt = np.arange(n) / SR
        u = tt / (b - a)
        noise = rng.standard_normal(n)
        r = np.zeros(n)
        for i in range(0, n, 1200):
            fc = 200 + 3800 * u[i] ** 2
            r[i:i + 1200] = bp(noise[max(0, i - 2400):i + 1200], fc * 0.7, fc * 1.3)[-len(r[i:i + 1200]):]
        f = 110 * 2 ** (2.5 * u)
        tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5
        rise = (r * 2.5 + tone) * u ** 2.2 * 0.22
        place(bus, rise, a)
    return bus


# ================================================================= SFX

def sfx_tick(pitch):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    click = rng.standard_normal(n) * np.exp(-t * 900)
    body = np.sin(2 * np.pi * pitch * t) * np.exp(-t * 120)
    return hp(click, 1500) * 0.6 + body * 0.5


def sfx_whoosh(dur=0.55):
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    for i in range(0, n, 600):
        fc = 300 + 2600 * np.sin(np.pi * u[i]) ** 2
        out[i:i + 600] = bp(noise[max(0, i - 1200):i + 600], fc * 0.6, fc * 1.5)[-len(out[i:i + 600]):]
    return out * np.sin(np.pi * u) ** 2 * 1.4


def sfx_impact():
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    f = 30 + 55 * np.exp(-t * 4)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    crack = lp(rng.standard_normal(n), 2500) * np.exp(-t * 14)
    metal = sum(np.sin(2 * np.pi * fr * t) * np.exp(-t * dk) for fr, dk in ((173, 3), (241, 4), (389, 5), (617, 7)))
    return np.tanh((sub * 1.3 + crack * 0.9 + metal * 0.12) * 1.4) * np.exp(-np.maximum(t - 0.6, 0) * 1.5)


def sfx_type():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    pitch = rng.uniform(1600, 2400)
    click = hp(rng.standard_normal(n), 2500) * np.exp(-t * 700)
    body = np.sin(2 * np.pi * pitch * t) * np.exp(-t * 260) * 0.4
    thock = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 90) * 0.5
    return (click + body + thock) * rng.uniform(0.7, 1.0)


def sfx_rustle(dur=0.35):
    n = int(dur * SR)
    out = np.zeros(n)
    for _ in range(int(dur * 120)):
        g = int(rng.uniform(0.002, 0.012) * SR)
        i = rng.integers(0, n - g)
        out[i:i + g] += rng.standard_normal(g) * np.hanning(g) * rng.uniform(0.2, 1)
    out = bp(out, 1800, 7000)
    return out * np.sin(np.pi * np.arange(n) / n) ** 0.5


def sfx_beep(f, dur=0.12):
    n = int(dur * SR)
    t = np.arange(n) / SR
    e = np.minimum(1, t / 0.005) * np.minimum(1, (dur - t) / 0.02)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * e


def sfx_thump():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 60 + 90 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) + lp(rng.standard_normal(n), 1500) * np.exp(-t * 40) * 0.5


def sfx_snap():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    f = 180 + 500 * (1 - np.exp(-t * 30))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18) * 0.7 + sfx_rustle(0.25) * 0.6


def sfx():
    bus = np.zeros((N, 2))
    for i, t in enumerate(tl.TICKS):
        u = i / (len(tl.TICKS) - 1)
        place(bus, sfx_tick(2600 if i % 2 == 0 else 2100), t, 0.25 + 0.3 * u, pan=0.15)
    for t, kind in tl.CUTS.items():
        if kind != "smash":
            pan_dir = -0.6 if kind == "whip" else 0.0
            w = sfx_whoosh()
            # split into a left->right sweep for the whip pans
            n = len(w)
            for c, sgn in ((0, 1), (1, -1)):
                g = np.linspace(0.5 + sgn * 0.4, 0.5 - sgn * 0.4, n) if kind == "whip" else np.full(n, 0.5)
                i0 = int((t - 0.3) * SR)
                bus[i0:i0 + n, c] += w * g * 0.55
    place(bus, sfx_impact(), tl.IMPACT_T, 0.95)
    for t in tl.type_click_times():
        place(bus, sfx_type(), t, 0.22, pan=rng.uniform(-0.2, 0.2))
    for t in tl.POSTER_TIMES + [16.95, 17.2]:
        place(bus, sfx_rustle(0.3), t - 0.05, 0.45, pan=rng.uniform(-0.4, 0.4))
    place(bus, sfx_snap(), tl.TAPE_T - 0.15, 0.55)
    place(bus, sfx_snap(), tl.TAPE_T + 0.02, 0.45, pan=0.3)
    place(bus, sfx_thump(), tl.STAMP_T + 0.18, 0.6)
    for t in tl.flip_times():
        place(bus, sfx_rustle(0.09), t - 0.02, 0.32, pan=0.45)
    for t in tl.BEEPS:
        place(bus, sfx_beep(1320), t, 0.18, pan=-0.3)
    place(bus, sfx_beep(990, 0.1), tl.MATCH_T, 0.2)
    place(bus, sfx_beep(1480, 0.22), tl.MATCH_T + 0.12, 0.2)
    place(bus, sfx_thump(), tl.MATCH_T, 0.35)
    place(bus, sfx_thump(), tl.MAP_LINE[1] + 0.05, 0.35)
    place(bus, sfx_impact()[: int(2.5 * SR)] * 0.5, tl.FINAL_TEXT_T - 0.25, 0.6)
    return bus


# ================================================================= voice + mix

def voice():
    info = json.load(open("../build/vo.json"))
    bus = np.zeros((N, 2))
    for it, t0 in zip(info, tl.VO_START):
        x, sr = sf.read(f"../build/vo_{it['i']}.wav")
        x = signal.resample_poly(x, SR, sr)
        x = hp(x, 70)
        # gentle low-mid warmth
        x = x + 0.25 * lp(x, 220)
        place(bus, x, t0, 1.0)
    # light compression
    env = np.abs(bus).max(axis=1)
    env = signal.lfilter([1 - np.exp(-1 / (0.01 * SR))], [1, -np.exp(-1 / (0.01 * SR))], env)
    thr = np.percentile(env[env > 1e-3], 70)
    gain = np.where(env > thr, (thr / np.maximum(env, 1e-9)) ** 0.5, 1.0)
    bus *= gain[:, None]
    return bus


def duck_gain(vo, depth_db=-10.0):
    """Gain curve for the music: -10 dB while the voice speaks, smooth attack/release."""
    frame = int(0.01 * SR)
    e = np.sqrt(np.convolve(vo.mean(axis=1) ** 2, np.ones(frame) / frame, mode="same"))
    active = (e > 0.01).astype(float)
    # hold through short gaps between words
    k = int(0.35 * SR)
    active = np.convolve(active, np.ones(k), mode="same") > 0
    active = active.astype(float)
    target = np.where(active > 0, db(depth_db), 1.0)
    out = np.empty(N)
    g = 1.0
    a_att, a_rel = np.exp(-1 / (0.08 * SR)), np.exp(-1 / (0.45 * SR))
    for i in range(0, N, 48):  # control-rate smoothing (1 ms)
        tg = target[i]
        a = a_att if tg < g else a_rel
        g = tg + (g - tg) * a ** 48
        out[i:i + 48] = g
    return out


def limiter(x, ceiling_db=-1.5):
    c = db(ceiling_db)
    # true-peak estimate: 4x oversampled
    up = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    tp = up[: 4 * len(x)].reshape(-1, 4).max(axis=1)
    peak = maximum_filter1d(tp, size=int(0.01 * SR) + 1)
    g = np.minimum(1.0, c / np.maximum(peak, 1e-9))
    rel = np.exp(-1 / (0.08 * SR))
    gs = signal.lfilter([1 - rel], [1, -rel], g)
    gs = np.minimum(gs, g)
    return x * gs[:, None]


MUSIC_DB, SFX_DB = -9.5, -10.0


def main():
    out = sys.argv[1]
    vo = voice()
    mus = music()
    fx = sfx()
    # rough level staging (relative), then duck music under the voice
    mus *= db(MUSIC_DB)
    fx *= db(SFX_DB)
    mus = mus * duck_gain(vo)[:, None]
    fx = fx * duck_gain(vo, -4.0)[:, None]
    mix = vo * db(0) + reverb(mus, 0.35) + reverb(fx, 0.18)
    # fade in / out with the picture
    fade = np.clip(T / 0.3, 0, 1) * np.clip((tl.DURATION - T) / 0.9, 0, 1)
    mix *= fade[:, None]
    meter = pyln.Meter(SR)
    loud = meter.integrated_loudness(mix)
    mix *= db(-14.0 - loud)
    for _ in range(3):
        mix = limiter(mix, -2.0)
        mix *= db(-14.0 - meter.integrated_loudness(mix))
    mix = limiter(mix, -1.6)
    print(f"loudness {meter.integrated_loudness(mix):.2f} LUFS, peak {20 * np.log10(np.abs(mix).max()):.2f} dBFS")
    sf.write(out, mix.astype(np.float32), SR, subtype="PCM_24")
    # balance report: voice vs. everything else while the voice speaks / overall
    bed = reverb(mus, 0.35) + reverb(fx, 0.18)
    for a, b in ((1.0, 7.5), (11.0, 15.5), (16.5, 18.7), (21.8, 25.8)):
        i, j = int(a * SR), int(b * SR)
        rv = 20 * np.log10(np.sqrt((vo[i:j] ** 2).mean()))
        rb = 20 * np.log10(np.sqrt((bed[i:j] ** 2).mean()))
        rm = 20 * np.log10(np.sqrt((mus[i:j] ** 2).mean()))
        rf = 20 * np.log10(np.sqrt((fx[i:j] ** 2).mean()) + 1e-9)
        print(f"  {a:5.1f}-{b:5.1f}s  voice {rv:6.1f}  bed {rb:6.1f}  music {rm:6.1f}  sfx {rf:6.1f}  (voice-bed {rv - rb:4.1f} dB)")
    # stems for checking
    sf.write(out.replace(".wav", "_vo.wav"), (vo * db(-14.0 - loud)).astype(np.float32), SR, subtype="PCM_24")


if __name__ == "__main__":
    main()
