#!/usr/bin/env python3
"""EP02 开发纪实竖版：上半设备画面 + 下半 Otty 终端录屏，旁白+字幕+BGM。"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
DEV_H = 608          # 上半设备画面区
OTTY_Y = 608         # Otty 区起点
OTTY_H = 800         # Otty 区高 (1080x800)
STRIP_Y = 1408       # 底部装饰区起点
BG = (40, 56, 64)
GOLD = (250, 200, 100)
LOGO = "/Volumes/RC500/dev/loom-os/logo/Zhi-Jie-logo.png"
HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
D = "/tmp/ep2live"

# ---------- 1. 底部装饰层 1080x512 ----------
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

# ---------- 1b. Otty 聚焦蒙层 1080x800 ----------
# 加深蒙层压住终端上部，底部命令行输出区（y650-800）保持清晰，向上 70px 羽化过渡
MASK_A, clear_top, feather = 170, 675, 60
mask = Image.new("RGBA", (W, OTTY_H), (0, 0, 0, MASK_A))
# 逐行设置透明度：y<clear_top 蒙层 MASK_A，clear_top-feather 起线性羽化到 0，以下全透
mpx = mask.load()
for y in range(clear_top - feather, OTTY_H):
    a = int(MASK_A * (clear_top - y) / feather) if y < clear_top else 0
    for x in range(W):
        mpx[x, y] = (0, 0, 0, a)
mask.save(f"{D}/otty-mask.png")

# ---------- 2. 旁白时间轴（v008 AI 第一人称版，whisper 对齐 + atempo 0.9346） ----------
# 音频 32.69s 摆放偏移 0.8s；时间 = whisper 原始时间 / 0.9346 + 0.8
CAPS = [
    (0.80, 3.37, "板子到手第二天 我没急着动手"),
    (3.37, 5.38, "先把它从里到外摸了一遍"),
    (5.38, 7.95, "串口通不通 端口有没有被占"),
    (7.95, 9.75, "相机能不能拍到画面"),
    (9.75, 13.34, "只看不改 弄坏了可没后悔药"),
    (13.34, 15.01, "接着验证Lua"),
    (15.01, 16.77, "说实话我心里也没底"),
    (16.77, 19.93, "真机脚本跑不跑得动 谁都不敢打包票"),
    (19.93, 23.87, "我就一条条试 跑不通就记下来 不猜也不装"),
    (23.87, 26.61, "我负责干活 人负责把关"),
    (26.61, 28.92, "出了问题随时能翻记录"),
    (28.92, 30.47, "关注织界"),
    (30.47, 33.42, "看一块板子长成孩子的探索工具"),
]
VIDEO_LEN = 35.8
CUT1, CUT2 = 13.34, 23.87     # 段落边界（与上下画面 xfade 同步）

caps = CAPS

GOLD_WORDS = ["只看", "Lua", "不猜", "关注织界"]

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
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},Badge,,0,0,0,,{{\\pos(540,120)}}──  织界创造日记 · EP03  ──")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T1,,0,0,0,,{{\\pos(540,200)}}我没急着动手")
lines.append(f"Dialogue: 0,{fmt(0)},{fmt(VIDEO_LEN)},T2,,0,0,0,,{{\\pos(540,300)}}先摸个底")
for st, en, tx in caps:
    lines.append(f"Dialogue: 0,{fmt(st)},{fmt(en)},Cap,,0,0,0,,{{\\pos(540,1470)}}{mark_gold(tx)}")
with open(f"{D}/dev.ass", "w") as f:
    f.write("\n".join(lines) + "\n")
print("ASS written,", len(caps), "captions, video", VIDEO_LEN, "s")

# ---------- 3. ffmpeg 渲染 ----------
# 关键帧动效（Remotion 语义）：interpolate(in, [0,24], [1,1.0X], {easing: out(cubic), clamp})
# = 每段起点关键帧，前 0.8s（24帧）ease-out 快速放大，之后 clamp 停住不漂移。
# easeOutCubic(t) = 1-(1-t)^3；视频流先超采样再 zoompan 缩回防糊。
def keyframe_zoom(zoom_max, frames=24):
    # z 表达式：ease-out 到位后 clamp（表达式内逗号需 \, 转义）
    return f"z='1+{zoom_max}*(1-pow(1-min(in/{frames}\\,1)\\,3))':fps=30"

# 下半终端：聚焦循环动效——每段「释放(全画幅) → 4.0s后 ease-in 聚焦左下 → 保持 → 段尾前2.3s 释放」
# zoom 分段：in<120 全画幅 1.0；120-144帧 ease-out 推进到 1.30；保持；N-69 起 24帧 ease-in 缩回 1.0
# （聚焦时机延后到命令真正执行后：ch1 素材 24.8s 起为 curl 输出滚动段，避开 20-22s 命令间隙）
# y='ih-ih/zoom-off'：off 抵消源帧底部黑边（live-02 74px/live-03 42px 换算超采样），聚焦视窗底边对齐命令行内容底、顶边抬高
# zoom=1 时 y=-off 被 clamp 到 0（全画幅）；x=0 恒左对齐命令行起点
def keyframe_zoom_cycle(seg_s, off, zoom_max=0.30, fin=120, flen=24, tail=69, fps=30):
    N = int(round(seg_s * fps))
    fout = N - tail
    z = (f"if(lt(in\\,{fin}),1,"
        f"if(lt(in\\,{fin + flen}),1+{zoom_max}*(1-pow(1-(in-{fin})/{flen}\\,3)),"
        f"if(lt(in\\,{fout}),1+{zoom_max},"
        f"if(lt(in\\,{fout + flen}),1+{zoom_max}-{zoom_max}*pow((in-{fout})/{flen}\\,3),1))))")
    # 注意 zoompan 必须显式 fps=30：zoompan 输出帧率默认 25，会导致 xfade 按 25fps 计时、
    # z 表达式（基于帧号 in）与 PTS 脱钩——聚焦进入延后、缩回被推入 xfade 过渡区永远看不到
    return f"z='{z}':x='0':y='ih-ih/zoom-{off}':fps=30"

# 每段 otty 链：zoompan 循环 + 动态蒙层（fade in 4.0-4.8s / fade out 段尾前 2.3-1.5s，与 zoom 同步）
# off = 源帧底部黑边换算到超采样(2160x1600)坐标：live-02(高1058,黑边74)→112；live-03(高1014,黑边42)→66
def otty_chain(seg_s, idx):
    N = int(round(seg_s * 30))
    fout_s = (N - 69) / 30
    crop = "crop=1428:1058:12:0" if idx == 1 else "crop=1368:1014:20:0"
    off = 112 if idx == 1 else 66
    vf = (f"{crop},scale=2160:1600,fps=30,"
        f"zoompan={keyframe_zoom_cycle(seg_s, off)}:d=1:s=1080x800,setsar=1,setpts=PTS-STARTPTS")
    mf = (f"[{8 + idx}:v]format=rgba,fade=t=in:st=4.0:d=0.8:alpha=1,"
        f"fade=t=out:st={fout_s:.2f}:d=0.8:alpha=1[m{idx}];")
    return (f"[{2 + idx}:v]{vf}[o{idx}];" + mf +
        f"[o{idx}][m{idx}]overlay=0:0[o{idx}m];")

vf_dev = ("crop=900:506:80:100,scale=2160:1216,fps=30,"
    f"zoompan={keyframe_zoom('0.08')}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    ":d=1:s=1080x608,setsar=1,setpts=PTS-STARTPTS")
cmd = [
    "ffmpeg", "-y", "-loglevel", "warning",
    "-ss", "3", "-t", "13.9", "-i", f"{D}/tp-verify20.mp4",               # 0 设备视频 ch1
    "-ss", "40", "-t", "11.1", "-i", f"{D}/tp-verify20.mp4",              # 1 设备视频 ch2
    "-ss", "88", "-t", "12.5", "-i", f"{D}/tp-verify20.mp4",              # 2 设备视频 ch3
    "-ss", "20", "-t", "13.9", "-i", f"{D}/OTTY-CODEX-live-02.mp4",    # 3 otty ch1（活跃输出段）
    "-ss", "8", "-t", "11.1", "-i", f"{D}/OTTY-CODEX-live-03.mp4",     # 4 otty ch2（活跃输出段）
    "-ss", "88", "-t", "12.5", "-i", f"{D}/OTTY-CODEX-live-03.mp4",    # 5 otty ch3（滚动高峰段）
    "-i", f"{D}/clone/full_tight2.wav",                                   # 6 旁白（AI第一人称 4.4字/秒）
    "-i", "/tmp/ep1/bgm-upbeat2.wav",                                     # 5 BGM
    "-i", f"{D}/bottom-strip.png",                                        # 8 底部装饰
    "-loop", "1", "-framerate", "30", "-t", "13.9", "-i", f"{D}/otty-mask.png",  # 9 蒙层 ch1
    "-loop", "1", "-framerate", "30", "-t", "11.1", "-i", f"{D}/otty-mask.png",  # 10 蒙层 ch2
    "-loop", "1", "-framerate", "30", "-t", "12.5", "-i", f"{D}/otty-mask.png",  # 11 蒙层 ch3
    "-filter_complex", (
        # 上半设备画面：TP 相机视频三段 xfade（与下半 Otty 切点同步 14.3/27.8）
        f"[0:v]{vf_dev}[d1];"
        f"[1:v]{vf_dev}[d2];"
        f"[2:v]{vf_dev}[d3];"
        f"[d1][d2]xfade=transition=fade:duration=0.5:offset={CUT1}[dx1];"
        f"[dx1][d3]xfade=transition=fade:duration=0.5:offset={CUT2}[dev];"
        f"color=c=0x283840:s=1080x1920:r=30:d={VIDEO_LEN}[base];"
        f"[base][dev]overlay=0:0[b1];"
        + otty_chain(13.9, 1) + otty_chain(11.1, 2) + otty_chain(12.5, 3) +
        f"[o1m][o2m]xfade=transition=fade:duration=0.5:offset={CUT1}[x1];"
        f"[x1][o3m]xfade=transition=fade:duration=0.5:offset={CUT2}[otty];"
        f"[b1][otty]overlay=0:{OTTY_Y}[a];"
        f"[a][8:v]overlay=0:{STRIP_Y}[b];"
        f"[b]ass={D}/dev.ass,format=yuv420p[v];"
        f"[6:a]adelay=800|800,volume=1.15,apad[vo];"
        f"[7:a]atrim=0:{VIDEO_LEN},volume=0.35,afade=t=out:st={VIDEO_LEN-2}:d=2[bg];"
        f"[vo][bg]amix=inputs=2:duration=first:normalize=0,aformat=channel_layouts=stereo,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[aout]"
    ),
    "-map", "[v]", "-map", "[aout]",
    "-t", str(VIDEO_LEN),
    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
    f"{D}/EP02-开发纪实-竖版-v019.mp4",
]
subprocess.run(cmd, check=True)
print("rendered")
