#!/usr/bin/env python3
"""EP11 内部试剪：单次整篇配音，阶段记录与后续结果分离；未完成隐私审查。"""
from pathlib import Path
import subprocess

base = Path('/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP11-正在更新固件')
d = base / '剪辑'
s = d / '素材'
output = base / '产物/EP11-方案A-内部样片-v003.mp4'
ass = d / '字幕11-内部样片-v003.ass'
if output.exists() or ass.exists():
    raise SystemExit('输出已存在，停止以保护已有文件')
# 单次 take 的句间静音以 -33dB / 0.16s 检测，时间包含 0.5 秒混音偏移。
subs = [
 (0.50,3.07,'文件传回来了，设备里为什么还看不见？'),
 (3.68,8.01,'我在做新固件，相关触摸检查通过了，\\N但没有真的点过设备。'),
 (8.96,11.50,'第一回，等了快十分钟，\\N还没开始编译。'),
 (12.11,16.19,'第二回，接着上回保留的一部分资料做，\\N又因为连接问题停了。'),
 (17.13,21.21,'还没做成，但进度没丢。\\N你猜，下一次能做成吗？'),
 (22.52,26.62,'后来固件构建成功，但还没刷进设备，\\N也没经过实机验证。'),
]
def ts(x):
    return f'0:{int(x//60):02d}:{x%60:05.2f}'
header = r'''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Badge,Hiragino Sans GB,40,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,1.2,0,8,40,40,0,1
Style: T1,Hiragino Sans GB,74,&H00F8FFF8,&H00F8FFF8,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,2,1.5,8,40,40,0,1
Style: T2,Hiragino Sans GB,96,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,2,1.5,8,40,40,0,1
Style: Cap,Hiragino Sans GB,48,&H00FFFFFF,&H00FFFFFF,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,3,2,0,2,40,40,0,1
Style: Info,Hiragino Sans GB,36,&H00E0E6E8,&H00E0E6E8,&H00151C20,&H00151C20,1,0,0,0,100,100,0,0,3,12,0,2,40,40,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:27.50,Badge,,0,0,0,,{\pos(540,56)}── 织界创造日记 · EP11 ──
Dialogue: 0,0:00:00.00,0:00:27.50,T1,,0,0,0,,{\pos(540,118)}设备里为什么还看不见
Dialogue: 0,0:00:00.00,0:00:27.50,T2,,0,0,0,,{\pos(540,184)}新固件，做到第二轮
'''
for a,b,text in subs:
    header += f'Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\pos(540,1530)}}{text}\n'
for a,b,text in [(0,3.1,'阶段记录：第二轮中途停止'),(3.1,8.9,'说明：离线检查通过，设备未实际点击'),(8.9,12.1,'记录：第一轮时间到，尚未开始编译'),(12.1,17.1,'记录：复用部分资料，连接失败'),(17.1,22.5,'阶段记录：进度保留，未刷写'),(22.5,27.5,'后续：固件构建成功，未刷设备及实机验证')]:
    header += f'Dialogue: 1,{ts(a)},{ts(b)},Info,,0,0,0,,{{\\pos(540,1100)}}{text}\n'
ass.write_text(header, encoding='utf-8')
s169=s/'2026-10-27-ep04-native-build-cache-169'
s164=s/'2026-10-27-ep04-input-tap-bridge-retest-164'
# 以两段录屏底部实际结果行定位；蒙层只作用于 OTTY 区域。
# 164: INPUT_TAP_OFFLINE_PASS；169: BUILD_DRIVER_EXIT=2。
from PIL import Image
mask_path = d / 'otty-focus-mask-v003.png'
mask = Image.new('RGBA', (1080,800), (0,0,0,170))
for y in range(615,800):
    a = round(170 * max(0, min(1, (675-y)/60)))
    for x in range(1080): mask.putpixel((x,y),(0,0,0,a))
mask.save(mask_path)

def zoom(start, finish):
    # 0.8 秒渐入，保持，0.8 秒渐出；向左下方结果行聚焦。
    z = (f"if(lt(in\\,{start}),1,if(lt(in\\,{start+24}),"
         f"1+0.3*(1-pow(1-(in-{start})/24\\,3)),"
         f"if(lt(in\\,{finish}),1.3,if(lt(in\\,{finish+24}),"
         f"1.3-0.3*pow((in-{finish})/24\\,3),1))))")
    return f"zoompan=z='{z}':x='0':y='ih-ih/zoom':d=1:s=1080x800:fps=30"

# 164 局部时间 1.0–5.6 秒；169 全片时间 12.2–17.1 秒。
filt = f'''[0:v]trim=start=200:duration=27.5,setpts=PTS-STARTPTS,crop=835:470:312:90,scale=1080:608,fps=30[top];
[1:v]trim=start=570:duration=27.5,setpts=PTS-STARTPTS,crop=1428:1058:12:0,scale=2160:1600,fps=30,{zoom(366,489)},setsar=1[screen1];
[2:v]trim=start=55:duration=6,setpts=PTS-STARTPTS,crop=1428:1058:12:0,scale=2160:1600,fps=30,{zoom(30,144)},setsar=1[screen2];
[5:v]format=rgba,fade=t=in:st=12.2:d=0.8:alpha=1,fade=t=out:st=16.3:d=0.8:alpha=1[m1];
[6:v]format=rgba,fade=t=in:st=1.0:d=0.8:alpha=1,fade=t=out:st=4.8:d=0.8:alpha=1[m2];
[screen1][m1]overlay=0:0:enable='between(t,12.2,17.1)'[screen1m];
[screen2][m2]overlay=0:0:enable='between(t,1.0,5.6)',setpts=PTS+3.1/TB[screen2m];
color=c=0x283840:s=1080x1920:r=30:d=27.5[base];
[base][top]overlay=0:0[a];[a][screen1m]overlay=0:608[b];[b][screen2m]overlay=0:608:enable='between(t,3.1,8.9)'[c];
[c]drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='{ass}'[v];
[3:a]adelay=500|500,volume=1.15,aresample=44100[voice];
[4:a]atrim=0:27.5,volume=0.8,afade=t=out:st=25.5:d=2,aresample=44100[bgm];
[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[aout]'''
cmd=['ffmpeg','-nostdin','-n','-v','error','-i',str(s169/'MAC-camera.mp4'),'-i',str(s169/'OTTY-screen.mp4'),'-i',str(s164/'OTTY-screen.mp4'),'-i',str(d/'音频/take-1-narration.wav'),'-i',str(d/'音频/bgm-ep11-v1.wav'),'-loop','1','-framerate','30','-t','27.5','-i',str(mask_path),'-loop','1','-framerate','30','-t','6','-i',str(mask_path),'-filter_complex',filt,'-map','[v]','-map','[aout]','-t','27.5','-c:v','libx264','-preset','veryfast','-crf','20','-c:a','aac','-b:a','128k','-movflags','+faststart',str(output)]
subprocess.run(cmd,check=True)
print('已渲染内部样片:',output)
