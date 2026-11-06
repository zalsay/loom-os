#!/usr/bin/env python3
"""EP22 动效段（设备区版）：1080x608，填满相机窗口位置，22 秒。
节拍对应旁白：1253 测试 → 21 次打包 1 次 exit2 → 两个目录找同一字体 → 四态条。
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess

OUT = Path(__file__).resolve().parent
W, H = 1080, 608
FPS = 30
DUR = 22.0
BG = (20, 27, 31)
WHITE = (248, 255, 248)
GOLD = (250, 200, 100)
RED = (255, 150, 120)
GREEN = (120, 220, 140)
DIM = (110, 126, 134)
FONT = '/System/Library/Fonts/Hiragino Sans GB.ttc'


def font(size, bold=False):
    try:
        return ImageFont.truetype(FONT, size, index=1 if bold else 0)
    except Exception:
        return ImageFont.load_default()


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    return 1 - (1 - t) ** 3


def beat_counter(d, t):
    # 0–3.4s
    if t > 3.6:
        return
    p = clamp(t / 1.3)
    v = int(round(1253 * ease(p)))
    a = int(255 * clamp(t / 0.35))
    d.text((540, 96), '电脑端测试', font=font(34), fill=DIM + (a,), anchor='ma')
    d.text((540, 168), str(v), font=font(96, True), fill=GOLD + (a,), anchor='ma')
    q = clamp((t - 0.9) / 0.4)
    if q > 0:
        d.text((540, 288), '全部通过', font=font(38, True), fill=WHITE + (int(255 * q),), anchor='ma')


def beat_grid(d, t):
    # 3.4–10s
    if t < 3.3 or t > 10.2:
        return
    a = clamp((t - 3.3) / 0.4)
    A = int(255 * a)
    d.text((540, 40), '21 次打包', font=font(32), fill=DIM + (A,), anchor='ma')
    cols, rows, cell, gap = 7, 3, 62, 10
    x0 = (W - cols * cell - (cols - 1) * gap) // 2
    y0 = 100
    for i in range(21):
        q = clamp((t - 3.4 - i * 0.05) / 0.2)
        if q <= 0:
            continue
        cx = x0 + (i % cols) * (cell + gap)
        cy = y0 + (i // cols) * (cell + gap)
        is_fail = i == 20
        red = is_fail and t > 6.6
        color = RED if red else (GOLD if is_fail else GREEN)
        d.rounded_rectangle([cx, cy, cx + cell, cy + cell], radius=10, fill=color + (int(120 + 130 * q),))
        if is_fail:
            d.text((cx + cell / 2, cy + cell / 2), '×', font=font(40, True), fill=BG + (int(255 * q),), anchor='mm')
    q = clamp((t - 6.6) / 0.35)
    if q > 0:
        d.text((540, 366), '20 次成功，1 次退出码 2', font=font(34, True), fill=RED + (int(255 * q),), anchor='ma')


def beat_paths(d, t):
    # 10–16.2s
    if t < 10.0 or t > 16.4:
        return
    a = int(255 * clamp((t - 10.0) / 0.4))
    lx, rx = 270, 810
    d.text((lx, 60), '配置生成在', font=font(30), fill=DIM + (a,), anchor='ma')
    d.text((lx, 108), '运行目录', font=font(42, True), fill=WHITE + (a,), anchor='ma')
    d.text((rx, 60), '打包去找在', font=font(30), fill=DIM + (a,), anchor='ma')
    d.text((rx, 108), '配置目录', font=font(42, True), fill=WHITE + (a,), anchor='ma')
    q1 = clamp((t - 10.5) / 0.4)
    if q1 > 0:
        b = int(255 * q1)
        for cx in (lx, rx):
            d.rounded_rectangle([cx - 100, 170, cx + 100, 258], radius=12, outline=GOLD + (b,), width=4)
            d.text((cx, 214), 'fonts/', font=font(32, True), fill=GOLD + (b,), anchor='mm')
    q2 = clamp((t - 11.4) / 0.4)
    if q2 > 0:
        c = int(255 * q2)
        d.line([(lx + 108, 214), (rx - 108, 214)], fill=DIM + (c,), width=4)
        d.text((540, 330), '找到 ≠ 同一处', font=font(46, True), fill=RED + (c,), anchor='ma')
    q3 = clamp((t - 12.6) / 0.4)
    if q3 > 0:
        d.text((540, 412), '字体在运行目录，打包却按配置目录找', font=font(30), fill=WHITE + (int(255 * q3),), anchor='ma')


def beat_track(d, t):
    # 16.2–22s
    if t < 16.1:
        return
    a = int(255 * clamp((t - 16.1) / 0.4))
    labels = ['测试通过', '产物生成', '离线审阅', '真机部署']
    y = 150
    x0, x1 = 190, 890
    d.line([(x0, y), (x1, y)], fill=DIM + (int(a * 0.7),), width=6)
    d.line([(x0, y), (x0 + (x1 - x0) / 3, y)], fill=GOLD + (a,), width=6)
    for i, lab in enumerate(labels):
        cx = x0 + (x1 - x0) * i / 3
        lit = i == 0
        r = 17 if lit else 13
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=(GOLD if lit else DIM) + (a,))
        d.text((cx, y + 48), lab, font=font(30, True), fill=(WHITE if lit else DIM) + (a,), anchor='ma')
    q1 = clamp((t - 17.0) / 0.4)
    if q1 > 0:
        d.text((540, 316), '测试通过 ≠ 打包能过', font=font(50, True), fill=RED + (int(255 * q1),), anchor='ma')
    q2 = clamp((t - 18.2) / 0.4)
    if q2 > 0:
        d.text((540, 420), '这一轮设备未连接，固件未构建', font=font(30), fill=DIM + (int(255 * q2),), anchor='ma')


def main():
    d = OUT / 'frames-dev'
    d.mkdir(exist_ok=True)
    for i in range(int(DUR * FPS)):
        t = i / FPS
        img = Image.new('RGB', (W, H), BG)
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(layer)
        beat_counter(dr, t)
        beat_grid(dr, t)
        beat_paths(dr, t)
        beat_track(dr, t)
        img = Image.alpha_composite(img.convert('RGBA'), layer).convert('RGB')
        img.save(d / f'f{i:04d}.png')
    out = OUT / '动效-EP22-设备区-v001.mp4'
    subprocess.run(['/opt/homebrew/bin/ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS),
                    '-i', str(d / 'f%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    '-crf', '18', '-movflags', '+faststart', str(out)], check=True)
    print('设备区动效已生成:', out)


if __name__ == '__main__':
    main()
