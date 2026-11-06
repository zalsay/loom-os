#!/usr/bin/env python3
"""v006 内部试剪：恢复上方设备相机画面，下方仅一个真实模拟终端；设备是旧状态，不代表新固件运行。
未完成逐帧隐私、来源事件与人耳音画验收；不用于发布。"""
from pathlib import Path
import subprocess
p=Path(__file__).resolve().parent; root=p.parent
out=root/'产物/EP13-设备与模拟试剪-v006-待审核.mp4'
inputs=[root/'素材'/str(n)/'OTTY-screen.mp4' for n in (174,177,178,179)]
inputs += [p/'音频/take-v003-whole.wav',p/'音频/bgm-v1.wav',p.parents[1]/'EP12-新固件做出来了/剪辑/底部装饰-v009.png',root/'素材/179/MAC-camera.mp4']
cmd=['ffmpeg','-nostdin','-n','-v','error']
for x in inputs[:6]: cmd += ['-i',str(x)]
cmd += ['-loop','1','-framerate','30','-i',str(inputs[6]),'-i',str(inputs[7])]
# 源 174 48–53 慢放2倍；177 22–28；178 22–29；179 23–36.5。时间和裁切尚需全片人工核查。
filters=[]
for i,(st,dur,slow) in enumerate(((48,5,2),(22,6,1),(22,7,1),(23,13.5,1))):
 filters.append(f'[{i}:v]trim=start={st}:duration={dur},setpts={slow}*(PTS-STARTPTS),crop=1300:420:65:75,scale=1080:348,setsar=1,fps=30[b{i}]')
for i in range(4):
 filters += [f'[b{i}]scale=1080:348,pad=1080:800:0:65:color=0x101917[bb{i}]']
filters += ['[7:v]trim=start=10:duration=36.5,setpts=PTS-STARTPTS,crop=608:342:405:145,scale=1080:608,fps=30[top]', '[bb0][bb1][bb2][bb3]concat=n=4:v=1:a=0[screen]',
 'color=c=0x283840:s=1080x1920:r=30:d=36.5[base]',
 '[base][top]overlay=0:280[b1]', '[b1][screen]overlay=0:888[b2]',
 "[b2][6:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='试剪-v006.ass'[v]",
 '[4:a]adelay=500|500,volume=1.15,aresample=44100[voice]',
 '[5:a]atrim=0:36.5,volume=0.8,afade=t=out:st=34.5:d=2,aresample=44100[bgm]',
 '[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]']
cmd += ['-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-t','36.5','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
subprocess.run(cmd,cwd=p,check=True)
