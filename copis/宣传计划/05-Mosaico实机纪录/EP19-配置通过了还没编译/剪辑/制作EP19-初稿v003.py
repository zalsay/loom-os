#!/usr/bin/env python3
"""EP19 v003：232 缓存失败 → 233 配置/生成通过 → 233 别名冲突未通过。
233 两幕改为下移取景（源 y≥500），避免整块路径列表占满画面；遮挡与蒙层在面板坐标绘制。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import subprocess
P = Path(__file__).resolve().parent
R = P.parent
OUT = P / 'EP19-初稿-v003-待验收.mp4'
if OUT.exists():
    raise SystemExit('已存在')
T = 19.5
V = 0.5
b = [0.00, 1.53, 2.21, 4.47, 6.55, 8.09, 10.39, 11.19, 13.38, 14.92, 16.52, 18.30]
segs = ['上一轮配置卡在缓存', '这一轮', '我把缓存补上了', '配置和生成都通过了',
        '但接下来检查依赖图', '因为一个别名冲突', '{\\c&H64C8FA&}没有通过',
        '所以这一轮仍然没有编译', '也没有新的固件', '设备上没有动过', '完整备份也还没做']
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
        f'Dialogue: 0,{ft(0)},{ft(T)},Badge,,0,0,0,,{{\\pos(540,25)}}── 织界探索日记 · EP19 ──',
        f'Dialogue: 0,{ft(0)},{ft(T)},T1,,0,0,0,,{{\\pos(540,95)}}配置通过了',
        f'Dialogue: 0,{ft(0)},{ft(T)},T2,,0,0,0,,{{\\pos(540,174)}}还是没编译']
for a, z, t in subs:
    assert a < z, (a, z, t)
    rows.append(f'Dialogue: 0,{ft(a)},{ft(z)},Cap,,0,0,0,,{{\\pos(540,1580)}}{t}')
ass = P / '字幕EP19-v003.ass'
ass.write_text('\n'.join(rows) + '\n', encoding='utf-8')

# 232 全程取景（源 1428x1058），遮挡在源坐标
M232 = [(560, 570, 850, 30), (60, 592, 1340, 30), (60, 614, 900, 30),
        (330, 662, 1070, 30), (500, 684, 860, 30), (380, 707, 1030, 30),
        (620, 728, 780, 30), (60, 952, 230, 30)]
# 233 取景：源 y 起点 500、高 558、宽 753（左对齐），缩放至 1080x800
CX, CY, CH, CW = 40, 500, 558, 753
K = 800 / CH          # 1.4337
def to_panel(y, h=22):
    return max(0, int((y - CY) * K)), max(8, int(h * K))
# 面板坐标下的遮挡（源行 → 面板）
rows233 = [(512, 40, 760), (535, 40, 760), (618, 560, 240), (641, 40, 220),
           (690, 310, 490), (712, 480, 320), (735, 360, 440), (756, 600, 200), (778, 40, 380)]
PANEL233 = []
for sy, sx, sw in rows233:
    py, ph = to_panel(sy, 24)
    px = int((sx - CX) * K)
    pw = int(sw * K)
    PANEL233.append((max(0, px), py, min(1080 - max(0, px), pw), ph))
def boxes(lst):
    return ','.join(f'drawbox=x={x}:y={y}:w={w}:h={h}:color=0x101713:t=fill' for x, y, w, h in lst)
# 聚焦蒙层（面板坐标 1080x800）
BANDS = [(212, 281), (60, 150), (410, 480)]
for j, (y0, y1) in enumerate(BANDS):
    mp = P / f'EP19-聚焦遮罩-v003-{j}.png'
    if mp.exists():
        raise SystemExit('遮罩已存在')
    a = Image.new('L', (1080, 800), 196)
    ImageDraw.Draw(a).rectangle((0, y0, 1079, y1), fill=0)
    a = a.filter(ImageFilter.GaussianBlur(24))
    m = Image.new('RGBA', (1080, 800), (0, 0, 0, 0))
    m.putalpha(a)
    m.save(mp)

src = {'232': R / '素材/232/Otty.mp4', '233': R / '素材/233/Otty.mp4'}
cam = {'232': R / '素材/232/MAC-camera-preview.mp4', '233': R / '素材/233/MAC-camera-preview.mp4'}
voice = P / '试听配音-EP19-final.wav'
bgm = P / 'bgm-v1.wav'
deco = P.parents[1] / 'EP12-新固件做出来了/剪辑/底部装饰-v009.png'
seg = [('232', 118, 6.2), ('233', 148, 6.0), ('233', 148, 6.4)]
inputs = [src['232'], cam['232'], src['233'], cam['233'], voice, bgm]
cmd = ['ffmpeg', '-nostdin', '-v', 'error']
for f in inputs:
    cmd += ['-i', str(f)]
cmd += ['-loop', '1', '-framerate', '30', '-i', str(deco)]
for j in range(3):
    cmd += ['-loop', '1', '-framerate', '30', '-i', str(P / f'EP19-聚焦遮罩-v003-{j}.png')]
idx = {'232': 0, '233': 2}
cidx = {'232': 1, '233': 3}
f = []
for j, (key, start, dur) in enumerate(seg):
    if key == '232':
        f.append(f'[{idx[key]}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,{boxes(M232)},crop=1428:1058:12:0,scale=2160:1600,fps=30,setsar=1[raw{j}]')
    else:
        f.append(f'[{idx[key]}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop={CW}:{CH}:{CX}:{CY},scale=1080:800,fps=30,setsar=1[raw{j}]')
    n = round(dur * 30)
    f.append(f'[{7+j}:v]format=rgba,fade=t=in:st=0.6:d=0.7:alpha=1,fade=t=out:st={dur-1.4}:d=0.7:alpha=1[shade{j}]')
    if key == '232':
        z = f"if(lt(on,30),1,if(lt(on,54),1+0.06*(on-30)/24,if(lt(on,{n-48}),1.06,if(lt(on,{n-24}),1.06-0.06*(on-{n-24})/24,1))))"
        f.append(f"[raw{j}]zoompan=z='{z}':x='(iw-iw/zoom)/2':y='min(ih-ih/zoom,300)':d=1:s=1080x800:fps=30,setsar=1[sh{j}]")
        f.append(f"[sh{j}][shade{j}]overlay=0:0:shortest=1[t{j}]")
    else:
        f.append(f"[raw{j}]{boxes(PANEL233)}[mb{j}]")
        f.append(f"[mb{j}][shade{j}]overlay=0:0[mm{j}]")
        f.append(f"[mm{j}]null[t{j}]")
    f.append(f'[{cidx[key]}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=650:366:395:155,scale=1080:608,fps=30,setsar=1[c{j}]')
# 蒙层淡入淡出：为 232 已叠加，233 直接叠；统一再加一次淡变体覆盖不了，改为对蒙层输入做 fade
f2 = []
for j in range(3):
    pass
f.append('[t0][t1][t2]concat=n=3:v=1:a=0[screen]')
f.append('[c0][c1][c2]concat=n=3:v=1:a=0[camera]')
f.append(f'color=c=0x283840:s=1080x1920:r=30:d={T}[base]')
f.append('[base][camera]overlay=0:280[b1]')
f.append('[b1][screen]overlay=0:888[b2]')
f.append(f"[b2][6:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='{ass.name}'[v]")
f.append('[4:a]adelay=500|500,volume=1.15,aresample=44100[voicea]')
f.append(f'[5:a]aresample=44100,atrim=0:{T},volume=0.8,afade=t=out:st={T-2}:d=2[bgm]')
f.append('[voicea][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]')
cmd += ['-filter_complex', ';'.join(f), '-map', '[v]', '-map', '[a]', '-t', str(T),
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(OUT)]
subprocess.run(cmd, cwd=P, check=True)
print('EP19 v003 已导出:', OUT)
