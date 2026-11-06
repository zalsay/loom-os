#!/usr/bin/env python3
"""EP11 v007: per-result-row zoom and feathered focus, with verified source windows."""
from pathlib import Path
import subprocess

base = Path('/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP11-正在更新固件')
d = base / '剪辑'
s = d / '素材'
output = base / '产物/EP11-方案A-内部样片-v007.mp4'
ass = d / '字幕11-内部样片-v007.ass'
if output.exists() or ass.exists():
    raise SystemExit('输出已存在，停止以保护已有文件')

# Timings come from take-4. Keep the approved wording and the verified facts.
subs = [
 (0.50, 3.26, '文件传回来了，设备里为什么还看不见？'),
 (4.24, 8.62, '我在做新固件，相关触摸检查通过了，\\N但没有真的点过设备。'),
 (9.82, 12.52, '第一回，等了快十分钟，\\N还没开始编译。'),
 (13.32, 18.02, '第二回，接着上回保留的一部分资料做，\\N又因为连接问题停了。'),
 (18.94, 24.14, '还没做成，但进度没丢。\\N你猜，下一次能做成吗？'),
 (25.02, 27.60, '后来新固件构建成功，\\N但还没刷进设备，也没经过实机验证。'),
]

def ts(x):
    return f'0:{int(x // 60):02d}:{x % 60:05.2f}'

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
Dialogue: 0,0:00:00.00,0:00:29.00,Badge,,0,0,0,,{\pos(540,56)}── 织界创造日记 · EP11 ──
Dialogue: 0,0:00:00.00,0:00:29.00,T1,,0,0,0,,{\pos(540,118)}设备里为什么还看不见
Dialogue: 0,0:00:00.00,0:00:29.00,T2,,0,0,0,,{\pos(540,184)}新固件，做到第二轮
'''
for a, b, text in subs:
    header += f'Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\pos(540,1530)}}{text}\n'
for a, b, text in [
    (0.0, 4.0, '阶段回顾：两次尝试的记录'),
    (4.0, 9.6, '离线检查通过，设备未实际点击'),
    (9.6, 13.0, '第一轮：时间到，尚未开始编译'),
    (13.0, 18.4, '第二轮：复用部分资料，连接失败'),
    (18.4, 24.5, '当时：未刷写设备'),
    (24.5, 29.0, '后续：构建成功，未刷设备及实机验证'),
]:
    header += f'Dialogue: 1,{ts(a)},{ts(b)},Info,,0,0,0,,{{\\pos(540,1100)}}{text}\n'
ass.write_text(header, encoding='utf-8')

from PIL import Image, ImageDraw

# Result row coordinates in OTTY's native 1452x1058 frame. The bands are
# deliberately local: each scene focuses its own ending line, not the same
# bottom strip. Feather runs inward from both sides of the clear band.
OTTY_W, OTTY_H = 1452, 1058
rows = {
    # 164: INPUT_TAP_OFFLINE_PASS is the penultimate green line.
    '168': (820, 940),
    # 169: BUILD_DRIVER_EXIT=2 / task ended; focus the last three green lines.
    '169': (858, 980),
    # 164: INPUT_TAP_OFFLINE_PASS is the penultimate green line.
    '164': (880, 945),
}
masks = {}
for name, (clear_top, clear_bottom) in rows.items():
    path = d / f'otty-focus-mask-v007-{name}.png'
    mask = Image.new('RGBA', (1080, 800), (0, 0, 0, 174))
    # The OTTY layer is scaled from 1058 to 1600 and displayed in 800px.
    # Convert source rows to display rows, then feather by 24px on each side.
    scale = 800 / OTTY_H
    top = round(clear_top * scale)
    bottom = round(clear_bottom * scale)
    feather = 24
    for y in range(800):
        if top <= y <= bottom:
            alpha = 0
        elif abs(y - top) <= feather:
            alpha = round(174 * (top - y) / feather)
        elif abs(y - bottom) <= feather:
            alpha = round(174 * (y - bottom) / feather)
        else:
            alpha = 174
        ImageDraw.Draw(mask).line((0, y, 1080, y), fill=(0, 0, 0, max(0, min(174, alpha))))
    mask.save(path)
    masks[name] = (path, top, bottom)

def zoom(zoom_start, hold_start, hold_end, restore_end, cx, cy, zoom_max=1.48):
    """Normal -> zoom -> hold -> restore, all in final timeline frames."""
    z = (f"if(lt(in\\,{zoom_start}),1,if(lt(in\\,{hold_start}),"
         f"1+{zoom_max - 1}*(1-pow(1-(in-{zoom_start})/{hold_start - zoom_start}\\,3)),"
         f"if(lt(in\\,{hold_end}),{zoom_max},if(lt(in\\,{restore_end}),"
         f"{zoom_max}-{zoom_max - 1}*pow((in-{hold_end})/{restore_end - hold_end}\\,3),1))))")
    # zoompan works on the scaled 2160x1600 layer. Clamp both axes so the
    # target row remains fully inside the viewport throughout the hold.
    x = f"max(0\\,min(iw-iw/zoom\\,{cx}*iw-iw/zoom/2))"
    y = f"max(0\\,min(ih-ih/zoom\\,{cy}*ih-ih/zoom/2))"
    return f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s=1080x800:fps=30"

# Use independent source windows for the three evidence shots. The camera
# stays on the device; terminal clips carry their own result-row focus.
filt = f'''[0:v]trim=start=200:duration=29,setpts=PTS-STARTPTS,crop=835:470:312:90,scale=1080:608,fps=30[top];
[1:v]trim=start=595:duration=5,setpts=PTS-STARTPTS,crop=1428:1058:12:0,scale=2160:1600,fps=30,{zoom(21,45,111,135,0.50,0.83)},setsar=1[s168];
[2:v]trim=start=580:duration=20,setpts=PTS-STARTPTS,crop=1428:1058:12:0,scale=2160:1600,fps=30,{zoom(402,426,540,564,0.50,0.83)},setsar=1[s169];
[3:v]trim=start=58:duration=7,setpts=PTS-STARTPTS,crop=1428:1058:12:0,scale=2160:1600,fps=30,{zoom(141,165,240,264,0.50,0.83)},setsar=1[s164];
[6:v]format=rgba,fade=t=in:st=0.5:d=0.8:alpha=1,fade=t=out:st=3.6:d=0.8:alpha=1[m168];
[7:v]format=rgba,fade=t=in:st=13.4:d=0.8:alpha=1,fade=t=out:st=17.8:d=0.8:alpha=1[m169];
[8:v]format=rgba,fade=t=in:st=4.7:d=0.8:alpha=1,fade=t=out:st=7.6:d=0.8:alpha=1[m164];
[s168][m168]overlay=0:0:enable='between(t,0.5,4.4)'[s168m];
[s169][m169]overlay=0:0:enable='between(t,13.4,18.6)'[s169m];
[s164][m164]overlay=0:0:enable='between(t,4.7,8.4)'[s164m];
color=c=0x283840:s=1080x1920:r=30:d=29[base];
[base][top]overlay=0:0[a];[a][s168m]overlay=0:608:enable='between(t,0.5,4.4)'[b];
[b][s164m]overlay=0:608:enable='between(t,4.7,8.4)'[c];[c][s169m]overlay=0:608:enable='between(t,13.4,18.6)'[d];
[d]drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='{ass}'[v];
[4:a]adelay=500|500,volume=1.15,aresample=44100[voice];
[5:a]atrim=0:29,volume=0.8,afade=t=out:st=27:d=2,aresample=44100[bgm];
[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[aout]'''

cmd = [
    'ffmpeg', '-nostdin', '-n', '-v', 'error',
    '-i', str(s / '2026-10-27-ep04-native-build-168/MAC-camera.mp4'),
    '-i', str(s / '2026-10-27-ep04-native-build-168/OTTY-screen.mp4'),
    '-i', str(s / '2026-10-27-ep04-native-build-cache-169/OTTY-screen.mp4'),
    '-i', str(s / '2026-10-27-ep04-input-tap-bridge-retest-164/OTTY-screen.mp4'),
    '-i', str(d / '音频/take-4-narration.wav'),
    '-i', str(d / '音频/bgm-ep11-v1.wav'),
    '-loop', '1', '-framerate', '30', '-t', '4.0', '-i', str(masks['168'][0]),
    '-loop', '1', '-framerate', '30', '-t', '5.0', '-i', str(masks['169'][0]),
    '-loop', '1', '-framerate', '30', '-t', '3.5', '-i', str(masks['164'][0]),
    '-filter_complex', filt, '-map', '[v]', '-map', '[aout]', '-t', '29',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(output),
]
subprocess.run(cmd, check=True)
print('已渲染内部样片:', output)
for name, (_, top, bottom) in masks.items():
    print(f'{name}: clear display band {top}-{bottom}')
