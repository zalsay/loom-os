#!/usr/bin/env python3
"""EP10 封面 v001 骨架：沿用 EP04–EP09 定稿版式（42/96/140、投影、短金线、版式带自动校正）。
双结果出口：RESULT 与 build_video10.py 保持一致（T1/T2 必须与成片同版本）。
素材：TODO-P0——session 相机帧（设备主体、无人脸）落位后填 CAM 路径；
     抽帧后先实测设备主体范围再定 crop，勿沿用 EP09 (320,100,800,593) 坐标。"""
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP10-只上传精确读回"
D = f"{BASE}/剪辑"
OUT = f"{BASE}/产物"
RESULT = "success"  # 与 build_video10.py 同步

CAM = f"{D}/素材/cover-src.jpg"   # TODO-P0: 从 ep10-segments 抽帧（无人脸帧，隐私排查通过）
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"

W, H = 1080, 1440
TOP_H = 640
BG = (40, 56, 64)
GOLD = (250, 200, 100)
WHITE = (248, 255, 248)
BADGE = "──  织界探索日记 · EP10  ──"
if RESULT == "success":
    T1 = "77 个文件传上去了"
    T2 = "这次，逐个读回来"
else:
    T1 = "传到第 N 个，停了"
    T2 = "后面没再传"
CONTENT_W = 1000

def fit(size, text):
    return min(size, int(CONTENT_W / len(text)))

def render(cam_img, badge_dy, t1_dy, t2_dy):
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
    canvas.paste(cam_img, (0, TOP_H))
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

if __name__ == "__main__":
    import os
    if not os.path.exists(CAM):
        print(f"[骨架未渲染] 封面照片未就位：{CAM}")
        print("P0 后：从 ep10-segments 相机帧抽 1080×800 聚焦设备帧（无人脸/无识别信息），")
        print("实测设备主体范围定 crop，替换 photo 区三行后重跑。")
        print("标题文本已就绪：", BADGE, "|", T1, "|", T2)
        raise SystemExit(2)
    photo = Image.open(CAM).convert("RGB").crop((320, 100, 320 + 800, 100 + 593)).resize((1080, 800), Image.LANCZOS)  # TODO-P0: 坐标按实测
    vign = Image.new("L", (1080, 800), 0)
    dv = ImageDraw.Draw(vign)
    dv.ellipse([-120, -60, 1200, 760], fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(90))
    black = Image.new("RGB", (1080, 800), (14, 20, 24))
    photo = Image.composite(photo, black, vign)

    canvas = render(photo, 86, 204, 353)
    (b1, b2, bw) = measure(canvas)
    print("初渲实测: 徽章", b1, " T2", b2, " T1", bw)
    if b1 and b2 and bw:
        canvas = render(photo, 86 + (94 - b1[0]), 204 + (214 - bw[0]), 353 + (365 - b2[0]))
        (b1, b2, bw) = measure(canvas)
        print("校正后: 徽章", b1, " T2", b2, " T1", bw)
    canvas.save(f"{OUT}/封面-EP10.png")
    print("cover saved", f"{OUT}/封面-EP10.png")
