#!/usr/bin/env python3
"""EP06 v010 竖版：session80 线（设备没碰，电脑上做只读探针）。
上半 = 新 Mac 相机紧裁设备（中心对准设备，修复偏右）；下半 = Otty 按 v014 定义恢复聚焦循环
（推近 1.30 → 保持 → 释放 + 动态蒙层同步），素材统一取任务结束后的稳定画面（-ss 90）。"""
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

# ---------- 1b. 标题条（上暗下透，亮设备上保标题可读） ----------
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

# ---------- 1c. Otty 聚焦蒙层（v014：alpha 170，聚焦带清晰，羽化过渡） ----------
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

make_mask("mask1.png", 700)   # act1 聚焦带：探针契约行（面板底部）
make_mask("mask2.png", 215)   # act2 聚焦带：38 tests / OK
make_mask("mask3.png", 400)   # act3 聚焦带：HOST 行 + exit

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
# 上半：新 Mac 相机紧裁设备（crop 左移含全部机身，zoom 中心 = 设备中心）
def mac_chain(seg_s, idx):
    vf = ("crop=640:360:440:100,scale=2160:1215:flags=lanczos,fps=30,"
          "zoompan=z='1+0.08*(1-pow(1-min(in/150\\,1)\\,3))'"
          ":x='min(max(962-iw/zoom/2\\,0)\\,iw-iw/zoom)'"
          ":y='min(max(783-ih/zoom/2\\,0)\\,ih-ih/zoom)'"
          ":d=1:s=1080x608,setsar=1,setpts=PTS-STARTPTS")
    return f"[{idx}:v]{vf}[d{idx}];"

# 下半：Otty 聚焦循环（v014 定义）：in<fin 全画幅 → fin..fin+24 ease-out 推进 ZMAX →
# 保持 → N-69 起 24 帧 ease-in 缩回；y 锚定聚焦行（K），x 左对齐保行首；蒙层同步淡入淡出
OTTY = [  # (cw, ch, cx, cy, K_scaled, fin_frames, zmax)
    (634, 470, 12,   0, 1472,  90, 1.30),   # act1 预检/命令 → 聚焦探针契约行
    (800, 593, 12, 460,  327,  90, 1.30),   # act2 全景 → 聚焦 Ran 38 tests / OK
    (800, 593, 12, 460,  751, 150, 1.05),   # act3 轻推 HOST/exit（不裁断整行）
]
def otty_chain(seg_s, idx, act):
    cw, ch, cx, cy, K, fin, zmax = OTTY[act]
    N = int(round(seg_s * 30))
    fout = N - 69
    z = (f"if(lt(in\\,{fin}),1,"
         f"if(lt(in\\,{fin + 24}),1+{zmax - 1:.2f}*(1-pow(1-(in-{fin})/24\\,3)),"
         f"if(lt(in\\,{fout}),{zmax:.2f},"
         f"if(lt(in\\,{fout + 24}),{zmax:.2f}-{zmax - 1:.2f}*pow((in-{fout})/24\\,3),1))))")
    vf = (f"crop={cw}:{ch}:{cx}:{cy},scale=2160:1600:flags=lanczos,fps=30,"
          f"zoompan=z='{z}':x='0'"
          f":y='min(max({K}-ih/zoom/2\\,0)\\,ih-ih/zoom)'"
          f":d=1:s=1080x800,setsar=1,setpts=PTS-STARTPTS")
    fin_s, fout_s = fin / 30, fout / 30
    mf = (f"[{9 + idx}:v]format=rgba,fade=t=in:st={fin_s:.2f}:d=0.8:alpha=1,"
          f"fade=t=out:st={fout_s:.2f}:d=0.8:alpha=1[m{idx}];")
    return (f"[{3 + idx}:v]{vf}[o{idx}];" + mf +
            f"[o{idx}][m{idx}]overlay=0:0[o{idx}m];")

cmd = [
    "ffmpeg", "-y", "-loglevel", "warning",
    "-ss", "0", "-t", f"{S1}", "-i", f"{D}/MAC-camera.mov",
    "-ss", "30", "-t", f"{S2}", "-i", f"{D}/MAC-camera.mov",
    "-ss", "70", "-t", f"{S3}", "-i", f"{D}/MAC-camera.mov",
    "-ss", "90", "-t", f"{S1}", "-i", f"{D}/OTTY-screen.mov",
    "-ss", "90", "-t", f"{S2}", "-i", f"{D}/OTTY-screen.mov",
    "-ss", "90", "-t", f"{S3}", "-i", f"{D}/OTTY-screen.mov",
    "-i", f"{D}/clone/full.wav",
    "-i", f"{D}/bottom-strip.png",
    "-i", f"{D}/title-scrim.png",
    "-loop", "1", "-framerate", "30", "-t", f"{S1}", "-i", f"{D}/mask1.png",
    "-loop", "1", "-framerate", "30", "-t", f"{S2}", "-i", f"{D}/mask2.png",
    "-loop", "1", "-framerate", "30", "-t", f"{S3}", "-i", f"{D}/mask3.png",
    "-filter_complex", (
        mac_chain(S1, 0) + mac_chain(S2, 1) + mac_chain(S3, 2) +
        f"[d0][d1]xfade=transition=fade:duration=0.5:offset={CUT1}[dx1];"
        f"[dx1][d2]xfade=transition=fade:duration=0.5:offset={CUT2}[dev];"
        f"color=c=0x283840:s=1080x1920:r=30:d={VIDEO_LEN}[base];"
        f"[base][dev]overlay=0:0[dv0];"
        f"[dv0][8:v]overlay=0:0[b1];"
        + otty_chain(S1, 0, 0) + otty_chain(S2, 1, 1) + otty_chain(S3, 2, 2) +
        f"[o0m][o1m]xfade=transition=fade:duration=0.5:offset={CUT1}[x1];"
        f"[x1][o2m]xfade=transition=fade:duration=0.5:offset={CUT2}[otty];"
        f"[b1][otty]overlay=0:{OTTY_Y}[a];"
        f"[a][7:v]overlay=0:{STRIP_Y}[b];"
        f"[b]ass={D}/ep06d.ass,format=yuv420p[v];"
        f"[6:a]atempo={TEMPO},adelay=500|500,volume=1.15,"
        f"aformat=channel_layouts=stereo,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[aout]"
    ),
    "-map", "[v]", "-map", "[aout]",
    "-t", f"{VIDEO_LEN}",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    f"{D}/EP06-先在电脑上摸底-竖版-v010.mp4",
]
subprocess.run(cmd, check=True)
print("rendered EP06 v010")
