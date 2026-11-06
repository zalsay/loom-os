#!/usr/bin/env python3
"""系列封面候选：使用真实浏览器模拟界面，不冒充设备运行。"""
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
from PIL import Image
p=Path(__file__).resolve().parent;root=p.parent;base=p.parents[1]
spec=spec_from_file_location('cover10',base/'EP10-只上传精确读回/剪辑/make_cover10.py');m=module_from_spec(spec);spec.loader.exec_module(m)
m.BADGE='──  织界探索日记 · EP14  ──';m.T1='真机还没验证';m.T2='界面先在电脑里动起来'
photo=Image.open(p/'素材抽帧/202-133.433.jpg').convert('RGB').crop((260,235,740,591)).resize((1080,800),Image.Resampling.LANCZOS)
canvas=m.render(photo,86,204,353);b1,b2,bw=m.measure(canvas)
if b1 and b2 and bw:canvas=m.render(photo,86+94-b1[0],204+214-bw[0],353+365-b2[0])
out=root/'产物/封面-EP14-候选-待审核.png'
if out.exists():raise SystemExit('已有封面，不覆盖')
canvas.save(out);print('字体带坐标',m.measure(canvas),'输出',out)
