#!/usr/bin/env python3
"""EP11「正在更新固件」竖版 v001 骨架（v2 失败/进行中出口，~18.5s）：
素材四组（2026-10-27 session164/167/168/169，压缩 mp4 已拉回，全部 release=pending——
发布前须完成全片隐私审查并获用户批准，此关不过不出片）。
事件线（均有验收记录/task-output 可证）：tap 桥 PASS → 原生控制就绪待固件 →
168 构建 530s 预算超时 → 169 cache 续接 BUILD_DRIVER_EXIT=2（进度保留，flash=not_run）。
事实红线（session164 原文）：不能声称固件就绪/能控制设备/已完成 ESP-IDF 完整构建。
时间窗 TODO-实测：抽帧核对后填 SEG；旁白后补（整篇 MiMo 合成+pauses 标签流程）。
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP11-正在更新固件"
D = f"{BASE}/剪辑"
OUT = f"{BASE}/产物"
SRC = f"{D}/素材"
W, H = 1080, 1920
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
TOTAL = 18.5
os.makedirs(f"{D}/帧-样片", exist_ok=True)
os.makedirs(OUT, exist_ok=True)

S164 = f"{SRC}/2026-10-27-ep04-input-tap-bridge-retest-164"
S167 = f"{SRC}/2026-10-27-ep04-native-control-167"
S168 = f"{SRC}/2026-10-27-ep04-native-build-168"
S169 = f"{SRC}/2026-10-27-ep04-native-build-cache-169"
BGM = f"{D}/音频/bgm-ep11-v1.wav"

T1, T2 = "设备里为什么还看不见", "新固件，做到第二轮"

# ---- 文本（失败/进行中出口；若 session170 构建成功切成功版） ----
SUBS = [
    (0.20, 3.00, "Gold", "77 个文件传上去了\\N设备里还看不见。"),
    (3.00, 6.30, "Cap",  "缺的一环，是新固件。"),
    (6.30, 9.30, "Cap",  "触摸测试，全都过了。"),
    (9.30, 12.60, "Cap", "第一回，等了快十分钟\\N还没做完。"),
    (12.60, 15.60, "Cap", "接着上回的进度做\\N又卡住了。"),
    (15.60, 18.30, "Gold", "还没做成，但进度没丢。\\N你猜，下一次能做成吗？"),
]
BARS = [
    ("本轮实际结果 · 提前展示", "", 0.0, 2.9),
    ("触摸能力就绪 · 还没装进设备", "", 2.9, 6.2),
    ("触摸测试全过 · 还没真点过屏幕", "", 6.2, 9.2),
    ("第 1 次做 · 时间到了没做完 · 真实记录", "", 9.2, 12.5),
    ("第 2 次接着做 · 中途停了 · 进度保住了", "", 12.5, 15.5),
    ("还没装进设备 · 还没真点过屏幕", "", 15.5, 18.5),
]

# ---------- 标题暗底条 / HUD / 标注条 / ASS（复用 EP10 版式） ----------
scrim = Image.new("L", (1, 330))
for i in range(330):
    a = 226 if i < 250 else int(226 * (1 - (i - 250) / 80) ** 1.3)
    scrim.putpixel((0, i), a)
scrim = scrim.resize((W, 330))
sc = Image.new("RGBA", (W, 330), (10, 16, 20, 0))
sc.putalpha(scrim)
sc.save(f"{D}/帧-样片/title-scrim.png")

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dr = ImageDraw.Draw(img)
f_l = ImageFont.truetype(HIRA, 20, index=2)
f_v = ImageFont.truetype(HIRA, 26, index=0)
rows = [("做了", "2 次"), ("真点过屏幕", "0 次"), ("进度", "保住了")]
bw, bh = 360, 74
x, y = W - bw - 32, 640
dr.rounded_rectangle((x, y, x + bw, y + bh * 3), radius=10,
                     fill=(13, 21, 25, 205), outline=(92, 138, 148, 190), width=1)
for i, (k, v) in enumerate(rows):
    ry = y + 16 + i * bh
    dr.text((x + 20, ry), k, font=f_l, fill=(95, 211, 224, 255))
    dr.text((x + 118, ry - 4), v, font=f_v, fill=(220, 228, 232, 255))
img.save(f"{D}/帧-样片/hud-board.png")

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
    bar(text, f"cap11-{i}.png", prompt=prompt)

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
Dialogue: 0,0:00:00.00,0:00:{TOTAL:.2f},Badge,,0,0,0,,{{\\pos(540,56)}}── 织界探索日记 · EP11 ──
Dialogue: 0,0:00:00.00,0:00:{TOTAL:.2f},T1,,0,0,0,,{{\\pos(540,118)}}{T1}
Dialogue: 0,0:00:00.00,0:00:{TOTAL:.2f},T2,,0,0,0,,{{\\pos(540,184)}}{T2}
"""
open(f"{D}/titles11.ass", "w", encoding="utf-8").write(ass)

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
open(f"{D}/字幕11.ass", "w", encoding="utf-8").write(sub)

# ---------- 滤镜 ----------
# 输入索引：0 tty164 / 1 tty167 / 2 tty168 / 3 tty169 / 4 cam169 / 5 scrim / 6 hud /
#           7..12 bars / 13 bottom-strip / 14 bgm（旁白 take-1 后插为 15）
# 时间窗 TODO-实测：抽帧核对各 session 画面后填定；crop 为 EP10 同构近似值
def seg(idx, trim, crop="1080:800:186:150", zoom="0.08", zoompos="(ih-ih/zoom)/2", n=None):
    frames = int(float(trim.split(":")[1]) * 30 - float(trim.split(":")[0]) * 30)
    return (f"[{idx}:v]trim={trim},setpts=PTS-STARTPTS,fps=30,crop={crop},"
            f"zoompan=z='1.0+{zoom}*in/{frames}':x='(iw-iw/zoom)/2':y='{zoompos}':d=1:fps=30:s=1080x800[m{n}];")

mid = (
    # P1 0-3 结果先行：169 EXIT=2（TODO-实测：169 末段窗口）
    seg(3, "295:297.9", zoom="0.10", zoompos="ih-ih/zoom", n=1)
    # P2 3-6.3 缺的一环：167 原生控制就绪（TODO-实测窗口）
    + seg(1, "20:23.1", zoom="0.08", n=2)
    # P3 6.3-9.3 tap 桥 PASS：164 Lua PASS 滚动（TODO-实测窗口）
    + seg(0, "60:63.2", zoom="0.08", n=3)
    # P4 9.3-12.6 168 预算超时（TODO-实测窗口）
    + seg(2, "590:593.1", zoom="0.08", n=4)
    # P5 12.6-15.6 169 续接 EXIT=2（TODO-实测窗口）
    + seg(3, "588:591.1", zoom="0.08", n=5)
    # P6 15.6-18.5 下一问（TODO-实测窗口）
    + seg(3, "592:594.7", zoom="0.06", n=6)
    + "[m1][m2][m3][m4][m5][m6]concat=n=6:v=1:a=0,setsar=1[mid];"
)
top_cam = (
    f"[4:v]trim=200:208,setpts=PTS-STARTPTS,fps=30,crop=835:470:312:90,"
    f"scale=2160:1215:flags=lanczos,tpad=stop_mode=clone:stop_duration={TOTAL-8:.1f},"
    f"zoompan=z='1.0+0.05*in/{int(TOTAL*30)}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x608,setsar=1[top];"
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
    + "".join(cap_fade(7 + i, t0, t1) for i, (t0, t1) in enumerate(bar_windows))
    + f"[6:v]format=rgba,fade=t=in:st=9.3:d=0.3:alpha=1,fade=t=out:st=15.3:d=0.3:alpha=1[hud];"
    + f"[b2][hud]overlay=0:0[b3];"
    + "".join([f"[b{3+i}][c{7+i}]overlay=0:{CAP_Y}[b{4+i}];" for i in range(n_bars)])
    + f"[b{3+n_bars}][13:v]overlay=0:1408[b{4+n_bars}];"
    + f"[b{4+n_bars}]ass={D}/titles11.ass:fontsdir=/System/Library/Fonts,ass={D}/字幕11.ass:fontsdir=/System/Library/Fonts[v];"
    + f"[14:a]atrim=0:{TOTAL},volume=0.8,afade=t=out:st={TOTAL-2.0}:d=2.0[bgm];"
    + f"[bgm]aformat=channel_layouts=stereo,"
    + f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]"
)

cmd = ["ffmpeg", "-y", "-v", "error",
       "-i", f"{S164}/OTTY-screen.mp4",
       "-i", f"{S167}/OTTY-screen.mp4",
       "-i", f"{S168}/OTTY-screen.mp4",
       "-i", f"{S169}/OTTY-screen.mp4",
       "-i", f"{S169}/MAC-camera.mp4",
       "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/title-scrim.png",
       "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/hud-board.png"]
for i in range(n_bars):
    cmd += ["-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/cap11-{i}.png"]
cmd += ["-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/素材/bottom-strip.png",
        "-i", BGM,
        "-filter_complex", filters,
        "-map", "[v]", "-map", "[a]", "-t", str(TOTAL),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        f"{OUT}/EP11-正在更新固件-竖版-v001-样片.mp4"]

if __name__ == "__main__":
    subprocess.run(cmd, check=True)
    print(f"rendered: {cmd[-1]}  TOTAL={TOTAL}s（样片，无旁白；时间窗 TODO-实测）")
