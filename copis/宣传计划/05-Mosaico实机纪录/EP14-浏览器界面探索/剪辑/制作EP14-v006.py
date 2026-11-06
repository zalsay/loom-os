#!/usr/bin/env python3
"""EP14 v006：上方浏览器模拟、下方同轮终端，整篇take；待完整听审和隐私验收。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import subprocess,re
p=Path(__file__).resolve().parent; root=p.parent
out=root/'产物/EP14-浏览器与终端试剪-v006-待审核.mp4'
if out.exists(): raise SystemExit('已存在，拒绝覆盖')
# 白字/固定亮金，无逐字点亮；初轴来自本地转写，必须再人工逐句试听。
subs=[(0.50,3.24,'屏幕上的界面\u3000还没在{真机}上验证'),(3.24,5.46,'我们先在{浏览器里}试一试'),(6.08,7.24,'第一轮模拟中'),(7.24,9.36,'中文设置入口出现了'),(9.36,12.54,'示例页面打开\u3000又回到了入口'),(13.14,14.30,'画面录下来了'),(14.30,16.84,'但这轮{自动交接超时}'),(17.32,19.08,'不能说自动验证通过'),(19.08,20.52,'另一轮测试'),(20.52,23.56,'我们让程序{自动发送模拟按键}'),(24.16,25.38,'计数变了'),(25.38,28.30,'页面切到设置\u3000又回到主页'),(28.80,30.50,'这些都是电脑上的模拟'),(30.50,32.98,'不是真机手指触控'),(33.58,34.24,'下一步'),(34.24,35.78,'再去设备上验证')]
def ft(x): return f'0:{int(x//60):02d}:{x%60:05.2f}'
def gold(x): return re.sub(r'\{([^{}]+)\}',lambda m:r'{\c&H64C8FA&}'+m.group(1)+r'{\c&HFFFFFF&}',x)
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
lines=[header,r'Dialogue: 0,0:00:00.00,0:00:38.50,Badge,,0,0,0,,{\pos(540,25)}── 织界探索日记 · EP14 ──',r'Dialogue: 0,0:00:00.00,0:00:38.50,T1,,0,0,0,,{\pos(540,95)}真机还没验证',r'Dialogue: 0,0:00:00.00,0:00:38.50,T2,,0,0,0,,{\pos(540,167)}界面先在电脑里动起来']
for a,b,s in subs: lines.append(f'Dialogue: 0,{ft(a)},{ft(b)},Cap,,0,0,0,,{{\\pos(540,1480)}}{gold(s)}')
(p/'字幕14-v006.ass').write_text('\n'.join(lines)+'\n',encoding='utf-8')
# 半透明遮罩突出浏览器模拟屏，位置针对 189/202 左侧区域；不是隐私遮挡。
a=Image.new('L',(1080,800),170); d=ImageDraw.Draw(a); d.rounded_rectangle((175,155,605,625),radius=12,fill=0); a=a.filter(ImageFilter.GaussianBlur(30)); m=Image.new('RGBA',(1080,800),(0,0,0,0));m.putalpha(a);m.save(p/'模拟屏聚焦蒙层-v006.png')
cmd=['ffmpeg','-nostdin','-n','-v','error']
inputs=[root/'素材/189/Safari.mp4',root/'素材/202/Safari.mp4',root/'素材/189/Otty.mp4',root/'素材/202/Otty.mp4',p/'音频/take-v001-whole.wav',p/'音频/bgm-v1.wav']
for f in inputs: cmd += ['-i',str(f)]
cmd += ['-loop','1','-framerate','30','-i',str(p.parents[1]/'EP12-新固件做出来了/剪辑/底部装饰-v009.png')]
for _ in range(8):cmd += ['-loop','1','-framerate','30','-i',str(p/'终端聚焦蒙层-v006.png')]
segments=((0,286,9.2),(0,298,2),(0,308,4.8),(0,313,3),(1,128.5,6),(1,136,2),(1,142,2.5),(0,287,9))
f=[]
for j,(ix,start,dur) in enumerate(segments):
 # 模拟屏按原画比例裁切并放大。图形区是浏览器录屏，不是实体设备屏幕。
 x,y=(180,200) if ix==0 else (200,220)
 f.append(f'[{ix}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=600:338:{x}:{y},scale=1080:608,fps=30,setsar=1[top{j}]')
 # 严格使用同轮 Otty 的相同名义时间窗，素材并行启动仅毫秒级，不宣称帧级同步。
 oi=ix+2
 if ix==0:
  # 隐私和历史错误：189窗口源图 y=50..650 含宿主路径、188旧失败，先模糊再聚焦；不靠蒙层脱敏。
  f.append(f'[{oi}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=1428:1058:12:0,split=2[original{j}][private{j}]')
  f.append(f'[private{j}]crop=1428:600:0:50,boxblur=20:3[blur{j}]')
  f.append(f'[original{j}][blur{j}]overlay=0:50,scale=2160:1600,fps=30[terminal{j}]')
 else:
  f.append(f'[{oi}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=1428:1058:12:0,scale=2160:1600,fps=30[terminal{j}]')
 # 段落过短时按时长收缩入/出场，避免两个阶段重叠。
 n=round(dur*30); fi=15 if dur<=3 else 30; flen=15 if dur<=3 else 24; fo=max(fi+flen,n-flen-8)
 z=f"if(lt(in\\,{fi})\\,1\\,if(lt(in\\,{fi+flen})\\,1+0.25*(1-pow(1-(in-{fi})/{flen}\\,3))\\,if(lt(in\\,{fo})\\,1.25\\,if(lt(in\\,{fo+flen})\\,1.25-0.25*pow((in-{fo})/{flen}\\,3)\\,1))))"
 f.append(f"[terminal{j}]zoompan=z='{z}':x='0':y='ih-ih/zoom-112':d=1:s=1080x800:fps=30,setsar=1,setpts=PTS-STARTPTS[raw{j}]")
 f.append(f'[{7+j}:v]trim=duration={dur},setpts=PTS-STARTPTS,format=rgba,fade=t=in:st={fi/30:.3f}:d={flen/30:.3f}:alpha=1,fade=t=out:st={fo/30:.3f}:d={flen/30:.3f}:alpha=1[mask{j}]')
 f.append(f'[raw{j}][mask{j}]overlay=0:0:shortest=1[bottom{j}]')
f += [''.join(f'[top{j}]' for j in range(8))+'concat=n=8:v=1:a=0[top]', ''.join(f'[bottom{j}]' for j in range(8))+'concat=n=8:v=1:a=0[screen]',
 'color=c=0x283840:s=1080x1920:r=30:d=38.5[base]','[base][top]overlay=0:280[b1]','[b1][screen]overlay=0:888[b2]',
 "[b2][6:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='字幕14-v006.ass'[v]",
 '[4:a]adelay=500|500,volume=1.15,aresample=44100[voice]','[5:a]atrim=0:38.5,volume=0.8,afade=t=out:st=36.5:d=2,aresample=44100[bgm]',
 '[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]']
cmd += ['-filter_complex',';'.join(f),'-map','[v]','-map','[a]','-t','38.5','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
subprocess.run(cmd,cwd=p,check=True)
