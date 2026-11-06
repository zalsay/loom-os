#!/usr/bin/env python3
"""EP16真实视频内部试剪。字幕本地转写辅助定位，仍须听检及全片隐私复核。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import subprocess, re
p=Path(__file__).resolve().parent; root=p.parent
out=root/'产物/EP16-寻找分区表试剪-v001-待审核.mp4'
if out.exists(): raise SystemExit('禁止覆盖')
# 根据本地Whisper单词时间+0.5秒偏移，人工按原文分句；语音一致性仍待试听。
subs=[(0.50,2.86,'上次电脑{认出了设备}'),(2.86,4.62,'接下来　我想先弄清楚'),(4.62,6.98,'它原来的分区布局'),(7.26,9.56,'我从常见的默认位置'),(9.56,10.72,'只读了一次'),(11.22,12.70,'数据读回来了'),(12.90,15.90,'分区表格式却{没有通过检查}'),(16.46,18.22,'我没有急着刷机'),(18.22,20.68,'而是把前后几轮读回的内容'),(20.68,23.56,'在电脑里拼起来　逐步核对'),(24.04,27.58,'这才发现　默认位置还在{启动器里面}'),(28.06,29.68,'后来离线分析'),(29.68,32.22,'又找到了另一个候选位置'),(32.60,34.62,'再做一次只读验证'),(35.06,38.76,'这次现场分区表　{通过了校验}'),(39.14,40.50,'不过　新固件的候选布局'),(40.50,42.82,'和现场不一样'),(43.30,44.86,'备份也还没完成'),(45.40,47.82,'所以现在还不能直接安装')]
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
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
rows=[header,r'Dialogue: 0,0:00:00.00,0:00:49.50,Badge,,0,0,0,,{\pos(540,25)}── 织界探索日记 · EP16 ──',r'Dialogue: 0,0:00:00.00,0:00:49.50,T1,,0,0,0,,{\pos(540,95)}默认位置没找到',r'Dialogue: 0,0:00:00.00,0:00:49.50,T2,,0,0,0,,{\pos(540,167)}查到现场分区表']
for a,b,t in subs: rows.append(f'Dialogue: 0,{ft(a)},{ft(b)},Cap,,0,0,0,,{{\\pos(540,815)}}{gold(t)}')
(p/'字幕16-v001.ass').write_text('\n'.join(rows)+'\n',encoding='utf-8')
for name,rect in [('mask-210',(0,510,1080,710)),('mask-217',(0,305,1080,530)),('mask-219',(0,375,1080,610))]:
 a=Image.new('L',(1080,800),170); ImageDraw.Draw(a).rectangle(rect,fill=0); a=a.filter(ImageFilter.GaussianBlur(30)); im=Image.new('RGBA',(1080,800),(0,0,0,0)); im.putalpha(a); im.save(p/(name+'.png'))
files=[root/'素材/210/Otty.mp4',root/'素材/217/Otty.mp4',root/'素材/219/Otty.mp4',root/'素材/210/MAC-camera-preview.mp4',root/'素材/217/MAC-camera-preview.mp4',root/'素材/219/MAC-camera-preview.mp4',p/'音频/take-v001-whole.wav',p/'音频/bgm-v1.wav',p.parents[1]/'EP12-新固件做出来了/剪辑/底部装饰-v009.png']
cmd=['ffmpeg','-nostdin','-n','-v','error']
for x in files[:8]: cmd+=['-i',str(x)]
for x in files[8:]+[p/'mask-210.png',p/'mask-217.png',p/'mask-219.png']:cmd+=['-loop','1','-framerate','30','-i',str(x)]
segments=[(0,3,15,16.5),(1,4,17,16.1),(2,5,15,16.9)]
f=[]
for j,(i,c,start,dur) in enumerate(segments):
 f.append(f'[{c}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=608:342:405:155,scale=1080:608,fps=30,setsar=1[top{j}]')
 f.append(f'[{i}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=1428:1058:12:0[base{j}]')
 rects=([(175,225,265,45),(300,295,270,45),(660,603,745,36),(40,630,610,30)] if j==0 else [(660,342,745,38),(40,369,600,30)])
 boxes=','.join(f'drawbox=x={x}:y={y}:w={w}:h={h}:color=0x101713:t=fill' for x,y,w,h in rects)
 n=round(dur*30);fo=n-60;z=f"if(lt(in\\,30)\\,1\\,if(lt(in\\,54)\\,1+0.16*(1-pow(1-(in-30)/24\\,3))\\,if(lt(in\\,{fo})\\,1.16\\,if(lt(in\\,{fo+24})\\,1.16-0.16*pow((in-{fo})/24\\,3)\\,1))))"
 pan='ih-ih/zoom-112' if j==0 else 'ih/2-ih/zoom/2'
 f.append(f"[base{j}]{boxes},scale=2160:1600,fps=30,zoompan=z='{z}':x='0':y='{pan}':d=1:s=1080x800:fps=30,setsar=1,setpts=PTS-STARTPTS[raw{j}]")
 f.append(f'[{9+j}:v]trim=duration={dur},setpts=PTS-STARTPTS,format=rgba,fade=t=in:st=1:d=0.8:alpha=1,fade=t=out:st={fo/30:.3f}:d=0.8:alpha=1[mask{j}]')
 f.append(f'[raw{j}][mask{j}]overlay=0:0:shortest=1[bottom{j}]')
f+=['[top0][top1][top2]concat=n=3:v=1:a=0[top]','[bottom0][bottom1][bottom2]concat=n=3:v=1:a=0[screen]','color=c=0x283840:s=1080x1920:r=30:d=49.5[base]','[base][top]overlay=0:280[b1]','[b1][screen]overlay=0:888[b2]',"[b2][8:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='字幕16-v001.ass'[v]",'[6:a]adelay=500|500,volume=1.15,aresample=44100[voice]','[7:a]atrim=0:49.5,volume=0.8,afade=t=out:st=47.5:d=2,aresample=44100[bgm]','[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]']
cmd+=['-filter_complex',';'.join(f),'-map','[v]','-map','[a]','-t','49.5','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
subprocess.run(cmd,cwd=p,check=True)
