#!/usr/bin/env python3
"""EP07 v004：相机段恢复 EP06 设备紧裁规范。
只改相机链：crop=640:360:440:100 → scale=2160:1215 → 缓动微 zoompan → 1080x608，
不再使用 v002/v003 的近全画幅 crop=1275:718:57:52 与下移 150px。
标题、聚焦、PENDING 标注、旁白、BGM、时长全部沿用 v003。"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP07-我传完了还没跑"
D = f"{BASE}/剪辑"
OUT = f"{BASE}/产物"
W, H = 1080, 1920
BG = (40, 56, 64)
GOLD = (250, 200, 100)
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
CAM = f"{D}/素材/MAC-camera-26s.mov"
OTTY = f"{D}/素材/ep07-otty.mov"
BGM = f"{D}/音频/BGM-candidate-EP06.wav"
NARR = f"{D}/音频/narration-v001.wav"
ASS = f"{D}/字幕/ep07.ass"
TITLES = f"{D}/字幕/titles-v004.ass"

os.makedirs(f"{D}/帧-v004", exist_ok=True)
os.makedirs(OUT, exist_ok=True)

# ---------- 1b. 标题条（仅暗底，无文字；与 EP6g 同算法） ----------
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
sc.save(f"{D}/帧-v004/title-scrim.png")

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
strip.convert("RGB").save(f"{D}/帧-v004/bottom-strip.png")

# ---------- old-log clarification label (0-6.2s) ----------
old = Image.new("RGBA", (W, 70), (0, 0, 0, 0))
od = ImageDraw.Draw(old)
od.rounded_rectangle((40, 0, 1040, 58), radius=10, fill=(8, 14, 18, 225), outline=GOLD + (255,), width=2)
f_old = ImageFont.truetype(HIRA, 26, index=2)
od.text((62, 14), "说明", font=ImageFont.truetype(HIRA, 20, index=0), fill=GOLD + (255,))
od.text((112, 11), "历史 94/95 日志，非本轮结果", font=f_old, fill=GOLD + (255,))
old.save(f"{D}/帧-v004/oldlog-label-v004.png")

# ---------- focus mask (top old logs hidden + label) ----------
mask = Image.new("RGBA", (1080, 800), (0, 0, 0, 0))
m = Image.new("L", (1, 250))
for i in range(250):
    m.putpixel((0, i), 255 if i < 210 else int(255 * (1 - (i - 210) / 40)))
m = m.resize((1080, 250))
mo = Image.new("RGBA", (1080, 250), (6, 10, 13, 0))
mo.putalpha(m)
mask.alpha_composite(mo, (0, 0))
md = ImageDraw.Draw(mask)
md.text((24, 18), "本轮 session96", font=ImageFont.truetype(HIRA, 24, index=2), fill=GOLD + (255,))
mask.save(f"{D}/帧-v004/focus-mask-v004.png")

# ---------- render ----------
E = ("if(lt(in\\,186)\\,0\\,"
     "if(lt(in\\,210)\\,1-pow(1-(in-186)/24\\,3)\\,"
     "if(lt(in\\,282)\\,1\\,"
     "if(lt(in\\,306)\\,pow(1-(in-282)/24\\,3)\\,0))))")
P = ("if(lt(in\\,210)\\,0\\,"
     "if(lt(in\\,252)\\,(in-210)/42\\,1))")
out = f"{OUT}/EP07-我传完了还没跑-竖版-v004.mp4"
cmd = [
    "ffmpeg", "-y", "-loglevel", "error",
    "-i", CAM, "-i", OTTY,
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-v004/title-scrim.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-v004/bottom-strip.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧/overlay-pending.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-v004/oldlog-label-v004.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-v004/focus-mask-v004.png",
    "-i", NARR, "-i", BGM,
    "-filter_complex",
    # camera: EP06 device tight crop (640x360@440,100) -> 2160x1215 -> micro zoom -> 1080x608
    "[0:v]crop=640:360:440:100,scale=2160:1215:flags=lanczos,fps=30,"
    "zoompan=z='1+0.08*(1-pow(1-min(in/150\\,1)\\,3))'"
    ":x='min(max(962-iw/zoom/2\\,0)\\,iw-iw/zoom)'"
    ":y='min(max(783-ih/zoom/2\\,0)\\,ih-ih/zoom)'"
    ":d=1:fps=30:s=1080x608,setsar=1,setpts=PTS-STARTPTS[cam];"
    # terminal: continuous zoompan 1.0 -> 1.278 -> hold -> 1.0, fps=30
    f"[1:v]crop=1080:800:40:120,fps=30,setsar=1[term0];"
    f"[term0]zoompan=z='1+1.0*({E})':x='540*({P})*({E})':y='400*({E})':d=1:fps=30:s=1080x800,setpts=PTS-STARTPTS[term];"
    "[6:v]format=rgba,fade=t=in:st=6.2:d=0.5:alpha=1,fade=t=out:st=9.4:d=0.8:alpha=1[mask];"
    "[term][mask]overlay=0:0[termf];"
    "[5:v]format=rgba,fade=t=out:st=5.8:d=0.4:alpha=1[old];"
    "color=c=0x283840:s=1080x1920:r=30:d=24.5[bg];"
    "[bg][cam]overlay=0:0[b1];"
    "[b1][termf]overlay=0:608[b2];"
    "[b2][old]overlay=0:618:enable='between(t,0,6.2)'[b3];"
    "[b3][2:v]overlay=0:0[b4];"
    "[b4][3:v]overlay=0:1408[b5];"
    "[b5][4:v]overlay=0:0:enable='between(t,10.28,16.37)'[b6];"
    f"[b6]ass={TITLES}:fontsdir=/System/Library/Fonts,"
    f"ass={ASS}:fontsdir=/System/Library/Fonts[v];"
    "[7:a]adelay=500|500,volume=1.15[na];"
    "[8:a]atrim=0:24.5,volume=0.8,afade=t=out:st=22.5:d=2[bgm];"
    "[na][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,"
    "loudnorm=I=-14:TP=-1.6:LRA=11,aresample=44100,alimiter=limit=0.78:level=disabled[a]",
    "-map", "[v]", "-map", "[a]", "-t", "24.5",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out,
]
subprocess.run(cmd, check=True)
print("rendered", out)
