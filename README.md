# Sun Drop intro: style test

A 30-second intro test (1920×1080, 30 fps, H.264 + AAC) in the style of a flat-vector true-crime explainer.
Everything is generated in code: the graphics, the music, the SFX and the voice (offline Kokoro TTS).

- `out/sun_drop_intro_test.mp4`: the result
- `out/previews/`: preview frames
- `src/timeline.py`: one shared timeline for picture and sound (cuts, ticks, typewriter, beeps…)
- `src/gfx.py`: easing, flat shapes, plates, infographic characters
- `src/scenes.py`: 7 scenes as functions of time, with a Ken Burns camera and parallax layers
- `src/render.py`: whip-pan / plate-wipe transitions, rendering, ffmpeg
- `src/audio.py`: D-minor drone and 70 BPM pulse, risers, SFX, ducking (−10 dB), −14 LUFS
- `src/tts.py`: voice-over, one clip per sentence (voice `am_onyx`)

To rebuild: `./build.sh` (dependencies are listed in the script header).
To swap in your own voice-over, replace `build/vo_0..3.wav` (one sentence per file) and fix their
start times in `VO_START` in `src/timeline.py`; then run `audio.py` and the mux step.
