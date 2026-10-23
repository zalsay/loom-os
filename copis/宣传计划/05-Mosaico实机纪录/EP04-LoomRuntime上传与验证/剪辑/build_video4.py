#!/usr/bin/env python3
"""EP04 Runtime搬入 竖版 v001：上半 TP 设备画面 + 下半 Otty 终端，旁白+字幕+BGM。
配方 = EP03 v019 定稿（聚焦循环 1.30/蒙层170/zoompan fps=30/off=112），素材窗口按 EP04 YDIF 定标。"""
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
D = "/tmp/ep4live"

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

# ---------- 1b. Otty 聚焦蒙层（v016 定稿 alpha 170，清晰带底部 125px） ----------
MASK_A, clear_top, feather = 170, 675, 60
mask = Image.new("RGBA", (W, OTTY_H), (0, 0, 0, MASK_A))
mpx = mask.load()
for y in range(clear_top - feather, OTTY_H):
    a = int(MASK_A * (clear_top - y) / feather) if y < clear_top else 0
    for x in range(W):
        mpx[x, y] = (0, 0, 0, a)
mask.save(f"{D}/otty-mask.png")

# ---------- 2. 旁白时间轴（atempo 1.1861 校速后 33.19s = 4.40字/秒，四段摆放 0.5/10.8/15.8/28.3） ----------
CAPS = [
    (0.50, 3.14, "上集说过 要让板子真正跑起来"),
    (3.14, 5.98, "这一集我先把底层框架整个搬进去"),
    (5.98, 9.38, "六十八个文件 传一个验一个 全部对上"),
    (10.80, 12.16, "人按下重启"),
    (12.16, 13.52, "设备熄了又亮"),
    (13.52, 15.16, "里面的东西都还在"),
    (15.80, 17.00, "点开新作品"),
    (17.00, 18.44, "屏幕上一行红字"),
    (18.44, 19.36, "别慌"),
    (19.36, 21.56, "报告显示它跑通过一次"),
    (21.56, 23.24, "答案 四十二"),
    (23.24, 24.88, "再点一次就报错"),
    (24.88, 27.08, "更像是它拒绝重复交卷"),
    (28.30, 30.46, "六十九项旧文件再核一遍"),
    (30.46, 31.58, "依然全对"),
    (31.58, 33.02, "可真正的开机"),
    (33.06, 35.22, "还差一道触控门槛"),
    (35.22, 37.06, "下一集 我们去敲门"),
]
VIDEO_LEN = 38.0
CUT1, CUT2, CUT3 = 10.5, 15.5, 27.5
GOLD_WORDS = ["全部对上", "一行红字", "四十二", "触控门槛"]

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
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},Badge,,0,0,0,,{{\\pos(540,120)}}──  织界创造日记 · EP04  ──")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T1,,0,0,0,,{{\\pos(540,200)}}我把底层框架搬进板子")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T2,,0,0,0,,{{\\pos(540,300)}}报错是保护")
for st, en, tx in CAPS:
    lines.append(f"Dialogue: 0,{fmt(st)},{fmt(en)},Cap,,0,0,0,,{{\\pos(540,1470)}}{mark_gold(tx)}")
with open(f"{D}/ep04.ass", "w") as f:
    f.write("\n".join(lines) + "\n")
print("ASS written,", len(CAPS), "captions")

# ---------- 3. ffmpeg 渲染（v019 配方） ----------
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

# otty：全部 1452x1058，黑边同 EP03 live-02（内容底 984 → off=112）
def otty_chain(seg_s, idx, ss, src, fin):
    N = int(round(seg_s * 30))
    fout_s = (N - 69) / 30
    fin_s = fin / 30
    vf = (f"crop=1428:1058:12:0,scale=2160:1600,fps=30,"
        f"zoompan={keyframe_zoom_cycle(seg_s, 112, fin=fin)}:d=1:s=1080x800,setsar=1,setpts=PTS-STARTPTS")
    mf = (f"[{13 + idx}:v]format=rgba,fade=t=in:st={fin_s:.2f}:d=0.8:alpha=1,"
        f"fade=t=out:st={fout_s:.2f}:d=0.8:alpha=1[m{idx}];")
    return (f"[{3 + idx}:v]{vf}[o{idx}];" + mf +
        f"[o{idx}][m{idx}]overlay=0:0[o{idx}m];")

# TP：三段 1080p 同构图 crop=900:506:500:60；ch1 用 tp-38 俯拍 720p 单独定标
def tp_chain(idx, ss, src, crop):
    vf = (f"{crop},scale=2160:1216,fps=30,"
        f"zoompan={keyframe_zoom('0.08')}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        ":d=1:s=1080x608,setsar=1,setpts=PTS-STARTPTS")
    return f"[{idx}:v]{vf}[d{idx}];"

CROP_TP1080 = "crop=900:506:500:280"
CROP_TP38 = "crop=760:428:380:120"

cmd = [
    "ffmpeg", "-y", "-loglevel", "warning",
    "-ss", "8", "-t", "11.6", "-i", f"{D}/tp/tp-38-appupload.mp4",      # 0 TP ch1（上传近景 720p）
    "-ss", "8", "-t", "6.1", "-i", f"{D}/tp/tp-41-reboot.mp4",          # 1 TP ch2（熄屏→重亮）
    "-ss", "15", "-t", "13.1", "-i", f"{D}/tp/tp-42-error.mp4",         # 2 TP ch3（Works 红标）
    "-ss", "0", "-t", "11.1", "-i", f"{D}/tp/tp-43-check.mp4",          # 3 TP ch4（Works 全景）
    "-ss", "6", "-t", "11.6", "-i", f"{D}/otty/s34-screen.mov",         # 4 otty ch1（verified 递增）
    "-ss", "12.5", "-t", "6.1", "-i", f"{D}/otty/s41-screen.mov",       # 5 otty ch2（离线恢复）
    "-ss", "0.5", "-t", "13.1", "-i", f"{D}/otty/s42-screen.mov",       # 6 otty ch3（result.json）
    "-ss", "2", "-t", "11.1", "-i", f"{D}/otty/s43-screen.mov",         # 7 otty ch4（69项复核）
    "-i", f"{D}/clone/p1.wav",                                          # 8 旁白 P1
    "-i", f"{D}/clone/p2.wav",                                          # 9 旁白 P2
    "-i", f"{D}/clone/p3.wav",                                          # 10 旁白 P3
    "-i", f"{D}/clone/p4.wav",                                          # 11 旁白 P4
    "-i", "/tmp/ep1/bgm-upbeat2.wav",                                   # 12 BGM
    "-i", f"{D}/bottom-strip.png",                                      # 13 底部装饰
    "-loop", "1", "-framerate", "30", "-t", "11.0", "-i", f"{D}/otty-mask.png",  # 14 蒙层 ch1
    "-loop", "1", "-framerate", "30", "-t", "5.5", "-i", f"{D}/otty-mask.png",   # 15 蒙层 ch2
    "-loop", "1", "-framerate", "30", "-t", "12.5", "-i", f"{D}/otty-mask.png",  # 16 蒙层 ch3
    "-loop", "1", "-framerate", "30", "-t", "10.5", "-i", f"{D}/otty-mask.png",  # 17 蒙层 ch4
    "-filter_complex", (
        tp_chain(0, 8, "tp-38", CROP_TP38) +
        tp_chain(1, 6, "tp-41", CROP_TP1080) +
        tp_chain(2, 15, "tp-42", CROP_TP1080) +
        tp_chain(3, 0, "tp-43", CROP_TP1080) +
        f"[d0][d1]xfade=transition=fade:duration=0.5:offset={CUT1}[dx1];"
        f"[dx1][d2]xfade=transition=fade:duration=0.5:offset={CUT2}[dx2];"
        f"[dx2][d3]xfade=transition=fade:duration=0.5:offset={CUT3}[dev];"
        f"color=c=0x283840:s=1080x1920:r=30:d={VIDEO_LEN}[base];"
        f"[base][dev]overlay=0:0[b1];"
        + otty_chain(11.0, 1, 6, "s34", 75) +
        otty_chain(5.5, 2, 12.5, "s41", 45) +
        otty_chain(12.5, 3, 0.5, "s42", 90) +
        otty_chain(10.5, 4, 2, "s43", 75) +
        f"[o1m][o2m]xfade=transition=fade:duration=0.5:offset={CUT1}[x1];"
        f"[x1][o3m]xfade=transition=fade:duration=0.5:offset={CUT2}[x2];"
        f"[x2][o4m]xfade=transition=fade:duration=0.5:offset={CUT3}[otty];"
        f"[b1][otty]overlay=0:{OTTY_Y}[a];"
        f"[a][13:v]overlay=0:{STRIP_Y}[b];"
        f"[b]ass={D}/ep04.ass,format=yuv420p[v];"
        f"[8:a]adelay=500|500,volume=1.15[na1];"
        f"[9:a]adelay=10800|10800,volume=1.15[na2];"
        f"[10:a]adelay=15800|15800,volume=1.15[na3];"
        f"[11:a]adelay=28300|28300,volume=1.15[na4];"
        f"[12:a]atrim=0:{VIDEO_LEN},volume=0.35,afade=t=out:st={VIDEO_LEN-2}:d=2[bg];"
        f"[na1][na2][na3][na4][bg]amix=inputs=5:duration=longest:normalize=0,"
        f"aformat=channel_layouts=stereo,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[aout]"
    ),
    "-map", "[v]", "-map", "[aout]",
    "-t", str(VIDEO_LEN),
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    f"{D}/EP04-底层框架搬入-竖版-v002.mp4",
]
subprocess.run(cmd, check=True)
print("rendered EP04 v002")
