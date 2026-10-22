"""Offline transcription with timestamps: Silero VAD segments -> Whisper (sherpa-onnx).

usage: transcribe.py AUDIO_16k_mono.wav MODEL_DIR VAD.onnx OUT.json
Writes [{"start": s, "end": s, "text": "..."}] — one entry per speech segment.
"""
import json
import sys
import time

import numpy as np
import sherpa_onnx
import soundfile as sf

wav, model_dir, vad_path, out = sys.argv[1:5]
audio, sr = sf.read(wav, dtype="float32")
assert sr == 16000, "resample to 16 kHz mono first"

vad_cfg = sherpa_onnx.VadModelConfig()
vad_cfg.silero_vad.model = vad_path
vad_cfg.silero_vad.min_silence_duration = 0.35
vad_cfg.silero_vad.min_speech_duration = 0.25
vad_cfg.silero_vad.max_speech_duration = 25
vad_cfg.sample_rate = sr
vad = sherpa_onnx.VoiceActivityDetector(vad_cfg, buffer_size_in_seconds=60)

name = model_dir.rstrip("/").split("/")[-1].replace("sherpa-onnx-whisper-", "")
rec = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=f"{model_dir}/{name}-encoder.int8.onnx", decoder=f"{model_dir}/{name}-decoder.int8.onnx",
    tokens=f"{model_dir}/{name}-tokens.txt", language="en", task="transcribe", num_threads=4)

segments = []
t0 = time.time()


def flush():
    while not vad.empty():
        seg = vad.front
        start = seg.start / sr
        s = rec.create_stream()
        s.accept_waveform(sr, np.asarray(seg.samples, dtype=np.float32))
        rec.decode_stream(s)
        text = s.result.text.strip()
        if text:
            segments.append({"start": round(start, 2), "end": round(start + len(seg.samples) / sr, 2), "text": text})
            print(f"[{start:7.2f}] {text}", flush=True)
        vad.pop()


win = vad_cfg.silero_vad.window_size
for i in range(0, len(audio), win):
    vad.accept_waveform(audio[i:i + win])
    flush()
vad.flush()
flush()
json.dump(segments, open(out, "w"), indent=1, ensure_ascii=False)
print(f"{len(segments)} segments, {time.time() - t0:.0f}s")
