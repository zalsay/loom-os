#!/usr/bin/env python3
"""EP08 正式版 v001（待 TTS 音轨接入）
- 目的：供 reviewer/qwen 核对源入出点、事实标注、可读性与运动预算；不含 TTS。
- 源：session103 OTTY 136–160s、MAC 136–160s（本地转码副本，原片未动）。
- 入点：原片转折区间 (141.538333, 141.555000]；141.85s 为安全的完整回执入点（不称首次回执帧）。
- 样片版式：顶部相机 1080×608 + 中部内容 1080×800 + 底部背景；正式版式待样片审后定。
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP08-这次只回了一半"
D = f"{BASE}/剪辑"
OUT = f"{BASE}/产物"
SRC = f"{D}/素材"
OTTY = f"{SRC}/otty-136-160.mov"   # 本地时间 = 源时间 - 136
MAC = f"{SRC}/mac-136-160.mov"
BGM = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP07-我传完了还没跑/剪辑/音频/BGM-candidate-EP06.wav"
W, H = 1080, 1920
BG = (40, 56, 64)
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
os.makedirs(f"{D}/帧-样片", exist_ok=True)
os.makedirs(OUT, exist_ok=True)

# ---------- 标题暗底条 ----------
scrim = Image.new("L", (1, 330))
for i in range(330):
    a = 226 if i < 250 else int(226 * (1 - (i - 250) / 80) ** 1.3)
    scrim.putpixel((0, i), a)
scrim = scrim.resize((W, 330))
sc = Image.new("RGBA", (W, 330), (10, 16, 20, 0))
sc.putalpha(scrim)
sc.save(f"{D}/帧-样片/title-scrim.png")

# ---------- 标注条 ----------
def bar(text, fname, prompt=">"):
    img = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    bw, bh = 820, 48
    bx, by = (W - bw) // 2, 36
    dr.rounded_rectangle((bx, by, bx + bw - 1, by + bh - 1), radius=7,
                         fill=(13, 21, 25, 235), outline=(92, 138, 148, 190), width=1)
    f = ImageFont.truetype(HIRA, 26, index=0)
    fp = ImageFont.truetype(HIRA, 26, index=2)
    tw = f.getlength(text)
    pw = fp.getlength(prompt)
    total = pw + 10 + tw
    x = bx + (bw - total) // 2
    bb = f.getbbox(text)
    ty = by + (bh - (bb[3] - bb[1])) // 2 - bb[1]
    dr.text((x, ty), prompt, font=fp, fill=(95, 211, 224, 255))
    dr.text((x + pw + 10, ty), text, font=f, fill=(200, 210, 216, 255))
    ft = ImageFont.truetype(HIRA, 13, index=0)
    dr.rounded_rectangle((bx + 12, by - 16, bx + 12 + int(ft.getlength("说明")) + 16, by + 4),
                         radius=4, fill=(13, 21, 25, 255), outline=(92, 138, 148, 200))
    dr.text((bx + 20, by - 14), "说明", font=ft, fill=(170, 184, 190, 240))
    img.save(f"{D}/帧-样片/{fname}")

bar("实录 02:22 · 闪前先看", "cap-flashback.png")
bar("轮询 28 次 · 等待 139 秒", "cap-wait.png")
bar("底层七项基础接口可查", "cap-caps.png")
bar("状态：部分完成", "cap-partial.png")
bar("剩余项仍未确认", "cap-unknown.png")
bar("设备停在任务列表 · 剩余项仍未确认", "cap-device.png")
bar("下集 · 另一半", "cap-next.png", prompt="$")

# ---------- ASS 标题 ----------
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Badge,Hiragino Sans GB,40,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,1.2,0,8,40,40,0,1
Style: T1,Hiragino Sans GB,74,&H00F8FFF8,&H00F8FFF8,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.0,1.5,8,40,40,0,1
Style: T2,Hiragino Sans GB,96,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.0,1.5,8,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:24.50,Badge,,0,0,0,,{{\\pos(540,56)}}── 织界创造日记 · EP08 ──
Dialogue: 0,0:00:00.00,0:00:24.50,T1,,0,0,0,,{{\\pos(540,118)}}触发诊断之后
Dialogue: 0,0:00:00.00,0:00:24.50,T2,,0,0,0,,{{\\pos(540,184)}}这次它只回了一半
"""
open(f"{D}/帧-样片/titles-ass.ass", "w", encoding="utf-8").write(ass)

# ---------- 滤镜 ----------
# 中部内容（1080×800）：终端 5 段 + 相机近景 2 段
term = (
    f"[0:v]trim=5.85:8.85,setpts=PTS-STARTPTS,fps=30,crop=1080:800:40:120,"
    f"zoompan=z='if(lt(in,24),1+0.20*(1-pow(1-in/24,3)),if(lt(in,66),1.20,1.20-0.20*(1-pow(1-(in-66)/24,3))))':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[t1];"
    f"[0:v]trim=3.50:5.72,setpts=PTS-STARTPTS,fps=30,crop=1080:800:40:120,"
    f"tpad=stop_mode=clone:stop_duration=0.28,"
    f"zoompan=z='if(lt(in,30),1+0.15*(1-pow(1-in/30,3)),1.15)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[t2];"
    f"[0:v]trim=6.00:10.00,setpts=PTS-STARTPTS,fps=30,crop=1452:800:0:120,"
    f"zoompan=z='if(lt(in,24),1+0.15*(1-pow(1-in/24,3)),if(lt(in,96),1.15,1.15-0.15*(1-pow(1-(in-96)/24,3))))':x='min(max(700-iw/zoom/2,0),iw-iw/zoom)':y='min(max(280-ih/zoom/2,0),ih-ih/zoom)':d=1:fps=30:s=1080x800[t3];"
    f"[0:v]trim=10.00:12.50,setpts=PTS-STARTPTS,fps=30,crop=1452:800:0:120,"
    f"zoompan=z='if(lt(in,24),1+0.30*(1-pow(1-in/24,3)),if(lt(in,51),1.30,1.30-0.30*(1-pow(1-(in-51)/24,3))))':x='min(max(1080-iw/zoom/2,0),iw-iw/zoom)':y='min(max(380-ih/zoom/2,0),ih-ih/zoom)':d=1:fps=30:s=1080x800[t4];"
    f"[0:v]trim=12.50:17.00,setpts=PTS-STARTPTS,fps=30,crop=1452:800:0:120,"
    f"zoompan=z='if(lt(in,24),1+0.30*(1-pow(1-in/24,3)),if(lt(in,111),1.30,1.30-0.30*(1-pow(1-(in-111)/24,3))))':x='min(max(1000-iw/zoom/2,0),iw-iw/zoom)':y='min(max(345-ih/zoom/2,0),ih-ih/zoom)':d=1:fps=30:s=1080x800[t5];"
    f"[t1][t2][t3][t4][t5]concat=n=5:v=1:a=0,setsar=1[term];"
)
camera_mid = (
    f"[1:v]trim=5.00:12.00,setpts=(PTS-STARTPTS)*5/7,fps=30,crop=640:474:440:80,"
    f"scale=1080:800:flags=lanczos,"
    f"zoompan=z='1.0+0.08*in/150':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[cam1];"
    f"[1:v]trim=12.00:12.10,setpts=PTS-STARTPTS,fps=30,crop=640:474:440:80,"
    f"scale=1080:800:flags=lanczos,tpad=stop_mode=clone:stop_duration=2.9,"
    f"zoompan=z='1.08-0.08*in/90':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[cam2];"
    f"[term][cam1][cam2]concat=n=3:v=1:a=0,setsar=1[mid];"
)
top_cam = (
    f"[1:v]trim=4.00:12.00,setpts=(PTS-STARTPTS)*24.5/8,fps=30,crop=640:360:440:100,"
    f"scale=2160:1215:flags=lanczos,"
    f"zoompan=z='1.0+0.04*in/735':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x608,setsar=1[top];"
)
base = f"color=c=0x283840:s=1080x1920:r=30:d=24.5[base];"
overlays = (
    f"[base][top]overlay=0:0:enable='between(t,0,16.5)'[b1];"
    f"[b1][mid]overlay=0:608[b2];"
)
ann = (
    f"[2:v]format=rgba[scrim];"
    f"[b2][scrim]overlay=0:0[b3];"
    f"[b3][3:v]overlay=0:1180:enable='between(t,0,3.0)'[b4];"
    f"[b4][4:v]overlay=0:1180:enable='between(t,3.0,5.5)'[b5];"
    f"[b5][5:v]overlay=0:1180:enable='between(t,5.5,9.5)'[b6];"
    f"[b6][6:v]overlay=0:1180:enable='between(t,9.5,12.0)'[b7];"
    f"[b7][7:v]overlay=0:1180:enable='between(t,12.0,16.5)'[b8];"
    f"[b8][8:v]overlay=0:1180:enable='between(t,16.5,21.5)'[b9];"
    f"[b9][9:v]overlay=0:1180:enable='between(t,21.5,24.5)'[b10];"
    f"[10:v]format=rgba,fade=t=in:st=0:d=0.5:alpha=1,fade=t=out:st=16.0:d=0.5:alpha=1[vg];"
    f"[b10][vg]overlay=0:608:enable='between(t,0,16.5)'[b10v];"
    f"[11:v]format=rgba,fade=t=in:st=5.5:d=0.5:alpha=1,fade=t=out:st=15.9:d=0.5:alpha=1[fm];"
    f"[b10v][fm]overlay=0:608:enable='between(t,5.5,16.5)'[b10m];"
    f"[b10m][12:v]overlay=0:1408[b11];"
)
filters = (
    term + camera_mid + top_cam + base + overlays + ann +
    f"[b11]ass={D}/帧-样片/titles-ass.ass:fontsdir=/System/Library/Fonts,ass={D}/字幕/ep08.ass:fontsdir=/System/Library/Fonts[v];"
    f"[14:a]highpass=f=100,afade=t=in:ss=0:d=0.15,adelay=500|500,volume=1.15[na];"
    f"[13:a]atrim=0:24.5,lowpass=f=3500,volume=0.8[bgm];"
    f"[na][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,"
    f"loudnorm=I=-14:TP=-1.6:LRA=11,aresample=44100,alimiter=limit=0.78:level=disabled,afade=t=out:st=22.5:d=2[a]"
)

cmd = [
    "ffmpeg", "-y", "-v", "error",
    "-i", OTTY, "-i", MAC,
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-样片/title-scrim.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-样片/cap-flashback.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-样片/cap-wait.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-样片/cap-caps.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-样片/cap-partial.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-样片/cap-unknown.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-样片/cap-device.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/帧-样片/cap-next.png",
    "-loop", "1", "-framerate", "30", "-t", "16.5", "-i", f"{D}/帧-样片/vignette.png",
    "-loop", "1", "-framerate", "30", "-t", "16.5", "-i", f"{D}/帧-样片/focus-mask.png",
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP07-我传完了还没跑/剪辑/帧-v007/bottom-strip.png",
    "-i", BGM, "-i", f"{D}/音频/narration-v001.wav",
    "-filter_complex", filters,
    "-map", "[v]", "-map", "[a]", "-t", "24.5",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    f"{OUT}/EP08-这次只回了一半-竖版-v004.mp4",
]
subprocess.run(cmd, check=True)
print("rendered")
