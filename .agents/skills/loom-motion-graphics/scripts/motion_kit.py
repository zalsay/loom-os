#!/usr/bin/env python3
"""织界动效组件库：把事实数字画成竖屏动效段。

用法：
    python3 motion_kit.py spec.json out.mp4 [--frames DIR]

spec.json 结构见 references/design.md；每段 beat 有 type / start / end 和各自字段。
只依赖 Pillow 与 ffmpeg，不依赖 Manim，也不联网。
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
    '/System/Library/Fonts/PingFang.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
]

PALETTE = {
    'bg': '#141B1F',
    'white': '#F8FFF8',
    'gold': '#FAC864',
    'red': '#FF9678',
    'green': '#78DC8C',
    'dim': '#6E7E86',
}


def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(size, bold=False):
    path = next((p for p in FONT_CANDIDATES if Path(p).exists()), None)
    if not path:
        return ImageFont.load_default()
    try:
        return ImageFont.truetype(path, size, index=1 if bold else 0)
    except Exception:
        return ImageFont.load_default()


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    """ease-out cubic：进入不做弹跳，退出通常直接切。"""
    return 1 - (1 - t) ** 3


class Canvas:
    def __init__(self, spec):
        self.w, self.h = spec.get('size', [1080, 608])
        self.dur = float(spec['duration'])
        self.pal = {k: hex2rgb(spec.get('palette', {}).get(k, v)) for k, v in PALETTE.items()}


def draw_counter(c, d, t, b):
    if not (b['start'] <= t <= b['end']):
        return
    span = b.get('count_seconds', 1.3)
    p = clamp((t - b['start']) / span)
    v = int(round(b['value'] * ease(p)))
    a = int(255 * clamp((t - b['start']) / 0.35))
    d.text((c.w / 2, c.h * 0.16), b.get('label', ''), font=font(b.get('label_size', 34)),
           fill=c.pal['dim'] + (a,), anchor='ma')
    d.text((c.w / 2, c.h * 0.42), f"{v:,}".replace(',', ''), font=font(b.get('value_size', 96), True),
           fill=c.pal['gold'] + (a,), anchor='ma')
    q = clamp((t - b['start'] - span * 0.7) / 0.4)
    if q > 0 and b.get('caption'):
        d.text((c.w / 2, c.h * 0.62), b['caption'], font=font(b.get('caption_size', 38), True),
               fill=c.pal['white'] + (int(255 * q),), anchor='ma')


def draw_grid(c, d, t, b):
    if not (b['start'] <= t <= b['end']):
        return
    items = int(b.get('count', 21))
    cols = int(b.get('cols', 7))
    rows = (items + cols - 1) // cols
    cell = b.get('cell', 62)
    gap = b.get('gap', 10)
    x0 = (c.w - cols * cell - (cols - 1) * gap) // 2
    y0 = b.get('y', 100)
    fail_at = b.get('fail_at', b['start'] + 2)
    fail_idx = b.get('fail_index', items - 1)
    fail_color = c.pal[b.get('fail_color', 'red')]
    ok_color = c.pal[b.get('ok_color', 'green')]

    a = clamp((t - b['start']) / 0.4)
    if b.get('title'):
        d.text((c.w / 2, y0 - 52), b['title'], font=font(b.get('title_size', 32)),
               fill=c.pal['dim'] + (int(255 * a),), anchor='ma')
    for i in range(items):
        q = clamp((t - b['start'] - 0.1 - i * 0.05) / 0.2)
        if q <= 0:
            continue
        cx = x0 + (i % cols) * (cell + gap)
        cy = y0 + (i // cols) * (cell + gap)
        is_fail = i == fail_idx
        red = is_fail and t > fail_at
        color = fail_color if red else (c.pal['gold'] if is_fail else ok_color)
        d.rounded_rectangle([cx, cy, cx + cell, cy + cell], radius=10,
                            fill=color + (int(120 + 130 * q),))
        if is_fail:
            d.text((cx + cell / 2, cy + cell / 2), b.get('fail_mark', '×'),
                   font=font(int(cell * 0.66), True), fill=c.pal['bg'] + (int(255 * q),), anchor='mm')
    q = clamp((t - fail_at) / 0.35)
    if q > 0 and b.get('caption'):
        color = c.pal[b.get('caption_color', 'red')] if t > fail_at else c.pal['dim']
        d.text((c.w / 2, y0 + rows * (cell + gap) + 22), b['caption'],
               font=font(b.get('caption_size', 34), True), fill=color + (int(255 * q),), anchor='ma')


def draw_paths(c, d, t, b):
    if not (b['start'] <= t <= b['end']):
        return
    a = int(255 * clamp((t - b['start']) / 0.4))
    lx, rx = c.w * 0.25, c.w * 0.75
    d.text((lx, c.h * 0.10), b.get('left_label', ''), font=font(30), fill=c.pal['dim'] + (a,), anchor='ma')
    d.text((lx, c.h * 0.18), b.get('left_title', ''), font=font(42, True), fill=c.pal['white'] + (a,), anchor='ma')
    d.text((rx, c.h * 0.10), b.get('right_label', ''), font=font(30), fill=c.pal['dim'] + (a,), anchor='ma')
    d.text((rx, c.h * 0.18), b.get('right_title', ''), font=font(42, True), fill=c.pal['white'] + (a,), anchor='ma')
    q1 = clamp((t - b['start'] - 0.5) / 0.4)
    if q1 > 0:
        bb = int(255 * q1)
        box_h = b.get('box_height', 88)
        box_w = b.get('box_width', 200)
        for cx in (lx, rx):
            d.rounded_rectangle([cx - box_w / 2, c.h * 0.28, cx + box_w / 2, c.h * 0.28 + box_h],
                                radius=12, outline=c.pal['gold'] + (bb,), width=4)
            d.text((cx, c.h * 0.28 + box_h / 2), b.get('box_text', 'fonts/'),
                   font=font(32, True), fill=c.pal['gold'] + (bb,), anchor='mm')
    q2 = clamp((t - b['start'] - 1.4) / 0.4)
    if q2 > 0:
        ccolor = int(255 * q2)
        d.line([(lx + 108, c.h * 0.28 + 44), (rx - 108, c.h * 0.28 + 44)], fill=c.pal['dim'] + (ccolor,), width=4)
        d.text((c.w / 2, c.h * 0.56), b.get('verdict', '找到 ≠ 同一处'),
               font=font(46, True), fill=c.pal['red'] + (ccolor,), anchor='ma')
    q3 = clamp((t - b['start'] - 2.6) / 0.4)
    if q3 > 0 and b.get('note'):
        d.text((c.w / 2, c.h * 0.70), b['note'], font=font(30),
               fill=c.pal['white'] + (int(255 * q3),), anchor='ma')


def draw_track(c, d, t, b):
    if not (b['start'] <= t <= b['end']):
        return
    a = int(255 * clamp((t - b['start']) / 0.4))
    labels = b.get('labels', ['测试通过', '产物生成', '离线审阅', '真机部署'])
    lit = int(b.get('lit', 1))
    y = c.h * 0.26
    x0, x1 = c.w * 0.18, c.w * 0.82
    d.line([(x0, y), (x1, y)], fill=c.pal['dim'] + (int(a * 0.7),), width=6)
    if lit > 0:
        d.line([(x0, y), (x0 + (x1 - x0) * (lit - 1) / (len(labels) - 1), y)],
               fill=c.pal['gold'] + (a,), width=6)
    for i, lab in enumerate(labels):
        cx = x0 + (x1 - x0) * i / (len(labels) - 1)
        on = i < lit
        r = 17 if on else 13
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=(c.pal['gold'] if on else c.pal['dim']) + (a,))
        d.text((cx, y + 48), lab, font=font(30, True),
               fill=(c.pal['white'] if on else c.pal['dim']) + (a,), anchor='ma')
    q1 = clamp((t - b['start'] - 0.9) / 0.4)
    if q1 > 0 and b.get('verdict'):
        d.text((c.w / 2, c.h * 0.52), b['verdict'], font=font(50, True),
               fill=c.pal['red'] + (int(255 * q1),), anchor='ma')
    q2 = clamp((t - b['start'] - 2.0) / 0.4)
    if q2 > 0 and b.get('note'):
        d.text((c.w / 2, c.h * 0.70), b['note'], font=font(30),
               fill=c.pal['dim'] + (int(255 * q2),), anchor='ma')


BEATS = {
    'counter': draw_counter,
    'grid': draw_grid,
    'paths': draw_paths,
    'track': draw_track,
}


def render(spec, out_mp4, frames_dir):
    c = Canvas(spec)
    fps = int(spec.get('fps', 30))
    frames_dir.mkdir(parents=True, exist_ok=True)
    for i in range(int(c.dur * fps)):
        t = i / fps
        img = Image.new('RGB', (c.w, c.h), c.pal['bg'])
        layer = Image.new('RGBA', (c.w, c.h), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for b in spec['beats']:
            fn = BEATS.get(b['type'])
            if fn:
                fn(c, d, t, b)
        img = Image.alpha_composite(img.convert('RGBA'), layer).convert('RGB')
        img.save(frames_dir / f'f{i:04d}.png')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(fps),
                    '-i', str(frames_dir / 'f%04d.png'), '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-crf', '18', '-movflags', '+faststart',
                    str(out_mp4)], check=True)
    return out_mp4


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    spec = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    out = Path(sys.argv[2])
    frames = Path(sys.argv[3]) if len(sys.argv) > 3 else out.with_suffix('')
    render(spec, out, frames)
    print(f'动效段已生成: {out}')


if __name__ == '__main__':
    main()
