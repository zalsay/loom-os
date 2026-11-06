#!/usr/bin/env python3
"""EP13 内部试剪 v002：合入用户试听过的 v003 整篇配音；未对齐字幕、未实现重点行聚焦，不可发布。"""
from pathlib import Path
import subprocess
p=Path(__file__).resolve().parent
root=p.parent
prior=p.parents[1]/'EP12-新固件做出来了/剪辑'
out=p/'EP13-配音试剪-v002-不可发布.mp4'
inputs=[root/'素材'/str(n)/'OTTY-screen.mp4' for n in (174,177,178,179)]
inputs += [root/'素材/179/MAC-camera.mp4', p/'音频/take-v003-whole.wav',p/'音频/bgm-v1.wav',prior/'底部装饰-v009.png']
cmd=['ffmpeg','-nostdin','-n','-v','error']
for f in inputs[:6]: cmd+=['-i',str(f)]
cmd+=['-stream_loop','-1','-i',str(inputs[6]),'-loop','1','-framerate','30','-i',str(inputs[7])]
filters=[]
for i,start in enumerate((20,8,8,8)):
 filters.append(f'[{i}:v]trim=start={start}:duration=10,setpts=PTS-STARTPTS,crop=1428:1058:12:0,scale=1080:800,setsar=1,fps=30[v{i}]')
filters += [
 '[v0][v1][v2][v3]concat=n=4:v=1:a=0[screen]',
 '[4:v]trim=start=10:duration=40,setpts=PTS-STARTPTS,crop=608:342:405:145,scale=1080:608,fps=30[top]',
 'color=c=0x283840:s=1080x1920:r=30:d=40[base]',
 '[base][top]overlay=0:280[b1]', '[b1][screen]overlay=0:888[b2]',
 "[b2][7:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='试剪-v002.ass'[v]",
 '[5:a]adelay=500|500,volume=1.15,aresample=44100[voice]',
 '[6:a]atrim=0:40,volume=0.8,afade=t=out:st=38:d=2,aresample=44100[bgm]',
 '[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]']
cmd += ['-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-t','40','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
subprocess.run(cmd,cwd=p,check=True)
