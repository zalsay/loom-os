#!/usr/bin/env python3
"""EP06 v003 封面 1080x1440：上 = 深色纸纹+标题（它卡在交卷那一步 / 我先摸个底），下 = 新 Mac 相机帧（设备占满，按参考帧裁切）。"""
import subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1440
TOP_H = 640
D = "/tmp/ep6c"
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
BG = (26, 38, 45)
GOLD = (240, 196, 92)
WHITE = (248, 255, 248)
TEAL = (100, 200, 250)

# 1. MAC 相机帧提亮 + 裁剪到 1080x800
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "90", "-i", f"{D}/MAC-camera.mov",
    "-frames:v", "1", "-vf",
    "crop=800:593:282:110,eq=contrast=1.05:saturation=1.04,scale=1080:800:flags=lanczos",
    f"{D}/cover-mac.png"], check=True)
photo = Image.open(f"{D}/cover-mac.png").convert("RGB")

# 强暗角聚焦设备 + 顶部渐变融入标题区
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

# 2. 上半版面
canvas = Image.new("RGB", (W, H), BG)
top = Image.new("RGB", (W, TOP_H), BG)
dt = ImageDraw.Draw(top)
# 纸纹噪点
import random
random.seed(6)
for _ in range(2600):
    x, y = random.randrange(W), random.randrange(TOP_H)
    g = random.randint(0, 26)
    dt.point((x, y), fill=(BG[0]+g, BG[1]+g, BG[2]+g))
# 隐约大 Logo 底纹
logo = Image.open(LOGO).convert("RGBA")
lw = 760
lh = int(logo.height * lw / logo.width)
big = logo.resize((lw, lh), Image.LANCZOS)
big.putalpha(big.split()[3].point(lambda a: int(a * 0.06)))
top.paste(big, ((W - lw) // 2, (TOP_H - lh) // 2 - 20), big)

def center(draw, text, font, y, fill):
    w = draw.textlength(text, font=font)
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)

f_badge = ImageFont.truetype(HIRA, 40)
f_t1 = ImageFont.truetype(HIRA, 84)
f_t2 = ImageFont.truetype(HIRA, 118)
center(dt, "──  织界创造日记 · EP06  ──", f_badge, 78, TEAL)
center(dt, "它卡在交卷那一步", f_t1, 180, WHITE)
center(dt, "我先摸个底", f_t2, 330, GOLD)
# 分隔细线
dt.line([(160, 520), (W - 160, 520)], fill=(70, 92, 104), width=2)
canvas.paste(top, (0, 0))
canvas.paste(photo, (0, TOP_H))

# 3. 底部 Logo 条
strip_h = 120
bar = Image.new("RGBA", (W, strip_h), (26, 38, 45, 235))
lw2 = 260
lh2 = int(logo.height * lw2 / logo.width)
small = logo.resize((lw2, lh2), Image.LANCZOS)
small.putalpha(small.split()[3].point(lambda a: int(a * 0.95)))
bar.alpha_composite(small, ((W - lw2) // 2, (strip_h - lh2) // 2))
bar_rgb = bar.convert("RGB")
mask_rgb = bar.split()[3].convert("L")
canvas.paste(bar_rgb, (0, H - strip_h), mask_rgb)

canvas.save(f"{D}/封面-EP06-v009.png")
print("cover saved")
