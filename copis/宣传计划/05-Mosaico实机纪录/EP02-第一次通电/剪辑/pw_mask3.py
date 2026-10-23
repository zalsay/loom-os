# -*- coding: utf-8 -*-
"""EP02 WiFi 密码逐帧像素化 v3：
蓝色键盘定位 → 从键盘上缘向上找暗屏连续区顶 → 屏幕上部整块（标题/标签/输入行/提示）像素化；
辅以暗橙文字兜底。"""
from PIL import Image
import numpy as np, glob, os
from scipy import ndimage

files = sorted(glob.glob('/tmp/ep1/pwseg/f*.png'))
BLOCK, PAD = 14, 14

def pixelate(im, x0, y0, x1, y1):
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(im.shape[1], x1); y1 = min(im.shape[0], y1)
    reg = im[y0:y1, x0:x1]
    h, w = reg.shape[:2]
    if h < BLOCK or w < BLOCK:
        return
    small = reg[:h // BLOCK * BLOCK, :w // BLOCK * BLOCK].reshape(
        h // BLOCK, BLOCK, w // BLOCK, BLOCK, 3).mean(axis=(1, 3)).astype(np.uint8)
    up = np.kron(small, np.ones((BLOCK, BLOCK, 1), dtype=np.uint8))
    im[y0:y0 + up.shape[0], x0:x0 + up.shape[1]] = up

n_masked = 0
for fp in files:
    im = np.array(Image.open(fp).convert('RGB'))
    r, g, b = im[:, :, 0].astype(int), im[:, :, 1].astype(int), im[:, :, 2].astype(int)
    boxes = []

    blue = (b > 115) & (g > 85) & ((b - r) > 35) & ((g - r) > 10)
    blue = ndimage.binary_dilation(blue, iterations=5)
    lab, n = ndimage.label(blue)
    if n:
        sizes = ndimage.sum(blue, lab, range(1, n + 1))
        biggest = int(np.argmax(sizes)) + 1
        ys, xs = np.nonzero(lab == biggest)
        if len(ys) > 4000:
            kx0, kx1, ky0 = xs.min(), xs.max(), ys.min()
            # 向上找暗屏连续区顶：键盘上方 450px 内，逐行统计暗像素占比
            dark = (r + g + b) < 260
            y_start = max(0, ky0 - 450)
            frac = dark[y_start:ky0, kx0:kx1].mean(axis=1)
            good = np.nonzero(frac > 0.45)[0]
            if len(good):
                # 从键盘往上走，允许 ≤14px 的亮行间隙（输入框分隔线/标签间隙）
                idx = set(good.tolist())
                top_rel = ky0 - 1
                y_last_good = ky0 - 1
                y = ky0 - 1
                while y > y_start:
                    if (y - y_start) in idx:
                        y_last_good = y
                        gap = 0
                    else:
                        gap += 1
                        if gap > 14:
                            break
                    y -= 1
                screen_top = y_last_good
                boxes.append((kx0 - 12, screen_top - 4, kx1 + 13, ky0 - 4))

    # 暗橙文字兜底
    om = (r > 55) & (r < 215) & (g < r * 0.78) & (b < r * 0.65) & (b <= g + 10)
    darkm = (r + g + b) < 190
    om &= ndimage.binary_dilation(darkm, iterations=8)
    lab, n = ndimage.label(om)
    mask_acc = np.zeros_like(om)
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is None:
            continue
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if not (4 <= h <= 45 and 4 <= w <= 300):
            continue
        a = int((lab[sl] == i).sum())
        if 8 <= a <= 1500:
            mask_acc[sl] |= (lab[sl] == i)
    if mask_acc.any():
        line = ndimage.binary_dilation(mask_acc, structure=np.ones((1, 21)))
        lab2, n2 = ndimage.label(line)
        for i, sl in enumerate(ndimage.find_objects(lab2), 1):
            if sl is None:
                continue
            if sl[0].stop - sl[0].start <= 55:
                boxes.append((sl[1].start - PAD, sl[0].start - PAD,
                              sl[1].stop + PAD + 1, sl[0].stop + PAD + 1))

    for x0, y0, x1, y1 in boxes:
        pixelate(im, x0, y0, x1, y1)
    if boxes:
        n_masked += 1
    Image.fromarray(im).save(fp.replace('pwseg/', 'pwseg_m/'))

print(f"frames={len(files)} with_mask={n_masked}")
