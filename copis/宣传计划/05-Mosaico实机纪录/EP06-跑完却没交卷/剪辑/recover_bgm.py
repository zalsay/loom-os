#!/usr/bin/env python3
"""从 EP04/EP05 成片音频反解原版 bgm-upbeat2.wav。
原理：成片混音 = loudnorm(Σ旁白×1.15 + BGM×0.35)，除 loudnorm 慢变增益 g(t) 与
限幅器外全线性。用同款 ffmpeg 滤镜重建纯旁白混合轨 n(t)，逐帧最小二乘估计
c(t)≈g(t)·a，残差 /(0.35·c) 即 BGM；再除以 c/c_ref 消除增益呼吸。
EP04(38s)/EP05(32.5s) 同源同起点，互相交叉验证。"""
import numpy as np, wave, subprocess, sys

SR = 44100
D = "/tmp/ep6c"

def read_wav(path):
    """经 ffmpeg 解码为 44.1k 立体声裸 f32 读取。"""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)

def build_narr(stems, total):
    """stems = [(delay_sec, path)]，用同款滤镜链重建旁白混合轨（44.1k 立体声）。"""
    out = f"{D}/narrtmp.wav"
    inputs, parts, labels = [], [], []
    for i, (dl, p) in enumerate(stems):
        inputs += ["-i", p]
        parts.append(f"[{i}:a]adelay={int(dl*1000)}|{int(dl*1000)},volume=1.15[na{i}];")
        labels.append(f"[na{i}]")
    fc = "".join(parts) + "".join(labels) + \
        f"amix=inputs={len(stems)}:duration=longest:normalize=0," \
        f"aformat=channel_layouts=stereo,aresample=44100[aout]"
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + inputs +
                   ["-filter_complex", fc, "-map", "[aout]", "-t", str(total), out], check=True)
    return read_wav(out)  # (N,2)

def recover(prod_path, stems, total, tag):
    out = read_wav(prod_path)          # 成片 (N,2)
    out = out[: int(total * SR)]
    n = build_narr(stems, total)       # (N,2)
    N = min(len(out), len(n))
    out, n = out[:N], n[:N]

    # 逐帧最小二乘 c(t)：out ≈ c·n（仅旁白活跃帧），两轮迭代扣除 BGM 贡献
    frame, hop = 1024, 512
    nf = (N - frame) // hop
    energy = np.empty(nf); cc = np.full(nf, np.nan)
    nmono = n.mean(axis=1); omono = out.mean(axis=1)
    bgm_hat = np.zeros((N, 2), dtype=np.float64)
    for it in range(2):
        ref = nmono + 0.35 * bgm_hat.mean(axis=1)   # 第二轮把 BGM 计入参考
        for k in range(nf):
            s = k * hop
            ns = ref[s:s+frame]
            energy[k] = nmono[s:s+frame] @ nmono[s:s+frame]
        thr = energy.max() * 1e-4
        for k in range(nf):
            if energy[k] > thr:
                s = k * hop
                ns = ref[s:s+frame]
                cc[k] = (omono[s:s+frame] @ ns) / (ns @ ns)
        # 中值滤波去限幅器毛刺 + 0.5s 平滑 + 空洞插值
        valid = ~np.isnan(cc)
        med = np.copy(cc)
        for k in range(nf):
            w_ = cc[max(0, k-6):k+7][valid[max(0, k-6):k+7]]
            if len(w_): med[k] = np.median(w_)
        valid = ~np.isnan(med)
        cs = np.interp(np.arange(nf), np.flatnonzero(valid), med[valid])
        ker = np.ones(43) / 43
        cs = np.convolve(cs, ker, mode="same")
        t = (np.arange(nf) * hop + frame // 2) / SR
        c_t = np.interp(np.arange(N) / SR, t, cs)
        # 反解 BGM：r = out − c·n = g·0.35·b，除以 0.35·c 即得 b（同时消除增益呼吸）
        new_bgm = np.empty((N, 2), dtype=np.float64)
        for ch in range(2):
            new_bgm[:, ch] = (out[:, ch] - c_t * n[:, ch]) / (0.35 * c_t)
        bgm_hat = new_bgm
    print(f"[{tag}] c(t) 范围 {c_t.min():.3f}~{c_t.max():.3f}")
    return bgm_hat.astype(np.float32), c_t

# EP04: p1..p4 @ 0.5/10.8/15.8/28.3, VIDEO_LEN 38
bg4, c4 = recover(f"{D}/ep4audio.wav",
                  [(0.5, "/private/tmp/ep4live/clone/p1.wav"),
                   (10.8, "/private/tmp/ep4live/clone/p2.wav"),
                   (15.8, "/private/tmp/ep4live/clone/p3.wav"),
                   (28.3, "/private/tmp/ep4live/clone/p4.wav")], 38.0, "EP04")
# EP05: p1..p3 @ 0.5/11.0/22.3, VIDEO_LEN 32.5
bg5, c5 = recover(f"{D}/ep5audio.wav",
                  [(0.5, "/private/tmp/ep5live/clone/p1.wav"),
                   (11.0, "/private/tmp/ep5live/clone/p2.wav"),
                   (22.3, "/private/tmp/ep5live/clone/p3.wav")], 32.5, "EP05")

# 交叉验证 0-30s（EP05 尾 30.5 起淡出，避开）
L = int(30 * SR)
a4, a5 = bg4[:L].mean(axis=1), bg5[:L].mean(axis=1)
rn = min(len(a4), len(a5)); a4, a5 = a4[:rn], a5[:rn]
corr = np.corrcoef(a4, a5)[0, 1]
res = np.sqrt(np.mean((a4 - a5) ** 2)) / (np.sqrt(np.mean(a4 ** 2)) + 1e-9)
print(f"交叉验证 0-30s：相关系数 {corr:.4f}  相对残差 {res:.3f}")

# 干净窗口检查（EP05: 8.2-10.8 / 19.6-22.2 无旁白）
for w0, w1, name in [(8.2, 10.8, "EP05 gap1"), (19.6, 22.2, "EP05 gap2")]:
    s0, s1 = int(w0 * SR), int(w1 * SR)
    x = a5[s0:s1]
    print(f"[{name}] RMS {np.sqrt(np.mean(x**2))*32768:.0f}/32768  峰值 {np.abs(x).max():.3f}")

np.save(f"{D}/bgm-ep4.npy", bg4)
np.save(f"{D}/bgm-ep5.npy", bg5)
print("saved bgm-ep4.npy / bgm-ep5.npy")
