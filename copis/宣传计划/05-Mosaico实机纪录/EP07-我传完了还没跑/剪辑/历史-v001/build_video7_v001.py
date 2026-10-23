#!/usr/bin/env python3
"""EP07 v001 首版试片（连续原片版）：session96「传完还没跑」。
1080×1920，24.5s；全程使用正式原 MOV 的连续片段：
- 终端：ep07-otty.mov 0–24.5s（task 输出真实出现，之后真实静止）
- 相机：MAC-camera-26s.mov 0–24.5s（正式相机预览窗连续画面）
- 标题/底条/PENDING 为透明叠加层；PENDING 明确是说明标注，不伪造终端。
字幕按 0.5s 入声 + 23.48s 旁白 + 尾余量，成片 24.5s。"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP07-我传完了还没跑"
D = f"{BASE}/剪辑"
OUT = f"{BASE}/产物"
W, H = 1080, 1920
BG = (40, 56, 64)
GOLD = (250, 200, 100)
WHITE = (248, 255, 248)
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
CAM = f"{D}/素材/MAC-camera-26s.mov"
OTTY = f"{D}/素材/ep07-otty.mov"
BGM = f"{D}/音频/BGM-candidate-EP06.wav"
NARR = f"{D}/音频/narration-v001.wav"

os.makedirs(f"{D}/帧", exist_ok=True)
os.makedirs(f"{D}/字幕", exist_ok=True)
os.makedirs(OUT, exist_ok=True)

# ---------- title / strip overlay ----------
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
# scrim
scrim = Image.new("L", (1, 330))
for i in range(330):
    scrim.putpixel((0, i), 226 if i < 250 else int(226 * (1 - (i - 250) / 80) ** 1.3))
scrim = scrim.resize((W, 330))
sc = Image.new("RGBA", (W, 330), (10, 16, 20, 0))
sc.putalpha(scrim)
ov.alpha_composite(sc, (0, 0))

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

badge = "──  织界创造日记 · EP07  ──"
d = ImageDraw.Draw(ov)
bx = (W - d.textlength(badge, font=f_badge)) / 2
d.text((bx, 56), badge, font=f_badge, fill=GOLD + (255,))
shadowed(ov, "文件送进板子了", f_t1, 118, WHITE)
shadowed(ov, "我先没让它跑", f_t2, 184, GOLD)

# bottom strip
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
ov.alpha_composite(strip, (0, 1408))
ov.save(f"{D}/帧/overlay-title.png")

# ---------- PENDING annotation overlay ----------
pend = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(pend)
pd.rounded_rectangle((120, 1222, 960, 1318), radius=14, fill=(8, 14, 18, 228), outline=GOLD + (255,), width=2)
f_note = ImageFont.truetype(HIRA, 34, index=2)
f_tag = ImageFont.truetype(HIRA, 22, index=0)
pd.text((146, 1240), "说明", font=f_tag, fill=GOLD + (255,))
pd.text((212, 1238), "PENDING：主机预置的等待位", font=f_note, fill=GOLD + (255,))
pend.save(f"{D}/帧/overlay-pending.png")

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

# ---------- render ----------
out = f"{OUT}/EP07-我传完了还没跑-竖版-v001.mp4"
cmd = [
    "ffmpeg", "-y", "-loglevel", "error",
    "-i", CAM, "-i", OTTY,
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧/overlay-title.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧/overlay-pending.png",
    "-i", NARR, "-i", BGM,
    "-filter_complex",
    "[0:v]crop=1275:718:57:52,scale=1080:608,fps=30,setsar=1[cam];"
    "[1:v]crop=1080:800:40:120,fps=30,setsar=1[term];"
    "color=c=0x283840:s=1080x1920:r=30:d=24.5[bg];"
    "[bg][cam]overlay=0:0[b1];[b1][term]overlay=0:608[b2];"
    "[b2][2:v]overlay=0:0[b3];"
    "[b3][3:v]overlay=0:0:enable='between(t,10.28,16.37)'[b4];"
    f"[b4]ass={D}/字幕/ep07.ass:fontsdir=/System/Library/Fonts[v];"
    "[4:a]adelay=500|500,volume=1.15[na];"
    "[5:a]atrim=0:24.5,volume=0.8,afade=t=out:st=22.5:d=2[bgm];"
    "[na][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,"
    "loudnorm=I=-14:TP=-1.6:LRA=11,aresample=44100,alimiter=limit=0.78:level=disabled[a]",
    "-map", "[v]", "-map", "[a]", "-t", "24.5",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out,
]
subprocess.run(cmd, check=True)
print("rendered", out)
