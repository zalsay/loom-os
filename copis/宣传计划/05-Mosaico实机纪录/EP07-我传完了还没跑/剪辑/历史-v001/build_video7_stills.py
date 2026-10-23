#!/usr/bin/env python3
"""EP07 v001 首版试片：session96「传完还没跑」。
1080×1920，24.5s；0–6s 用 96 task 段真实终端输出，其余为真实定格 + 说明标注。
所有输入/输出都在项目持久路径；不依赖 /tmp。"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP07-我传完了还没跑"
D = f"{BASE}/剪辑"
OUT = f"{BASE}/产物"
W, H = 1080, 1920
CAM_Y, CAM_H = 0, 608
TERM_Y, TERM_H = 608, 800
STRIP_Y = 1408
BG = (40, 56, 64)
GOLD = (250, 200, 100)
WHITE = (248, 255, 248)
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
CAM_JPG = f"{D}/素材/session96-jpg/mac-0.jpg"
TERM_JPG = f"{D}/素材/session96-jpg/otty-task-output.jpg"
VIDEO = f"{D}/素材/OTTY-screen-task-1-7s.mov"
BGM = f"{D}/音频/BGM-candidate-EP06.wav"
NARR = f"{D}/音频/narration-v001.wav"

os.makedirs(f"{D}/帧", exist_ok=True)
os.makedirs(f"{D}/字幕", exist_ok=True)

# ---------- panels ----------
cam = Image.open(CAM_JPG).convert("RGB").crop((57, 52, 57 + 1275, 52 + 718)).resize((1080, 608), Image.LANCZOS)
term = Image.open(TERM_JPG).convert("RGB").crop((40, 120, 40 + 1080, 120 + 800))

# ---------- bottom strip ----------
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
strip = strip.convert("RGB")

# ---------- title scrim ----------
scrim = Image.new("L", (1, 330))
for i in range(330):
    if i < 250:
        a = 226
    else:
        a = int(226 * (1 - (i - 250) / 80) ** 1.3)
    scrim.putpixel((0, i), a)
scrim = scrim.resize((W, 330))
sc = Image.new("RGBA", (W, 330), (10, 16, 20, 0))
sc.putalpha(scrim)

# ---------- base ----------
base = Image.new("RGB", (W, H), BG)
base.paste(cam, (0, CAM_Y))
base.paste(term, (0, TERM_Y))
base.paste(strip, (0, STRIP_Y))
base = base.convert("RGBA")
base.alpha_composite(sc, (0, 0))

f_badge = ImageFont.truetype(HIRA, 40, index=0)
f_t1 = ImageFont.truetype(HIRA, 74, index=2)
f_t2 = ImageFont.truetype(HIRA, 96, index=2)

def shadowed(im, text, font, y, fill):
    d = ImageDraw.Draw(im)
    x = (W - d.textlength(text, font=font)) / 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 160))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
    ImageDraw.Draw(im).text((x, y), text, font=font, fill=fill + (255,))

# badge
d = ImageDraw.Draw(base)
badge = "──  织界创造日记 · EP07  ──"
bx = (W - d.textlength(badge, font=f_badge)) / 2
d.text((bx, 56), badge, font=f_badge, fill=GOLD + (255,))
shadowed(base, "文件送进板子了", f_t1, 118, WHITE)
shadowed(base, "我先没让它跑", f_t2, 184, GOLD)

frame_term = base.convert("RGB")
frame_term.save(f"{D}/帧/frame-terminal.png")

# PENDING annotation (说明标注，不伪装终端)
pending = base.copy()
over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(over)
od.rounded_rectangle((120, 1222, 960, 1318), radius=14, fill=(8, 14, 18, 228), outline=GOLD + (255,), width=2)
f_note = ImageFont.truetype(HIRA, 34, index=2)
f_tag = ImageFont.truetype(HIRA, 22, index=0)
od.text((146, 1240), "说明", font=f_tag, fill=GOLD + (255,))
od.text((212, 1238), "PENDING：主机预置的等待位", font=f_note, fill=GOLD + (255,))
pending.alpha_composite(over)
pending.convert("RGB").save(f"{D}/帧/frame-pending.png")

# camera emphasis: dim terminal
camframe = base.copy()
dim = Image.new("RGBA", (W, TERM_H), (0, 0, 0, 120))
camframe.alpha_composite(dim, (0, TERM_Y))
camframe.convert("RGB").save(f"{D}/帧/frame-camera.png")

# final: terminal bright
base.convert("RGB").save(f"{D}/帧/frame-final.png")

# ---------- ASS ----------
def fmt(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

caps = [
    (1.00, 2.97, "文件传进板子了，它就一定会跑吗？"),
    (2.97, 8.39, r"我先只做了一件事：\N把文件传进去，再逐个读回核对。"),
    (8.39, 10.28, "读回对得上。"),
    (10.28, 16.37, r"结果那一格，\N是我预先留的等待位，\N设备还没有执行报告。"),
    (16.37, 20.16, r"这一步，我先停在这里，\N{\c&H64C8FA&}没有让它运行{\c&HFFFFFF&}。"),
    (20.16, 23.72, r"{\c&H64C8FA&}上传完成，不等于运行成功{\c&HFFFFFF&}。"),
]
lines = [
    "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
    "[V4+ Styles]",
    "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
    "Style: Cap,Hiragino Sans GB,58,&H00FFFFFF,&H00FFFFFF,&H00101B22,&H00101B22,1,0,0,0,100,100,1,0,1,2.2,1.2,8,40,40,0,1",
    "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
]
for st, en, tx in caps:
    lines.append(f"Dialogue: 0,{fmt(st)},{fmt(en)},Cap,,0,0,0,,{{\\pos(540,1470)}}{tx}")
open(f"{D}/字幕/ep07.ass", "w").write("\n".join(lines) + "\n")

# ---------- segments ----------
def run(cmd):
    subprocess.run(cmd, check=True)

run(["ffmpeg", "-y", "-loglevel", "error",
     "-loop", "1", "-framerate", "30", "-t", "6", "-i", f"{D}/帧/frame-terminal.png",
     "-i", VIDEO,
     "-filter_complex",
     "[1:v]crop=1080:800:40:120,fps=30,setsar=1[term];[0:v][term]overlay=0:608:shortest=1,format=yuv420p[v]",
     "-map", "[v]", "-t", "6", "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-an",
     f"{D}/帧/seg0.mp4"])

def still(img, dur, out):
    run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-t", str(dur),
         "-i", img, "-vf", "scale=1080:1920,setsar=1,format=yuv420p,fps=30",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-an", out])

still(f"{D}/帧/frame-terminal.png", 3.0, f"{D}/帧/seg1.mp4")
still(f"{D}/帧/frame-pending.png", 7.4, f"{D}/帧/seg2.mp4")
still(f"{D}/帧/frame-camera.png", 3.8, f"{D}/帧/seg3.mp4")
still(f"{D}/帧/frame-final.png", 4.3, f"{D}/帧/seg4.mp4")

with open(f"{D}/帧/concat.txt", "w") as f:
    for i in range(5):
        f.write(f"file '{D}/帧/seg{i}.mp4'\n")
run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{D}/帧/concat.txt",
     "-c", "copy", f"{D}/帧/concat.mp4"])

# ---------- final ----------
out = f"{OUT}/EP07-我传完了还没跑-竖版-v001.mp4"
run(["ffmpeg", "-y", "-loglevel", "error",
     "-i", f"{D}/帧/concat.mp4", "-i", NARR, "-i", BGM,
     "-filter_complex",
     f"[0:v]ass={D}/字幕/ep07.ass:fontsdir=/System/Library/Fonts[v];"
     f"[1:a]adelay=500|500,volume=1.15[na];"
     f"[2:a]atrim=0:24.5,volume=0.8,afade=t=out:st=22.5:d=2[bg];"
     f"[na][bg]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,"
     f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]",
     "-map", "[v]", "-map", "[a]", "-t", "24.5",
     "-c:v", "libx264", "-preset", "medium", "-crf", "20",
     "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out])
print("rendered", out)
