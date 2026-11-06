#!/usr/bin/env python3
"""EP13 v007 内部试剪：恢复完整 OTTY 窗口、模仿 EP05 正常-推入-保持-退出聚焦；
取景及聚焦仅供审查，含敏感路径和174错误自动判定，未经隐私与事实验收不得发布。"""
from pathlib import Path
import subprocess
p=Path(__file__).resolve().parent; root=p.parent
out=root/'产物/EP13-完整终端聚焦试剪-v007-待审核.mp4'
inputs=[root/'素材'/str(n)/'OTTY-screen.mp4' for n in (174,177,178,179)]
inputs += [p/'音频/take-v003-whole.wav',p/'音频/bgm-v1.wav',p.parents[1]/'EP12-新固件做出来了/剪辑/底部装饰-v009.png',root/'素材/179/MAC-camera.mp4']
cmd=['ffmpeg','-nostdin','-n','-v','error']
for x in inputs[:6]: cmd += ['-i',str(x)]
cmd += ['-loop','1','-framerate','30','-i',str(inputs[6]),'-i',str(inputs[7])]
filters=[]
for i,(st,dur,slow,center_y) in enumerate(((48,5,2,250),(22,6,1,750),(22,7,1,750),(23,13.5,1,900))):
 n=round(dur*slow*30); fi=30; fo=n-60
 z=(f'if(lt(in\\,{fi})\\,1\\,if(lt(in\\,{fi+24})\\,1+0.20*(1-pow(1-(in-{fi})/24\\,3))\\,if(lt(in\\,{fo})\\,1.20\\,if(lt(in\\,{fo+24})\\,1.20-0.20*pow((in-{fo})/24\\,3)\\,1))))')
 # 出入 24 帧，定位到左侧源行，坐标仅为画面试验、并不声称每幕为关键结果。
 filters.append(f'[{i}:v]trim=start={st}:duration={dur},setpts={slow}*(PTS-STARTPTS),crop=1428:1058:12:0,scale=2160:1600,fps=30,zoompan=z=\'{z}\':x=\'0\':y=\'max(0\\,min(ih-ih/zoom\\,{center_y}-ih/zoom/2))\':d=1:s=1080x800:fps=30,setsar=1,setpts=PTS-STARTPTS[bb{i}]')
filters += ['[7:v]trim=start=10:duration=36.5,setpts=PTS-STARTPTS,crop=608:342:405:145,scale=1080:608,fps=30[top]', '[bb0][bb1][bb2][bb3]concat=n=4:v=1:a=0[screen]',
 'color=c=0x283840:s=1080x1920:r=30:d=36.5[base]', '[base][top]overlay=0:280[b1]', '[b1][screen]overlay=0:888[b2]',
 "[b2][6:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='试剪-v006.ass'[v]",
 '[4:a]adelay=500|500,volume=1.15,aresample=44100[voice]', '[5:a]atrim=0:36.5,volume=0.8,afade=t=out:st=34.5:d=2,aresample=44100[bgm]',
 '[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]']
cmd += ['-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-t','36.5','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
subprocess.run(cmd,cwd=p,check=True)
