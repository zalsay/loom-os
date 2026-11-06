#!/usr/bin/env python3
"""EP12 v003 内部试剪：新增暂定旁白字幕：v005 整篇配音、系列BGM；字幕和隐私未审，不可发布。"""
from pathlib import Path
import subprocess
p=Path(__file__).resolve().parent
out=p/'EP12-配音试剪-v003-不可发布.mp4'
cmd=['ffmpeg','-nostdin','-n','-v','error',
     '-i',str(p/'素材/203/203-相机-原片30到45秒.mov'),
     '-i',str(p/'素材/172/172-终端-原片570到600秒.mov'),
     '-i',str(p/'素材/203/Otty.mp4'),
     '-i',str(p/'音频/take-v005-whole.wav'),
     '-stream_loop','-1','-i',str(p/'音频/bgm-v1.wav')]
f="""[0:v]setpts=2.5*PTS,crop=1056:594:168:70,scale=1080:608,fps=30[top];
[1:v]trim=start=6:duration=18,setpts=PTS-STARTPTS,crop=1428:1058:12:0,scale=1080:800,setsar=1,fps=30[a];
[2:v]trim=start=30:duration=18.5,setpts=PTS-STARTPTS,crop=1428:1058:12:0,scale=1080:800,setsar=1,fps=30[b];
[a][b]concat=n=2:v=1:a=0[screen];
color=c=0x283840:s=1080x1920:r=30:d=36.5[base];
[base][top]overlay=0:0[base1];[base1][screen]overlay=0:608,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='字幕12-内部试剪-v003.ass'[v];
[3:a]adelay=500|500,volume=1.15,aresample=44100[voice];
[4:a]atrim=0:36.5,volume=0.8,afade=t=out:st=34.5:d=2,aresample=44100[bgm];
[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.75:level=disabled[aout]"""
cmd += ['-filter_complex',f,'-map','[v]','-map','[aout]','-t','36.5','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
subprocess.run(cmd,cwd=p,check=True)
