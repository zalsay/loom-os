#!/usr/bin/env python3
"""EP17 系列封面候选；仅供用户审核，不代表放行发布。"""
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from PIL import Image
import hashlib
p=Path(__file__).resolve().parent
root=p.parent
base=p.parents[1]
spec=spec_from_file_location('cover10',base/'EP10-只上传精确读回/剪辑/make_cover10.py')
m=module_from_spec(spec);spec.loader.exec_module(m)
m.BADGE='──  织界探索日记 · EP17  ──'
m.T1='先不装'
m.T2='能在电脑里做什么？'
source=p/'素材抽帧/camera-15.jpg'
# 与成片同一 224 相机，15 秒；等比例裁剪为 1080:800；不使用终端画面。
photo=Image.open(source).convert('RGB').crop((395,135,1070,635)).resize((1080,800),Image.Resampling.LANCZOS)
canvas=m.render(photo,86,204,353)
b1,b2,bw=m.measure(canvas)
if b1 and b2 and bw:
 canvas=m.render(photo,86+94-b1[0],204+214-bw[0],353+365-b2[0])
out=root/'产物/封面-EP17-v001-待审核.png'
if out.exists(): raise SystemExit('候选封面已存在，不覆盖')
canvas.save(out)
print('文字带（徽章、金色、白色）:',m.measure(canvas))
print('尺寸:',canvas.size,'标题字号:',m.fit(96,m.T1),m.fit(140,m.T2))
print('sha256:',hashlib.sha256(out.read_bytes()).hexdigest())
