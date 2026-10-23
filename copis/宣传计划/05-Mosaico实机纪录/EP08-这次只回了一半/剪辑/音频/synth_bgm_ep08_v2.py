#!/usr/bin/env python3
"""EP08 专属 BGM v2（bgm-ep08-clean-v2.wav）—— 对标原版 upbeat2 听感重建轻快感。
v1 反馈：不如原版轻快。v1 照搬 EP06 regen 配方（112BPM、谐波 0.35/0.15、无打击），
而该配方正是 EP06 曾被否掉的"错误的重新合成版"。v2 改为按原版 upbeat2 实测特征合成：
  - 120 BPM（原版自相关实测 0.499s 主拍）
  - 连续 8 分音符琶音（原版 onset 率 3.91/s）
  - 亮音色：谐波 1/0.45/0.35/0.15（原版实测 3f≈2f）
  - 反拍 hi-hat（原版 6–11kHz 占 12% 能量来源；用干净合成噪声脉冲，无反解残留）
  - 和弦铺底 A–E–F#m–D、低音根音保持系列家族
RMS 定标 -33.1 dBFS，33s。对比 v1：bgm-ep08-clean.wav（保留归档）。
"""
import numpy as np, wave

SR = 44100
BPM = 120
BEAT = 60 / BPM            # 0.5s
BAR = 4 * BEAT             # 2.0s
SEG = 2 * BAR              # 每和弦 4.0s
CHORDS = [
    (57, 61, 64),   # A
    (52, 56, 59),   # E
    (54, 57, 61),   # F#m
    (50, 54, 57),   # D
]
CYCLES = 4                  # 120BPM 下 SEG=4s，4 循环 = 64s? 不：SEG*4*CYCLES=64s 太长 → 用 2
CYCLES = 2                  # SEG*4*CYCLES=32s + 尾 ≈ 33s
TOTAL = SEG * 4 * CYCLES + BEAT  # ≈ 32.5s

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
    """亮音色 pluck：谐波 1/0.45/0.35/0.15，衰减 exp(-5t)（原版实测 3f≈2f 的亮谐波列）"""
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
    """干净合成 hi-hat：白噪 + 6–12kHz 带通感（一阶差分高通近似）+ 快衰减，零直流"""
    n = int(dur * SR)
    rng = np.random.default_rng(int(dur * 1e6) + 7)
    x = rng.standard_normal(n)
    x = np.diff(x, prepend=0.0)          # 高通去低频，留"嚓"感
    x /= np.abs(x).max() + 1e-12
    x *= np.exp(-np.arange(n) / SR * 70)  # 更短促，高频嚓感
    x[:32] *= np.linspace(0, 1, 32)
    return x

mix = np.zeros(int(TOTAL * SR))

# 1. 持续和弦铺底（中音层，音量略降给节奏让位）
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

# 2. 连续 8 分琶音（亮音色，音量提至 0.20 —— 轻快感主载体）
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

# 3. 低音根音（每小节 1、3 拍）+ 反拍低音轻点（推进感）
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

# 4. hi-hat：每 8 分反拍（弱拍"嚓"），副歌段(每和弦后半)加密到每个 8 分
hh = hihat()
tt = 0.0
while tt < TOTAL - 0.1:
    on_beat = abs(tt / BEAT - round(tt / BEAT)) < 1e-6
    i0 = int(tt * SR)
    g = 0.09 if on_beat else 0.16           # 每个 8 分都打：正拍轻、反拍重（原版 onset 3.91/s ≈ 全 8 分覆盖）
    mix[i0:i0 + len(hh)] += hh * g
    tt += BEAT / 2

# 5. 尾奏终止：最后一拍 A 根音长音
tail_i = int((TOTAL - BEAT * 2) * SR)
seg = pluck_bright(midi_hz(45), 2.0)
seg = seg[:max(0, len(mix) - tail_i)]
if len(seg) > 0:
    mix[tail_i:tail_i + len(seg)] += seg * 0.20

# 6. 立体声展宽 + 首尾淡入淡出 + RMS 定标 -33.1 dBFS
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

n_out = min(int(33.0 * SR) * 2, len(left) * 2)
stereo = np.empty(n_out)
stereo[0::2] = left[:n_out // 2]
stereo[1::2] = right[:n_out // 2]
pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
out = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP08-这次只回了一半/剪辑/音频/bgm-ep08-clean-v2.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"written {out}: {len(pcm)/2/SR:.1f}s, RMS={20*np.log10(target):.1f} dBFS")
