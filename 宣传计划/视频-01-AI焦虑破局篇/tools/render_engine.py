#!/usr/bin/env python3
"""High-fidelity pycairo + Pillow + numpy implementation of the Zhi-Jie Crayon Book Renderer."""
import json
import math
from pathlib import Path
import sys
import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 24

C = {
    'background': '#2b3b49',
    'paper': '#fff3da',
    'text': '#fff3da',
    'secondary': '#d6e0e0',
    'tealInk': '#217b68',
    'coralInk': '#c64832',
    'blueInk': '#28698c',
    'ink': '#302924',
    'coral': '#ff7961',
    'blue': '#57bdeb',
    'mustard': '#ffd052',
    'green': '#8cd66a',
    'olive': '#c5df81',
    'teal': '#63ddc3',
    'soil': '#c18b60',
    'skin': '#ffd4aa',
    'rose': '#ffaaa0',
    'white': '#fffaf1',
}

FONT_REGULAR = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
FONT_BOLD = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'


def hex_rgb(col):
    h = col.lstrip('#')
    return int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0


def hex_rgb_int(col):
    h = col.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rnd(n):
    x = math.sin(n * 127.1 + 91.7) * 43758.5453123
    return x - math.floor(x)


def clamp(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp(x)
    return x * x * (3.0 - 2.0 * x)


_WAX_CACHE = {}


def get_wax_pattern(col, p=0.8):
    key = (col, round(p, 3))
    if key not in _WAX_CACHE:
        r, g, b = hex_rgb_int(col)
        idx = np.arange(128 * 128, dtype=np.float64)
        # Deterministic tooth + fibre matching crayon_contrast.cjs
        state = np.uint32(3187)
        teeth = np.empty(128 * 128, dtype=np.float32)
        # Vectorized LCG usingsin/hash approximation + exact fibre
        tx = idx % 128
        ty = idx // 128
        tooth = np.mod(np.sin(idx * 12.9898 + 78.233) * 43758.5453, 1.0)
        fibre = 0.09 * np.sin(tx * 0.13 + ty * 0.8)
        a = np.clip((tooth + fibre - (1.0 - p)) * 7.0, 0.0, 1.0)
        alpha = np.floor(a * 238.0).astype(np.uint8)
        # Cairo FORMAT_ARGB32 on little-endian x86_64 stores [B, G, R, A] premultiplied
        af = alpha.astype(np.float32) / 255.0
        buf = np.zeros((128 * 128, 4), dtype=np.uint8)
        buf[:, 0] = np.round(b * af).astype(np.uint8)
        buf[:, 1] = np.round(g * af).astype(np.uint8)
        buf[:, 2] = np.round(r * af).astype(np.uint8)
        buf[:, 3] = alpha
        surf = cairo.ImageSurface.create_for_data(bytearray(buf.tobytes()), cairo.FORMAT_ARGB32, 128, 128, 128 * 4)
        pat = cairo.SurfacePattern(surf)
        pat.set_extend(cairo.EXTEND_REPEAT)
        _WAX_CACHE[key] = (surf, pat)
    return _WAX_CACHE[key][1]


def make_paper_surface(w, h):
    r0, g0, b0 = hex_rgb_int(C['background'])
    y_grid, x_grid = np.mgrid[0:h, 0:w].astype(np.float32)
    n = np.mod(np.sin(x_grid * 12.9898 + y_grid * 78.233) * 43758.5453, 1.0) - 0.5
    v = (
        n * 5.0
        + np.sin(y_grid * 1.87 + x_grid * 0.09) * 0.6
        + np.sin(x_grid * 0.03 + y_grid * 0.02) * 0.6
        + np.cos(x_grid * 0.008 - y_grid * 0.014) * 0.8
    )
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = np.clip(b0 + v, 0, 255).astype(np.uint8)
    arr[:, :, 1] = np.clip(g0 + v, 0, 255).astype(np.uint8)
    arr[:, :, 2] = np.clip(r0 + v, 0, 255).astype(np.uint8)
    arr[:, :, 3] = 255
    surf = cairo.ImageSurface.create_for_data(bytearray(arr.tobytes()), cairo.FORMAT_ARGB32, w, h, w * 4)
    ctx = cairo.Context(surf)
    gr = cairo.RadialGradient(w * 0.49, h * 0.43, h * 0.1, w * 0.49, h * 0.43, h * 0.7)
    gr.add_color_stop_rgba(0.0, 0xA4 / 255, 0xBF / 255, 0xD0 / 255, 0x0C / 255)
    gr.add_color_stop_rgba(0.55, 0xA4 / 255, 0xBF / 255, 0xD0 / 255, 0.0)
    gr.add_color_stop_rgba(1.0, 0x09 / 255, 0x13 / 255, 0x1C / 255, 0x4A / 255)
    ctx.set_source(gr)
    ctx.rectangle(0, 0, w, h)
    ctx.fill()
    return surf


def make_wash_surface():
    size = 1560
    r0, g0, b0 = hex_rgb_int(C['teal'])
    y_grid, x_grid = np.mgrid[0:size, 0:size].astype(np.float32)
    dx = np.abs(x_grid - 780.0) - 420.0
    dy = np.abs(y_grid - 780.0) - 620.0
    d = -(np.hypot(np.maximum(dx, 0.0), np.maximum(dy, 0.0)) + np.minimum(np.maximum(dx, dy), 0.0) - 48.0)
    mask = d > 0
    alpha = np.zeros((size, size), dtype=np.float32)
    dm = d[mask]
    xm = x_grid[mask]
    ym = y_grid[mask]
    no = 0.5 + 0.5 * np.sin(xm * 0.04) * np.cos(ym * 0.04)
    pool = np.exp(-dm / 7.0) * 0.18
    a_val = (0.58 + 0.14 * no + pool) * np.minimum(1.0, dm / 3.0)
    alpha[mask] = np.clip(a_val, 0.0, 1.0)
    a_u8 = np.round(alpha * 255.0).astype(np.uint8)
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[:, :, 0] = np.round(b0 * alpha).astype(np.uint8)
    arr[:, :, 1] = np.round(g0 * alpha).astype(np.uint8)
    arr[:, :, 2] = np.round(r0 * alpha).astype(np.uint8)
    arr[:, :, 3] = a_u8
    return cairo.ImageSurface.create_for_data(bytearray(arr.tobytes()), cairo.FORMAT_ARGB32, size, size, size * 4)


_FONT_CACHE = {}
_CHAR_SURFACE_CACHE = {}


def get_font(size):
    sz = int(round(size))
    if sz not in _FONT_CACHE:
        _FONT_CACHE[sz] = ImageFont.truetype(FONT_REGULAR, sz)
    return _FONT_CACHE[sz]


def get_char_surface(ch, size, col, stroke_width=0):
    key = (ch, int(round(size)), col, int(round(stroke_width)))
    if key not in _CHAR_SURFACE_CACHE:
        font = get_font(size)
        pad = int(stroke_width * 2 + 12)
        bbox = font.getbbox(ch)
        cw = max(1, (bbox[2] - bbox[0]) if bbox else int(size))
        ch_h = max(1, (bbox[3] - bbox[1]) if bbox else int(size))
        iw = cw + pad * 2
        ih = int(size * 1.45) + pad * 2
        img = Image.new('L', (iw, ih), 0)
        draw = ImageDraw.Draw(img)
        sw = int(round(stroke_width))
        draw.text((iw / 2, ih / 2), ch, font=font, fill=255, anchor='mm', stroke_width=sw, stroke_fill=255)
        mask = np.array(img, dtype=np.float32) / 255.0
        # Apply subtle crayon wax tooth to characters
        r, g, b = hex_rgb_int(col)
        h_m, w_m = mask.shape
        yy, xx = np.mgrid[0:h_m, 0:w_m]
        tooth = 0.86 + 0.14 * np.sin(xx * 0.7 + yy * 0.9)
        alpha = np.clip(mask * tooth, 0.0, 1.0)
        a_u8 = np.round(alpha * 255.0).astype(np.uint8)
        arr = np.zeros((h_m, w_m, 4), dtype=np.uint8)
        arr[:, :, 0] = np.round(b * alpha).astype(np.uint8)
        arr[:, :, 1] = np.round(g * alpha).astype(np.uint8)
        arr[:, :, 2] = np.round(r * alpha).astype(np.uint8)
        arr[:, :, 3] = a_u8
        surf = cairo.ImageSurface.create_for_data(bytearray(arr.tobytes()), cairo.FORMAT_ARGB32, w_m, h_m, w_m * 4)
        advance = draw.textlength(ch, font=font)
        _CHAR_SURFACE_CACHE[key] = (surf, w_m, h_m, advance)
    return _CHAR_SURFACE_CACHE[key]


class Crayon:
    def __init__(self, ctx, t=0.0):
        self.g = ctx
        self.frame = int(math.floor(t * 12))
        self.boil = self.frame % 3
        self.id = 0

    def line(self, points, col=C['ink'], w=4.0, p=0.9, boil=1.0):
        if len(points) < 2:
            return
        g = self.g
        cid = self.id
        self.id += 1
        seed = cid * 11 + self.boil * 3
        g.new_path()
        index = 0
        for i in range(1, len(points)):
            x0, y0 = points[i - 1]
            x1, y1 = points[i]
            dist = math.hypot(x1 - x0, y1 - y0)
            steps = max(1, int(math.ceil(dist / 18.0)))
            for s in range(steps + 1):
                f = s / steps
                jx = (rnd(seed + index) - 0.5) * 1.8 * boil
                jy = (rnd(seed + index + 1) - 0.5) * 1.8 * boil
                index += 2
                x = x0 + (x1 - x0) * f + jx
                y = y0 + (y1 - y0) * f + jy
                if i == 1 and s == 0:
                    g.move_to(x, y)
                else:
                    g.line_to(x, y)
        g.set_source(get_wax_pattern(col, p))
        g.set_line_width(w)
        g.set_line_cap(cairo.LINE_CAP_ROUND)
        g.set_line_join(cairo.LINE_JOIN_ROUND)
        g.stroke()

    def poly(self, points, col, p=0.75, outline=True, width=3.5):
        if not points:
            return
        g = self.g
        g.new_path()
        for i, (x, y) in enumerate(points):
            if i == 0:
                g.move_to(x, y)
            else:
                g.line_to(x, y)
        g.close_path()
        pr, pg, pb = hex_rgb(C['paper'])
        g.set_source_rgb(pr, pg, pb)
        g.fill_preserve()

        cr, cg, cb = hex_rgb(col)
        g.set_source_rgba(cr, cg, cb, 0.22)
        g.fill_preserve()

        g.set_source(get_wax_pattern(col, max(0.2, p - 0.22)))
        g.fill()

        g.save()
        mx = sum(pt[0] for pt in points) / len(points)
        my = sum(pt[1] for pt in points) / len(points)
        g.new_path()
        for i, (x, y) in enumerate(points):
            nx = mx + (x - mx) * 1.018
            ny = my + (y - my) * 1.018
            if i == 0:
                g.move_to(nx, ny)
            else:
                g.line_to(nx, ny)
        g.close_path()
        g.clip()

        xs = [pt[0] for pt in points]
        ys = [pt[1] for pt in points]
        x0, x1 = min(xs) - 5.0, max(xs) + 5.0
        y0, y1 = min(ys) - 5.0, max(ys) + 5.0
        g.set_source(get_wax_pattern(col, p))
        g.set_line_width(4.6)
        g.set_line_cap(cairo.LINE_CAP_ROUND)
        y = y0
        while y <= y1:
            g.new_path()
            g.move_to(x0, y + (rnd(y + self.boil) - 0.5) * 2.0)
            g.line_to(x1, y + (rnd(y + 9 + self.boil) - 0.5) * 2.0)
            g.stroke()
            y += 7.0
        if y1 - y0 > 65.0:
            g.set_source_rgba(cr, cg, cb, 0.22)
            g.set_line_width(2.0)
            x = x0
            while x <= x1:
                g.new_path()
                g.move_to(x, y0)
                g.line_to(x, y1)
                g.stroke()
                x += 11.0
        g.restore()

        if outline:
            closed = list(points) + [points[0]]
            if x1 - x0 > 80.0 and y1 - y0 > 45.0:
                self.line(closed, C['paper'], width + 2.3, 0.8, 0.35)
            self.line(closed, C['ink'], width, 0.96)

    def ellipse(self, x, y, rx, ry, col, p=0.7, rotation=0.0, outline=True):
        pts = []
        cr = math.cos(rotation)
        sr = math.sin(rotation)
        for i in range(36):
            a = (i / 36.0) * math.pi * 2.0
            xx = math.cos(a) * rx
            yy = math.sin(a) * ry
            pts.append((x + xx * cr - yy * sr, y + xx * sr + yy * cr))
        self.poly(pts, col, p, outline)

    def rect(self, x, y, w, h, col, p=0.7):
        self.poly([(x, y), (x + w, y - 1), (x + w + 1, y + h), (x - 1, y + h + 1)], col, p)

    def text(self, s, x, y, size=54, col=C['text'], align='center', reveal=1.0, stroke_width=0):
        if not s:
            return
        g = self.g
        chars = [get_char_surface(ch, size, col, stroke_width) for ch in s]
        widths = [c[3] for c in chars]
        total = sum(widths)
        if align == 'center':
            xx = x - total / 2.0
        elif align == 'right':
            xx = x - total
        else:
            xx = x
        num = int(math.ceil(len(s) * min(1.0, max(0.0, reveal))))
        for i in range(num):
            surf, sw, sh, ww = chars[i]
            g.save()
            g.translate(xx + ww / 2.0, y + (rnd(i * 17 + self.boil) - 0.5) * 1.2)
            g.rotate((rnd(i * 31 + self.boil) - 0.5) * 0.02)
            g.set_source_surface(surf, -sw / 2.0, -sh / 2.0)
            g.paint()
            g.restore()
            xx += ww


def tire(q, x, y, r, t, near=True):
    q.ellipse(x, y, r, r * 0.98, C['ink'], 0.92)
    q.ellipse(x, y, r * 0.61, r * 0.61, C['mustard'], 0.78)
    q.ellipse(x, y, r * 0.22, r * 0.22, C['paper'], 0.9)
    for i in range(12):
        a = (i / 12.0) * math.pi * 2.0 + t
        q.line(
            [
                (x + math.cos(a) * r * 0.79, y + math.sin(a) * r * 0.79),
                (x + math.cos(a + 0.08) * r * 0.95, y + math.sin(a + 0.08) * r * 0.95),
            ],
            C['paper'],
            1.7,
            0.75,
        )
    for i in range(5):
        a = (i / 5.0) * math.pi * 2.0 + t
        q.ellipse(x + math.cos(a) * r * 0.43, y + math.sin(a) * r * 0.43, 3, 3, C['ink'], 0.9)


def car(q, x, y, s=1.0, t=0.0, wide=False):
    g = q.g
    g.save()
    g.translate(x, y)
    g.scale(s, s)
    col = C['blue'] if wide else C['mustard']
    span = 145 if wide else 125
    tire(q, -span, -28, 30, t, False)
    tire(q, span, -25, 30, t, False)
    q.poly([(-173, -48), (143, -48), (203, -18), (-113, -18)], col, 0.68)
    q.poly([(-113, -18), (203, -18), (203, 28), (-113, 28)], col, 0.78)
    q.poly([(-173, -48), (-113, -18), (-113, 28), (-173, -1)], col, 0.7)
    for i in range(11):
        q.ellipse(-98 + i * 27, 4, 5.5, 5.5, C['ink'], 0.96)
        q.ellipse(-129 + i * 27, -38, 5, 3.5, C['mustard'], 0.94)
    for i in range(8):
        q.ellipse(-87 + i * 30, -24, 5, 3.5, C['mustard'], 0.94)
    q.rect(-95, -83, 92, 42, C['blue'], 0.8)
    q.line([(-48, -82), (-48, -42)], C['ink'], 2)
    for xx in (-75, -28):
        q.ellipse(xx, -62, 11, 11, C['paper'], 0.65)
        q.line([(xx - 5, -62), (xx + 5, -62)], C['ink'], 2)
        q.line([(xx, -67), (xx, -57)], C['ink'], 2)
    q.rect(70, -83, 66, 36, C['coral'], 0.7)
    for j in range(7):
        q.line([(80 + j * 7, -82), (80 + j * 7, -50)], C['ink'], 3)
    q.rect(145, -62, 32, 27, C['teal'], 0.75)
    for i in range(4):
        q.line([(143, -58 + i * 6), (137, -58 + i * 6)], C['ink'], 1.7)
    q.line([(-3, -57), (17, -73), (43, -55), (70, -59)], C['coral'], 2.5)
    q.line([(-3, -49), (22, -62), (49, -47), (70, -48)], C['ink'], 2)
    q.rect(-6, -86, 37, 40, C['teal'], 0.6)
    q.ellipse(12, -85, 19, 7, C['teal'], 0.8)
    q.rect(0, -100, 25, 12, C['blue'], 0.8)
    q.ellipse(12, -101, 13, 4, C['blue'], 0.8)
    q.line([(4, -78), (4, -57)], C['paper'], 3, 0.95)
    tire(q, -105, 29, 39, t)
    tire(q, 175, 29, 39, t)
    q.line([(-127, 27), (-149, 27)], C['ink'], 4)
    q.rect(-143, 10, 18, 32, C['mustard'], 0.8)
    q.ellipse(-137, 24, 8, 8, C['paper'], 0.8)
    for i in range(7):
        a = (i / 7.0) * math.pi * 2.0
        q.line(
            [
                (-137 + math.cos(a) * 7, 24 + math.sin(a) * 7),
                (-137 + math.cos(a) * 12, 24 + math.sin(a) * 12),
            ],
            C['ink'],
            2,
        )
    g.restore()


def leaf(q, x, y, angle, length, width, col):
    g = q.g
    g.save()
    g.translate(x, y)
    g.rotate(angle)
    pts = []
    for i in range(15):
        f = i / 14.0
        pts.append((math.sin(math.pi * f) * width, -f * length))
    for i in range(13, -1, -1):
        f = i / 14.0
        pts.append((-math.sin(math.pi * f) * width, -f * length))
    q.poly(pts, col, 0.72, True, 2.2)
    q.line([(0, 0), (0, -length)], C['olive'], 2, 0.83)
    for j in range(1, 4):
        q.line([(0, -length * j / 4.0), (width * 0.65, -length * j / 4.0 - 9)], C['olive'], 1, 0.75)
    g.restore()


def plant(q, x, y, height=100.0, kind=0, grow=1.0):
    height *= grow
    q.line([(x, y), (x + 5, y - height)], C['green'], 4, 0.9)
    col = C['olive'] if kind == 2 else C['green']
    for j in range(5):
        yy = y - height * (0.2 + j * 0.15)
        lw = 16 if kind == 1 else (7 if kind == 2 else 11)
        ll = 66 if kind == 2 else 56
        leaf(q, x + 3, yy, -0.9 if (j % 2) else 0.9, ll * grow, lw * grow, col)
    leaf(q, x + 5, y - height + 0.1, 0, 30 * grow, 11 * grow, C['green'])


def plot(q, x, y, s=1.0, grow=1.0, id=1, tag=None):
    g = q.g
    g.save()
    g.translate(x, y)
    g.scale(s, s)
    label = tag or f'A{id}'
    q.poly([(-158, -15), (122, -15), (178, 22), (-102, 22)], C['olive'], 0.7)
    q.poly([(-102, 22), (178, 22), (178, 92), (-102, 92)], C['green'], 0.67)
    q.poly([(-158, -15), (-102, 22), (-102, 92), (-158, 52)], C['green'], 0.6)
    q.poly([(-142, -13), (112, -13), (155, 14), (-96, 14)], C['soil'], 0.53)
    for i in range(43):
        xx = -135 + rnd(i + 61) * 264
        yy = -10 + rnd(i + 19) * 24
        q.ellipse(xx, yy, 1.2 + rnd(i + 93) * 1.8, 1.2, C['soil'], 0.82)
    for xx in (-64, -26, 13, 50, 88, 128):
        q.line([(xx, 31), (xx, 81)], C['olive'], 2, 0.85)
    q.rect(8, 43, 76, 30, C['paper'], 0.92)
    q.text(label, 46, 58, 23, C['ink'])
    q.line([(178, 41), (198, 49), (198, 70), (179, 62)], C['paper'], 6.5, 0.85)
    q.line([(-155, 8), (-172, 11), (-172, 32), (-153, 30)], C['paper'], 6.5, 0.85)
    q.line([(178, 41), (198, 49), (198, 70), (179, 62)], C['ink'], 4)
    q.line([(-155, 8), (-172, 11), (-172, 32), (-153, 30)], C['ink'], 4)
    for xx in (-83, 116):
        q.line([(xx, 81), (xx + 11, 81)], C['ink'], 2)
    for j in range(3):
        plant(q, -100 + j * 101, 7 + j * 2, 100 + rnd(j + id * 8) * 30, id % 3, grow)
    q.line([(136, 6), (136, -116)], C['soil'], 4)
    q.rect(115, -132, 60, 34, C['paper'], 0.9)
    q.text(label, 145, -115, 27, C['ink'])
    g.restore()


def child(q, x, y, s=1.0, which=0, pose='happy', t=0.0):
    g = q.g
    g.save()
    g.translate(x, y)
    g.scale(s, s)
    colour = C['blue'] if which else C['coral']
    bb = (int(math.floor(t * 2)) % 2) * 2 if pose == 'happy' else 0
    q.line([(-18, 37), (-29, 100)], C['paper'], 17, 0.9)
    q.line([(18, 37), (29, 100)], C['paper'], 17, 0.9)
    q.line([(-18, 37), (-29, 100)], C['ink'], 13)
    q.line([(18, 37), (29, 100)], C['ink'], 13)
    q.ellipse(-31, 104, 22, 10, C['mustard'], 0.9)
    q.ellipse(33, 104, 22, 10, C['mustard'], 0.9)
    q.poly([(-39, -46), (39, -46), (50, 40), (-46, 40)], colour, 0.8)
    ly = -65 if pose == 'think' else (12 - bb)
    ry = -22 if pose == 'build' else (-77 if pose == 'happy' else 11)
    q.line([(-35, -35), (-60, -8), (-81, ly)], C['skin'], 18)
    q.line([(37, -33), (60, -3), (91, ry)], C['skin'], 18)
    q.ellipse(-81, ly, 12, 13, C['skin'], 0.85)
    q.ellipse(91, ry, 12, 13, C['skin'], 0.85)
    q.ellipse(0, -104, 45, 47, C['skin'], 0.67)
    hair = (
        [(-44, -109), (-42, -143), (-18, -154), (11, -151), (39, -132), (42, -108), (20, -130), (-12, -127), (-29, -110)]
        if which
        else [(-44, -107), (-47, -139), (-22, -158), (16, -154), (43, -139), (46, -111), (25, -119), (20, -139), (-5, -125), (-22, -134)]
    )
    q.poly(hair, C['ink'], 0.94)
    q.ellipse(-15, -103, 4, 5, C['ink'], 0.96)
    q.ellipse(17, -103, 4, 5, C['ink'], 0.96)
    q.ellipse(-16, -105, 1, 1, C['white'], 0.99, 0, False)
    q.ellipse(16, -105, 1, 1, C['white'], 0.99, 0, False)
    q.ellipse(-29, -86, 7, 4, C['rose'], 0.6, 0, False)
    q.ellipse(29, -86, 7, 4, C['rose'], 0.6, 0, False)
    q.line([(-10, -81), (0, -83 if pose == 'think' else -74), (10, -80)], C['ink'], 2.5)
    if pose == 'think':
        q.line([(-24, -116), (-10, -121)], C['ink'], 2)
        q.line([(12, -121), (25, -116)], C['ink'], 2)
    q.line([(-6, -38), (-6, 22)], C['paper'], 1.5)
    q.ellipse(7, 3, 2, 2, C['mustard'], 0.9)
    g.restore()


def thought(q, x, y, lines):
    q.poly(
        [
            (x - 180, y - 68),
            (x + 185, y - 64),
            (x + 188, y + 64),
            (x - 85, y + 66),
            (x - 137, y + 96),
            (x - 127, y + 63),
            (x - 184, y + 60),
        ],
        C['paper'],
        0.95,
    )
    for i, ln in enumerate(lines):
        q.text(ln, x + 4, y - 2 + (i - (len(lines) - 1) / 2.0) * 50, 42, C['ink'])


def draw_lines(q, ss, x, y, size=52, gap=78, col=C['text'], reveal=1.0):
    total = sum(len(s) for s in ss)
    count = int(math.ceil(total * clamp(reveal)))
    for i, s in enumerate(ss):
        if count <= 0:
            break
        part = s[:count]
        count -= len(s)
        q.text(part, x, y + i * gap, size, col, 'center', 1.0)


def draw_card(q, body, x=150, y=500, w=780, h=320):
    q.rect(x, y, w, h, C['paper'], 0.94)
    if not body:
        return
    gap = 62
    start_y = y + h / 2.0 - ((len(body) - 1) * gap) / 2.0
    for i, ln in enumerate(body):
        q.text(ln, x + w / 2.0, start_y + i * gap, 44, C['ink'])


def draw_object(q, kind, x, y, scale=1.5, step=0.0):
    if kind == 'car':
        car(q, x, y, scale, step)
    elif kind == 'garden':
        plot(q, x, y, scale, 1.0, 1)
    else:
        car(q, x - 210, y + 22, scale * 0.64, step)
        plot(q, x + 215, y + 12, scale * 0.64, 1.0, 1)


def load_logo_surface(project_dir, width=216):
    logo_path = Path(project_dir) / 'Zhi-Jie-logo.png'
    img = Image.open(logo_path).convert('RGBA')
    h = int(round(width * img.height / img.width))
    img = img.resize((width, h), Image.Resampling.LANCZOS)
    arr = np.array(img, dtype=np.float32)
    alpha = arr[:, :, 3:4] / 255.0
    bgra = np.zeros((h, width, 4), dtype=np.uint8)
    bgra[:, :, 0] = np.round(arr[:, :, 2] * alpha[:, :, 0]).astype(np.uint8)
    bgra[:, :, 1] = np.round(arr[:, :, 1] * alpha[:, :, 0]).astype(np.uint8)
    bgra[:, :, 2] = np.round(arr[:, :, 0] * alpha[:, :, 0]).astype(np.uint8)
    bgra[:, :, 3] = arr[:, :, 3].astype(np.uint8)
    return cairo.ImageSurface.create_for_data(bytearray(bgra.tobytes()), cairo.FORMAT_ARGB32, width, h, width * 4)


def main():
    project_dir = Path(sys.argv[1]).resolve()
    flags = set(sys.argv[2:])
    cfg = json.loads((project_dir / 'episode.json').read_text(encoding='utf-8'))
    scenes = []
    duration = 0.0
    for s in cfg['scenes']:
        scenes.append(dict(s, a=duration, b=duration + float(s['duration']), duration=float(s['duration'])))
        duration += float(s['duration'])

    (project_dir / 'out').mkdir(exist_ok=True)
    paper = make_paper_surface(W, H)
    wash = make_wash_surface()
    logo_surf = load_logo_surface(project_dir, 216)

    page = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    output = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    g = cairo.Context(page)
    og = cairo.Context(output)

    scene_cache = {}
    previous = {}

    def render_scene_to_page(t, k, u):
        s = scenes[k]
        step = math.floor(t * 12.0) / 12.0
        boil = int(math.floor(t * 12.0)) % 3
        bob = int(math.floor(t * 2.0)) % 2
        # Cache static states after title reveal (u >= 0.65) for scenes without continuous motion
        is_continuous = s['type'] in ('test', 'growth') or (s['type'] == 'ai' and abs(u - s['duration'] * 0.4) < 0.1)
        cache_key = None
        if u >= 0.65 and not is_continuous:
            ai_phase = 0 if (s['type'] == 'ai' and u < s['duration'] * 0.4) else 1
            cache_key = (k, boil, bob, ai_phase)
            if cache_key in scene_cache:
                g.save()
                g.set_operator(cairo.OPERATOR_SOURCE)
                g.set_source_surface(scene_cache[cache_key], 0, 0)
                g.paint()
                g.restore()
                return

        q = Crayon(g, t)
        g.save()
        g.set_operator(cairo.OPERATOR_CLEAR)
        g.paint()
        g.restore()

        g.save()
        g.set_source_surface(wash, -240, 180)
        g.paint_with_alpha(0.16)
        g.restore()

        g.set_source_surface(logo_surf, 82, 106)
        g.paint()

        q.text(f"织界 · {cfg.get('header', '创造日记')}", 565, 146, 38, C['secondary'])
        q.text(f"{k + 1} / {len(scenes)}", 980, 147, 36, C['secondary'], 'right')

        if s['type'] != 'end':
            two = len(s['title']) > 1
            draw_lines(q, s['title'], 540, 264 if two else 304, 66, 84, C['text'], u / 0.65)
            yy = 411 if two else 366
            q.line([(327, yy), (455, yy + 3), (590, yy - 2), (758, yy + 2)], C['mustard'], 8, 0.86)

        stype = s['type']
        if stype == 'idea':
            child(q, 270, 765, 1.5, 0, 'think', step)
            thought(q, 745, 680, (s.get('body') or [])[:2])
            draw_object(q, s.get('illustration', 'generic'), 525, 1190, 1.65, step)
        elif stype == 'build':
            draw_card(q, s.get('body') or [], 150, 490, 780, 310)
            draw_object(q, s.get('illustration', 'generic'), 520, 1085, 1.68, step)
            child(q, 218, 1425, 0.86, 0, 'build', step)
            child(q, 858, 1425, 0.86, 1, 'build', step)
        elif stype == 'test':
            q.line([(185, 960), (450, 960), (700, 1010), (890, 1130)], C['olive'], 6, 0.7)
            prog = ease(u / s['duration'])
            draw_object(q, s.get('illustration', 'generic'), 340 + 330 * prog, 830 + 210 * prog, 1.5, step)
            draw_card(q, s.get('body') or [], 180, 1210, 720, 310)
        elif stype == 'compare':
            draw_card(q, s.get('before') or [], 130, 615, 385, 380)
            draw_card(q, s.get('after') or [], 565, 615, 385, 380)
            q.text(s.get('before_label', '方案 A'), 320, 544, 44, C['coral'])
            q.text(s.get('after_label', '方案 B'), 757, 544, 44, C['teal'])
            draw_object(q, s.get('illustration', 'generic'), 520, 1250, 1.5, step)
            child(q, 210, 1430, 0.75, 0, 'think', step)
            child(q, 872, 1430, 0.75, 1, 'build', step)
        elif stype == 'ai':
            pose = 'think' if u < s['duration'] * 0.4 else 'happy'
            child(q, 235, 760, 1.32, 0, pose, step)
            draw_card(q, s.get('body') or [], 420, 560, 520, 330)
            q.rect(580, 492, 200, 54, C['teal'], 0.88)
            q.text('交互示意', 680, 519, 34, C['ink'])
            draw_object(q, s.get('illustration', 'generic'), 530, 1210, 1.48, step)
        elif stype == 'garden':
            tags = ['A1', 'A2', 'B1', 'B2']
            coords = [(310, 745), (770, 745), (310, 1215), (770, 1215)]
            body = s.get('body') or []
            for i in range(4):
                px, py = coords[i]
                plot(q, px, py, 0.92, 1.0, i + 1, tags[i])
                if i < len(body):
                    q.rect(px - 165, py + 105, 330, 62, C['paper'], 0.92)
                    q.text(body[i], px, py + 136, 36, C['ink'])
        elif stype == 'growth':
            g_factor = 0.35 + 0.65 * ease(u / s['duration'])
            plot(q, 540, 940, 1.7, g_factor, 1)
            draw_card(q, s.get('body') or [], 180, 1210, 720, 260)
        elif stype == 'record':
            draw_card(q, s.get('body') or [], 150, 510, 780, 400)
            draw_object(q, s.get('illustration', 'generic'), 540, 1240, 1.55, step)
            child(q, 210, 1410, 0.82, 0, 'happy', step)
            child(q, 870, 1410, 0.82, 1, 'happy', step)
        elif stype == 'end':
            draw_lines(q, s['title'], 540, 310, 58, 76, C['secondary'], u / 0.65)
            q.text('织界', 540, 620, 235, C['mustard'], 'center', 1.0, 6)
            q.line([(280, 775), (540, 779), (800, 773)], C['teal'], 8, 0.9)
            q.text('AI 引导，孩子思考，共同实现', 540, 875, 50, C['text'])
            draw_card(q, s.get('body') or [], 160, 995, 760, 230)
            child(q, 260, 1435, 0.80, 0, 'happy', step)
            child(q, 820, 1435, 0.80, 1, 'happy', step)

        captions = s.get('caption') or []
        if captions:
            cy = 1595 if len(captions) > 1 else 1635
            draw_lines(q, captions, 540, cy, 52, 74, C['text'], 1.0)

        if cache_key is not None:
            cached = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
            cg = cairo.Context(cached)
            cg.set_source_surface(page, 0, 0)
            cg.paint()
            scene_cache[cache_key] = cached

    def render(t):
        k = len(scenes) - 1
        for idx, sc in enumerate(scenes):
            if sc['a'] <= t < sc['b']:
                k = idx
                break
        u = t - scenes[k]['a']
        if k > 0 and u < 0.55 and k not in previous:
            render_scene_to_page(scenes[k]['a'] - 0.1, k - 1, scenes[k - 1]['duration'] - 0.1)
            old = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
            oc = cairo.Context(old)
            oc.set_source_surface(page, 0, 0)
            oc.paint()
            previous[k] = old

        render_scene_to_page(t, k, u)
        og.save()
        og.set_operator(cairo.OPERATOR_SOURCE)
        og.set_source_surface(paper, 0, 0)
        og.paint()
        og.restore()

        og.save()
        z = 1.0 + 0.008 * ease(u / scenes[k]['duration'])
        og.translate(W / 2.0, H / 2.0)
        og.scale(z, z)
        og.set_source_surface(page, -W / 2.0, -H / 2.0)
        og.paint()
        og.restore()

        if k > 0 and u < 0.55:
            p = ease(u / 0.55)
            x = W * (1.0 - p)
            fold = 34.0 + math.sin(p * math.pi) * 92.0
            og.save()
            og.rectangle(0, 0, x, H)
            og.clip()
            og.set_source_surface(paper, 0, 0)
            og.paint()
            og.set_source_surface(previous[k], 0, 0)
            og.paint()
            og.restore()

            og.new_path()
            og.move_to(x, 0)
            og.curve_to(x - fold, H * 0.27, x + fold * 0.22, H * 0.69, x, H)
            og.line_to(x - fold * 0.63, H)
            og.curve_to(x - fold * 1.05, H * 0.64, x - fold * 0.86, H * 0.27, x, 0)
            og.close_path()
            gr = cairo.LinearGradient(x - fold, 0, x + 15, 0)
            gr.add_color_stop_rgb(0.0, 0x14 / 255, 0x23 / 255, 0x31 / 255)
            gr.add_color_stop_rgb(0.55, 0x65 / 255, 0x7A / 255, 0x85 / 255)
            gr.add_color_stop_rgb(1.0, 0x34 / 255, 0x4B / 255, 0x5C / 255)
            og.set_source(gr)
            og.fill()

    def surface_to_rgba_bytes(surf):
        buf = np.frombuffer(surf.get_data(), dtype=np.uint8).reshape((H, W, 4))
        # Cairo ARGB32 on little-endian is BGRA; swap B and R to get RGBA
        rgba = buf[:, :, [2, 1, 0, 3]]
        return rgba.tobytes()

    if '--stills' in flags:
        for k, sc in enumerate(scenes):
            render(sc['a'] + min(2.0, sc['duration'] * 0.65))
            output.write_to_png(str(project_dir / 'out' / f'scene-{k + 1:02d}.png'))
            if k > 0:
                render(sc['a'] + 0.24)
                output.write_to_png(str(project_dir / 'out' / f'turn-{k + 1:02d}.png'))
        return

    if '--raw' not in flags:
        raise SystemExit('Use --stills or --raw')

    total_frames = int(round(duration * FPS))
    out_stream = sys.stdout.buffer
    for f in range(total_frames):
        render(f / FPS)
        out_stream.write(surface_to_rgba_bytes(output))
        if f % 120 == 0:
            sys.stderr.write(f'Episode {f / FPS:.1f}s\n')
            sys.stderr.flush()
    out_stream.flush()


if __name__ == '__main__':
    main()
