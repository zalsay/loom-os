#!/usr/bin/env python3
"""EP08 封面 v001：沿用 EP04/EP05/EP06 定稿版式（W3/W6、42/96/140、投影、短金线、版式带校正）。
素材：session96 相机帧 mac-0.jpg；输出 1080×1440。"""
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP08-这次只回了一半"
D = f"{BASE}/剪辑"
OUT = f"{BASE}/产物"
CAM = f"{D}/素材/cover-src.jpg"
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"

W, H = 1080, 1440
TOP_H = 640
BG = (40, 56, 64)
GOLD = (250, 200, 100)
WHITE = (248, 255, 248)
BADGE = "──  织界创造日记 · EP08  ──"
T1 = "触发诊断之后"
T2 = "这次它只回了一半"
CONTENT_W = 1000

def fit(size, text):
    return min(size, int(CONTENT_W / len(text)))

# photo: 1392×832 -> crop 800×593 @ (282,110) -> 1080×800
photo = Image.open(CAM).convert("RGB").crop((282, 110, 282 + 800, 110 + 593)).resize((1080, 800), Image.LANCZOS)
vign = Image.new("L", (1080, 800), 0)
dv = ImageDraw.Draw(vign)
dv.ellipse([-120, -60, 1200, 760], fill=255)
vign = vign.filter(ImageFilter.GaussianBlur(90))
black = Image.new("RGB", (1080, 800), (14, 20, 24))
photo = Image.composite(photo, black, vign)

def render(badge_dy, t1_dy, t2_dy):
    canvas = Image.new("RGB", (W, H), BG)
    top = Image.new("RGB", (W, TOP_H), BG)
    dt = ImageDraw.Draw(top)
    random.seed(7)
    for _ in range(2600):
        x, y = random.randrange(W), random.randrange(TOP_H)
        g = random.randint(0, 26)
        dt.point((x, y), fill=(BG[0] + g, BG[1] + g, BG[2] + g))
    logo = Image.open(LOGO).convert("RGBA")
    lw = 760
    lh = int(logo.height * lw / logo.width)
    big = logo.resize((lw, lh), Image.LANCZOS)
    big.putalpha(big.split()[3].point(lambda a: int(a * 0.06)))
    top.paste(big, ((W - lw) // 2, (TOP_H - lh) // 2 - 20), big)

    f_badge = ImageFont.truetype(HIRA, 42, index=0)
    f_t1 = ImageFont.truetype(HIRA, fit(96, T1), index=2)
    f_t2 = ImageFont.truetype(HIRA, fit(140, T2), index=2)

    def center(draw, text, font, y, fill):
        w = draw.textlength(text, font=font)
        draw.text(((W - w) / 2, y), text, font=font, fill=fill)

    def shadowed(top_rgba, text, font, y, fill):
        x = (W - ImageDraw.Draw(top_rgba).textlength(text, font=font)) / 2
        sh = Image.new("RGBA", top_rgba.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 160))
        top_rgba.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
        ImageDraw.Draw(top_rgba).text((x, y), text, font=font, fill=fill)

    center(dt, BADGE, f_badge, badge_dy, GOLD)
    dt.line([(440, 167), (640, 167)], fill=GOLD, width=3)
    top_rgba = top.convert("RGBA")
    shadowed(top_rgba, T1, f_t1, t1_dy, WHITE)
    shadowed(top_rgba, T2, f_t2, t2_dy, GOLD)
    canvas.paste(top_rgba.convert("RGB"), (0, 0))
    canvas.paste(photo, (0, TOP_H))
    bar = Image.new("RGBA", (W, 120), (26, 38, 45, 235))
    lw2 = 260
    lh2 = int(logo.height * lw2 / logo.width)
    small = logo.resize((lw2, lh2), Image.LANCZOS)
    small.putalpha(small.split()[3].point(lambda a: int(a * 0.95)))
    bar.alpha_composite(small, ((W - lw2) // 2, (120 - lh2) // 2))
    canvas.paste(bar.convert("RGB"), (0, H - 120), bar.split()[3].convert("L"))
    return canvas

def measure(canvas):
    a = np.asarray(canvas)[:620].astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gold = ((r > 180) & (g > 140) & (g < 220) & (b < 140)).sum(axis=1)
    white = ((r > 220) & (g > 220) & (b > 215)).sum(axis=1)
    def band(cnt, y0, y1):
        seg = cnt[y0:y1]
        idx = np.where(seg > 3)[0]
        return (y0 + idx.min(), y0 + idx.max()) if len(idx) else None
    return band(gold, 60, 160), band(gold, 200, 620), band(white, 160, 360)

canvas = render(86, 204, 353)
(b1, b2, bw) = measure(canvas)
print("初渲实测: 徽章", b1, " T2", b2, " T1", bw)
if b1 and b2 and bw:
    canvas = render(86 + (94 - b1[0]), 204 + (214 - bw[0]), 353 + (365 - b2[0]))
    (b1, b2, bw) = measure(canvas)
    print("校正后: 徽章", b1, " T2", b2, " T1", bw)
canvas.save(f"{OUT}/封面-EP08.png")
print("cover saved", f"{OUT}/封面-EP08.png")
