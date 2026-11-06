#!/usr/bin/env python3
"""动效层可行性验证：纯 PIL 逐帧 + ffmpeg 合成，不依赖 Manim。
演示三种可复用动效：数字滚动、四态状态条、六分区地图高亮。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, math

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
DUR = 6.0
BG = (40, 56, 64)
WHITE = (248, 255, 248)
GOLD = (250, 200, 100)
DIM = (90, 110, 118)

FONT = '/System/Library/Fonts/Hiragino Sans GB.ttc'


def font(size, bold=False):
    try:
        return ImageFont.truetype(FONT, size, index=1 if bold else 0)
    except Exception:
        return ImageFont.load_default()


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def png_dir():
    d = OUT / 'demo-frames'
    d.mkdir(exist_ok=True)
    return d


def draw_counter(d, t):
    # 0.0-2.2s：0 → 1353
    p = clamp((t - 0.1) / 2.0)
    v = int(round(1353 * ease_out_cubic(p)))
    alpha = int(255 * clamp(p * 3))
    d.text((540, 300), '电脑端测试', font=font(52, True), fill=WHITE + (alpha,), anchor='mm')
    d.text((540, 420), str(v), font=font(150, True), fill=GOLD + (alpha,), anchor='mm')
    # 副标题在 1.8s 后淡入
    q = clamp((t - 1.8) / 0.6)
    if q > 0:
        d.text((540, 530), '全部通过', font=font(60, True), fill=WHITE + (int(255 * q),), anchor='mm')


def draw_track(d, t):
    # 1.6-4.4s：四态状态条逐个点亮，最后一态保持未发生
    labels = ['测试通过', '产物生成', '离线审阅', '真机部署']
    start, span = 1.6, 0.55
    y = 760
    x0, x1 = 170, 910
    # 轨道底
    d.line([(x0, y), (x1, y)], fill=DIM + (200,), width=6)
    for i, lab in enumerate(labels):
        cx = x0 + (x1 - x0) * i / 3
        lit = clamp((t - (start + i * span)) / 0.35)
        if i == 3:
            color = DIM          # 真机部署：始终暗
            ring = (140, 140, 140)
        else:
            color = GOLD if lit > 0 else DIM
            ring = GOLD if lit > 0.2 else DIM
        if lit > 0 and i < 3:
            d.line([(x0, y), (cx, y)], fill=GOLD + (255,), width=6)
        r = 14 + 8 * math.sin(math.pi * clamp(lit)) if lit > 0 else 14
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=color + (255,), outline=ring + (255,), width=3)
        a = int(255 * (0.35 + 0.65 * lit)) if i < 3 else 110
        d.text((cx, y + 52), lab, font=font(38, True), fill=(WHITE if i < 3 else DIM) + (a,), anchor='ma')
    q = clamp((t - 4.2) / 0.5)
    if q > 0:
        d.text((540, y + 150), '真机部署：未发生', font=font(44, True), fill=(255, 150, 120, int(255 * q)), anchor='ma')


def draw_partitions(d, t):
    # 3.2-6.0s：六分区地图，三段依次高亮
    names = ['bootloader', 'partition table', 'otadata', 'factory', 'ui_apps', 'system']
    q0 = clamp((t - 3.2) / 0.5)
    if q0 <= 0:
        return
    top = 1060
    block_h = 96
    left, right = 150, 930
    d.text((540, top - 60), '现场六分区', font=font(44, True), fill=WHITE + (int(255 * q0),), anchor='ma')
    for i, n in enumerate(names):
        y = top + i * (block_h + 10)
        highlight = n in ('factory', 'ui_apps', 'system') and t > 4.0 + (('factory', 'ui_apps', 'system').index(n)) * 0.35
        fill = (GOLD if highlight else (58, 78, 88)) + (int(255 * q0),)
        d.rounded_rectangle([left, y, right, y + block_h - 14], radius=14, fill=fill)
        d.text((left + 28, y + (block_h - 14) / 2), n, font=font(40, True),
               fill=(BG if highlight else WHITE) + (int(255 * q0),), anchor='lm')


def main():
    d = png_dir()
    for i in range(int(DUR * FPS)):
        t = i / FPS
        img = Image.new('RGBA', (W, H), BG + (255,))
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(layer)
        draw_counter(dr, t)
        draw_track(dr, t)
        draw_partitions(dr, t)
        img = Image.alpha_composite(img, layer).convert('RGB')
        img.save(d / f'f{i:04d}.png')
    out = OUT / '动效层-演示-v001.mp4'
    subprocess.run(['/opt/homebrew/bin/ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS),
                    '-i', str(d / 'f%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    '-crf', '20', '-movflags', '+faststart', str(out)], check=True)
    print('演示已生成:', out)


if __name__ == '__main__':
    main()
