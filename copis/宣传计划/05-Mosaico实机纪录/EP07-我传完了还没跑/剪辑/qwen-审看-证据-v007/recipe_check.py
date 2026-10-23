#!/usr/bin/env python3
"""qwen re-runnability check: EP07 v007 gold-scan recipe, verbatim per 审核证据-v007/README.md.
- decode both renders RGB24 with crop=1080:792:0:608, stream frame-by-frame
- strict gold mask on v007 (int16): R>=180, G>=120, B<=160, R>=G+15, G>=B+25
- sub-ROI x window totals (cropped coords): oldlog [220,860)x[10,64) t<=6.2;
  focus [0,1080)x[0,60) 6.2<=t<=10.2; pending [240,840)x[627,687) 10.28<=t<=16.37
- second tier: loose warm mask on v006 same frame (R>=120,G>=90,B<=180,R>=G+3,G>=B+10),
  7x7 (±3px) dilation via 49 shifts, match every v007 strict-gold pixel; unmatched expected 0
"""
import subprocess, numpy as np, sys

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP07-我传完了还没跑"
V7 = f"{BASE}/产物/EP07-我传完了还没跑-竖版-v007.mp4"
V6 = f"{BASE}/剪辑/历史-v006/EP07-我传完了还没跑-竖版-v006.mp4"
CW, CH = 1080, 792
FS = CW * CH * 3

def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", "crop=1080:792:0:608",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE, bufsize=FS * 4)
    while True:
        buf = p.stdout.read(FS)
        if len(buf) < FS:
            break
        yield np.frombuffer(buf, np.uint8).reshape(CH, CW, 3)
    p.wait()

def strict_gold(a):
    r = a[..., 0].astype(np.int16); g = a[..., 1].astype(np.int16); b = a[..., 2].astype(np.int16)
    return (r >= 180) & (g >= 120) & (b <= 160) & (r >= g + 15) & (g >= b + 25)

def loose_warm(a):
    r = a[..., 0].astype(np.int16); g = a[..., 1].astype(np.int16); b = a[..., 2].astype(np.int16)
    return (r >= 120) & (g >= 90) & (b <= 180) & (r >= g + 3) & (g >= b + 10)

def dilate7x7(m):
    out = m.copy()
    for dx in range(-3, 4):
        s = np.roll(out, dx, axis=1) if dx else out
        # shift-and-accumulate row-band style: build union of all 7x7 via separable shifts
    # simpler: two-pass separable OR
    v = m.copy()
    for k in range(1, 4):
        v |= np.roll(m, k, axis=0); v |= np.roll(m, -k, axis=0)
    h = v.copy()
    for k in range(1, 4):
        h |= np.roll(v, k, axis=1); h |= np.roll(v, -k, axis=1)
    return h

ROI = {  # name: (x0,x1,y0,y1, t0,t1)   (closed windows as documented)
    "oldlog":  (220, 860, 10, 64, 0.0, 6.2),
    "focus":   (0, 1080, 0, 60, 6.2, 10.2),
    "pending": (240, 840, 627, 687, 10.28, 16.37),
}
tot = {k: 0 for k in ROI}; mx = {k: 0 for k in ROI}
all_gold = 0; unmatched = 0; perframe_remain_min = None; perframe_remain_max = 0; n = 0
g7 = frames(V7); g6 = frames(V6)
for f7, f6 in zip(g7, g6):
    t = n / 30.0
    gold = strict_gold(f7)
    cnt = int(gold.sum()); all_gold += cnt
    for k, (x0, x1, y0, y1, t0, t1) in ROI.items():
        if t0 <= t <= t1:
            c = int(gold[y0:y1, x0:x1].sum())
            tot[k] += c; mx[k] = max(mx[k], c)
    warm = dilate7x7(loose_warm(f6))
    ys, xs = np.where(gold)
    if len(ys):
        rem = int((~warm[ys, xs]).sum())
    else:
        rem = 0
    unmatched += rem
    perframe_remain_min = rem if perframe_remain_min is None else min(perframe_remain_min, rem)
    perframe_remain_max = max(perframe_remain_max, rem)
    n += 1
print(f"frames={n} (expect 735)")
print(f"strict_gold_total_all_frames={all_gold}")
print(f"sub-ROI visible gold: " + ", ".join(f"{k}={tot[k]} (max/frame {mx[k]})" for k in ROI))
print(f"second-tier unmatched vs v006 warm ±3px: total={unmatched}, min/frame={perframe_remain_min}, max/frame={perframe_remain_max}")
ok = n == 735 and all(v == 0 for v in tot.values()) and all(v == 0 for v in mx.values()) and unmatched == 0
print("RECIPE-VERDICT:", "REPRODUCED (0/0/0, unmatched 0)" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
