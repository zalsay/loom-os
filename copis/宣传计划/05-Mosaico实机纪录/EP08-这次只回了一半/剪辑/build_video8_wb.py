#!/usr/bin/env python3
"""EP08 wb001（WorkBuddy 重渲版，基于 v001/v002 链路）
对齐《剪辑与音频规范-实机纪录》修复项：
1. 字幕：删 Gold 金色强调样式，全 6 行统一 Cap 暖白 62px（EP06 系列基准）；
   标注条整体上移 40px（1180→1140），为 62px 两行字幕让位，消除碰撞。
2. 标注层：7 条标注条全部加 0.3s alpha 淡入/淡出（EP07 生命周期规范），不再硬切。
3. 混音：回归定稿公式 loudnorm TP=-1.5 / alimiter limit=0.80；片尾 afade 移回 BGM 段。
4. BGM 与 bottom-strip 使用本集归档副本（剪辑/音频/、剪辑/素材/），不再跨集引用 EP07。
5. 标题 ASS 写入 剪辑/titles-wb.ass（资产归位，不再放 帧-样片/）。
6. 音轨双指纹渲染后实测并写入 产物/EP08-wb001-核查与指纹.md。
未改动（保留 v001 设计）：镜头映射、旁白与字幕文本、相机 crop、七项接口横向截断、
双相机重复、/Users/sisu 路径（发布前人工隐私复核项）。
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
BGM = f"{D}/音频/bgm-ep08-clean-v2.wav"   # EP08 独立新合成 v2（synth_bgm_ep08_v2.py）：120BPM+亮音色+全8分hi-hat，对标原版轻快感
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

# ---------- 标注条（整体上移 40px：overlay y=1140） ----------
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

# ---------- ASS 标题（归位到 剪辑/） ----------
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
open(f"{D}/titles-wb.ass", "w", encoding="utf-8").write(ass)

# ---------- 字幕 wb 版：全 Cap 62px 暖白（EP06 基准），去 Gold ----------
sub = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Hiragino Sans GB,62,&H00FFFFFF,&H00FFFFFF,&H00101B22,&H00101B22,1,0,0,0,100,100,1,0,1,2.2,1.2,2,40,40,80,1
Style: Note,Hiragino Sans GB,38,&H00FFFFFF,&H00FFFFFF,&H00101B22,&H00101B22,1,0,0,0,100,100,1,0,1,2.0,1.0,7,40,40,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:05.50,0:00:16.50,Note,,0,0,0,,{{\pos(30,618)}}{{\c&HE0D35F&>}}{{\c&HFFFFFF&}}本轮 session103
Dialogue: 0,0:00:00.50,0:00:03.75,Cap,,0,0,0,,{{\\pos(540,1400)}}设备回话了——它只说了一半。
Dialogue: 0,0:00:03.75,0:00:06.99,Cap,,0,0,0,,{{\\pos(540,1400)}}等了两分多钟，终端才跳出回执。
Dialogue: 0,0:00:06.99,0:00:11.66,Cap,,0,0,0,,{{\\pos(540,1400)}}七项底层接口可查，\\N但状态停在“部分完成”。
Dialogue: 0,0:00:11.66,0:00:13.89,Cap,,0,0,0,,{{\\pos(540,1400)}}能回话，不等于能跑。
Dialogue: 0,0:00:13.89,0:00:17.74,Cap,,0,0,0,,{{\\pos(540,1400)}}剩余项未知，它在响应，但还没交卷。
Dialogue: 0,0:00:17.74,0:00:24.50,Cap,,0,0,0,,{{\\pos(540,1400)}}算开了头。\\N下一集，把剩下的一半问回来。
"""
open(f"{D}/字幕/ep08-wb.ass", "w", encoding="utf-8").write(sub)

# ---------- 滤镜 ----------
# 中部内容（1080×800）：终端 5 段 + 相机近景 2 段（与 v001 一致）
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

# 标注条时间窗（与 v001 相同）+ 0.3s alpha 淡入淡出（不再硬切，去掉 enable 依赖 alpha 可见性）
CAP_Y = 1140
def cap_fade(idx, t0, t1):
    parts = ["format=rgba"]
    if t0 > 0:
        parts.append(f"fade=t=in:st={t0}:d=0.3:alpha=1")
    if t1 < 24.5:
        parts.append(f"fade=t=out:st={t1-0.3}:d=0.3:alpha=1")
    return f"[{idx}:v]" + ",".join(parts) + f"[c{idx}];"
ann_caps = "".join([
    cap_fade(3, 0.0, 3.0), cap_fade(4, 3.0, 5.5), cap_fade(5, 5.5, 9.5),
    cap_fade(6, 9.5, 12.0), cap_fade(7, 12.0, 16.5), cap_fade(8, 16.5, 21.5),
    cap_fade(9, 21.5, 24.5),
])
ann = (
    f"[2:v]format=rgba[scrim];"
    f"[b2][scrim]overlay=0:0[b3];"
    + "".join([
        f"[b{3+i}][c{3+i}]overlay=0:{CAP_Y}[b{4+i}];" for i in range(7)
    ])
    + f"[10:v]format=rgba,fade=t=in:st=0:d=0.5:alpha=1,fade=t=out:st=16.0:d=0.5:alpha=1[vg];"
    f"[b10][vg]overlay=0:608:enable='between(t,0,16.5)'[b10v];"
    f"[11:v]format=rgba,fade=t=in:st=5.5:d=0.5:alpha=1,fade=t=out:st=15.9:d=0.5:alpha=1[fm];"
    f"[b10v][fm]overlay=0:608:enable='between(t,5.5,16.5)'[b10m];"
    f"[b10m][12:v]overlay=0:1408[b11];"
)
filters = (
    term + camera_mid + top_cam + base + overlays + ann_caps + ann +
    f"[b11]ass={D}/titles-wb.ass:fontsdir=/System/Library/Fonts,ass={D}/字幕/ep08-wb.ass:fontsdir=/System/Library/Fonts[v];"
    f"[14:a]highpass=f=100,afade=t=in:ss=0:d=0.15,adelay=500|500,volume=1.15[na];"
    f"[13:a]atrim=0:24.5,volume=0.8,afade=t=out:st=22.5:d=2[bgm];"
    f"[na][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,"
    f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]"
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
    "-loop", "1", "-framerate", "30", "-t", "24.5", "-i", f"{D}/素材/bottom-strip.png",
    "-i", BGM, "-i", f"{D}/音频/narration-v001.wav",
    "-filter_complex", filters,
    "-map", "[v]", "-map", "[a]", "-t", "24.5",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    f"{OUT}/EP08-这次只回了一半-竖版-wb003.mp4",
]
subprocess.run(cmd, check=True)
print("rendered:", cmd[-1])
