"""Validate a story.yaml, voice every sentence with Kokoro, and build the absolute timeline.

usage: story_timeline.py STORY.yaml OUT_DIR [--kokoro DIR] [--no-tts]

Writes OUT_DIR/vo/<scene>_<item>.wav (one file per sentence) and OUT_DIR/timeline.json
(absolute start/end of every vo item, shot, overlay and sfx cue). Prints a duration report.
With --no-tts the durations are estimated (2.6 words/s) so the structure can be checked fast.
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import yaml

ANCHOR = re.compile(r"^(\d+)(e?)([+-]\d+(?:\.\d+)?)?$")


def fail(errors, msg):
    errors.append(msg)


def validate(story):
    errors, warnings = [], []
    cont = set(story["CONTINUITY"])
    lib = set(story["SFX_LIBRARY"])
    styles = set(story["OVERLAY_STYLES"])
    shot_ids = {}
    for sc in story["scenes"]:
        sid, n = sc["id"], len(sc["vo"])
        for i, it in enumerate(sc["vo"], 1):
            if ("t" in it) == ("beat" in it):
                fail(errors, f"{sid} item {i}: needs exactly one of t / beat")
        # shots must partition items 1..n in order
        expect = 1
        for sh in sc["shots"]:
            a, b = sh["covers"]
            if a != expect or b < a:
                fail(errors, f"{sid} shot {sh['id']}: covers {a}-{b}, expected to start at {expect}")
            expect = b + 1
            for r in sh.get("refs", []):
                if r not in cont:
                    fail(errors, f"{sid} shot {sh['id']}: unknown ref {r}")
            if sh["id"] in shot_ids:
                fail(errors, f"duplicate shot id {sh['id']}")
            shot_ids[sh["id"]] = sid
        if expect != n + 1:
            fail(errors, f"{sid}: shots cover items up to {expect - 1}, scene has {n}")

        def check_anchor(a, what):
            m = ANCHOR.match(str(a))
            if not m or not 1 <= int(m.group(1)) <= n:
                fail(errors, f"{sid} {what}: bad anchor {a!r}")

        for ov in sc.get("overlays", []):
            if ov["style"] not in styles:
                fail(errors, f"{sid} overlay: unknown style {ov['style']}")
            check_anchor(ov["in"], "overlay.in")
            check_anchor(ov["out"], "overlay.out")
        for cue in sc.get("sfx", []):
            if cue["cue"] not in lib:
                fail(errors, f"{sid} sfx: unknown cue {cue['cue']}")
            check_anchor(cue["in"], "sfx.in")
            if "out" in cue:
                check_anchor(cue["out"], "sfx.out")
        for key in ("drop_out_at", "back_in_at", "out_at"):
            if key in sc.get("music", {}):
                check_anchor(sc["music"][key], f"music.{key}")
    for sc in story["scenes"]:
        for sh in sc["shots"]:
            if "reuse_of" in sh and sh["reuse_of"] not in shot_ids:
                fail(errors, f"{sh['id']}: reuse_of unknown shot {sh['reuse_of']}")
        for ov in sc.get("overlays", []):
            if "anchor_shot" in ov and shot_ids.get(ov["anchor_shot"]) != sc["id"]:
                fail(errors, f"{sc['id']} overlay: anchor_shot {ov['anchor_shot']} not in this scene")
    return errors, warnings


def tts_durations(story, out_dir, kokoro_dir, no_tts):
    nar = story["narrator"]
    durs = {}
    if not no_tts:
        import soundfile as sf
        from kokoro_onnx import Kokoro
        k = Kokoro(f"{kokoro_dir}/kokoro-v1.0.onnx", f"{kokoro_dir}/voices-v1.0.bin")
        os.makedirs(f"{out_dir}/vo", exist_ok=True)
    for sc in story["scenes"]:
        for i, it in enumerate(sc["vo"], 1):
            if "beat" in it:
                continue
            key = f"{sc['id']}_{i:02d}"
            if no_tts:
                durs[key] = len(it["t"].split()) / 2.6
                continue
            path = f"{out_dir}/vo/{key}.wav"
            if not os.path.exists(path):
                a, sr = k.create(it["t"], voice=nar["voice"], speed=nar["speed"], lang="en-us")
                idx = np.where(np.abs(a) > 0.01)[0]
                a = a[max(idx[0] - int(0.02 * sr), 0): idx[-1] + int(0.08 * sr)]
                sf.write(path, a, sr)
            info = sf.info(path)
            durs[key] = info.frames / info.samplerate
    return durs


def build(story, durs):
    nar = story["narrator"]
    t = 0.0
    tl = {"scenes": [], "shots": [], "vo": [], "overlays": [], "sfx": [], "music": []}
    for sc in story["scenes"]:
        s0 = t
        starts, ends = {}, {}
        for i, it in enumerate(sc["vo"], 1):
            starts[i] = t
            if "beat" in it:
                t += it["beat"]
            else:
                key = f"{sc['id']}_{i:02d}"
                tl["vo"].append({"id": key, "text": it["t"], "start": round(t, 3), "dur": round(durs[key], 3)})
                t += durs[key] + it.get("p", nar["default_pause"])
            ends[i] = t
        # shot.hold adds air after the shot's last item; shift everything after it
        for sh in sc["shots"]:
            a, b = sh["covers"]
            hold = sh.get("hold", 0.0)
            tl["shots"].append({"id": sh["id"], "scene": sc["id"], "start": round(starts[a], 3),
                                "end": round(ends[b] + hold, 3), "framing": sh["framing"], "camera": sh["camera"],
                                "refs": sh.get("refs", []), "prompt": sh["prompt"], "reuse_of": sh.get("reuse_of")})

        def at(a):
            m = ANCHOR.match(str(a))
            i, edge, off = int(m.group(1)), m.group(2), float(m.group(3) or 0)
            return round((ends[i] if edge else starts[i]) + off, 3)

        for ov in sc.get("overlays", []):
            tl["overlays"].append({**ov, "scene": sc["id"], "in": at(ov["in"]), "out": at(ov["out"])})
        for cue in sc.get("sfx", []):
            tl["sfx"].append({**cue, "scene": sc["id"], "in": at(cue["in"]),
                              **({"out": at(cue["out"])} if "out" in cue else {})})
        mus = dict(sc.get("music", {}))
        for key in ("drop_out_at", "back_in_at", "out_at"):
            if key in mus:
                mus[key] = at(mus[key])
        tl["music"].append({"scene": sc["id"], "start": round(s0, 3), "end": round(t, 3), **mus})
        tl["scenes"].append({"id": sc["id"], "title": sc["title"], "start": round(s0, 3), "end": round(t, 3),
                             "hud": sc.get("hud")})
    tl["duration"] = round(t, 3)
    return tl


def report(story, tl):
    words = sum(len(it["t"].split()) for sc in story["scenes"] for it in sc["vo"] if "t" in it)
    speech = sum(v["dur"] for v in tl["vo"])
    print(f"{'scene':6} {'start':>6} {'len':>6}  shots  title")
    for sc in tl["scenes"]:
        n = sum(1 for s in tl["shots"] if s["scene"] == sc["id"])
        st = sc["start"]
        print(f"{sc['id']:6} {int(st // 60)}:{st % 60:04.1f} {sc['end'] - st:5.1f}s  {n:5d}  {sc['title']}")
    lens = [s["end"] - s["start"] for s in tl["shots"]]
    print(f"\nTOTAL {tl['duration'] / 60:.2f} min | words {words} | speech {speech / 60:.2f} min | "
          f"{len(lens)} shots, avg {np.mean(lens):.1f}s, min {min(lens):.1f}s, max {max(lens):.1f}s")
    long_ = [(s["id"], round(s["end"] - s["start"], 1)) for s in tl["shots"] if s["end"] - s["start"] > 12]
    short = [(s["id"], round(s["end"] - s["start"], 1)) for s in tl["shots"] if s["end"] - s["start"] < 2.0]
    if long_:
        print("shots > 12 s (split them or plan a slow camera move):", long_)
    if short:
        print("shots < 2 s:", short)
    lo, hi = story["project"]["target_minutes"]
    ok = lo <= tl["duration"] / 60 <= hi
    print(f"target {lo}-{hi} min: {'OK' if ok else 'OUT OF RANGE'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("out")
    ap.add_argument("--kokoro", default="/tmp/claude-0/kokoro")
    ap.add_argument("--no-tts", action="store_true")
    args = ap.parse_args()
    story = yaml.safe_load(open(args.story))
    errors, _ = validate(story)
    if errors:
        print("INVALID:\n  " + "\n  ".join(errors))
        sys.exit(1)
    os.makedirs(args.out, exist_ok=True)
    durs = tts_durations(story, args.out, args.kokoro, args.no_tts)
    tl = build(story, durs)
    json.dump(tl, open(f"{args.out}/timeline.json", "w"), indent=1, ensure_ascii=False)
    ok = report(story, tl)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
