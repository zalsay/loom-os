#!/usr/bin/env python3
"""EP07 v002：只修两项——标题 T1/T2 实际字形间距、Otty 证据局部聚焦。
旁白/配音/BGM/时长/文案/封面不变；v001 工程与资产已归档到 剪辑/历史-v001/。
聚焦：1.3× session96 关键行块，6.2s 进、保持、9.8s 出；fps=30；不伪造滚动/点击/日志。"""
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
ASS = f"{D}/字幕/ep07.ass"

os.makedirs(f"{D}/帧-v002", exist_ok=True)
os.makedirs(OUT, exist_ok=True)

# ---------- title overlay (new bbox-based layout) ----------
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
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
d.text((bx, 48), badge, font=f_badge, fill=GOLD + (255,))
shadowed(ov, "文件送进板子了", f_t1, 104, WHITE)
shadowed(ov, "我先没让它跑", f_t2, 198, GOLD)

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
ov.save(f"{D}/帧-v002/overlay-title-v002.png")

# ---------- old-log clarification label (0-6.2s) ----------
old = Image.new("RGBA", (W, 70), (0, 0, 0, 0))
od = ImageDraw.Draw(old)
od.rounded_rectangle((40, 0, 1040, 58), radius=10, fill=(8, 14, 18, 225), outline=GOLD + (255,), width=2)
f_old = ImageFont.truetype(HIRA, 26, index=2)
od.text((62, 14), "说明", font=ImageFont.truetype(HIRA, 20, index=0), fill=GOLD + (255,))
od.text((112, 11), "历史 94/95 日志，非本轮结果", font=f_old, fill=GOLD + (255,))
old.save(f"{D}/帧-v002/oldlog-label-v002.png")

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
mask.save(f"{D}/帧-v002/focus-mask-v002.png")

# ---------- render ----------
# E: 0 before 6.2s, ease-out to 1 by 7.0s, hold to 9.4s, ease-in back to 0 by 10.2s
E = ("if(lt(in\\,186)\\,0\\,"
     "if(lt(in\\,210)\\,1-pow(1-(in-186)/24\\,3)\\,"
     "if(lt(in\\,282)\\,1\\,"
     "if(lt(in\\,306)\\,pow(1-(in-282)/24\\,3)\\,0))))")
P = ("if(lt(in\\,210)\\,0\\,"
     "if(lt(in\\,252)\\,(in-210)/42\\,1))")
out = f"{OUT}/EP07-我传完了还没跑-竖版-v002.mp4"
cmd = [
    "ffmpeg", "-y", "-loglevel", "error",
    "-i", CAM, "-i", OTTY,
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-v002/overlay-title-v002.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧/overlay-pending.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-v002/oldlog-label-v002.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-v002/focus-mask-v002.png",
    "-i", NARR, "-i", BGM,
    "-filter_complex",
    # camera: shift down 150 then crop bottom
    "[0:v]crop=1275:718:57:52,scale=1080:608,fps=30,setsar=1,"
    "pad=1080:758:0:150:color=0x283840,crop=1080:608:0:0[cam];"
    # terminal: continuous zoompan 1.0 -> 1.278 -> hold -> 1.0, fps=30
    f"[1:v]crop=1080:800:40:120,fps=30,setsar=1[term0];"
    f"[term0]zoompan=z='1+1.0*({E})':x='540*({P})*({E})':y='400*({E})':d=1:fps=30:s=1080x800,setpts=PTS-STARTPTS[term];"
    "[5:v]format=rgba,fade=t=in:st=6.2:d=0.5:alpha=1,fade=t=out:st=9.4:d=0.8:alpha=1[mask];"
    "[term][mask]overlay=0:0[termf];"
    "[4:v]format=rgba,fade=t=out:st=5.8:d=0.4:alpha=1[old];"
    "color=c=0x283840:s=1080x1920:r=30:d=24.5[bg];"
    "[bg][cam]overlay=0:0[b1];"
    "[b1][termf]overlay=0:608[b2];"
    "[b2][old]overlay=0:618:enable='between(t,0,6.2)'[b3];"
    "[b3][2:v]overlay=0:0[b4];"
    "[b4][3:v]overlay=0:0:enable='between(t,10.28,16.37)'[b5];"
    f"[b5]ass={ASS}:fontsdir=/System/Library/Fonts[v];"
    "[6:a]adelay=500|500,volume=1.15[na];"
    "[7:a]atrim=0:24.5,volume=0.8,afade=t=out:st=22.5:d=2[bgm];"
    "[na][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,"
    "loudnorm=I=-14:TP=-1.6:LRA=11,aresample=44100,alimiter=limit=0.78:level=disabled[a]",
    "-map", "[v]", "-map", "[a]", "-t", "24.5",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out,
]
subprocess.run(cmd, check=True)
print("rendered", out)
