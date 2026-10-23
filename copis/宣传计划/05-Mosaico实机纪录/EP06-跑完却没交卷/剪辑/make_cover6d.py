#!/usr/bin/env python3
"""EP06 封面 v011：对齐定稿脚本 make_cover.py 的权威参数。
v010 实测对齐版式后仍四处偏差（对照定稿脚本）：徽章 40→42px、T1/T2 字重 W3→W6（ttc index 2）、
标题缺投影（3px 偏移 blur3 rgba(0,0,0,160)，徽章不带）、背景 #1A262D→#283840。
版式 y 带目标（EP04/EP05 实测）：徽章 94-131、T1 214-303、T2 365-495。"""
import subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

W, H = 1080, 1440
TOP_H = 640
D = "/tmp/ep6c"
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
BG = (40, 56, 64)          # 定稿 #283840 深青灰（与视频背景一致）
GOLD = (250, 200, 100)     # 定稿 #FAC864 亮金
WHITE = (248, 255, 248)    # 定稿 #F8FFF8 暖白
BADGE_TEXT = "──  织界创造日记 · EP06  ──"
T1_TEXT = "它卡在交卷那一步"          # = 成片 T1
T2_TEXT = "我先在电脑上摸个底"        # = 成片 T2（封面旧版「我先摸个底」不一致，已改）
CONTENT_W = 1000                     # 版心宽，超宽自动缩字号

def fit(font_size, text):
    return min(font_size, int(CONTENT_W / len(text)))

# 1. MAC 相机帧（同 v009）
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "90", "-i", f"{D}/MAC-camera.mov",
    "-frames:v", "1", "-vf",
    "crop=800:593:282:110,eq=contrast=1.05:saturation=1.04,scale=1080:800:flags=lanczos",
    f"{D}/cover-mac.png"], check=True)
photo = Image.open(f"{D}/cover-mac.png").convert("RGB")
vign = Image.new("L", (1080, 800), 0)
dv = ImageDraw.Draw(vign)
dv.ellipse([-120, -60, 1200, 760], fill=255)
vign = vign.filter(ImageFilter.GaussianBlur(90))
black = Image.new("RGB", (1080, 800), (14, 20, 24))
photo = Image.composite(photo, black, vign)
grad = Image.new("L", (1, 130))
for i in range(130):
    grad.putpixel((0, i), int(255 * (i / 130) ** 1.2))
grad = grad.resize((1080, 130))
bg_layer = Image.new("RGB", (1080, 130), BG)
photo.paste(Image.composite(bg_layer, photo.crop((0, 0, 1080, 130)), grad.point(lambda a: 255 - a)), (0, 0))

def render(badge_dy, t1_dy, t2_dy):
    canvas = Image.new("RGB", (W, H), BG)
    top = Image.new("RGB", (W, TOP_H), BG)
    dt = ImageDraw.Draw(top)
    import random
    random.seed(6)
    for _ in range(2600):
        x, y = random.randrange(W), random.randrange(TOP_H)
        g = random.randint(0, 26)
        dt.point((x, y), fill=(BG[0]+g, BG[1]+g, BG[2]+g))
    logo = Image.open(LOGO).convert("RGBA")
    lw = 760
    lh = int(logo.height * lw / logo.width)
    big = logo.resize((lw, lh), Image.LANCZOS)
    big.putalpha(big.split()[3].point(lambda a: int(a * 0.06)))
    top.paste(big, ((W - lw) // 2, (TOP_H - lh) // 2 - 20), big)

    def center(draw, text, font, y, fill):
        w = draw.textlength(text, font=font)
        draw.text(((W - w) / 2, y), text, font=font, fill=fill)

    def center_shadowed(top_rgba, text, font, y, fill):
        """两行标题专用：3px 偏移 + blur3 + rgba(0,0,0,160) 投影，再叠正文（均水平居中）。"""
        x = (W - ImageDraw.Draw(top_rgba).textlength(text, font=font)) / 2
        sh = Image.new("RGBA", top_rgba.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 160))
        top_rgba.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
        ImageDraw.Draw(top_rgba).text((x, y), text, font=font, fill=fill)

    # 定稿字体：徽章 W3（ttc index 0）42px；T1/T2 W6（index 2）
    f_badge = ImageFont.truetype(HIRA, 42, index=0)
    f_t1 = ImageFont.truetype(HIRA, fit(96, T1_TEXT), index=2)
    f_t2 = ImageFont.truetype(HIRA, fit(140, T2_TEXT), index=2)
    center(dt, BADGE_TEXT, f_badge, badge_dy, GOLD)      # 徽章不带投影
    # 徽章下短金线（模板元素，200px 居中 y167）——必须在 RGBA 转换前画（dt 绑定旧图）
    dt.line([(440, 167), (640, 167)], fill=GOLD, width=3)
    top_rgba = top.convert("RGBA")
    center_shadowed(top_rgba, T1_TEXT, f_t1, t1_dy, WHITE)
    center_shadowed(top_rgba, T2_TEXT, f_t2, t2_dy, GOLD)
    top = top_rgba.convert("RGB")
    canvas.paste(top, (0, 0))
    canvas.paste(photo, (0, TOP_H))
    strip_h = 120
    bar = Image.new("RGBA", (W, strip_h), (26, 38, 45, 235))
    lw2 = 260
    lh2 = int(logo.height * lw2 / logo.width)
    small = logo.resize((lw2, lh2), Image.LANCZOS)
    small.putalpha(small.split()[3].point(lambda a: int(a * 0.95)))
    bar.alpha_composite(small, ((W - lw2) // 2, (strip_h - lh2) // 2))
    canvas.paste(bar.convert("RGB"), (0, H - strip_h), bar.split()[3].convert("L"))
    return canvas

def measure(canvas):
    """返回各文字带实测 y（金色/白色首行带顶部）。"""
    a = np.asarray(canvas)[:620].astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gold = ((r > 180) & (g > 140) & (g < 220) & (b < 140)).sum(axis=1)
    white = ((r > 220) & (g > 220) & (b > 215)).sum(axis=1)
    def band(cnt, y0, y1):
        seg = cnt[y0:y1]
        idx = np.where(seg > 3)[0]
        return (y0 + idx.min(), y0 + idx.max()) if len(idx) else None
    return band(gold, 60, 160), band(gold, 200, 620), band(white, 160, 360)

# 目标带（EP04/EP05 实测）：徽章 94-131、T2 365-495、T1 214-303
canvas = render(86, 204, 353)
(b1, b2, bw) = measure(canvas)
print("初渲实测: 徽章", b1, " T2", b2, " T1", bw)
# 一轮自动校正（对齐带顶部）
if b1 and b2 and bw:
    canvas = render(86 + (94 - b1[0]), 204 + (214 - bw[0]), 353 + (365 - b2[0]))
    (b1, b2, bw) = measure(canvas)
    print("校正后: 徽章", b1, " T2", b2, " T1", bw)
canvas.save(f"{D}/封面-EP06.png")
print("cover saved 封面-EP06.png")
