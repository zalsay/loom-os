#!/usr/bin/env python3
"""EP13 封面候选：基于系列 EP10 模板与 179 相机旧画面；未经隐私及用户审核。"""
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import subprocess
from PIL import Image, ImageDraw, ImageFilter
p=Path(__file__).resolve().parent
root=p.parent
base=p.parents[1]
source=root/'素材/179/MAC-camera.mp4'
frame=p/'审核证据-v004/封面源-179-60s.jpg'
subprocess.run(['ffmpeg','-v','error','-ss','60','-i',str(source),'-frames:v','1','-n',str(frame)],check=True)
spec=spec_from_file_location('cover10',base/'EP10-只上传精确读回/剪辑/make_cover10.py')
m=module_from_spec(spec); spec.loader.exec_module(m)
m.BADGE='──  织界探索日记 · EP13  ──'
m.T1='新固件做好以后'; m.T2='先在电脑里试试'
# 设备取景先沿视频的 608x342 源框，中心裁为 1.35:1，保留自然比例；候选须核对设备四边和隐私。
photo=Image.open(frame).convert('RGB').crop((478,145,940,487)).resize((1080,800),Image.Resampling.LANCZOS)
vign=Image.new('L',(1080,800),0); ImageDraw.Draw(vign).ellipse([-120,-60,1200,760],fill=255); vign=vign.filter(ImageFilter.GaussianBlur(90))
photo=Image.composite(photo,Image.new('RGB',(1080,800),(14,20,24)),vign)
canvas=m.render(photo,86,204,353); b1,b2,bw=m.measure(canvas)
if b1 and b2 and bw: canvas=m.render(photo,86+94-b1[0],204+214-bw[0],353+365-b2[0])
print('bands',m.measure(canvas)); canvas.save(root/'产物/封面-EP13-候选-待审核.png')
