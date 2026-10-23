#!/usr/bin/env python3
"""EP05 它把自己锁了 竖版 v001：上半 TP 设备画面 + 下半 Otty 终端，旁白+字幕+BGM。
配方 = EP03 v019 + EP04 v002 修正（amix duration=longest）。素材 = session44 单事件 90s 双路，三幕复用不同聚焦。"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
DEV_H = 608
OTTY_Y = 608
OTTY_H = 800
STRIP_Y = 1408
BG = (40, 56, 64)
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
D = "/tmp/ep5live"

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

# ---------- 2. 旁白时间轴（atempo 1.0667 校速后 22.06s = 4.40字/秒，三段摆放 0.5/11.0/22.3） ----------
CAPS = [
    (0.50, 2.22, "敲门的结果出来了"),
    (2.22, 3.86, "六十八项编译全过"),
    (3.86, 6.02, "六十二个依赖 一个不缺"),
    (6.02, 7.98, "可它把自己锁在了门里"),
    (11.00, 12.08, "门槛亮了"),
    (12.08, 15.24, "触摸没确认之前 连界面都不许起"),
    (15.24, 16.28, "别骂它"),
    (16.28, 17.24, "这是保护"),
    (17.24, 19.48, "先证明你能摸 再谈开机"),
    (22.30, 24.38, "我没重跑 也没碰它"),
    (24.38, 25.74, "只把报告读完"),
    (25.74, 27.30, "开锁的钥匙怎么配"),
    (27.30, 28.46, "下一集见"),
]
VIDEO_LEN = 32.5
CUT1, CUT2 = 10.5, 21.0
GOLD_WORDS = ["一个不缺", "锁在了门里", "不许起", "先证明你能摸"]

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
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},Badge,,0,0,0,,{{\\pos(540,120)}}──  织界创造日记 · EP05  ──")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T1,,0,0,0,,{{\\pos(540,200)}}六十八项全过之后")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T2,,0,0,0,,{{\\pos(540,300)}}它把自己锁了")
for st, en, tx in CAPS:
    lines.append(f"Dialogue: 0,{fmt(st)},{fmt(en)},Cap,,0,0,0,,{{\\pos(540,1470)}}{mark_gold(tx)}")
with open(f"{D}/ep05.ass", "w") as f:
    f.write("\n".join(lines) + "\n")
print("ASS written,", len(CAPS), "captions")

# ---------- 3. ffmpeg 渲染（v019 配方 + v002 修正） ----------
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

# otty：1452x1058，黑边同 EP03/04（内容底 984 → off=112）
def otty_chain(seg_s, idx, fin):
    N = int(round(seg_s * 30))
    fout_s = (N - 69) / 30
    fin_s = fin / 30
    vf = (f"crop=1428:1058:12:0,scale=2160:1600,fps=30,"
        f"zoompan={keyframe_zoom_cycle(seg_s, 112, fin=fin)}:d=1:s=1080x800,setsar=1,setpts=PTS-STARTPTS")
    mf = (f"[{11 + idx}:v]format=rgba,fade=t=in:st={fin_s:.2f}:d=0.8:alpha=1,"
        f"fade=t=out:st={fout_s:.2f}:d=0.8:alpha=1[m{idx}];")
    return (f"[{3 + idx}:v]{vf}[o{idx}];" + mf +
        f"[o{idx}][m{idx}]overlay=0:0[o{idx}m];")

def tp_chain(idx, crop):
    vf = (f"{crop},scale=2160:1216,fps=30,"
        f"zoompan={keyframe_zoom('0.08')}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        ":d=1:s=1080x608,setsar=1,setpts=PTS-STARTPTS")
    return f"[{idx}:v]{vf}[d{idx}];"

CROP_TP = "crop=900:506:500:280"

cmd = [
    "ffmpeg", "-y", "-loglevel", "warning",
    "-ss", "5", "-t", "11.6", "-i", f"{D}/tp/tp-44-inspect.mp4",       # 0 TP ch1
    "-ss", "20", "-t", "11.0", "-i", f"{D}/tp/tp-44-inspect.mp4",      # 1 TP ch2
    "-ss", "40", "-t", "11.5", "-i", f"{D}/tp/tp-44-inspect.mp4",      # 2 TP ch3
    "-ss", "0", "-t", "11.6", "-i", f"{D}/otty/s44-screen.mov",        # 3 otty ch1（GET 活跃段 1-7s）
    "-ss", "20", "-t", "11.0", "-i", f"{D}/otty/s44-screen.mov",       # 4 otty ch2（静止+聚焦 BLOCKED 行）
    "-ss", "45", "-t", "11.5", "-i", f"{D}/otty/s44-screen.mov",       # 5 otty ch3（静止+释放收尾）
    "-i", f"{D}/clone/p1.wav",                                          # 6 旁白 P1
    "-i", f"{D}/clone/p2.wav",                                          # 7 旁白 P2
    "-i", f"{D}/clone/p3.wav",                                          # 8 旁白 P3
    "-i", "/tmp/ep1/bgm-upbeat2.wav",                                   # 9 BGM
    "-i", f"{D}/bottom-strip.png",                                      # 10 底部装饰
    "-loop", "1", "-framerate", "30", "-t", "11.0", "-i", f"{D}/otty-mask.png",  # 11 蒙层 ch1
    "-loop", "1", "-framerate", "30", "-t", "11.0", "-i", f"{D}/otty-mask.png",  # 12 蒙层 ch2
    "-loop", "1", "-framerate", "30", "-t", "11.5", "-i", f"{D}/otty-mask.png",  # 13 蒙层 ch3
    "-filter_complex", (
        tp_chain(0, CROP_TP) +
        tp_chain(1, CROP_TP) +
        tp_chain(2, CROP_TP) +
        f"[d0][d1]xfade=transition=fade:duration=0.5:offset={CUT1}[dx1];"
        f"[dx1][d2]xfade=transition=fade:duration=0.5:offset={CUT2}[dev];"
        f"color=c=0x283840:s=1080x1920:r=30:d={VIDEO_LEN}[base];"
        f"[base][dev]overlay=0:0[b1];"
        + otty_chain(11.0, 0, 45) +
        otty_chain(11.0, 1, 75) +
        otty_chain(11.5, 2, 60) +
        f"[o0m][o1m]xfade=transition=fade:duration=0.5:offset={CUT1}[x1];"
        f"[x1][o2m]xfade=transition=fade:duration=0.5:offset={CUT2}[otty];"
        f"[b1][otty]overlay=0:{OTTY_Y}[a];"
        f"[a][10:v]overlay=0:{STRIP_Y}[b];"
        f"[b]ass={D}/ep05.ass,format=yuv420p[v];"
        f"[6:a]adelay=500|500,volume=1.15[na1];"
        f"[7:a]adelay=11000|11000,volume=1.15[na2];"
        f"[8:a]adelay=22300|22300,volume=1.15[na3];"
        f"[9:a]atrim=0:{VIDEO_LEN},volume=0.35,afade=t=out:st={VIDEO_LEN-2}:d=2[bg];"
        f"[na1][na2][na3][bg]amix=inputs=4:duration=longest:normalize=0,"
        f"aformat=channel_layouts=stereo,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[aout]"
    ),
    "-map", "[v]", "-map", "[aout]",
    "-t", str(VIDEO_LEN),
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    f"{D}/EP05-它把自己锁了-竖版-v001.mp4",
]
subprocess.run(cmd, check=True)
print("rendered EP05 v001")
