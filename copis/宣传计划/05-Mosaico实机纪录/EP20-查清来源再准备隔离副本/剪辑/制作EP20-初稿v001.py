#!/usr/bin/env python3
"""EP20 v001：239 来源核对与离线清单预演 → 244 真实隔离准备与读回（仍未求解/未编译）。
旁白整篇单次合成后 atempo 1.19；字幕按实测停顿映射；含聚焦蒙层与隐私遮挡。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import subprocess
P = Path(__file__).resolve().parent
R = P.parent
OUT = P / 'EP20-初稿-v001-待验收.mp4'
if OUT.exists():
    raise SystemExit('已存在')
T = 25.5
V = 0.5
b = [0.000, 2.112, 3.501, 6.956, 10.862, 12.270, 14.031, 16.087, 18.368, 20.454, 22.278, 24.343]
segs = ['这一轮先把依赖来源查清楚', '再准备隔离副本',
        '来源核对和离线清单预演都通过了', '一百六十二项电脑端测试也通过',
        '真正做隔离准备时', '一百八十五项测试通过', '准备和读回也完成',
        '但这只是准备好了', '还没有真正求解依赖图', '也没有配置或编译',
        '{\\c&H64C8FA&}设备上还是没动过']
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
        f'Dialogue: 0,{ft(0)},{ft(T)},Badge,,0,0,0,,{{\\pos(540,25)}}── 织界探索日记 · EP20 ──',
        f'Dialogue: 0,{ft(0)},{ft(T)},T1,,0,0,0,,{{\\pos(540,95)}}查清来源',
        f'Dialogue: 0,{ft(0)},{ft(T)},T2,,0,0,0,,{{\\pos(540,174)}}先准备副本']
for a, z, t in subs:
    assert a < z, (a, z, t)
    rows.append(f'Dialogue: 0,{ft(a)},{ft(z)},Cap,,0,0,0,,{{\\pos(540,1580)}}{t}')
ass = P / '字幕EP20-v001.ass'
ass.write_text('\n'.join(rows) + '\n', encoding='utf-8')
MASK = [(60, 955, 230, 30)]
def boxes(lst):
    return ','.join(f'drawbox=x={x}:y={y}:w={w}:h={h}:color=0x101713:t=fill' for x, y, w, h in lst)
BANDS = [(672, 862), (672, 736), (782, 892)]
for j, (y0, y1) in enumerate(BANDS):
    mp = P / f'EP20-聚焦遮罩-v001-{j}.png'
    if mp.exists():
        raise SystemExit('遮罩已存在')
    a = Image.new('L', (1428, 1058), 196)
    ImageDraw.Draw(a).rectangle((0, y0, 1428, y1), fill=0)
    a = a.filter(ImageFilter.GaussianBlur(26))
    m = Image.new('RGBA', (1428, 1058), (0, 0, 0, 0))
    m.putalpha(a)
    m.save(mp)
src = {'239': R / '素材/239/Otty.mp4', '244': R / '素材/244/Otty.mp4'}
cam = {'239': R / '素材/239/MAC-camera-preview.mp4', '244': R / '素材/244/MAC-camera-preview.mp4'}
voice = P / '试听配音-EP20-final.wav'
bgm = P / 'bgm-v1.wav'
deco = P.parents[1] / 'EP12-新固件做出来了/剪辑/底部装饰-v009.png'
seg = [('239', 100, 8.4), ('244', 150, 8.2), ('244', 150, 8.9)]
inputs = [src['239'], cam['239'], src['244'], cam['244'], voice, bgm]
cmd = ['ffmpeg', '-nostdin', '-v', 'error']
for f in inputs:
    cmd += ['-i', str(f)]
cmd += ['-loop', '1', '-framerate', '30', '-i', str(deco)]
for j in range(3):
    cmd += ['-loop', '1', '-framerate', '30', '-i', str(P / f'EP20-聚焦遮罩-v001-{j}.png')]
idx = {'239': 0, '244': 2}
cidx = {'239': 1, '244': 3}
f = []
for j, (key, start, dur) in enumerate(seg):
    f.append(f'[{idx[key]}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,{boxes(MASK)},crop=1428:1058:12:0,scale=2160:1600,fps=30,setsar=1[raw{j}]')
    f.append(f'[{7+j}:v]scale=2160:1600,format=rgba,fade=t=in:st=0.6:d=0.7:alpha=1,fade=t=out:st={dur-1.4}:d=0.7:alpha=1,trim=duration={dur},setpts=PTS-STARTPTS[shade{j}]')
    f.append(f'[raw{j}][shade{j}]overlay=0:0:shortest=1[tm{j}]')
    n = round(dur * 30)
    z = f"if(lt(on,30),1,if(lt(on,54),1+0.08*(on-30)/24,if(lt(on,{n-48}),1.08,if(lt(on,{n-24}),1.08-0.08*(on-{n-24})/24,1))))"
    yk = 640 if j == 0 else (560 if j == 1 else 700)
    f.append(f"[tm{j}]zoompan=z='{z}':x='(iw-iw/zoom)/2':y='min(ih-ih/zoom,{yk})':d=1:s=1080x800:fps=30,setsar=1[z{j}]")
    f.append(f'[{cidx[key]}:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=650:366:395:155,scale=1080:608,fps=30,setsar=1[c{j}]')
f.append('[z0][z1][z2]concat=n=3:v=1:a=0[screen]')
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
print('EP20 初稿已导出:', OUT)
