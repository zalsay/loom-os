# 字幕规范

沉淀自 2026-10-14 v002 A 版多轮样式迭代（用户逐版反馈定稿）。烧录字幕前先读本文。

## 终版样式（用户定稿，勿回退）

**卡拉OK 逐字点亮流动字幕，无底框**

| 参数 | 值 | 说明 |
| --- | --- | --- |
| 已读字色 | `&H0064C8FA`（#FAC864） | logo 实测亮金主色。金色值必须用 PIL 从 `assets/engine` 的 Logo 采样，勿凭感觉写 |
| 未读字色 | `&H55FFFFFF` | 半透明暖白，暗淡可辨 |
| 描边 | `&H002B1D1D`，Outline=2.0 | 深棕，与深色纸纹页面呼应 |
| 阴影 | Shadow=1.2，BackColour=&H60000000 | |
| 字体/字号 | PingFang SC，FontSize=54 | ASS 内声明 `PlayResY: 1920`，字号直接用像素值 |
| 位置 | Alignment=2（底居中），MarginV=34 | |
| 动效 | `\kf` 填充式逐字点亮 | 读到哪里亮到哪里，与配音逐字对齐 |

## 硬规则（踩坑沉淀）

1. **满屏卡片视频字幕必须保证可读遮底**：页面底部常有原文案，纯细描边无底框会叠字不可读。两个可行方案：① 卡拉OK + 强描边（当前定稿，金色与页面文案色差够大）；② 贴合小底框（`BorderStyle=3, Outline=0.9` 收窄 padding）。**深色底框已被用户明确否决**；若用底框须暖色（奶油白 `&H26DCEEF5` + 深棕字）。
2. **BorderStyle=3 底框颜色由 OutlineColour 决定**，不是 BackColour（libass 行为）。只改 BackColour 无效，会出现深字叠默认黑框。
3. **force_style 走 PlayResY=288 基准**：FontSize=9 ≈ 60px、12.5 ≈ 83px（1080×1920 下），换算易错。要精确像素控制就写 .ass 文件并声明 `PlayResY: 1920`。
4. **逐字计时按字符权重分配，勿机械均分**：中文 1.0 / 标点 0.55 / ASCII 字母数字 0.62 / 空格 0.3。每条字幕时长 = 该句配音实测时长（测 wav → atempo 后定值）。
5. **多片段切片各自独立 .ass**（seg 内相对时间从 0 起），烧录：
   `ffmpeg -vf "subtitles=segN.ass:fontsdir=/System/Library/Fonts"`
6. **交付前抽帧验证**：每个页面至少 1 帧；同一条卡拉OK字幕抽 2 个时刻确认点亮进度在推进；确认字幕不与页面文案重叠。
7. **换旁白必须同步重生成字幕**：旁白文案/切片变更后沿用旧 ASS 必然字声错位（EP01 v005 踩坑）。逐句时间轴以实测语音为准（段内取静音图谱停顿比按字数比例更准），相邻句首尾相接防闪断，逐字权重分配规则同上。

## 配音时间轴约束（字幕计时的上游）

- 语音起点 = 片段起点 + 0.25s；允许语音延伸进 0.3s 过渡区，禁止跨入下一页正片。
- 页面窗口不够时优先精简文案（删（停顿）标签/破折号），其次 atempo（≤1.12 语速仍自然）。
- MiMo 语速 ~4.4 字/秒；带（停顿）（吸气）等音频标签时按 ~4.0 字/秒预算，每个标签额外 +0.3~1s。
- 片尾句不得被输出 `-t` 截断：混音前确认 `语音结束时刻 ≤ 片长`，不够就延长结尾定帧。
- 风格标签与音频标签（(温柔)、（停顿）、（吸气）等）写在 `episode.json` 的 narration 里即可进入 role:assistant content，无需改 TTS 代码；标签本身不得进入字幕文本。

## 示例 ASS 骨架

```ass
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Flow,PingFang SC,54,&H0064C8FA,&H55FFFFFF,&H002B1D1D,&H60000000,0,0,0,0,100,100,1.5,0,1,2.0,1.2,2,40,40,34,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.25,0:00:03.10,Flow,,0,0,0,,{\kf18}AI{\kf10} {\kf19}一{\kf19}秒{\kf19}写{\kf19}完{\kf19}代{\kf19}码
```
