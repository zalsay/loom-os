#!/usr/bin/env python3
"""EP16 封面候选：复用系列 make_cover10 版式；T1/T2 与成片屏内标题同版（H4 口径）。
相机帧隐私初查由抽帧目视完成，全片/封面人工隐私审查仍是独立关卡。"""
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
from PIL import Image
p=Path(__file__).resolve().parent;root=p.parent;base=p.parents[1]
spec=spec_from_file_location('cover10',base/'EP10-只上传精确读回/剪辑/make_cover10.py');m=module_from_spec(spec);spec.loader.exec_module(m)
m.BADGE='──  织界探索日记 · EP16  ──';m.T1='找到分区表了';m.T2='为什么还不装新固件'
photo=Image.open(p/'素材抽帧/219-MAC-camera-preview-25.jpg').convert('RGB').crop((330,30,1010,540)).resize((1080,800),Image.Resampling.LANCZOS)
canvas=m.render(photo,86,204,353);b1,b2,bw=m.measure(canvas)
if b1 and b2 and bw:canvas=m.render(photo,86+94-b1[0],204+214-bw[0],353+365-b2[0])
out=root/'产物/封面-EP16-候选-待审核.png'
if out.exists():raise SystemExit('已有封面，不覆盖')
canvas.save(out);print('字体带',m.measure(canvas))
