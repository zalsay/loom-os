#!/usr/bin/env python3
"""EP06 v014 竖版：补回 BGM。
v013 起 otty 画面链与 v013 完全一致（stretchA ×16.9 / stretchB ×8 / act3 聚焦循环）。
音频：旁白 full.wav + BGM（bgm-upbeat2.wav 重合成版，A 大调 112BPM，RMS -26.8dBFS）
按 skill 配方混音：BGM atrim→volume 0.4→尾 2s 淡出 → amix inputs=2 duration=longest normalize=0
→ loudnorm I=-14 TP=-1.5 → alimiter 0.80 level=disabled。"""
import os, subprocess, json

W, H = 1080, 1920
OTTY_Y, OTTY_H = 608, 800
STRIP_Y = 1408
BG = (40, 56, 64)
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
D = "/tmp/ep6c"
VIDEO_LEN = 33.0
TEMPO = 1.188
CUT1, CUT2 = 7.44, 15.85
S1 = CUT1 + 0.5
S2 = CUT2 - CUT1 + 0.5
S3 = VIDEO_LEN - CUT2

from PIL import Image, ImageFilter

# ---------- 1. 底部装饰层 ----------
strip = Image.new("RGBA", (W, 512), BG + (255,))
logo = Image.open(LOGO).convert("RGBA")
lw = 900
lh = int(logo.height * lw / logo.width)
big = logo.resize((lw, lh), Image.LANCZOS)
big.putalpha(big.split()[3].point(lambda a: int(a * 0.05)))
strip.alpha_composite(big, ((W - lw) // 2, (512 - lh) // 2))
lw2 = 300
lh2 = int(logo.height * lw2 / logo.width)
small = logo.resize((lw2, lh2), Image.LANCZOS)
small.putalpha(small.split()[3].point(lambda a: int(a * 0.92)))
strip.alpha_composite(small, ((W - lw2) // 2, 512 - lh2 - 30))
strip.convert("RGB").save(f"{D}/bottom-strip.png")

# ---------- 1b. 标题条 ----------
scrim = Image.new("L", (1, 330))
SOLID, EDGE = 250, 330
for i in range(330):
    if i < SOLID:
        a = 226
    else:
        a = int(226 * (1 - (i - SOLID) / (EDGE - SOLID)) ** 1.3)
    scrim.putpixel((0, i), a)
scrim = scrim.resize((W, 330))
sc = Image.new("RGBA", (W, 330), (10, 16, 20, 0))
sc.putalpha(scrim)
sc.save(f"{D}/title-scrim.png")

# ---------- 1c. 仅 act3 保留聚焦蒙层（act1/2 真实打印镜头全亮） ----------
def make_mask(name, center, half=120, feather=55):
    m = Image.new("L", (1, OTTY_H), 170)
    px = m.load()
    for y in range(OTTY_H):
        d = abs(y - center)
        if d <= half:
            a = 0
        elif d <= half + feather:
            a = int(170 * (d - half) / feather)
        else:
            a = 170
        px[0, y] = a
    m = m.resize((W, OTTY_H))
    rgba = Image.new("RGBA", (W, OTTY_H), (0, 0, 0, 0))
    rgba.putalpha(m)
    rgba.save(f"{D}/{name}")

make_mask("mask3.png", 400)   # act3 聚焦带：HOST 行 + exit

# ---------- 2. 字幕时间轴 ----------
CAPS = [tuple(c) for c in json.load(open(f"{D}/clone/caps.json"))]
GOLD_WORDS = ["全过", "主机验证通过", "送进设备"]

def fmt(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def mark_gold(text):
    for gw in GOLD_WORDS:
        if gw in text:
            return text.replace(gw, r"{\c&H64C8FA&}" + gw + r"{\c&HFFFFFF&}")
    return text

lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]",
    "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
    "Style: Cap,Hiragino Sans GB,62,&H00FFFFFF,&H00FFFFFF,&H00101B22,&H00101B22,1,0,0,0,100,100,1,0,1,2.2,1.2,8,40,40,0,1",
    "Style: Badge,Hiragino Sans GB,40,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,1.2,0,8,40,40,0,1",
    "Style: Note,Hiragino Sans GB,34,&H00C8D2D8,&H00C8D2D8,&H00101B22,&H00101B22,0,0,0,0,100,100,0,0,3,1.0,0,8,40,40,0,1",
    "Style: T1,Hiragino Sans GB,74,&H00F8FFF8,&H00F8FFF8,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.0,1.5,8,40,40,0,1",
    "Style: T2,Hiragino Sans GB,96,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.0,1.5,8,40,40,0,1",
    "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},Badge,,0,0,0,,{{\\pos(540,56)}}──  织界创造日记 · EP06  ──")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T1,,0,0,0,,{{\\pos(540,118)}}它卡在交卷那一步")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T2,,0,0,0,,{{\\pos(540,184)}}我先在电脑上摸个底")
lines.append(f"Dialogue: 0,{fmt(8.0)},{fmt(VIDEO_LEN)},Note,,0,0,0,,{{\\pos(540,1252)}}终端红字是负向测试的预期输出  不是这一轮的失败")
for st, en, tx in CAPS:
    lines.append(f"Dialogue: 0,{fmt(st)},{fmt(en)},Cap,,0,0,0,,{{\\pos(540,1470)}}{mark_gold(tx)}")
with open(f"{D}/ep06d.ass", "w") as f:
    f.write("\n".join(lines) + "\n")
print("ASS written,", len(CAPS), "captions")

# ---------- 3. 画面链 ----------
# 上半：新 Mac 相机紧裁设备（与 v011 一致）
def mac_chain(seg_s, idx):
    vf = ("crop=640:360:440:100,scale=2160:1215:flags=lanczos,fps=30,"
          "zoompan=z='1+0.08*(1-pow(1-min(in/150\\,1)\\,3))'"
          ":x='min(max(962-iw/zoom/2\\,0)\\,iw-iw/zoom)'"
          ":y='min(max(783-ih/zoom/2\\,0)\\,ih-ih/zoom)'"
          ":d=1:fps=30:s=1080x608,setsar=1,setpts=PTS-STARTPTS")
    return f"[{idx}:v]{vf}[d{idx}];"

# 下半 act1：live-stretch 终端特写（728x540 @ (12,0)），静态框 + 真实打印运动
def otty_act1(idx):
    vf = ("crop=728:540:12:0,scale=1080:800:flags=lanczos,setsar=1,fps=30,"
          "setpts=PTS-STARTPTS")
    return f"[{idx}:v]{vf}[o0];"

# 下半 act2：同框位，下摇与打印同步：n 帧 30 起步 159 帧（1.0→6.3s）缓出，y 0→450 落 HOST 行
def otty_act2(idx):
    vf = ("crop=728:540:12:'450*(1-pow(1-min(max((n-30)/159\\,0)\\,1)\\,2))',"
          "scale=1080:800:flags=lanczos,setsar=1,fps=30,setpts=PTS-STARTPTS")
    return f"[{idx}:v]{vf}[o1];"

# 下半 act3：终态 + v014 聚焦循环（v011 参数不变）
K3, FIN3, ZMAX3 = 751, 150, 1.05
def otty_act3(seg_s, idx, midx):
    N = int(round(seg_s * 30))
    fout = N - 69
    z = (f"if(lt(in\\,{FIN3}),1,"
         f"if(lt(in\\,{FIN3 + 24}),1+{ZMAX3 - 1:.2f}*(1-pow(1-(in-{FIN3})/24\\,3)),"
         f"if(lt(in\\,{fout}),{ZMAX3:.2f},"
         f"if(lt(in\\,{fout + 24}),{ZMAX3:.2f}-{ZMAX3 - 1:.2f}*pow((in-{fout})/24\\,3),1))))")
    vf = (f"crop=800:593:12:460,scale=2160:1600:flags=lanczos,fps=30,"
          f"zoompan=z='{z}':x='0'"
          f":y='min(max({K3}-ih/zoom/2\\,0)\\,ih-ih/zoom)'"
          f":d=1:fps=30:s=1080x800,setsar=1,setpts=PTS-STARTPTS")
    fin_s, fout_s = FIN3 / 30, fout / 30
    mf = (f"[{midx}:v]format=rgba,fade=t=in:st={fin_s:.2f}:d=0.8:alpha=1,"
          f"fade=t=out:st={fout_s:.2f}:d=0.8:alpha=1[m2];")
    return (f"[{idx}:v]{vf}[o2];" + mf +
            f"[o2][m2]overlay=0:0[o2m];")

cmd = [
    "ffmpeg", "-y", "-loglevel", "warning",
    "-ss", "0", "-t", f"{S1}", "-i", f"{D}/MAC-camera.mov",
    "-ss", "30", "-t", f"{S2}", "-i", f"{D}/MAC-camera.mov",
    "-ss", "70", "-t", f"{S3}", "-i", f"{D}/MAC-camera.mov",
    "-ss", "0", "-t", f"{S1}", "-i", f"{D}/stretchA.mp4",
    "-ss", "0", "-t", f"{S2 + 0.5}", "-i", f"{D}/stretchB.mp4",
    "-ss", "90", "-t", f"{S3}", "-i", f"{D}/OTTY-screen.mov",
    "-i", f"{D}/clone/full.wav",
    "-i", f"{D}/bottom-strip.png",
    "-i", f"{D}/title-scrim.png",
    "-loop", "1", "-framerate", "30", "-t", f"{S3}", "-i", f"{D}/mask3.png",
    "-i", f"{D}/bgm-upbeat2.wav",
    "-filter_complex", (
        mac_chain(S1, 0) + mac_chain(S2, 1) + mac_chain(S3, 2) +
        f"[d0][d1]xfade=transition=fade:duration=0.5:offset={CUT1}[dx1];"
        f"[dx1][d2]xfade=transition=fade:duration=0.5:offset={CUT2}[dev];"
        f"color=c=0x283840:s=1080x1920:r=30:d={VIDEO_LEN}[base];"
        f"[base][dev]overlay=0:0[dv0];"
        f"[dv0][8:v]overlay=0:0[b1];"
        + otty_act1(3) + otty_act2(4) + otty_act3(S3, 5, 9) +
        f"[o0][o1]xfade=transition=fade:duration=0.5:offset={CUT1}[x1];"
        f"[x1][o2m]xfade=transition=fade:duration=0.5:offset={CUT2}[otty];"
        f"[b1][otty]overlay=0:{OTTY_Y}[a];"
        f"[a][7:v]overlay=0:{STRIP_Y}[b];"
        f"[b]ass={D}/ep06d.ass,format=yuv420p[v];"
        f"[6:a]atempo={TEMPO},adelay=500|500,volume=1.15[na];"
        f"[10:a]atrim=0:{VIDEO_LEN},volume=0.4,afade=t=out:st={VIDEO_LEN - 2}:d=2[bg];"
        f"[na][bg]amix=inputs=2:duration=longest:normalize=0,"
        f"aformat=channel_layouts=stereo,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[aout]"
    ),
    "-map", "[v]", "-map", "[aout]",
    "-t", f"{VIDEO_LEN}",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    f"{D}/EP06-先在电脑上摸底-竖版-v014.mp4",
]
subprocess.run(cmd, check=True)
print("rendered EP06 v014")
