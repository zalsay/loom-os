#!/usr/bin/env python3
"""EP06 v003 竖版：session80 线（设备没碰，电脑上做只读探针）。
上半 = 新 Mac 相机（按用户参考帧裁切：设备占满、背景最少）；下半 = Otty 三幕聚焦。
配方沿 EP05/EP06v002：xfade 三幕 + 慢推 + loudnorm/alimiter。"""
import os, subprocess, json

W, H = 1080, 1920
OTTY_Y, OTTY_H = 608, 800
STRIP_Y = 1408
BG = (40, 56, 64)
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
D = "/tmp/ep6c"
VIDEO_LEN = 33.0
TEMPO = 1.188
CUT1, CUT2 = 7.4, 15.9          # 幕1 结束 / 幕2 结束（按 whisper 幕边界反推）
S1 = CUT1 + 0.5
S2 = CUT2 - CUT1 + 0.5
S3 = VIDEO_LEN - CUT2

# ---------- 1. 底部装饰层 ----------
from PIL import Image
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

# ---------- 2. 字幕时间轴（caps.json：whisper 段 / TEMPO + 0.5，按分句等比切分） ----------
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
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},Badge,,0,0,0,,{{\\pos(540,120)}}──  织界创造日记 · EP06  ──")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T1,,0,0,0,,{{\\pos(540,200)}}它卡在交卷那一步")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T2,,0,0,0,,{{\\pos(540,300)}}我先在电脑上摸个底")
# 事实注释：第二幕终端里的红字是负向测试的预期输出
lines.append(f"Dialogue: 0,{fmt(8.0)},{fmt(15.4)},Note,,0,0,0,,{{\\pos(540,1368)}}红字是负向测试的预期输出  不是这一轮的失败")
for st, en, tx in CAPS:
    lines.append(f"Dialogue: 0,{fmt(st)},{fmt(en)},Cap,,0,0,0,,{{\\pos(540,1470)}}{mark_gold(tx)}")
with open(f"{D}/ep06c.ass", "w") as f:
    f.write("\n".join(lines) + "\n")
print("ASS written,", len(CAPS), "captions")

# ---------- 3. 画面链 ----------
# 上半：新 Mac 相机，按参考帧裁切（去掉 QuickTime 黑边，设备占满画面）
def mac_chain(seg_s, idx):
    vf = ("crop=1275:718:57:36,scale=2160:1216:flags=lanczos,fps=30,"
          "zoompan=z='1+0.08*(1-pow(1-min(in/150\\,1)\\,3))'"
          ":x='min(max(1128-iw/zoom/2,0),iw-iw/zoom)'"
          ":y='min(max(476-ih/zoom/2,0),ih-ih/zoom)'"
          ":d=1:s=1080x608,setsar=1,setpts=PTS-STARTPTS")
    return f"[{idx}:v]{vf}[d{idx}];"

# 下半：Otty 三幕裁切（左对齐保留行首），轻微推近
OTTY_CROPS = [(720, 533, 12, 0), (752, 557, 12, 360), (640, 474, 12, 520)]
def otty_chain(seg_s, idx, act):
    cw, ch, cx, cy = OTTY_CROPS[act]
    vf = (f"crop={cw}:{ch}:{cx}:{cy},scale=2160:1600:flags=lanczos,fps=30,"
          "zoompan=z='1+0.04*(1-pow(1-min(in/150\\,1)\\,3))':x='0':y='ih/2-(ih/zoom/2)'"
          ":d=1:s=1080x800,setsar=1,setpts=PTS-STARTPTS")
    return f"[{3 + idx}:v]{vf}[o{idx}];"

cmd = [
    "ffmpeg", "-y", "-loglevel", "warning",
    "-ss", "0", "-t", f"{S1}", "-i", f"{D}/MAC-camera.mov",
    "-ss", "30", "-t", f"{S2}", "-i", f"{D}/MAC-camera.mov",
    "-ss", "70", "-t", f"{S3}", "-i", f"{D}/MAC-camera.mov",
    "-ss", "0", "-t", f"{S1}", "-i", f"{D}/OTTY-screen.mov",
    "-ss", "30", "-t", f"{S2}", "-i", f"{D}/OTTY-screen.mov",
    "-ss", "70", "-t", f"{S3}", "-i", f"{D}/OTTY-screen.mov",
    "-i", f"{D}/clone/full.wav",
    "-i", f"{D}/bottom-strip.png",
    "-filter_complex", (
        mac_chain(S1, 0) + mac_chain(S2, 1) + mac_chain(S3, 2) +
        f"[d0][d1]xfade=transition=fade:duration=0.5:offset={CUT1}[dx1];"
        f"[dx1][d2]xfade=transition=fade:duration=0.5:offset={CUT2}[dev];"
        f"color=c=0x283840:s=1080x1920:r=30:d={VIDEO_LEN}[base];"
        f"[base][dev]overlay=0:0[b1];"
        + otty_chain(S1, 0, 0) + otty_chain(S2, 1, 1) + otty_chain(S3, 2, 2) +
        f"[o0][o1]xfade=transition=fade:duration=0.5:offset={CUT1}[x1];"
        f"[x1][o2]xfade=transition=fade:duration=0.5:offset={CUT2}[otty];"
        f"[b1][otty]overlay=0:{OTTY_Y}[a];"
        f"[a][7:v]overlay=0:{STRIP_Y}[b];"
        f"[b]ass={D}/ep06c.ass,format=yuv420p[v];"
        f"[6:a]atempo={TEMPO},adelay=500|500,volume=1.15,"
        f"aformat=channel_layouts=stereo,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[aout]"
    ),
    "-map", "[v]", "-map", "[aout]",
    "-t", f"{VIDEO_LEN}",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    f"{D}/EP06-先在电脑上摸底-竖版-v003.mp4",
]
subprocess.run(cmd, check=True)
print("rendered EP06 v003")
