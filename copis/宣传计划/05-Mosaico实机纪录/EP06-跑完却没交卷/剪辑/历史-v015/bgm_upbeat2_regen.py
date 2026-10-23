#!/usr/bin/env python3
"""重合成 EP 系列 upbeat BGM（原 /tmp/ep1/bgm_upbeat2.py 已被清理）。
配方（2026-10-16 沉淀）：持续和弦铺底层 + 琶音点缀 + 低音根音，RMS 定标 ≈1500（int16 满幅 32768 的 4.6%）。
A 大调上行进行 A–E–F#m–D，112 BPM，每和弦 4 拍 ×2 小节 = 8s，双循环 32s + 尾。"""
import numpy as np, wave

SR = 44100
BPM = 112
BEAT = 60 / BPM            # 0.5357s
BAR = 4 * BEAT             # 2.143s
SEG = 2 * BAR              # 每和弦 8.57s
CHORDS = [                  # (根音, 三音, 五音) MIDI
    (57, 61, 64),           # A  (A3 C#4 E4)
    (52, 56, 59),           # E  (E3 G#3 B3)
    (54, 57, 61),           # F#m(F#3 A3  C#4)
    (50, 54, 57),           # D  (D3  F#3 A3)
]
CYCLES = 2
TOTAL = SEG * 4 * CYCLES + BEAT  # ≈ 34.7s

def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def env(n, a, r, sus=1.0):
    """attack/release 线性包络"""
    e = np.ones(n) * sus
    na, nr = int(a * SR), int(r * SR)
    if na > 0:
        e[:na] = np.linspace(0, sus, na)
    if nr > 0:
        e[-nr:] = e[-nr:] * np.linspace(1, 0, nr)
    return e

def pluck(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2 * t) + 0.15 * np.sin(2 * np.pi * f * 3 * t)
    x *= np.exp(-t * 6.0)                    # 快速衰减
    x[:64] *= np.linspace(0, 1, 64)          # 去咔哒
    return x

mix = np.zeros(int(TOTAL * SR))

# 1. 持续和弦铺底层（正弦叠置 + 缓慢起伏）
for ci, ch in enumerate(CHORDS * CYCLES):
    start = int(ci * SEG * SR)
    n = int(SEG * SR)
    t = np.arange(n) / SR
    pad = np.zeros(n)
    for m in ch:
        f = midi_hz(m + 12)                  # 高八度铺底，避免糊
        pad += np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * (f * 1.003) * t)  # 微失谐加宽
        pad += 0.4 * np.sin(2 * np.pi * midi_hz(m) * t)                                # 中音层
    wob = 1.0 + 0.10 * np.sin(2 * np.pi * 0.25 * t)   # 慢呼吸
    mix[start:start + n] += pad * wob * env(n, 0.3, 0.6) * 0.30

# 2. 琶音（8 分音符，和弦音上行循环）
step = BEAT / 2
k = 0
tt = 0.0
while tt < TOTAL - 0.5:
    ci = int(tt // SEG) % 4
    ch = CHORDS[ci]
    m = ch[[0, 1, 2, 1][k % 4]] + 24         # 高两个八度点缀
    seg = pluck(midi_hz(m), min(0.9, TOTAL - tt))
    i0 = int(tt * SR)
    mix[i0:i0 + len(seg)] += seg * 0.16
    k += 1
    tt += step

# 3. 低音根音（每小节第 1、3 拍）
for ci, ch in enumerate(CHORDS * CYCLES):
    for beat in (0, 2):
        tt = ci * SEG + beat * BEAT
        seg = pluck(midi_hz(ch[0] - 12), 0.8)
        i0 = int(tt * SR)
        if i0 + len(seg) < len(mix):
            mix[i0:i0 + len(seg)] += seg * 0.22

# 4. 立体声展宽 + 首尾淡入淡出 + RMS 定标（对齐 EP05 成片实测：混音 0.4 后纯 BGM ≈ -37.4dB）
delay = int(0.011 * SR)
left = mix.copy()
right = np.concatenate([np.zeros(delay), mix[:-delay]])
fade_in = int(0.3 * SR)
dither = int(0.5 * SR)
env_full = np.ones(len(left))
env_full[:fade_in] = np.linspace(0, 1, fade_in)
env_full[-dither:] *= np.linspace(1, 0, dither)
left *= env_full
right *= env_full

rms = np.sqrt(np.mean((0.5 * (left + right)) ** 2))
target = 720 / 32768                       # ≈ -33.1 dBFS（EP05 同款听感：混音 0.4 后纯 BGM ≈ -37dB）
gain = target / rms
left *= gain
right *= gain
peak = max(np.abs(left).max(), np.abs(right).max())
if peak > 0.98:
    left *= 0.98 / peak
    right *= 0.98 / peak

stereo = np.empty(len(left) * 2)
stereo[0::2] = left
stereo[1::2] = right
pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
with wave.open("/tmp/ep6c/bgm-upbeat2.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"bgm-upbeat2.wav written: {len(pcm)/SR/2:.1f}s, RMS={20*np.log10(target):.1f} dBFS")
