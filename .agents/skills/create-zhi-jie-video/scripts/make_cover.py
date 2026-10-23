#!/usr/bin/env python3
"""织界视频封面生成（用户定稿版式）：1080x1440 (3:4)，标题放大居中，下半部实拍画面。

用法：
  python3 make_cover.py --frame frame.jpg --badge "──  织界创造日记 · EP01  ──" \
      --line1 "给孩子造的设备" --line2 "开箱第一眼" --out 封面-EP01.png

帧来源：从剪辑基底/成片抽取 1080x810 帧（ffmpeg -ss T -i in.mp4 -frames:v 1 -vf crop=...）。
字体：Hiragino Sans GB（PingFang 受 SIP 保护 PIL 不可直读）；W6 粗体 = index 2。
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

BG = (40, 56, 64)        # #283840，与视频背景一致
GOLD = (250, 200, 100)   # #FAC864 亮金
WHITE = (248, 255, 248)
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "engine", "Zhi-Jie-logo.png")
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"

F_BADGE = ImageFont.truetype(HIRA, 42, index=0)   # W3
F_T1 = ImageFont.truetype(HIRA, 96, index=2)      # W6 白色主标题
F_T2 = ImageFont.truetype(HIRA, 140, index=2)     # W6 亮金副标题


def center_text(draw, y, text, fnt, fill, shadow=True):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    x = (1080 - (bbox[2] - bbox[0])) / 2 - bbox[0]
    if shadow:
        sh = Image.new("RGBA", (1080, 300), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x + 3, y + 3), text, font=fnt, fill=(0, 0, 0, 160))
        sh = sh.filter(ImageFilter.GaussianBlur(3))
    draw.text((x, y), text, font=fnt, fill=fill)


def make_cover(frame_path, badge, line1, line2, out_path):
    canvas = Image.new("RGB", (1080, 1440), BG)

    # 上半部标题区 y0-630：弱水印 logo 底 + 居中放大标题
    top = Image.new("RGBA", (1080, 630), BG + (255,))
    logo = Image.open(LOGO).convert("RGBA")
    lw = 940
    lh = int(logo.height * lw / logo.width)
    big = logo.resize((lw, lh), Image.LANCZOS)
    big.putalpha(big.split()[3].point(lambda a: int(a * 0.05)))
    top.alpha_composite(big, ((1080 - lw) // 2, (630 - lh) // 2))

    d = ImageDraw.Draw(top)
    center_text(d, 92, badge, F_BADGE, GOLD, shadow=False)
    d.line([(440, 168), (640, 168)], fill=GOLD + (255,), width=3)
    center_text(d, 210, line1, F_T1, WHITE)
    center_text(d, 360, line2, F_T2, GOLD)
    canvas.paste(top.convert("RGB"), (0, 0))

    # 下半部实拍画面 y630-1440：提亮 + 底部渐变压暗 + logo
    frame = Image.open(frame_path).convert("RGB")
    if frame.size != (1080, 810):
        frame = frame.resize((1080, 810), Image.LANCZOS)
    frame = ImageEnhance.Brightness(frame).enhance(1.08)
    frame = ImageEnhance.Contrast(frame).enhance(1.05)
    canvas.paste(frame, (0, 630))

    grad = Image.new("L", (1, 810), 0)
    for yy in range(810):
        grad.putpixel((0, yy), 0 if yy < 560 else int(150 * (yy - 560) / 250))
    dark = Image.new("RGB", (1080, 810), (16, 24, 30))
    canvas.paste(dark, (0, 630), grad.resize((1080, 810)))

    overlay = Image.new("RGBA", (1080, 1440), (0, 0, 0, 0))
    lw2 = 300
    lh2 = int(logo.height * lw2 / logo.width)
    small = logo.resize((lw2, lh2), Image.LANCZOS)
    small.putalpha(small.split()[3].point(lambda a: int(a * 0.92)))
    overlay.alpha_composite(small, ((1080 - lw2) // 2, 1440 - lh2 - 40))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    canvas.save(out_path, quality=95)
    print("saved", out_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--frame", required=True, help="1080x810 实拍帧（或任意比例图，自动缩放）")
    p.add_argument("--badge", required=True, help="系列徽章行，如 ──  织界创造日记 · EP01  ──")
    p.add_argument("--line1", required=True, help="主标题（白色）")
    p.add_argument("--line2", required=True, help="副标题（亮金）")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    make_cover(a.frame, a.badge, a.line1, a.line2, a.out)
