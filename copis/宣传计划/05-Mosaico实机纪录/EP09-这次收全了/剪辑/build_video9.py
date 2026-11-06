#!/usr/bin/env python3
"""EP09「这次收全了」竖版 v001（沿用 EP08 wb 链路规范）：
1. 结构：倒叙闪前（结果行特写）→ 补叙（49 测试/授权窗口）→ 设备端 → 真实点击 →
   结果与校验 → 边界如实 → 下一关（session152 背板）。总长 40s。
2. 字幕：全 Cap 暖白 62px（EP06 基准）；标注条 0.3s alpha 淡入淡出（EP07 生命周期规范）。
3. 混音：旁白 take-1（MiMo voiceclone，33.76s）+ bgm-ep09-v1（EP08 v2 配方），
   loudnorm TP=-1.5 / alimiter limit=0.80 定稿公式。
4. 素材：147-segments/*（远端 ffmpeg crf26 定点转码，源 MOV 未动）+ tty152.mov（原始 90s）。
5. 事实边界：等待已快进（标注条声明）；"收全"仅指一份绑定 Lua 文件；152 背板标"未上传"。
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

BASE = "/Volumes/RC500/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP09-这次收全了"
D = f"{BASE}/剪辑"
OUT = f"{BASE}/产物"
SEG = f"{D}/素材/147-segments"
TTY_CLICK = f"{SEG}/tty-click.mp4"
TTY_EARLY = f"{SEG}/tty-early.mp4"
CAM_W2 = f"{SEG}/cam-w2.mp4"
TTY152 = f"{D}/素材/tty152.mov"
BGM = f"{D}/音频/bgm-ep09-v1.wav"
NARR = f"{D}/音频/take-2-narration.wav"
W, H = 1080, 1920
BG = (40, 56, 64)
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
TOTAL = 40.0
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
    bw, bh = 860, 48
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

bar("最终结果 · 提前展示", "cap-flash.png")
bar("49 项测试 · 单次授权窗口", "cap-tests.png")
bar("设备端 · Works 列表", "cap-device.png")
bar("主机已接收点击确认", "cap-click.png")
bar("实际等待 35 秒 · 此段已快进", "cap-settle.png")
bar("边界如实 · 非整机备份", "cap-boundary.png")
bar("本地模拟测试 · 0 设备请求 · 未上传", "cap-next.png", prompt="$")

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
Dialogue: 0,0:00:00.00,0:00:40.00,Badge,,0,0,0,,{{\\pos(540,56)}}── 织界探索日记 · EP09 ──
Dialogue: 0,0:00:00.00,0:00:40.00,T1,,0,0,0,,{{\\pos(540,118)}}上一集只回了一半
Dialogue: 0,0:00:00.00,0:00:40.00,T2,,0,0,0,,{{\\pos(540,184)}}这份备份，收全了
"""
open(f"{D}/titles9.ass", "w", encoding="utf-8").write(ass)

# ---------- 字幕（跟随场景窗口，与旁白分句对位） ----------
sub = f"""[Script Info]
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
Dialogue: 0,0:00:00.20,0:00:03.10,Gold,,0,0,0,,{{\\pos(540,1495)}}这次，是真的收全了。
Dialogue: 0,0:00:03.30,0:00:09.00,Cap,,0,0,0,,{{\\pos(540,1495)}}上一集它只回了一半。\\N这一份绑定备份，就等一次人工点击。
Dialogue: 0,0:00:09.20,0:00:12.00,Cap,,0,0,0,,{{\\pos(540,1495)}}设备那头，列表里多了它。
Dialogue: 0,0:00:12.20,0:00:15.50,Cap,,0,0,0,,{{\\pos(540,1495)}}点一下，35 秒保护期，不轮询。
Dialogue: 0,0:00:15.70,0:00:21.50,Cap,,0,0,0,,{{\\pos(540,1495)}}7 次读取全部成功\\N90189 字节，校验值三处一致。
Dialogue: 0,0:00:21.70,0:00:28.00,Cap,,0,0,0,,{{\\pos(540,1495)}}收全的，只是一份绑定 Lua 文件，不是整机\\NRuntime 还没跑起来。
Dialogue: 0,0:00:28.20,0:00:34.00,Cap,,0,0,0,,{{\\pos(540,1495)}}下一关：把新的 Runtime 完整传上去\\N传输协议已通过本地模拟测试
Dialogue: 0,0:00:34.20,0:00:39.50,Gold,,0,0,0,,{{\\pos(540,1495)}}下一集：只上传，精确读回。
"""
open(f"{D}/字幕9.ass", "w", encoding="utf-8").write(sub)

# ---------- 滤镜 ----------
# 中部 8 段（1080×800）：tty 特写/宽景交替 + 设备端 + 152 背板
def zp(z_in, z_hold):
    return (f"zoompan=z='if(lt(in,{z_in[0]}),1+{z_in[1]}*(1-pow(1-in/{z_in[0]},3)),"
            f"if(lt(in,{z_hold[0]}),{1 + z_in[1]}, {1 + z_in[1]}-{z_hold[1]}*(1-pow(1-(in-{z_hold[0]})/{z_hold[2]},3))))'"
            ":x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800")

mid = (
    # m1 V1 0-3.2 结果行特写（闪前；seg≈45 起结果 JSON 可见）
    f"[0:v]trim=45.5:48.7,setpts=PTS-STARTPTS,fps=30,crop=900:667:126:330,"
    f"zoompan=z='if(lt(in,40),1+0.18*(1-pow(1-in/40,3)),1.18)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m1];"
    # m2 V2 3.2-9.2 49 测试滚动 + CLICK READY
    f"[1:v]trim=0:6,setpts=PTS-STARTPTS,fps=30,crop=1200:889:126:169,"
    f"zoompan=z='if(lt(in,60),1+0.12*(1-pow(1-in/60,3)),if(lt(in,150),1.12,1.12-0.12*(1-pow(1-(in-150)/30,3))))':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m2];"
    # m3 V3 9.2-12.2 设备端 Works 列表（聚焦设备：源 810×600 @ (325,133)，去多余背景）
    f"[2:v]trim=1:4,setpts=PTS-STARTPTS,fps=30,crop=810:600:325:133,"
    f"scale=1080:800:flags=lanczos,"
    f"zoompan=z='1.0+0.08*in/90':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m3];"
    # m4 V4 12.2-15.7 点击确认时刻（seg 7.6 附近）
    f"[0:v]trim=5.8:9.3,setpts=PTS-STARTPTS,fps=30,crop=1200:889:126:169,"
    f"zoompan=z='1.10-0.10*in/105':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m4];"
    # m5 V5 15.7-21.7 结果与校验宽景
    f"[0:v]trim=43.5:49.5,setpts=PTS-STARTPTS,fps=30,crop=1200:889:126:169,"
    f"zoompan=z='if(lt(in,50),1+0.14*(1-pow(1-in/50,3)),1.14)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m5];"
    # m6 V6 21.7-28.2 边界（exit=0 收尾区域）
    f"[0:v]trim=48.5:55,setpts=PTS-STARTPTS,fps=30,crop=1200:889:126:169,"
    f"zoompan=z='1.10-0.10*in/195':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m6];"
    # m7 V7 28.2-34.2 下一关背板（152 末态）
    f"[3:v]trim=10:16,setpts=PTS-STARTPTS,fps=30,crop=1200:889:126:169,"
    f"zoompan=z='if(lt(in,60),1+0.10*(1-pow(1-in/60,3)),1.10)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m7];"
    # m8 V8 34.2-40.0 152 背板缓推
    f"[3:v]trim=16:21.8,setpts=PTS-STARTPTS,fps=30,crop=1200:889:126:169,"
    f"zoompan=z='1.06+0.06*in/174':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x800[m8];"
    f"[m1][m2][m3][m4][m5][m6][m7][m8]concat=n=8:v=1:a=0,setsar=1[mid];"
)
# 顶部 1080×608：设备端聚焦（cam-w2 源 835×470 @ (312,90)，克隆延长 + 缓推）
top_cam = (
    f"[2:v]trim=0:8,setpts=PTS-STARTPTS,fps=30,crop=835:470:312:90,"
    f"scale=2160:1215:flags=lanczos,tpad=stop_mode=clone:stop_duration=32.2,"
    f"zoompan=z='1.0+0.05*in/1200':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:fps=30:s=1080x608,setsar=1[top];"
)
base = f"color=c=0x283840:s=1080x1920:r=30:d={TOTAL}[base];"
overlays = (
    f"[base][top]overlay=0:0:enable='between(t,0,{TOTAL})'[b1];"
    f"[mid]crop=1080:712:0:44,setsar=1[midc];"
    f"[b1][midc]overlay=0:608[b2];"
)

# 标注条时间窗 + 0.3s alpha 淡入淡出
CAP_Y = 1140
def cap_fade(idx, t0, t1):
    parts = ["format=rgba"]
    if t0 > 0:
        parts.append(f"fade=t=in:st={t0}:d=0.3:alpha=1")
    if t1 < TOTAL:
        parts.append(f"fade=t=out:st={t1-0.3}:d=0.3:alpha=1")
    return f"[{idx}:v]" + ",".join(parts) + f"[c{idx}];"

bar_windows = [(0.0, 3.2), (3.2, 9.2), (9.2, 12.2), (12.2, 15.7),
               (15.7, 21.7), (21.7, 28.2), (28.2, 40.0)]
ann_caps = "".join(cap_fade(3 + i, t0, t1) for i, (t0, t1) in enumerate(bar_windows))
ann = (
    f"[2:v]format=rgba[scrim];"  # 注意：占位输入见下方 cmd 输入顺序
    f"[b2][scrim]overlay=0:0[b3];"
    + "".join([
        f"[b{3+i}][c{3+i}]overlay=0:{CAP_Y}[b{4+i}];" for i in range(7)
    ])
)
filters = (
    mid + top_cam + base + overlays + ann_caps + ann +
    f"[b10]ass={D}/titles9.ass:fontsdir=/System/Library/Fonts,ass={D}/字幕9.ass:fontsdir=/System/Library/Fonts[v];"
    f"[4:a]highpass=f=100,afade=t=in:ss=0:d=0.15,adelay=300|300,volume=1.15[na];"
    f"[5:a]atrim=0:{TOTAL},volume=0.8,afade=t=out:st=37.5:d=2.5[bgm];"
    f"[na][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,"
    f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]"
)

cmd = [
    "ffmpeg", "-y", "-v", "error",
    "-i", TTY_CLICK, "-i", TTY_EARLY, "-i", CAM_W2, "-i", TTY152,
    "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/title-scrim.png",
    "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/cap-flash.png",
    "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/cap-tests.png",
    "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/cap-device.png",
    "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/cap-click.png",
    "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/cap-settle.png",
    "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/cap-boundary.png",
    "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/帧-样片/cap-next.png",
    "-loop", "1", "-framerate", "30", "-t", str(TOTAL), "-i", f"{D}/素材/bottom-strip.png",
    "-i", BGM, "-i", NARR,
    "-filter_complex", filters,
    "-map", "[v]", "-map", "[a]", "-t", str(TOTAL),
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    f"{OUT}/EP09-这次收全了-竖版-v001.mp4",
]
# 输入索引核对：0 tty-click / 1 tty-early / 2 cam-w2 / 3 tty152 / 4 scrim / 5-11 bars(7) / 12 bottom-strip / 13 bgm / 14 narr
# 修正 filter 中的索引：scrim=[4:v], bars=[5..11:v], bottom-strip=[12:v], bgm=[13:a], narr=[14:a]
filters_fixed = (
    mid + top_cam + base + overlays
    + "".join(cap_fade(5 + i, t0, t1) for i, (t0, t1) in enumerate(bar_windows))
    + (
        f"[4:v]format=rgba[scrim];"
        f"[b2][scrim]overlay=0:0[b3];"
        + "".join([f"[b{3+i}][c{5+i}]overlay=0:{CAP_Y}[b{4+i}];" for i in range(7)])
        + f"[b10][12:v]overlay=0:1408[b11];"
        + f"[b11]ass={D}/titles9.ass:fontsdir=/System/Library/Fonts,ass={D}/字幕9.ass:fontsdir=/System/Library/Fonts[v];"
        + f"[14:a]highpass=f=100,afade=t=in:ss=0:d=0.15,adelay=300|300,volume=1.15[na];"
        + f"[13:a]atrim=0:{TOTAL},volume=0.8,afade=t=out:st=37.5:d=2.5[bgm];"
        + f"[na][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,"
        + f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]"
    )
)
cmd[cmd.index("-filter_complex") + 1] = filters_fixed
subprocess.run(cmd, check=True)
print("rendered:", cmd[-1])
