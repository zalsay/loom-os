#!/usr/bin/env python3
"""EP15 内部试剪：真实相机与同场终端；待完整逐帧隐私和用户听感验收。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import re,subprocess
p=Path(__file__).resolve().parent;root=p.parent;out=root/'产物/EP15-主设备紧裁试剪-v004-待审核.mp4'
if out.exists():raise SystemExit('禁止覆盖')
subs=[(0.50,2.10,'设备连着网络'),(2.10,4.18,'电脑却两次没找到{可用串口}'),(4.18,5.92,'自动进入下载模式'),(5.92,7.20,'这次没法验证'),(7.20,9.02,'所以我们停下了　没有刷写'),(9.02,11.00,'后来　在{正式录像之前}'),(11.00,13.06,'手动让设备进入引导模式'),(13.06,14.55,'电脑只读询问了一次'),(14.55,15.54,'{认出了芯片}'),(15.54,17.06,'没有复位或擦写'),(17.06,20.74,'但握手后紧接着的{一次系统检查}'),(20.74,21.78,'没有看到端口'),(22.20,24.20,'整轮仍然标记为{失败}'),(24.20,26.22,'认出芯片只是第一步'),(26.22,28.62,'能否安全部署　还要继续核对')]
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
rows=[header,r'Dialogue: 0,0:00:00.00,0:00:30.00,Badge,,0,0,0,,{\pos(540,25)}── 织界探索日记 · EP15 ──',r'Dialogue: 0,0:00:00.00,0:00:30.00,T1,,0,0,0,,{\pos(540,95)}没找到应用串口',r'Dialogue: 0,0:00:00.00,0:00:30.00,T2,,0,0,0,,{\pos(540,167)}手动引导后只读握手']
for a,b,t in subs:rows.append(f'Dialogue: 0,{ft(a)},{ft(b)},Cap,,0,0,0,,{{\\pos(540,815)}}{gold(t)}')
(p/'字幕15-v004.ass').write_text('\n'.join(rows)+'\n',encoding='utf-8')
for name,rect in [('mask-bottom',(0,675,1080,799)),('mask-mid',(0,330,1080,525)),('mask-result',(0,565,1080,740))]:
 a=Image.new('L',(1080,800),170);ImageDraw.Draw(a).rectangle(rect,fill=0);a=a.filter(ImageFilter.GaussianBlur(30));m=Image.new('RGBA',(1080,800),(0,0,0,0));m.putalpha(a);m.save(p/(name+'.png'))
files=[root/'素材/204/Otty.mp4',root/'素材/208/Otty.mp4',root/'素材/204/MAC-camera-preview.mp4',root/'素材/208/MAC-camera-preview.mp4',p/'音频/take-v002-whole.wav',p/'音频/bgm-v1.wav']
cmd=['ffmpeg','-nostdin','-n','-v','error']
for x in files:cmd+=['-i',str(x)]
cmd += ['-loop','1','-framerate','30','-i',str(p.parents[1]/'EP12-新固件做出来了/剪辑/底部装饰-v009.png')]
for name in ['mask-bottom.png','mask-mid.png','mask-result.png']:cmd+=['-loop','1','-framerate','30','-i',str(p/name)]
segments=[(0,2,5,11),(1,3,3,9.5),(1,3,12.5,9.5)] # (otty, camera, start, duration)
f=[]
for j,(i,c,start,dur) in enumerate(segments):
 # EP12 v009 的等比例 608×342 紧裁；依两轮主设备位置分别定标。
 x,ycam=(405,145) if c==2 else (415,165)
 f.append(f'[{c}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=608:342:{x}:{ycam},scale=1080:608,fps=30,setsar=1[top{j}]')
 f.append(f'[{i}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=1428:1058:12:0,split=2[base{j}][private{j}]')
 # 204 upper region contains host paths/IP; 208 top contains host paths, but its serial port remains a known risk to be reviewed.
 y,h=(40,740) if i==0 else (40,390)
 f.append(f'[private{j}]crop=1428:{h}:0:{y},boxblur=20:3[blur{j}]')
 pan='0' if j==1 else 'ih-ih/zoom-112'
 n=round(dur*30); fo=n-60
 z=f"if(lt(in\\,30)\\,1\\,if(lt(in\\,54)\\,1+0.20*(1-pow(1-(in-30)/24\\,3))\\,if(lt(in\\,{fo})\\,1.20\\,if(lt(in\\,{fo+24})\\,1.20-0.20*pow((in-{fo})/24\\,3)\\,1))))"
 f.append(f"[base{j}][blur{j}]overlay=0:{y}"+(",drawbox=x=303:y=472:w=210:h=32:color=black:t=fill" if i==1 else "")+f",scale=2160:1600,fps=30,zoompan=z='{z}':x='0':y='{pan}':d=1:s=1080x800:fps=30,setsar=1,setpts=PTS-STARTPTS[raw{j}]")
 f.append(f'[{7+j}:v]trim=duration={dur},setpts=PTS-STARTPTS,format=rgba,fade=t=in:st=1:d=0.8:alpha=1,fade=t=out:st={fo/30:.3f}:d=0.8:alpha=1[mask{j}]')
 f.append(f'[raw{j}][mask{j}]overlay=0:0:shortest=1[bottom{j}]')
f+=['[top0][top1][top2]concat=n=3:v=1:a=0[top]','[bottom0][bottom1][bottom2]concat=n=3:v=1:a=0[screen]','color=c=0x283840:s=1080x1920:r=30:d=30[base]','[base][top]overlay=0:280[b1]','[b1][screen]overlay=0:888[b2]',"[b2][6:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='字幕15-v004.ass'[v]",'[4:a]adelay=500|500,volume=1.15,aresample=44100[voice]','[5:a]atrim=0:30,volume=0.8,afade=t=out:st=28:d=2,aresample=44100[bgm]','[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]']
cmd+=['-filter_complex',';'.join(f),'-map','[v]','-map','[a]','-t','30','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
subprocess.run(cmd,cwd=p,check=True)
