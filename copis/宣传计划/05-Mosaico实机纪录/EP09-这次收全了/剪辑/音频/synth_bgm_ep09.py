#!/usr/bin/env python3
"""EP09 BGM（bgm-ep09-v1.wav）—— 完全沿用 EP08 v2 定稿配方（120BPM 亮音色琶音+全8分hi-hat），
仅 CYCLES 2→3（≈48.5s 长料），由 build_video9 按成片时长 atrim。RMS 定标 -33.1 dBFS 不变。"""
import numpy as np, wave

SR = 44100
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
SEG = 2 * BAR
CHORDS = [
    (57, 61, 64),   # A
    (52, 56, 59),   # E
    (54, 57, 61),   # F#m
    (50, 54, 57),   # D
]
CYCLES = 3
TOTAL = SEG * 4 * CYCLES + BEAT

def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def env(n, a, r, sus=1.0):
    e = np.ones(n) * sus
    na, nr = int(a * SR), int(r * SR)
    if na > 0:
        e[:na] = np.linspace(0, sus, na)
    if nr > 0:
        e[-nr:] = e[-nr:] * np.linspace(1, 0, nr)
    return e

def pluck_bright(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t)
         + 0.45 * np.sin(2 * np.pi * f * 2 * t)
         + 0.35 * np.sin(2 * np.pi * f * 3 * t)
         + 0.15 * np.sin(2 * np.pi * f * 4 * t))
    x *= np.exp(-t * 5.0)
    x[:64] *= np.linspace(0, 1, 64)
    return x

def hihat(dur=0.06):
    n = int(dur * SR)
    rng = np.random.default_rng(int(dur * 1e6) + 7)
    x = rng.standard_normal(n)
    x = np.diff(x, prepend=0.0)
    x /= np.abs(x).max() + 1e-12
    x *= np.exp(-np.arange(n) / SR * 70)
    x[:32] *= np.linspace(0, 1, 32)
    return x

mix = np.zeros(int(TOTAL * SR))

for ci, ch in enumerate(CHORDS * CYCLES):
    start = int(ci * SEG * SR)
    n = int(SEG * SR)
    t = np.arange(n) / SR
    pad = np.zeros(n)
    for m in ch:
        f = midi_hz(m + 12)
        pad += np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * (f * 1.002) * t)
        pad += 0.35 * np.sin(2 * np.pi * midi_hz(m) * t)
    wob = 1.0 + 0.08 * np.sin(2 * np.pi * 0.25 * (t + 0.8))
    mix[start:start + n] += pad * wob * env(n, 0.25, 0.5) * 0.22

step = BEAT / 2
k = 0
tt = 0.0
while tt < TOTAL - 0.4:
    ci = int(tt // SEG) % 4
    ch = CHORDS[ci]
    m = ch[[0, 1, 2, 1][k % 4]] + 24
    seg = pluck_bright(midi_hz(m), min(0.7, TOTAL - tt))
    i0 = int(tt * SR)
    mix[i0:i0 + len(seg)] += seg * 0.22
    k += 1
    tt += step

for ci, ch in enumerate(CHORDS * CYCLES):
    for beat in (0, 2):
        tt = ci * SEG + beat * BEAT
        seg = pluck_bright(midi_hz(ch[0] - 12), 0.7)
        i0 = int(tt * SR)
        if i0 + len(seg) < len(mix):
            mix[i0:i0 + len(seg)] += seg * 0.22
    for beat in (1, 3):
        tt = ci * SEG + beat * BEAT + BEAT / 2
        seg = pluck_bright(midi_hz(ch[0] - 12), 0.35)
        i0 = int(tt * SR)
        if i0 + len(seg) < len(mix):
            mix[i0:i0 + len(seg)] += seg * 0.10

hh = hihat()
tt = 0.0
while tt < TOTAL - 0.1:
    on_beat = abs(tt / BEAT - round(tt / BEAT)) < 1e-6
    i0 = int(tt * SR)
    g = 0.09 if on_beat else 0.16
    mix[i0:i0 + len(hh)] += hh * g
    tt += BEAT / 2

tail_i = int((TOTAL - BEAT * 2) * SR)
seg = pluck_bright(midi_hz(45), 2.0)
seg = seg[:max(0, len(mix) - tail_i)]
if len(seg) > 0:
    mix[tail_i:tail_i + len(seg)] += seg * 0.20

delay = int(0.011 * SR)
left = mix.copy()
right = np.concatenate([np.zeros(delay), mix[:-delay]])
fade_in = int(0.25 * SR)
dither = int(0.5 * SR)
env_full = np.ones(len(left))
env_full[:fade_in] = np.linspace(0, 1, fade_in)
env_full[-dither:] *= np.linspace(1, 0, dither)
left *= env_full
right *= env_full

rms = np.sqrt(np.mean((0.5 * (left + right)) ** 2))
target = 720 / 32768
gain = target / rms
left *= gain
right *= gain
peak = max(np.abs(left).max(), np.abs(right).max())
if peak > 0.98:
    left *= 0.98 / peak
    right *= 0.98 / peak

n_out = min(int(TOTAL * SR) * 2, len(left) * 2)
stereo = np.empty(n_out)
stereo[0::2] = left[:n_out // 2]
stereo[1::2] = right[:n_out // 2]
pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
out = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP09-这次收全了/剪辑/音频/bgm-ep09-v1.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"written {out}: {len(pcm)/2/SR:.1f}s")
