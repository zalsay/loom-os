#!/usr/bin/env python3
"""EP22 v001：285 真实终端（前 9.5s）+ 动效段（9.5–22.0s，占终端面板区），相机全程实拍。
旁白单次合成后 atempo 0.80 放缓到 4.6 字/秒；字幕按实测停顿映射。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import subprocess

P = Path(__file__).resolve().parent
R = P.parent
OUT = P / 'EP22-初稿-v001-待验收.mp4'
if OUT.exists():
    raise SystemExit('已存在')
T = 22.0
V = 0.5
REAL = 9.5
b = [0.000, 2.07, 2.81, 4.84, 5.77, 6.88, 7.81, 9.35, 10.27, 11.94, 15.70, 16.44, 18.57, 20.06]
segs = ['一千二百五十三项测试', '{\\c&H64C8FA&}全部通过',
        '可第一次真正去打包界面', '还是失败了', '二十一次打包', '二十次成功', '{\\c&HFF9678&}一次退出码二',
        '原因很具体', '配置按运行目录生成', '字体却按配置文件所在的目录去找',
        '测试通过', '{\\c&HFF9678&}不等于打包能过', '这一轮也没碰设备']
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
        f'Dialogue: 0,{ft(0)},{ft(T)},Badge,,0,0,0,,{{\\pos(540,25)}}── 织界探索日记 · EP22 ──',
        f'Dialogue: 0,{ft(0)},{ft(T)},T1,,0,0,0,,{{\\pos(540,95)}}一千多项测试都过了',
        f'Dialogue: 0,{ft(0)},{ft(T)},T2,,0,0,0,,{{\\pos(540,174)}}打包还是失败']
for a, z, t in subs:
    assert a < z, (a, z, t)
    rows.append(f'Dialogue: 0,{ft(a)},{ft(z)},Cap,,0,0,0,,{{\\pos(540,1580)}}{t}')
ass = P / '字幕EP22-v001.ass'
ass.write_text('\n'.join(rows) + '\n', encoding='utf-8')

MASK = [(60, 92, 1330, 54), (60, 952, 250, 34)]
def boxes(lst):
    return ','.join(f'drawbox=x={x}:y={y}:w={w}:h={h}:color=0x101713:t=fill' for x, y, w, h in lst)
# 实拍段聚焦蒙层（源坐标），清晰带对准 START/END 三行
mp = P / 'EP22-聚焦遮罩-v001.png'
if not mp.exists():
    a = Image.new('L', (1428, 1058), 196)
    ImageDraw.Draw(a).rectangle((0, 380, 1428, 640), fill=0)
    a = a.filter(ImageFilter.GaussianBlur(26))
    m = Image.new('RGBA', (1428, 1058), (0, 0, 0, 0))
    m.putalpha(a)
    m.save(mp)

otty = R / '素材/285/Otty.mp4'
cam = R / '素材/285/MAC-camera-preview.mp4'
anim = P / '动效-EP22-v001.mp4'
voice = P / '试听配音-EP22-final.wav'
bgm = P / 'bgm-v1.wav'
deco = P.parents[1] / 'EP12-新固件做出来了/剪辑/底部装饰-v009.png'
SRC_START = 55.0
cmd = ['ffmpeg', '-nostdin', '-v', 'error',
       '-i', str(otty), '-i', str(cam), '-i', str(anim), '-i', str(voice), '-i', str(bgm),
       '-loop', '1', '-framerate', '30', '-i', str(deco),
       '-loop', '1', '-framerate', '30', '-i', str(mp)]
f = []
# 实拍段 → 1080x800
f.append(f'[0:v]trim=start={SRC_START}:duration={REAL},setpts=PTS-STARTPTS,{boxes(MASK)},crop=1428:1058:12:0,scale=1080:800,fps=30,setsar=1[raw]')
f.append(f'[6:v]scale=1080:800,format=rgba,fade=t=in:st=0.5:d=0.6:alpha=1,trim=duration={REAL},setpts=PTS-STARTPTS[shade]')
f.append('[raw][shade]overlay=0:0:shortest=1[real]')
# 动效段补齐到面板尺寸
f.append(f'[2:v]trim=duration={T-REAL},setpts=PTS-STARTPTS,fps=30,scale=1080:800,setsar=1[anim]')
f.append('[real][anim]concat=n=2:v=1:a=0[screen]')
# 相机全程
f.append(f'[1:v]trim=start={SRC_START}:duration={T},setpts=PTS-STARTPTS,crop=650:366:395:155,scale=1080:608,fps=30,setsar=1[camera]')
f.append(f'color=c=0x283840:s=1080x1920:r=30:d={T}[base]')
f.append('[base][camera]overlay=0:280[b1]')
f.append('[b1][screen]overlay=0:888[b2]')
f.append(f"[b2][5:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='{ass.name}'[v]")
f.append('[3:a]adelay=500|500,volume=1.15,aresample=44100[voicea]')
f.append(f'[4:a]aresample=44100,atrim=0:{T},volume=0.8,afade=t=out:st={T-2}:d=2[bgm]')
f.append('[voicea][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]')
cmd += ['-filter_complex', ';'.join(f), '-map', '[v]', '-map', '[a]', '-t', str(T),
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(OUT)]
subprocess.run(cmd, cwd=P, check=True)
print('EP22 初稿已导出:', OUT)
