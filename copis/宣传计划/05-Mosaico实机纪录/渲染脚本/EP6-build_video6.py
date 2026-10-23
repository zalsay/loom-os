#!/usr/bin/env python3
"""EP06 跑完却没交卷 竖版 v001：上半 MAC 相机（设备亮屏 Works）+ 下半 Otty 终端聚焦循环。
配方 = EP05 v001（xfade 三幕 + zoompan + loudnorm/alimiter）。素材 = session78 双路 120s。
音频：纯旁白（BGM 素材已失，走深夜诊断氛围），整篇 atempo=1.101 校速至 4.4字/秒。"""
import os, subprocess
from PIL import Image

W, H = 1080, 1920
DEV_H = 608
OTTY_Y = 608
OTTY_H = 800
STRIP_Y = 1408
BG = (40, 56, 64)
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
D = "/tmp/ep6live"
VIDEO_LEN = 33
TEMPO = 1.072
CUT1, CUT2 = 8.1, 16.5

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

# ---------- 1b. Otty 聚焦蒙层（alpha 170，清晰带底部 125px） ----------
MASK_A, clear_top, feather = 170, 675, 60
mask = Image.new("RGBA", (W, OTTY_H), (0, 0, 0, MASK_A))
mpx = mask.load()
for y in range(clear_top - feather, OTTY_H):
    a = int(MASK_A * (clear_top - y) / feather) if y < clear_top else 0
    for x in range(W):
        mpx[x, y] = (0, 0, 0, a)
mask.save(f"{D}/otty-mask.png")

# ---------- 2. 字幕时间轴（clone/caps.json：whisper 段 / TEMPO + 0.5 delay，按分句等比切分） ----------
import json
CAPS = [tuple(c) for c in json.load(open(f"{D}/clone/caps.json"))]
GOLD_WORDS = ["一个不差", "四零四", "讲清楚"]

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
    "Style: T1,Hiragino Sans GB,74,&H00F8FFF8,&H00F8FFF8,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.0,1.5,8,40,40,0,1",
    "Style: T2,Hiragino Sans GB,96,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.0,1.5,8,40,40,0,1",
    "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},Badge,,0,0,0,,{{\\pos(540,120)}}──  织界创造日记 · EP06  ──")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T1,,0,0,0,,{{\\pos(540,200)}}七十三项就位之后")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T2,,0,0,0,,{{\\pos(540,300)}}跑完却没交卷")
for st, en, tx in CAPS:
    lines.append(f"Dialogue: 0,{fmt(st)},{fmt(en)},Cap,,0,0,0,,{{\\pos(540,1470)}}{mark_gold(tx)}")
with open(f"{D}/ep06.ass", "w") as f:
    f.write("\n".join(lines) + "\n")
print("ASS written,", len(CAPS), "captions")

# ---------- 3. ffmpeg 渲染 ----------
def keyframe_zoom(zoom_max, frames=24):
    return f"z='1+{zoom_max}*(1-pow(1-min(in/{frames}\\,1)\\,3))':fps=30"

def keyframe_zoom_cycle(seg_s, off, zoom_max=0.30, fin=120, flen=24, tail=69, fps=30):
    N = int(round(seg_s * fps))
    fout = N - tail
    z = (f"if(lt(in\\,{fin}),1,"
        f"if(lt(in\\,{fin + flen}),1+{zoom_max}*(1-pow(1-(in-{fin})/{flen}\\,3)),"
        f"if(lt(in\\,{fout}),1+{zoom_max},"
        f"if(lt(in\\,{fout + flen}),1+{zoom_max}-{zoom_max}*pow((in-{fout})/{flen}\\,3),1))))")
    return f"z='{z}':x='0':y='ih-ih/zoom-{off}':fps=30"

# otty：1452x1058，同 EP03/04/05（内容底 984 → off=112）
def otty_chain(seg_s, idx, fin, zoom_max):
    N = int(round(seg_s * 30))
    fout_s = (N - 69) / 30
    fin_s = fin / 30
    vf = (f"crop=1428:1058:12:0,scale=2160:1600,fps=30,"
        f"zoompan={keyframe_zoom_cycle(seg_s, 112, zoom_max=zoom_max, fin=fin)}:d=1:s=1080x800,setsar=1,setpts=PTS-STARTPTS")
    mf = (f"[{8 + idx}:v]format=rgba,fade=t=in:st={fin_s:.2f}:d=0.8:alpha=1,"
        f"fade=t=out:st={fout_s:.2f}:d=0.8:alpha=1[m{idx}];")
    return (f"[{3 + idx}:v]{vf}[o{idx}];" + mf +
        f"[o{idx}][m{idx}]overlay=0:0[o{idx}m];")

# mac：1392x832 → 裁 1392x784:0:24 → 提亮 → 缓推（中心偏向设备屏幕）
def mac_chain(seg_s, idx):
    vf = (f"crop=1392:784:0:24,eq=gamma=1.7:brightness=0.05:saturation=1.1,scale=2160:1216,fps=30,"
        f"zoompan={keyframe_zoom('0.10', frames=96)}:x='iw*0.42-(iw/zoom/2)':y='ih*0.38-(ih/zoom/2)'"
        ":d=1:s=1080x608,setsar=1,setpts=PTS-STARTPTS")
    return f"[{idx}:v]{vf}[d{idx}];"

S1, S2, S3 = CUT1 + 0.5, CUT2 - CUT1 + 0.5, VIDEO_LEN - CUT2

cmd = [
    "ffmpeg", "-y", "-loglevel", "warning",
    "-ss", "0", "-t", str(S1), "-i", f"{D}/MAC-camera.mov",          # 0 mac ch1
    "-ss", "20", "-t", str(S2), "-i", f"{D}/MAC-camera.mov",         # 1 mac ch2
    "-ss", "40", "-t", str(S3), "-i", f"{D}/MAC-camera.mov",         # 2 mac ch3
    "-ss", "0", "-t", str(S1), "-i", f"{D}/OTTY-screen.mov",         # 3 otty ch1（SETUP/preflight 区）
    "-ss", "20", "-t", str(S2), "-i", f"{D}/OTTY-screen.mov",        # 4 otty ch2（聚焦 export_failed JSON）
    "-ss", "40", "-t", str(S3), "-i", f"{D}/OTTY-screen.mov",        # 5 otty ch3（JSON + exit:1 收尾）
    "-i", f"{D}/clone/full.wav",                                     # 6 旁白整篇
    "-i", f"{D}/bottom-strip.png",                                   # 7 底部装饰
    "-loop", "1", "-framerate", "30", "-t", str(S1), "-i", f"{D}/otty-mask.png",  # 8 蒙层 ch1
    "-loop", "1", "-framerate", "30", "-t", str(S2), "-i", f"{D}/otty-mask.png",  # 9 蒙层 ch2
    "-loop", "1", "-framerate", "30", "-t", str(S3), "-i", f"{D}/otty-mask.png",  # 10 蒙层 ch3
    "-filter_complex", (
        mac_chain(S1, 0) + mac_chain(S2, 1) + mac_chain(S3, 2) +
        f"[d0][d1]xfade=transition=fade:duration=0.5:offset={CUT1}[dx1];"
        f"[dx1][d2]xfade=transition=fade:duration=0.5:offset={CUT2}[dev];"
        f"color=c=0x283840:s=1080x1920:r=30:d={VIDEO_LEN}[base];"
        f"[base][dev]overlay=0:0[b1];"
        + otty_chain(S1, 0, 45, 0.28) +
        otty_chain(S2, 1, 60, 0.42) +
        otty_chain(S3, 2, 75, 0.34) +
        f"[o0m][o1m]xfade=transition=fade:duration=0.5:offset={CUT1}[x1];"
        f"[x1][o2m]xfade=transition=fade:duration=0.5:offset={CUT2}[otty];"
        f"[b1][otty]overlay=0:{OTTY_Y}[a];"
        f"[a][7:v]overlay=0:{STRIP_Y}[b];"
        f"[b]ass={D}/ep06.ass,format=yuv420p[v];"
        f"[6:a]atempo={TEMPO},adelay=500|500,volume=1.15,"
        f"aformat=channel_layouts=stereo,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[aout]"
    ),
    "-map", "[v]", "-map", "[aout]",
    "-t", str(VIDEO_LEN),
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    f"{D}/EP06-跑完却没交卷-竖版-v002.mp4",
]
subprocess.run(cmd, check=True)
print("rendered EP06 v002")
