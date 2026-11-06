#!/usr/bin/env python3
"""EP10「只上传，精确读回」竖版 v001 终版（v3.1 实录版，21.2s）：
素材 session160（2026-10-27 ep04-runtime-upload-160，双路各 300s，压缩 mp4 已拉回）。
实录形态：0-240s 等待确认（静态）→ ~1s 内 299 请求瞬时完成 → 结果 JSON 常驻至尾。
P1 结果先行 / P2 等待流程文字 / P3 launcher 最后传+设备 / P4 日志还原数据板 /
P5 三层结果 / P6 下一问。HUD 与 P4/P5 标注条必带"按执行日志"（不得伪装实录画面）。
事实边界：73 清单文件 SHA 全一致 0 不符（本地复算）；launcher 最后传（POST 顺序实录）；
runtime not_run（未做触摸/Runtime 验收）；"上传过程画面不存在，只可日志还原"。
注：本样片无旁白（BGM only）；crop 为近似值，待抽帧质检精调；旁白定稿后走 clone_tts 管线。
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP10-只上传精确读回"
D = f"{BASE}/剪辑"
OUT = f"{BASE}/产物"
SRC = f"{D}/素材/session160/压缩素材"
W, H = 1080, 1920
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
TOTAL = 21.2
os.makedirs(f"{D}/帧-样片", exist_ok=True)
os.makedirs(OUT, exist_ok=True)

TTY = f"{SRC}/OTTY-screen.mp4"
CAM = f"{SRC}/MAC-camera.mp4"
BGM = f"{D}/音频/bgm-ep10-v1.wav"
# operator 规则：整篇单次合成 take-4（含 MiMo (pauses) 标签句间停顿），整轨混入；字幕起点=实测句边界-0.1s 预显示（静音检测+能量曲线定位）
NARR = f"{D}/音频/take-4-narration.wav"

T1, T2 = "77 个文件传上去了", "这次，逐个读回来"

SUBS = [
    (0.20, 3.25, "Gold", "77 个文件，逐个读回来了。"),
    (3.25, 8.55, "Cap",  "每个文件都要读回来\\N一处没过，这轮就停。"),
    (8.55, 11.10, "Cap", "这轮上传，launcher 排在最后。"),
    (11.10, 15.38, "Cap", "77 个上传，77 个读回"),
    (15.38, 19.05, "Cap", "73 个与清单哈希一致\\N0 个不符"),
    (19.05, 21.00, "Gold", "设备里，能看见吗？"),
]
BARS = [
    ("本轮实际结果 · 提前展示", "", 0.0, 3.0),
    ("录制前确认等待 · 尚未开始上传", "", 3.0, 8.3),
    ("本轮上传顺序 · 据执行日志", "", 8.3, 11.0),
    ("执行日志统计 · 非实时上传画面", "", 11.0, 15.1),
    ("本地复算摘要：73 个清单哈希一致", "", 15.1, 19.0),
    ("未做触摸与 Runtime 验收", "", 19.0, 21.2),
]

# ---------- 标题暗底条 ----------
scrim = Image.new("L", (1, 330))
for i in range(330):
    a = 226 if i < 250 else int(226 * (1 - (i - 250) / 80) ** 1.3)
    scrim.putpixel((0, i), a)
scrim = scrim.resize((W, 330))
sc = Image.new("RGBA", (W, 330), (10, 16, 20, 0))
sc.putalpha(scrim)
sc.save(f"{D}/帧-样片/title-scrim.png")

# ---------- HUD 数据板（按执行日志） ----------
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dr = ImageDraw.Draw(img)
f_l = ImageFont.truetype(HIRA, 20, index=2)
f_v = ImageFont.truetype(HIRA, 26, index=0)
rows = [("上传", "77 个"), ("请求总数", "299"), ("规则", "失败即停")]
bw, bh = 360, 74
x, y = W - bw - 32, 640
dr.rounded_rectangle((x, y, x + bw, y + bh * 3), radius=10,
                     fill=(13, 21, 25, 205), outline=(92, 138, 148, 190), width=1)
for i, (k, v) in enumerate(rows):
    ry = y + 16 + i * bh
    dr.text((x + 20, ry), k, font=f_l, fill=(95, 211, 224, 255))
    dr.text((x + 118, ry - 4), v, font=f_v, fill=(220, 228, 232, 255))
img.save(f"{D}/帧-样片/hud-board.png")

# ---------- 标注条 ----------
def bar(text, fname, prompt=">"):
    im = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(im)
    bw2, bh2 = 880, 48
    bx, by = (W - bw2) // 2, 36
    d2.rounded_rectangle((bx, by, bx + bw2 - 1, by + bh2 - 1), radius=7,
                         fill=(13, 21, 25, 235), outline=(92, 138, 148, 190), width=1)
    f = ImageFont.truetype(HIRA, 26, index=0)
    fp = ImageFont.truetype(HIRA, 26, index=2)
    tw, pw = f.getlength(text), fp.getlength(prompt)
    xx = bx + (bw2 - pw - 10 - tw) // 2
    bb = f.getbbox(text)
    ty = by + (bh2 - (bb[3] - bb[1])) // 2 - bb[1]
    d2.text((xx, ty), prompt, font=fp, fill=(95, 211, 224, 255))
    d2.text((xx + pw + 10, ty), text, font=f, fill=(200, 210, 216, 255))
    ft = ImageFont.truetype(HIRA, 13, index=0)
    d2.rounded_rectangle((bx + 12, by - 16, bx + 12 + int(ft.getlength("说明")) + 16, by + 4),
                         radius=4, fill=(13, 21, 25, 255), outline=(92, 138, 148, 200))
    d2.text((bx + 20, by - 14), "说明", font=ft, fill=(170, 184, 190, 240))
    im.save(f"{D}/帧-样片/{fname}")

for i, (text, prompt, t0, t1) in enumerate(BARS):
    bar(text, f"cap10-{i}.png", prompt=prompt)

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
Dialogue: 0,0:00:00.00,0:00:{TOTAL:.2f},Badge,,0,0,0,,{{\\pos(540,56)}}── 织界探索日记 · EP10 ──
Dialogue: 0,0:00:00.00,0:00:{TOTAL:.2f},T1,,0,0,0,,{{\\pos(540,118)}}{T1}
Dialogue: 0,0:00:00.00,0:00:{TOTAL:.2f},T2,,0,0,0,,{{\\pos(540,184)}}{T2}
"""
open(f"{D}/titles10.ass", "w", encoding="utf-8").write(ass)

# ---------- 字幕 ----------
sub = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Hiragino Sans GB,54,&H00FFFFFF,&H00FFFFFF,&H00101B22,&H00101B22,1,0,0,0,100,100,1,0,1,2.2,1.2,2,40,40,80,1
Style: Gold,Hiragino Sans GB,62,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2.4,1.4,2,40,40,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
def ts(t):
    return f"0:{int(t//60):02d}:{t-60*int(t//60):05.2f}"
for (t0, t1, style, text) in SUBS:
    sub += f"Dialogue: 0,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\pos(540,1495)}}{text}\n"
open(f"{D}/字幕10.ass", "w", encoding="utf-8").write(sub)

# ---------- 滤镜（crop 为样片近似值，抽帧质检后精调） ----------
# tty 源 1452x1058；结果 JSON 在底部；等待流程文字中部偏下
mid = (
    # P1 0-3 结果 JSON 特写（源 291-294s，向底部推近）
    f"[0:v]trim=291:293.95,setpts=PTS-STARTPTS,fps=30,crop=1080:800:186:150,"
    f"zoompan=z='1.0+0.10*in/90':x='(iw-iw/zoom)/2':y='ih-ih/zoom':d=1:fps=30:s=1080x800[m1];"
    # P2 3-6 等待流程文字（源 120-123s 静态）
    f"[0:v]trim=120:125.05,setpts=PTS-STARTPTS,fps=30,crop=1080:800:186:150,"
    f"zoompan=z='1.0+0.08*in/90':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m2];"
    # P3 7.5-10.3 Otty 会话横幅段（tty 0-10s，下半部分全部固定为命令行画面）
    f"[0:v]trim=2:5.0,setpts=PTS-STARTPTS,fps=30,crop=1080:800:186:100,"
    f"zoompan=z='1.0+0.06*in/99':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m3];"
    # P4 10-18 结果常驻画面 + HUD 数据板
    f"[0:v]trim=294.8:298.6,setpts=PTS-STARTPTS,fps=30,crop=1200:889:126:169,"
    f"zoompan=z='1.0+0.06*in/240':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m4];"
    # P5 18-22 结果 JSON 二次特写
    f"[0:v]trim=285:288.8,setpts=PTS-STARTPTS,fps=30,crop=1080:800:186:145,"
    f"zoompan=z='1.0+0.10*in/120':x='(iw-iw/zoom)/2':y='ih-ih/zoom':d=1:fps=30:s=1080x800[m5];"
    # P6 22-25 not_run 钩子
    f"[0:v]trim=292:294.6,setpts=PTS-STARTPTS,fps=30,crop=1080:800:186:140,"
    f"zoompan=z='1.06+0.06*in/90':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m6];"
    f"[m1][m2][m3][m4][m5][m6]concat=n=6:v=1:a=0,setsar=1[mid];"
)
top_cam = (
    f"[1:v]trim=100:108,setpts=PTS-STARTPTS,fps=30,crop=835:470:312:90,"
    f"scale=2160:1215:flags=lanczos,tpad=stop_mode=clone:stop_duration=17.2,"
    f"zoompan=z='1.0+0.05*in/750':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x608,setsar=1[top];"
)
base = f"color=c=0x283840:s=1080x1920:r=30:d={TOTAL}[base];"
overlays = (
    f"[base][top]overlay=0:0:enable='between(t,0,{TOTAL})'[b1];"
    f"[mid]crop=1080:712:0:44,setsar=1[midc];"
    f"[b1][midc]overlay=0:608[b2];"
)
CAP_Y = 1140
def cap_fade(idx, t0, t1):
    parts = ["format=rgba"]
    if t0 > 0:
        parts.append(f"fade=t=in:st={t0}:d=0.3:alpha=1")
    if t1 < TOTAL:
        parts.append(f"fade=t=out:st={t1-0.3}:d=0.3:alpha=1")
    return f"[{idx}:v]" + ",".join(parts) + f"[c{idx}];"

n_bars = len(BARS)
bar_windows = [(t0, t1) for (_, _, t0, t1) in BARS]
filters = (
    mid + top_cam + base + overlays
    + "".join(cap_fade(4 + i, t0, t1) for i, (t0, t1) in enumerate(bar_windows))
    + f"[3:v]format=rgba,fade=t=in:st=11.0:d=0.3:alpha=1,fade=t=out:st=18.8:d=0.3:alpha=1[hud];"
    + f"[b2][hud]overlay=0:0[b3];"
    + "".join([f"[b{3+i}][c{4+i}]overlay=0:{CAP_Y}[b{4+i}];" for i in range(n_bars)])
    + f"[b{3+n_bars}][{4+n_bars}:v]overlay=0:1408[b{4+n_bars}];"
    + f"[b{4+n_bars}]ass={D}/titles10.ass:fontsdir=/System/Library/Fonts,ass={D}/字幕10.ass:fontsdir=/System/Library/Fonts[v];"
    + f"[{5+n_bars}:a]atrim=0:{TOTAL},volume=0.8,afade=t=out:st={TOTAL-2.2}:d=2.0[bgm];"
    + f"[{6+n_bars}:a]highpass=f=100,afade=t=in:ss=0:d=0.15,adelay=300|300,volume=1.15[na];"
    + f"[na][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,"
    + f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]"
)

cmd = ["ffmpeg", "-y", "-v", "error",
       "-i", TTY, "-i", CAM,
       "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/title-scrim.png",
       "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/hud-board.png"]
for i in range(n_bars):
    cmd += ["-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/cap10-{i}.png"]
cmd += ["-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/素材/bottom-strip.png",
        "-i", BGM, "-i", NARR,
        "-filter_complex", filters,
        "-map", "[v]", "-map", "[a]", "-t", str(TOTAL),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        f"{OUT}/EP10-只上传精确读回-竖版-v001.mp4"]
# 输入索引：0 tty / 1 cam / 2 scrim / 3 hud / 4..(3+n) bars / (4+n) bottom-strip / (5+n) bgm / (6+n) 旁白整篇

if __name__ == "__main__":
    subprocess.run(cmd, check=True)
    print(f"rendered: {cmd[-1]}  TOTAL=21.2s（登记总时长）")
    print("旁白为整篇单次合成（take-4，含 MiMo (pauses) 句间标签）整轨混入；字幕按实测句边界预显示。")
