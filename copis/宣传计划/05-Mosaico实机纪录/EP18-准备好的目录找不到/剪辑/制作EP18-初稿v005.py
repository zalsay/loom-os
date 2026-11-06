#!/usr/bin/env python3
"""EP18 内部初稿 v005：含整篇旁白、临时字幕、局部脱敏；未授发布，隐私/听感待用户审查。
源：session226 正式 Otty 与同轮 Mac 相机预览（600s）。关键行：70 项测试、mdns 路径缺失、配置未完成、build_exit 2。
字幕时轴按能量谷与字数比例估计，未逐句听检。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import subprocess
P = Path(__file__).resolve().parent
R = P.parent
OUT = P / 'EP18-初稿-v005-待验收.mp4'
if OUT.exists():
    raise SystemExit('初稿已存在，拒绝覆盖')
# 旁白时间轴：按实测停顿重算，起播偏移 0.5s
T = 25.6
V = 0.5
b = [0.00, 2.23, 3.52, 4.96, 6.92, 8.00, 9.33, 14.12, 14.86, 16.02, 17.66, 19.03, 21.55, 24.17]
segs = [
    '上一轮在电脑副本里准备',
    '卡在了依赖获取',
    '这一轮接着来',
    '七十项电脑端测试',
    '{\\c&H64C8FA&}全部通过',
    '但配置时',
    '工具先把十一个\\N它认为没用的组件目录清掉了',
    '里面就有 {\\c&H64C8FA&}mdns',
    '再要找它',
    '路径已经不在了',
    '{\\c&H64C8FA&}配置没走完',
    '这一轮没有生成最终固件',
    '设备上的效果也还没验证',
]
subs = [(V + b[i], V + b[i + 1], segs[i]) for i in range(len(segs))]
header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,Hiragino Sans GB,50,&H00FFFFFF,&H00FFFFFF,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,2.2,1.2,8,40,40,0,1
Style: Badge,Hiragino Sans GB,40,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,1.2,0,8,40,40,0,1
Style: T1,Hiragino Sans GB,74,&H00F8FFF8,&H00F8FFF8,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.0,1.5,8,40,40,0,1
Style: T2,Hiragino Sans GB,80,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.0,1.5,8,40,40,0,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
def ft(x):
    return f'0:{int(x // 60):02d}:{x % 60:05.2f}'
rows = [header,
        f'Dialogue: 0,{ft(0)},{ft(T)},Badge,,0,0,0,,{{\\pos(540,25)}}── 织界探索日记 · EP18 ──',
        f'Dialogue: 0,{ft(0)},{ft(T)},T1,,0,0,0,,{{\\pos(540,95)}}刚准备的目录',
        f'Dialogue: 0,{ft(0)},{ft(T)},T2,,0,0,0,,{{\\pos(540,174)}}怎么又不见了？']
for a, z, t in subs:
    assert a < z, (a, z, t)
    rows.append(f'Dialogue: 0,{ft(a)},{ft(z)},Cap,,0,0,0,,{{\\pos(540,1580)}}{t}')
ass = P / '字幕EP18-初稿v005.ass'
ass.write_text('\n'.join(rows) + '\n', encoding='utf-8')
# 隐私遮挡（源坐标 1452x1058）：仅覆盖本机路径、构建目录与窗口标签，保留错误语义与结果字段。
priv = [
    (350, 78, 1040, 30), (60, 100, 660, 30), (350, 120, 1040, 30), (60, 142, 660, 30),
    (185, 255, 1200, 34), (95, 322, 1300, 52), (150, 522, 1150, 32),
    (600, 655, 800, 30), (60, 682, 1400, 32), (330, 728, 1070, 32), (500, 748, 850, 32),
    (330, 772, 1070, 32), (640, 794, 760, 32), (60, 818, 420, 32), (60, 955, 230, 30),
]

# 聚焦遮罩（EP05 式：正常→推入保持→退出），源坐标系 1428x1058；清晰带覆盖当幕关键行
BANDS = [(815, 895), (250, 410), (848, 962)]
for j, (y0, y1) in enumerate(BANDS):
    mp = P / f'EP18-聚焦遮罩-v005-{j}.png'
    if mp.exists():
        raise SystemExit('遮罩已存在')
    alpha = Image.new('L', (1428, 1058), 170)
    ImageDraw.Draw(alpha).rectangle((0, y0, 1428, y1), fill=0)
    alpha = alpha.filter(ImageFilter.GaussianBlur(28))
    m = Image.new('RGBA', (1428, 1058), (0, 0, 0, 0))
    m.putalpha(alpha)
    m.save(mp)

mask = ','.join(f'drawbox=x={x}:y={y}:w={w}:h={h}:color=0x101713:t=fill' for x, y, w, h in priv)
tab = 'drawbox=x=60:y=952:w=230:h=30:color=0x101713:t=fill'
cam = R / '素材/226/MAC-camera-preview.mp4'
osrc = R / '素材/226/Otty.mp4'
voice = P / '试听配音-EP18-v001.wav'
bgm = P / 'bgm-v1.wav'
deco = P.parents[1] / 'EP12-新固件做出来了/剪辑/底部装饰-v009.png'
seg = [(10, 8.8, False), (40, 8.6, True), (40, 8.2, True)]
f = []
inputs = [str(osrc)]
if cam.exists():
    inputs.append(str(cam))
cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-i', str(osrc)]
if cam.exists():
    cmd += ['-i', str(cam)]
cmd += ['-i', str(voice), '-i', str(bgm)]
cmd += ['-loop', '1', '-framerate', '30', '-i', str(deco)]
for j in range(3):
    cmd += ['-loop', '1', '-framerate', '30', '-i', str(P / f'EP18-聚焦遮罩-v005-{j}.png')]
for j, (start, dur, hid) in enumerate(seg):
    if j == 0:
        vt = f'trim=start={start}:duration=6,setpts=PTS-STARTPTS,fps=30,loop=loop=2:size=180:start=0,trim=duration={dur},setpts=PTS-STARTPTS'
        f.append(f'[0:v]{vt},{tab},crop=1428:1058:12:0,scale=2160:1600,fps=30,setsar=1[raw{j}]')
    else:
        f.append(f'[0:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,{mask},crop=1428:1058:12:0,scale=2160:1600,fps=30,setsar=1[raw{j}]')
    f.append(f'[{5+j}:v]scale=2160:1600,format=rgba,fade=t=in:st=0.6:d=0.7:alpha=1,fade=t=out:st={dur-1.4}:d=0.7:alpha=1,trim=duration={dur},setpts=PTS-STARTPTS[shade{j}]')
    f.append(f'[raw{j}][shade{j}]overlay=0:0:shortest=1[tm{j}]')
    f.append(f'[tm{j}]null[t{j}]')
    n = round(dur * 30)
    z = f"if(lt(on,30),1,if(lt(on,54),1+0.10*(on-30)/24,if(lt(on,{n-48}),1.10,if(lt(on,{n-24}),1.10-0.10*(on-{n-24})/24,1))))"
    yk = 520 if j == 0 else (150 if j == 1 else 980)
    f.append(f"[t{j}]zoompan=z='{z}':x='(iw-iw/zoom)/2':y='min(ih-ih/zoom,{yk})':d=1:s=1080x800:fps=30,setsar=1[z{j}]")
    if cam.exists():
        f.append(f'[1:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=650:366:395:155,scale=1080:608,fps=30,setsar=1[c{j}]')
f.append('[z0][z1][z2]concat=n=3:v=1:a=0[screen]')
if cam.exists():
    f.append('[c0][c1][c2]concat=n=3:v=1:a=0[camera]')
    f.append(f'color=c=0x283840:s=1080x1920:r=30:d={T}[base]')
    f.append('[base][camera]overlay=0:280[b1]')
    f.append('[b1][screen]overlay=0:888[b2]')
else:
    f.append(f'color=c=0x283840:s=1080x1920:r=30:d={T}[base]')
    f.append('[base][screen]overlay=0:280[b2]')
f.append(f"[b2][4:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='{ass.name}'[v]")
f.append(f'[2:a]adelay=500|500,volume=1.15,aresample=44100[voice]')
f.append(f'[3:a]aresample=44100,atrim=0:{T},volume=0.8,afade=t=out:st={T-2}:d=2[bgm]')
f.append('[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]')
cmd += ['-filter_complex', ';'.join(f), '-map', '[v]', '-map', '[a]', '-t', str(T),
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(OUT)]
subprocess.run(cmd, cwd=P, check=True)
print('初稿已导出（字幕未听检、隐私未验收）:', OUT)
