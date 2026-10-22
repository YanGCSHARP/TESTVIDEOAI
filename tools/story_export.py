"""Export story.yaml + timeline.json into one readable document: narration and animation prompts.

usage: story_export.py STORY.yaml TIMELINE.json OUT.md
"""
import json
import sys

import yaml


def tc(s):
    return f"{int(s // 60):02d}:{s % 60:04.1f}"


story = yaml.safe_load(open(sys.argv[1]))
tl = json.load(open(sys.argv[2]))
cont, style = story["CONTINUITY"], story["STYLE"]
out = []
w = out.append
w(f"# {story['project']['title']}\n")
w(f"Duration from the measured voice-over: **{tl['duration'] / 60:.1f} min** · {len(tl['shots'])} shots · "
  f"voice: Kokoro `{story['narrator']['voice']}`, speed {story['narrator']['speed']} · one narrator, no dialogue.\n")
w("## Part 1. Narration script (en-US)\n")
for sc in story["scenes"]:
    s = next(x for x in tl["scenes"] if x["id"] == sc["id"])
    w(f"**{sc['id']} · {sc['title']}** `{tc(s['start'])}`\n")
    w(" ".join(it["t"] if "t" in it else f"*[pause {it['beat']:.0f} s]*" for it in sc["vo"]) + "\n")
w("\n## Part 2. Animation prompts\n")
w("### Applied to every shot\n")
w(f"**Style (prepend to every prompt):** {style['prompt']}\n")
w(f"**Negative prompt:** {style['negative']}\n")
w("**Characters and objects (insert the description wherever a shot names them in `refs`):**\n")
for k, v in cont.items():
    extra = f" Reveal (from S14 on): {v['reveal']}" if "reveal" in v else ""
    w(f"- **{k}**: {v['desc']}{extra}")
w("\nRules: no readable text inside images (signs, the phone and paper are overlays); no speaking characters; "
  "Daniel always sits on the left and never lowers the window; the truck never breaks down; "
  "the infected keep their faces hidden until S14.\n")
for sc in story["scenes"]:
    s = next(x for x in tl["scenes"] if x["id"] == sc["id"])
    w(f"\n### {sc['id']} · {sc['title']} `{tc(s['start'])}–{tc(s['end'])}`\n")
    if s.get("hud"):
        h = s["hud"]
        w(f"HUD: {h['time']}" + (f" · {h['miles_to_exit']} MI TO EXIT" if h.get("miles_to_exit") else "") + "\n")
    w("| Time | Shot | Framing / camera | Animation prompt |\n|---|---|---|---|")
    for sh in [x for x in tl["shots"] if x["scene"] == sc["id"]]:
        refs = ", ".join(sh["refs"]) or "—"
        reuse = f" (reuse of {sh['reuse_of']})" if sh.get("reuse_of") else ""
        w(f"| {tc(sh['start'])}–{tc(sh['end'])} ({sh['end'] - sh['start']:.1f} s) | {sh['id']}{reuse} | "
          f"{sh['framing']}; {sh['camera']} | {sh['prompt']} · refs: {refs} |")
    ovs = [o for o in tl["overlays"] if o["scene"] == sc["id"]]
    if ovs:
        w("\nOverlays: " + "; ".join(f"`{tc(o['in'])}–{tc(o['out'])}` {o['style']}: «{o['text'].replace(chr(10), ' / ')}»" for o in ovs))
    fx = [f for f in tl["sfx"] if f["scene"] == sc["id"]]
    m = next(x for x in tl["music"] if x["scene"] == sc["id"])
    w("\nSound: " + "; ".join(f"`{tc(f['in'])}` {f['cue']}" + (f"→`{tc(f['out'])}`" if "out" in f else "") for f in fx)
      + f". Music: {m.get('state')} ({m.get('intensity')}).")
open(sys.argv[3], "w").write("\n".join(out) + "\n")
print("written", sys.argv[3])
