#!/usr/bin/env python3
"""EP16 v004：定稿旁白 take-v004b（37.44s）、三幕按句界重排、去 zoompan 横裁、离线环节字幕卡。
字幕句界=能量谷+字数比例辅助估计，仍待人工听检；隐私遮挡未逐帧复核，本版未放行。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import subprocess, re
p=Path(__file__).resolve().parent; root=p.parent
out=root/'产物/EP16-寻找分区表试剪-v004-待审核.mp4'
if out.exists(): raise SystemExit('禁止覆盖')
T=40.0
V=0.5  # 旁白起播偏移
# 8 句实测句界（take-v004b，静音探测+字数比例）：S1|S2|S3|S4|S5|S6|S7|S8
b=[0.0,3.28,6.42,8.08,14.08,21.72,26.94,30.9,37.44]
SUBS=[  # (起,止,文本；{}=亮金重点) —— 句内小句按字数比例，待听检微调
 (V+b[0],V+3.58,'给设备装新固件前'),(V+3.58,V+b[1],'{先核对分区表}'),
 (V+b[1],V+5.54,'默认位置读回了数据'),(V+5.54,V+b[2],'但{格式检查没过}'),
 (V+b[2],V+b[3],'{这不等于设备坏了}'),
 (V+b[3],V+11.94,'把前后几轮读回的字节{组合校验}'),(V+11.94,V+b[4],'不是{同一时刻的全盘备份}'),
 (V+b[4],V+17.70,'核对发现默认位置{还在启动器范围内}'),(V+17.70,V+19.90,'{后来的离线分析}'),(V+19.90,V+b[5],'给出另一个候选位置'),
 (V+b[5],V+24.30,'再到现场{只读核对}'),(V+24.30,V+26.00,'表里有{六个分区}'),(V+26.00,V+b[6],'{表级校验通过}'),
 (V+b[6],V+29.30,'这不等于能部署'),(V+29.30,V+b[7],'也不代表{已安装或已备份}'),
 (V+b[7],V+33.60,'{事后离线比对}发现'),(V+33.60,V+35.80,'新固件候选布局与现场不同'),(V+35.80,V+37.94,'备份还没完成，所以{先不装}'),
]
CARDS=[  # 解释性标注卡（独立于旁白字幕）：跨轮组合(S4)、离线分析(S5后)、边界(S7)、离线比对(S8)
 (V+b[3],V+b[4],'跨轮组合校验 · 非同一时刻全盘备份'),
 (V+17.70,V+b[5],'事后离线分析 · 未操作设备'),
 (V+b[6],V+b[7],'只读验证 · 未备份 · 未部署'),
 (V+b[7],V+38.44,'事后离线比对 · 未操作设备'),
]
def ft(x):return f'0:{int(x//60):02d}:{x%60:05.2f}'
def gold(x):return re.sub(r'\{([^{}]+)\}',lambda m:r'{\c&H64C8FA&}'+m.group(1)+r'{\c&HFFFFFF&}',x)
header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,Hiragino Sans GB,54,&H00FFFFFF,&H00FFFFFF,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,2.2,1.2,8,40,40,0,1
Style: Badge,Hiragino Sans GB,40,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,1.2,0,8,40,40,0,1
Style: T1,Hiragino Sans GB,74,&H00F8FFF8,&H00F8FFF8,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.0,1.5,8,40,40,0,1
Style: T2,Hiragino Sans GB,96,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.0,1.5,8,40,40,0,1
Style: Note,Hiragino Sans GB,38,&H00E6E6E6,&H00E6E6E6,&H00101B22,&H00000000,1,0,0,0,100,100,0,0,1,1.5,0,8,40,40,0,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
rows=[header,
 r'Dialogue: 0,0:00:00.00,0:00:40.00,Badge,,0,0,0,,{\pos(540,25)}── 织界探索日记 · EP16 ──',
 r'Dialogue: 0,0:00:00.00,0:00:40.00,T1,,0,0,0,,{\pos(540,95)}找到分区表了',
 r'Dialogue: 0,0:00:00.00,0:00:40.00,T2,,0,0,0,,{\pos(540,167)}为什么还不装新固件']
for a,b_,t in CARDS: rows.append(f'Dialogue: 0,{ft(a)},{ft(b_)},Note,,0,0,0,,{{\\pos(540,930)}}{t}')
for a,b_,t in SUBS: rows.append(f'Dialogue: 0,{ft(a)},{ft(b_)},Cap,,0,0,0,,{{\\pos(540,815)}}{gold(t)}')
(p/'字幕16-v004.ass').write_text('\n'.join(rows)+'\n',encoding='utf-8')
# 清晰带遮罩：沿用 v003 定位作起点，各幕新窗口起点不变（210@15、217@17、219@15），待逐幕抽帧复核
for name,rect in [('mask-210',(0,510,1080,710)),('mask-217',(0,305,1080,530)),('mask-219',(0,375,1080,610))]:
 a=Image.new('L',(1080,800),170); ImageDraw.Draw(a).rectangle(rect,fill=0); a=a.filter(ImageFilter.GaussianBlur(30)); im=Image.new('RGBA',(1080,800),(0,0,0,0)); im.putalpha(a); im.save(p/(name+'.png'))
files=[root/'素材/210/Otty.mp4',root/'素材/217/Otty.mp4',root/'素材/219/Otty.mp4',root/'素材/210/MAC-camera-preview.mp4',root/'素材/217/MAC-camera-preview.mp4',root/'素材/219/MAC-camera-preview.mp4',p/'音频/take-v004b-whole.wav',p/'音频/bgm-v1.wav',p.parents[1]/'EP12-新固件做出来了/剪辑/底部装饰-v009.png']
cmd=['ffmpeg','-nostdin','-v','error']
for x in files[:8]: cmd+=['-i',str(x)]
for x in files[8:]+[p/'mask-210.png',p/'mask-217.png',p/'mask-219.png']:cmd+=['-loop','1','-framerate','30','-i',str(x)]
# 三幕边界=句界：Act1 0–8.58(S1–S3,210) | Act2 8.58–22.22(S4–S5,217) | Act3 22.22–40(S6–S8+尾,219)
segments=[(0,3,15.0,8.58),(1,4,17.0,13.64),(2,5,15.0,17.78)]
f=[]
for j,(i,c,start,dur) in enumerate(segments):
 f.append(f'[{c}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=608:342:405:155,scale=1080:608,fps=30,setsar=1[top{j}]')
 f.append(f'[{i}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=1428:1058:12:0[base{j}]')
 rects=([(175,225,265,45),(300,295,270,45),(660,603,745,36),(40,630,610,30)] if j==0 else [(660,342,745,38),(40,369,600,30)])
 boxes=','.join(f'drawbox=x={x}:y={y}:w={w}:h={h}:color=0x101713:t=fill' for x,y,w,h in rects)
 n=round(dur*30);fo=n-60
 f.append(f"[base{j}]{boxes},scale=1080:800,fps=30,setsar=1,setpts=PTS-STARTPTS[raw{j}]")  # 去 zoompan：全宽无横裁
 f.append(f'[{9+j}:v]trim=duration={dur},setpts=PTS-STARTPTS,format=rgba,fade=t=in:st=0.4:d=0.8:alpha=1,fade=t=out:st={fo/30:.3f}:d=0.8:alpha=1[mask{j}]')
 f.append(f'[raw{j}][mask{j}]overlay=0:0:shortest=1[bottom{j}]')
f+=['[top0][top1][top2]concat=n=3:v=1:a=0[top]','[bottom0][bottom1][bottom2]concat=n=3:v=1:a=0[screen]',f'color=c=0x283840:s=1080x1920:r=30:d={T}[base]',f'[base][top]overlay=0:280[b1]',f'[b1][screen]overlay=0:888[b2]',f"[b2][8:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='字幕16-v004.ass'[v]",'[6:a]adelay=500|500,volume=1.15,aresample=44100[voice]',f'[7:a]atrim=0:{T},volume=0.8,afade=t=out:st={T-2:.2f}:d=2,aresample=44100[bgm]','[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]']
cmd+=['-filter_complex',';'.join(f),'-map','[v]','-map','[a]','-t',str(T),'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
subprocess.run(cmd,cwd=p,check=True)
print('rendered',out)
