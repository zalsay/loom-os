#!/usr/bin/env python3
"""EP18 系列封面候选；沿用 EP10 模板，与成片标题逐字一致。仅候选，待用户确认。"""
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from PIL import Image
import hashlib
p = Path(__file__).resolve().parent
root = p.parent
base = p.parents[1]
spec = spec_from_file_location('cover10', base / 'EP10-只上传精确读回/剪辑/make_cover10.py')
m = module_from_spec(spec)
spec.loader.exec_module(m)
m.BADGE = '──  织界探索日记 · EP18  ──'
m.T1 = '刚准备的目录'
m.T2 = '怎么又不见了？'
src = p / '素材抽帧/cam-12.jpg'
photo = Image.open(src).convert('RGB').crop((150, 20, 1230, 820)).resize((1080, 800), Image.Resampling.LANCZOS)
canvas = m.render(photo, 86, 204, 353)
b1, b2, bw = m.measure(canvas)
if b1 and b2 and bw:
    canvas = m.render(photo, 86 + 94 - b1[0], 204 + 214 - bw[0], 353 + 365 - b2[0])
out = root / '产物/封面-EP18-v001-待确认.png'
if out.exists():
    raise SystemExit('封面已存在，不覆盖')
canvas.save(out)
print('文字带（徽章/金色/白色）:', m.measure(canvas))
print('尺寸:', canvas.size, 'T1/T2 字号:', m.fit(96, m.T1), m.fit(140, m.T2))
print('sha256:', hashlib.sha256(out.read_bytes()).hexdigest())
