#!/usr/bin/env python3
"""EP14内部试剪：真实相机+真实浏览器模拟，整篇take；待完整听审和隐私验收。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import subprocess,re
p=Path(__file__).resolve().parent; root=p.parent
out=root/'产物/EP14-浏览器模拟试剪-v005-待审核.mp4'
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
(p/'字幕14-v005.ass').write_text('\n'.join(lines)+'\n',encoding='utf-8')
# 半透明遮罩突出浏览器模拟屏，位置针对 189/202 左侧区域；不是隐私遮挡。
a=Image.new('L',(1080,800),170); d=ImageDraw.Draw(a); d.rounded_rectangle((175,155,605,625),radius=12,fill=0); a=a.filter(ImageFilter.GaussianBlur(30)); m=Image.new('RGBA',(1080,800),(0,0,0,0));m.putalpha(a);m.save(p/'模拟屏聚焦蒙层-v005.png')
cmd=['ffmpeg','-nostdin','-n','-v','error','-i',str(root/'素材/189/Safari.mp4'),'-i',str(root/'素材/202/Safari.mp4'),'-i',str(root/'素材/202/MAC-camera-preview.mp4'),'-i',str(p/'音频/take-v001-whole.wav'),'-i',str(p/'音频/bgm-v1.wav'),'-loop','1','-framerate','30','-i',str(p.parents[1]/'EP12-新固件做出来了/剪辑/底部装饰-v009.png'),'-loop','1','-framerate','30','-i',str(p/'模拟屏聚焦蒙层-v005.png')]
f=[]
# 189: 286–295.2,298–300,308–312.8,313–316; 变换时刻非连续跳切。202:128.5–134.5、136–138、142–144.5；收尾回到189:287–296，均按真实素材跳切。
for j,(ix,start,dur) in enumerate(((0,286,9.2),(0,298,2),(0,308,4.8),(0,313,3),(1,128.5,6),(1,136,2),(1,142,2.5),(0,287,9))):
 f.append(f'[{ix}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,scale=1080:800:force_original_aspect_ratio=decrease,pad=1080:800:(ow-iw)/2:(oh-ih)/2:color=0x101917,setsar=1,fps=30'+f'[s{j}]')
f += ['[s0][s1][s2][s3][s4][s5][s6][s7]concat=n=8:v=1:a=0[browser]',
 "[browser]scale=2160:1600,zoompan=z='if(lt(in\\,45)\\,1\\,if(lt(in\\,69)\\,1+0.12*(1-pow(1-(in-45)/24\\,3))\\,if(lt(in\\,1080)\\,1.12\\,if(lt(in\\,1104)\\,1.12-0.12*pow((in-1080)/24\\,3)\\,1))))':x='0':y='0':d=1:s=1080x800:fps=30,setsar=1[zoom]",
 '[6:v]format=rgba,fade=t=in:st=1.5:d=0.8:alpha=1,fade=t=out:st=36:d=0.8:alpha=1[mask]',
 '[zoom][mask]overlay=0:0:shortest=1[screen]',
 '[2:v]trim=start=120:duration=38.5,setpts=PTS-STARTPTS,crop=600:338:400:125,scale=1080:608,fps=30[top]',
 'color=c=0x283840:s=1080x1920:r=30:d=38.5[base]','[base][top]overlay=0:280[b1]','[b1][screen]overlay=0:888[b2]',
 "[b2][5:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='字幕14-v005.ass'[v]",
 '[3:a]adelay=500|500,volume=1.15,aresample=44100[voice]','[4:a]atrim=0:38.5,volume=0.8,afade=t=out:st=36.5:d=2,aresample=44100[bgm]',
 '[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]']
cmd += ['-filter_complex',';'.join(f),'-map','[v]','-map','[a]','-t','38.5','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
subprocess.run(cmd,cwd=p,check=True)
