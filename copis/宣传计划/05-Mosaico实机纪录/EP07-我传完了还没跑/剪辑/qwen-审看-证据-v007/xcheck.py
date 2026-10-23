#!/usr/bin/env python3
"""qwen cross-check for EP07 v007: title band pixel positions + gold-residue scan.
Independent measurement: classify gold/white/cyan-ish pixels row-by-row, no trust in QC doc."""
import sys
from PIL import Image
import numpy as np

W = "/tmp/qwen-v007-xcheck"

def load(p):
    return np.asarray(Image.open(f"{W}/{p}").convert("RGB")).astype(int)

def row_bands(mask2d, min_px=3, gap=4):
    """Return list of (y0,y1) bands where rows have >= min_px True pixels, merging small gaps."""
    rows = np.where(mask2d.sum(axis=1) >= min_px)[0]
    if len(rows) == 0:
        return []
    bands, s, prev = [], rows[0], rows[0]
    for y in rows[1:]:
        if y - prev > gap:
            bands.append((int(s), int(prev)))
            s = y
        prev = y
    bands.append((int(s), int(prev)))
    return bands

def classify(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gold = (r > 195) & (g > 150) & (g < 225) & (b < 150)
    white = (r > 225) & (g > 230) & (b > 225)
    cyan = (b > 150) & (g > 150) & (r < 150)
    return gold, white, cyan

print("== 1. 顶部标题行带（成片 v007 vs EP06 基准 vs 文案声称 62–91/129–183/199–270）==")
for name in ("v007-0.30.png", "ep06-5.00.png"):
    a = load(name)
    top = a[0:330]
    gold, white, _ = classify(top)
    print(f"  {name}: Badge gold band {row_bands(gold)} | T1 white band {row_bands(white)} | T2 gold band {row_bands(gold[190:330], gap=4) and [(y0+190,y1+190) for y0,y1 in row_bands(gold[190:330])]}")

print("== 2. 水平居中核对（v007@0.30 三带 x 中心）==")
a = load("v007-0.30.png")
gold, white, _ = classify(a[0:330])
for (y0,y1) in row_bands(gold):
    xs = np.where(gold[y0:y1+1].any(axis=0))[0]
    print(f"  gold band y{y0}-{y1}: x [{xs.min()},{xs.max()}], center {int((xs.min()+xs.max())/2)}")
for (y0,y1) in row_bands(white):
    xs = np.where(white[y0:y1+1].any(axis=0))[0]
    print(f"  white band y{y0}-{y1}: x [{xs.min()},{xs.max()}], center {int((xs.min()+xs.max())/2)}")

print("== 3. 中段标注层金色扫描（y608–1400）：v007 vs v006 对照 ==")
import subprocess
for t in ("1.00","5.90","8.40","12.00"):
    a = load(f"v007-{t}.png")
    mid = a[608:1400]
    g,_,c = classify(mid)
    print(f"  v007 @{t}s mid-region: gold px={int(g.sum())}, cyan px={int(c.sum())}")

# oldlog label body x220-859 y628-671 (v007 coords from QC): count gold vs cyan/gray there
for t in ("1.00","5.90"):
    a = load(f"v007-{t}.png")
    lab = a[628:672, 220:860]
    g, wh, c = classify(lab)
    gray = (np.abs(lab[...,0]-200)<30)&(np.abs(lab[...,1]-210)<30)&(np.abs(lab[...,2]-216)<30)
    print(f"  v007 oldlog-label body @{t}s: gold={int(g.sum())} cyan={int(c.sum())} gray={int(gray.sum())}")
# focus text (24,18)+(1080x800 overlay at 608) -> band ~y626-660, x24-300
a = load("v007-8.40.png")
fz = a[620:680, 0:400]
g,_,c = classify(fz)
print(f"  v007 focus text area @8.4s: gold={int(g.sum())} cyan={int(c.sum())}")

print("== 4. 终端原片黄/金残留是否只在真实内容（对照 v006 同帧）==")
subprocess.run(["ffmpeg","-v","error","-y","-ss","1.00","-i","EP06-跑完却没交卷/产物/../../EP07-我传完了还没跑/剪辑/历史-v006/EP07-我传完了还没跑-竖版-v006.mp4","-frames:v","1",f"{W}/v006-1.00.png"],check=True)
subprocess.run(["ffmpeg","-v","error","-y","-ss","8.40","-i","EP07-我传完了还没跑/剪辑/历史-v006/EP07-我传完了还没跑-竖版-v006.mp4","-frames:v","1",f"{W}/v006-8.40.png"],check=True)
for t in ("1.00","8.40"):
    a6 = np.asarray(Image.open(f"{W}/v006-{t}.png").convert("RGB")).astype(int)
    g6,_,_ = classify(a6[608:1400])
    lab6 = classify(a6[628:672, 220:860])[0].sum()
    print(f"  v006 @{t}s: mid gold px={int(g6.sum())}, label-body gold={int(lab6)}")

print("== 5. 封面-EP07.png 文字带（声称 94–131/214–303/365–494）==")
cov = np.asarray(Image.open("EP07-我传完了还没跑/产物/封面-EP07.png").convert("RGB")).astype(int)
g, wh, _ = classify(cov[0:560])
badges = row_bands(g[0:200]); t1 = row_bands(wh[200:330]); t2 = [(y0+330,y1+330) for y0,y1 in row_bands(g[330:560])]
print(f"  cover size={cov.shape[1]}x{cov.shape[0]} badge={badges} T1white={[ (y0+200,y1+200) for y0,y1 in t1]} T2gold={t2}")
