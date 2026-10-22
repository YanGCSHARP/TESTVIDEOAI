"""Align a recorded narration to story.yaml, cut the spoken chapter headers, build the timeline.

usage: align_vo.py STORY.yaml TRANSCRIPT.json VOICE_AUDIO OUT_DIR

TRANSCRIPT.json comes from tools/transcribe.py. The recording may contain spoken chapter
headers ("S03 · The only lit building 02:05.7"): every transcript word that does not align to the
narration and sits between two scenes is treated as a header and cut out.
Writes OUT_DIR/vo_clean.wav (48 kHz mono) and OUT_DIR/timeline.json (same shape as story_timeline.py).
"""
import difflib
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
import yaml

sys.path.insert(0, os.path.dirname(__file__))
from story_timeline import ANCHOR, validate  # noqa: E402

SR = 48000
SCENE_GAP = 1.0      # silence between scenes (s), plus any beat at the end of a scene
PRE, POST = 0.12, 0.30


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def transcript_words(segs):
    out = []
    for si, s in enumerate(segs):
        words = s["text"].split()
        total = sum(len(w) + 1 for w in words)
        pos = 0
        for i, w in enumerate(words):
            t0 = s["start"] + (s["end"] - s["start"]) * pos / total
            pos += len(w) + 1
            t1 = s["start"] + (s["end"] - s["start"]) * pos / total
            out.append({"w": norm(w), "t0": t0, "t1": t1, "seg_start": s["start"], "first": i == 0, "seg": si})
    return [w for w in out if w["w"]]


def main():
    story_p, trans_p, audio_p, out = sys.argv[1:5]
    story = yaml.safe_load(open(story_p))
    errors, _ = validate(story)
    if errors:
        sys.exit("story invalid: " + "; ".join(errors))
    segs = json.load(open(trans_p))
    tw = transcript_words(segs)

    # story words with (scene index, item index)
    sw = []
    for si, sc in enumerate(story["scenes"]):
        for ii, it in enumerate(sc["vo"], 1):
            if "t" in it:
                for w in it["t"].split():
                    if norm(w):
                        sw.append({"w": norm(w), "si": si, "ii": ii})
    sm = difflib.SequenceMatcher(None, [w["w"] for w in sw], [w["w"] for w in tw], autojunk=False)
    match = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            match[a + k] = b + k
    print(f"aligned {len(match)}/{len(sw)} narration words ({100 * len(match) / len(sw):.1f}%)")
    # transcript segments with no narration word in them = spoken headers / noise
    used = {tw[j]["seg"] for j in match.values()}
    header_segs = [s for k, s in enumerate(segs) if k not in used]
    scene_first_seg, scene_last_seg = {}, {}
    for i, j in match.items():
        si, sg = sw[i]["si"], tw[j]["seg"]
        scene_first_seg[si] = min(scene_first_seg.get(si, sg), sg)
        scene_last_seg[si] = max(scene_last_seg.get(si, sg), sg)

    # time for every story word: matched, or interpolated between matched neighbours
    idx = sorted(match)
    for i, w in enumerate(sw):
        if i in match:
            t = tw[match[i]]
            w["t0"], w["t1"] = t["t0"], t["t1"]
            w["seg_start"] = t["seg_start"] if t["first"] else None
    for i, w in enumerate(sw):
        if "t0" not in w:
            lo = max([j for j in idx if j < i], default=None)
            hi = min([j for j in idx if j > i], default=None)
            if lo is None:
                w["t0"] = w["t1"] = sw[hi]["t0"]
            elif hi is None:
                w["t0"] = w["t1"] = sw[lo]["t1"]
            else:
                u = (i - lo) / (hi - lo)
                w["t0"] = w["t1"] = sw[lo]["t1"] + u * (sw[hi]["t0"] - sw[lo]["t1"])
            w["seg_start"] = None

    # item spans in the original recording
    spans = {}
    for w in sw:
        key = (w["si"], w["ii"])
        s = spans.setdefault(key, {"t0": w["t0"], "t1": w["t1"], "snap": w["seg_start"]})
        s["t1"] = max(s["t1"], w["t1"])
    seg_starts = np.array([s["start"] for s in segs])
    for s in spans.values():  # snap sentence starts to the nearest VAD segment start
        if s["snap"] is not None:
            s["t0"] = s["snap"]
        else:
            near = seg_starts[np.abs(seg_starts - s["t0"]) < 0.6]
            if len(near):
                s["t0"] = float(near[np.argmin(np.abs(near - s["t0"]))])

    # audio: cut each scene's speech chunk, drop everything between scenes (the headers)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", audio_p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    pieces, t_out = [], 0.0
    tl = {"scenes": [], "shots": [], "vo": [], "overlays": [], "sfx": [], "music": [], "cuts": []}
    n_sc = len(story["scenes"])
    for si, sc in enumerate(story["scenes"]):
        items = [(ii, it) for ii, it in enumerate(sc["vo"], 1)]
        spoken = [spans[(si, ii)] for ii, it in items if "t" in it]
        c0 = spoken[0]["t0"] - PRE
        c1 = spoken[-1]["t1"] + POST
        # never include a header: stop before the first narration-free segment after the scene,
        # start after the last one before it
        first_t = segs[scene_first_seg[si]]["start"]
        last_t = segs[scene_last_seg[si]]["end"]
        after = [h["start"] for h in header_segs if h["start"] >= last_t - 0.01]
        before = [h["end"] for h in header_segs if h["end"] <= first_t + 0.01]
        if after:
            c1 = min(c1, after[0] - 0.15) if c1 > after[0] - 0.15 else c1
            c1 = max(c1, last_t + 0.1) if after[0] - 0.15 > last_t + 0.1 else c1
            spoken[-1]["t1"] = min(spoken[-1]["t1"], c1 - 0.05)
        if before:
            c0 = max(c0, before[-1] + 0.1)
        chunk = audio[int(max(c0, 0) * SR):int(c1 * SR)].copy()
        fade = int(0.012 * SR)
        chunk[:fade] *= np.linspace(0, 1, fade)
        chunk[-fade:] *= np.linspace(1, 0, fade)
        scene_start = t_out
        starts, ends = {}, {}
        last_end = None
        for ii, it in items:
            if "t" in it:
                s = spans[(si, ii)]
                starts[ii] = scene_start + (s["t0"] - c0)
                ends[ii] = scene_start + (s["t1"] - c0)
                tl["vo"].append({"id": f"{sc['id']}_{ii:02d}", "text": it["t"], "start": round(starts[ii], 3),
                                 "dur": round(ends[ii] - starts[ii], 3)})
                last_end = ends[ii]
            else:
                starts[ii] = (last_end or scene_start) + 0.25
                ends[ii] = starts[ii] + it["beat"]
                last_end = ends[ii]
        tail_beat = sc["vo"][-1].get("beat", 0.0)
        scene_end = scene_start + len(chunk) / SR + tail_beat + SCENE_GAP
        pieces.append(chunk)
        pieces.append(np.zeros(int((scene_end - scene_start - len(chunk) / SR) * SR), np.float32))
        tl["cuts"].append({"scene": sc["id"], "src_from": round(c0, 2), "src_to": round(c1, 2)})
        # anchors: "N" = start of item N, "Ne" = start of the next item (or scene end)
        order = [ii for ii, _ in items]
        nexts = {ii: (starts[order[k + 1]] if k + 1 < len(order) else scene_end) for k, ii in enumerate(order)}

        def at(a):
            m = ANCHOR.match(str(a))
            i, edge, off = int(m.group(1)), m.group(2), float(m.group(3) or 0)
            return round((nexts[i] if edge else starts[i]) + off, 3)

        shots = sc["shots"]
        for k, sh in enumerate(shots):
            a, b = sh["covers"]
            st = scene_start if k == 0 else starts[a]
            en = scene_end if k == len(shots) - 1 else starts[shots[k + 1]["covers"][0]]
            tl["shots"].append({"id": sh["id"], "scene": sc["id"], "start": round(st, 3), "end": round(en, 3),
                                "framing": sh["framing"], "camera": sh["camera"], "refs": sh.get("refs", []),
                                "prompt": sh["prompt"], "reuse_of": sh.get("reuse_of")})
        for ov in sc.get("overlays", []):
            tl["overlays"].append({**ov, "scene": sc["id"], "in": at(ov["in"]), "out": at(ov["out"])})
        for cue in sc.get("sfx", []):
            tl["sfx"].append({**cue, "scene": sc["id"], "in": at(cue["in"]),
                              **({"out": at(cue["out"])} if "out" in cue else {})})
        mus = dict(sc.get("music", {}))
        for key in ("drop_out_at", "back_in_at", "out_at"):
            if key in mus:
                mus[key] = at(mus[key])
        tl["music"].append({"scene": sc["id"], "start": round(scene_start, 3), "end": round(scene_end, 3), **mus})
        tl["scenes"].append({"id": sc["id"], "title": sc["title"], "start": round(scene_start, 3),
                             "end": round(scene_end, 3), "hud": sc.get("hud")})
        t_out = scene_end
    tl["duration"] = round(t_out, 3)
    clean = np.concatenate(pieces)
    os.makedirs(out, exist_ok=True)
    sf.write(f"{out}/vo_clean.wav", clean, SR, subtype="PCM_24")
    json.dump(tl, open(f"{out}/timeline.json", "w"), indent=1, ensure_ascii=False)

    # report: what was cut between scenes
    print(f"clean narration {len(clean) / SR / 60:.2f} min (source {len(audio) / SR / 60:.2f} min)")
    prev_end = 0.0
    for c in tl["cuts"]:
        cut = [s["text"] for s in segs if s["end"] > prev_end + 0.05 and s["start"] < c["src_from"] - 0.02]
        print(f"  before {c['scene']}: removed {cut}")
        prev_end = c["src_to"]
    tail = [s["text"] for s in segs if s["start"] > prev_end]
    print(f"  after the end: removed {tail}")
    lens = [s["end"] - s["start"] for s in tl["shots"]]
    print(f"{len(lens)} shots, avg {np.mean(lens):.1f}s, min {min(lens):.1f}s, max {max(lens):.1f}s")


if __name__ == "__main__":
    main()
