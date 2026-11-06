#!/usr/bin/env python3
"""EP22 动效段：1080x800，12.5 秒，仅供终端面板区。
节拍：1253 测试 → 21 次打包里 1 次 exit 2 → 运行目录 vs 配置目录 → 四态状态条。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, math

OUT = Path(__file__).resolve().parent
W, H = 1080, 800
FPS = 30
DUR = 12.5
BG = (16, 23, 19)          # 与终端底色接近
WHITE = (248, 255, 248)
GOLD = (250, 200, 100)
RED = (255, 150, 120)
GREEN = (120, 220, 140)
DIM = (96, 112, 104)
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
    # 0.0–3.0s：1253 数字 + 21 格开始出现
    p = clamp(t / 1.2)
    v = int(round(1253 * ease(p)))
    a = int(255 * clamp(t / 0.4))
    d.text((540, 40), '电脑端测试', font=font(38), fill=DIM + (a,), anchor='ma')
    d.text((540, 120), str(v), font=font(104, True), fill=GOLD + (a,), anchor='ma')
    d.text((540, 228), '全部通过', font=font(40, True), fill=WHITE + (int(255 * clamp((t - 0.8) / 0.5)),), anchor='ma')


def cell_grid(d, t, start=0.15, x0=200, y0=300, cols=7, rows=3, cell=78, gap=10):
    # 21 格：20 绿，1 红（exit 2）
    idx_fail = 20
    for i in range(21):
        appear = 0.15 + i * 0.012
        q = clamp((t - appear) / 0.25)
        if q <= 0:
            continue
        cx = x0 + (i % cols) * (cell + gap)
        cy = y0 + (i // cols) * (cell + gap)
        is_fail = i == idx_fail
        # 红格延后到 3.6s 才变红
        red_on = t > 0.6 if is_fail else False
        fill = (RED if red_on else GREEN) + (int(90 + 120 * q),) if not is_fail else (GOLD if not red_on else RED) + (int(90 + 120 * q),)
        d.rounded_rectangle([cx, cy, cx + cell, cy + cell], radius=12, fill=fill)
        if is_fail:
            d.text((cx + cell / 2, cy + cell / 2), '×', font=font(54, True), fill=BG + (int(255 * q),), anchor='mm')
    if t > 0.6:
        q = clamp((t - 0.6) / 0.3)
        d.text((540, 590), '21 次打包：20 次成功，1 次退出码 2', font=font(34, True), fill=RED + (int(255 * q),), anchor='ma')
    else:
        q = clamp((t - 0.15) / 0.3)
        d.text((540, 590), '21 次打包', font=font(34), fill=DIM + (int(255 * q),), anchor='ma')


def beat_paths(d, t, t0=1.2):
    # 6.2–9.2s：两个目录去找同一个字体
    q0 = clamp((t - t0) / 0.45)
    if q0 <= 0:
        return
    a = int(255 * q0)
    left_x, right_x = 250, 830
    d.text((left_x, 60), '配置生成在', font=font(34), fill=DIM + (a,), anchor='ma')
    d.text((left_x, 110), '运行目录', font=font(46, True), fill=WHITE + (a,), anchor='ma')
    d.text((right_x, 60), '打包去找在', font=font(34), fill=DIM + (a,), anchor='ma')
    d.text((right_x, 110), '配置目录', font=font(46, True), fill=WHITE + (a,), anchor='ma')
    # 文件夹 + 字体图标
    q1 = clamp((t - t0 - 0.5) / 0.4)
    if q1 > 0:
        b = int(255 * q1)
        for cx, label in ((left_x, 'fonts/'), (right_x, 'fonts/')):
            d.rounded_rectangle([cx - 110, 190, cx + 110, 290], radius=14, outline=GOLD + (b,), width=4)
            d.text((cx, 240), label, font=font(36, True), fill=GOLD + (b,), anchor='mm')
    q2 = clamp((t - t0 - 1.2) / 0.4)
    if q2 > 0:
        c = int(255 * q2)
        d.line([(left_x + 120, 240), (right_x - 120, 240)], fill=DIM + (c,), width=4)
        d.text((540, 360), '找到 ≠ 同一处', font=font(52, True), fill=RED + (c,), anchor='ma')
        d.text((540, 440), '字体在运行目录，打包却按配置目录找', font=font(34), fill=WHITE + (c,), anchor='ma')


def beat_track(d, t, t0=6.5):
    # 9.4–12.5s：四态条，只点亮“测试通过”
    q0 = clamp((t - t0) / 0.4)
    if q0 <= 0:
        return
    a = int(255 * q0)
    labels = ['测试通过', '产物生成', '离线审阅', '真机部署']
    y = 180
    x0, x1 = 170, 910
    d.line([(x0, y), (x1, y)], fill=DIM + (int(a * 0.8),), width=6)
    d.line([(x0, y), (x0 + (x1 - x0) / 3, y)], fill=GOLD + (a,), width=6)
    for i, lab in enumerate(labels):
        cx = x0 + (x1 - x0) * i / 3
        lit = i == 0
        r = 18 if lit else 14
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=(GOLD if lit else DIM) + (a,))
        d.text((cx, y + 56), lab, font=font(34, True), fill=(WHITE if lit else DIM) + (a,), anchor='ma')
    q1 = clamp((t - t0 - 0.9) / 0.5)
    if q1 > 0:
        b = int(255 * q1)
        d.text((540, 340), '测试通过 ≠ 打包能过', font=font(56, True), fill=RED + (b,), anchor='ma')
    q2 = clamp((t - t0 - 1.8) / 0.5)
    if q2 > 0:
        c = int(255 * q2)
        d.text((540, 470), '这一轮没碰设备：Firmware / Runtime 均未启动', font=font(32), fill=DIM + (c,), anchor='ma')


def main():
    d = OUT / 'frames2'
    d.mkdir(exist_ok=True)
    for i in range(int(DUR * FPS)):
        t = i / FPS
        img = Image.new('RGB', (W, H), BG)
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(layer)
        # 分节拍，避免叠加
        if t < 1.2:
            beat_counter(dr, t)
            cell_grid(dr, t)
        elif t < 6.5:
            beat_paths(dr, t, t0=1.2)
        else:
            beat_track(dr, t, t0=6.5)
        img = Image.alpha_composite(img.convert('RGBA'), layer).convert('RGB')
        img.save(d / f'f{i:04d}.png')
    out = OUT / '动效-EP22-v002.mp4'
    subprocess.run(['/opt/homebrew/bin/ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS),
                    '-i', str(d / 'f%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    '-crf', '18', '-movflags', '+faststart', str(out)], check=True)
    print('动效段已生成:', out)


if __name__ == '__main__':
    main()
