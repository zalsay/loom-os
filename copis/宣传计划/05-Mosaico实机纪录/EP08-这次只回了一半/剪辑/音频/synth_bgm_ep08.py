#!/usr/bin/env python3
"""EP08 专属 BGM 新合成（bgm-ep08-clean.wav）
背景：《剪辑与音频规范》§3 —— 各集 BGM 是每次独立合成的不同波形；EP06/07 共用的
bgm-upbeat2.wav 是从 EP04 成片反解的恢复版，自带反解残留杂音（loudnorm 增益呼吸残差
+ 宽频毛刺，实测与音乐本体纠缠、谱减降噪无效）。EP08 按同配方（配方沉淀自
EP06 剪辑/历史-v015/bgm_upbeat2_regen.py）独立合成干净波形，保持系列听感家族一致：
A 大调 A–E–F#m–D，112 BPM，持续和弦铺底 + 琶音 + 低音根音，RMS 定标 ≈ -33.1 dBFS。
独立波形体现在：失谐系数 1.002、呼吸相位偏移、琶音节奏加花（隔小节 16 分连音）、
尾奏终止式，均为本集新变化。时长 33s（与 24.5s 片长匹配，atrim 使用）。
"""
import numpy as np, wave

SR = 44100
BPM = 112
BEAT = 60 / BPM
BAR = 4 * BEAT
SEG = 2 * BAR
CHORDS = [
    (57, 61, 64),   # A
    (52, 56, 59),   # E
    (54, 57, 61),   # F#m
    (50, 54, 57),   # D
]
CYCLES = 2
TOTAL = SEG * 4 * CYCLES + BEAT  # ≈ 34.7s → 输出截 33s

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

def pluck(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2 * t) + 0.15 * np.sin(2 * np.pi * f * 3 * t)
    x *= np.exp(-t * 6.0)
    x[:64] *= np.linspace(0, 1, 64)
    return x

mix = np.zeros(int(TOTAL * SR))

# 1. 持续和弦铺底（失谐 1.002、呼吸相位 0.8s 偏移 —— 与 upbeat2 的 1.003/0 相位区分）
for ci, ch in enumerate(CHORDS * CYCLES):
    start = int(ci * SEG * SR)
    n = int(SEG * SR)
    t = np.arange(n) / SR
    pad = np.zeros(n)
    for m in ch:
        f = midi_hz(m + 12)
        pad += np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * (f * 1.002) * t)
        pad += 0.4 * np.sin(2 * np.pi * midi_hz(m) * t)
    wob = 1.0 + 0.10 * np.sin(2 * np.pi * 0.25 * (t + 0.8))
    mix[start:start + n] += pad * wob * env(n, 0.3, 0.6) * 0.30

# 2. 琶音（隔小节加入 16 分连音加花，本集独立节奏形态）
step = BEAT / 2
k = 0
tt = 0.0
while tt < TOTAL - 0.5:
    ci = int(tt // SEG) % 4
    ch = CHORDS[ci]
    m = ch[[0, 1, 2, 1][k % 4]] + 24
    seg = pluck(midi_hz(m), min(0.9, TOTAL - tt))
    i0 = int(tt * SR)
    mix[i0:i0 + len(seg)] += seg * 0.16
    # 每小节第 4 拍后加 16 分上行三连点缀（本集加花）
    bar_pos = (tt % SEG) / BEAT
    if 3.0 <= bar_pos < 3.75 and (int(tt // SEG) % 2 == 1):
        for j, extra in enumerate([ch[2], ch[0] + 12, ch[1] + 12]):
            seg2 = pluck(midi_hz(extra + 24), 0.35)
            j0 = i0 + int(j * BEAT / 3 * SR)
            if j0 + len(seg2) < len(mix):
                mix[j0:j0 + len(seg2)] += seg2 * 0.10
    k += 1
    tt += step

# 3. 低音根音（每小节 1、3 拍）+ 尾奏终止式（第 4 和弦后加一次 A 根音长音）
for ci, ch in enumerate(CHORDS * CYCLES):
    for beat in (0, 2):
        tt = ci * SEG + beat * BEAT
        seg = pluck(midi_hz(ch[0] - 12), 0.8)
        i0 = int(tt * SR)
        if i0 + len(seg) < len(mix):
            mix[i0:i0 + len(seg)] += seg * 0.22

# 尾奏：最后一个和弦区补 A 长低音（终止感）
tail_i = int((TOTAL - BEAT * 2) * SR)
seg = pluck(midi_hz(45), 2.0)  # A2
seg = seg[:max(0, len(mix) - tail_i)]   # 裁到缓冲区剩余长度，防越界
if len(seg) > 0:
    mix[tail_i:tail_i + len(seg)] += seg * 0.18

# 4. 立体声展宽 + 首尾淡入淡出 + RMS 定标（对齐系列：-33.1 dBFS）
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
target = 720 / 32768
gain = target / rms
left *= gain
right *= gain
peak = max(np.abs(left).max(), np.abs(right).max())
if peak > 0.98:
    left *= 0.98 / peak
    right *= 0.98 / peak

# 截取 33s
n_out = int(33.0 * SR) * 2
stereo = np.empty(n_out)
stereo[0::2] = left[:n_out // 2]
stereo[1::2] = right[:n_out // 2]
pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
out = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP08-这次只回了一半/剪辑/音频/bgm-ep08-clean.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"written {out}: {len(pcm)/2/SR:.1f}s, RMS={20*np.log10(target):.1f} dBFS")
