---
name: create-zhi-jie-video
description: 根据织界课程进展制作或更新竖屏视频，包括品牌宣传、课程周报、孩子探索过程、作品展示和阶段回顾。统一织界 Logo、深色蜡笔绘本风格、分镜、逐字稿、MiMo TTS 配音、混音、字幕、导出和保存。用户说“做本周课程视频”“更新织界宣传片”“根据课堂记录做视频”“做小车或农场阶段回顾”时使用。
---

# 织界课程视频

延续已确认的品牌与风格，把每期课程事实变成孩子主导的故事。

## 阅读入口

- 先读 [品牌与视觉](references/brand.md) 和 [课程叙事](references/course-story.md)。
- 制作时读 [执行流程](references/production.md)；修改分镜时读 [项目格式](references/episode-format.md)。
- 配音前读 [MiMo 配音](references/mimo-tts.md)，检查其中官方文档的当前接口。
- 烧录字幕前读 [字幕规范](references/subtitles.md)：卡拉OK逐字点亮亮金样式为用户定稿，含样式表、硬规则与配音时间轴约束。

## 每期执行

1. 定位用户给的课堂记录、草图、照片、数据和视频源文件。读取当前内容，按对应连接器技能访问 Drive/Library。直接使用已授权来源，不重复询问已知品牌和风格。
2. 选视频用途：宣传突出课程方法；周报突出本次变化；过程片突出方案与测试；展示突出孩子解释与局限。默认约60秒、9:16。事实不足时先完成框架，集中补问孩子尝试、发现与下一步；不要虚构引语、数值或成果。
3. 用 `scripts/new_episode.py` 创建每期独立目录。填写 `lesson-input.md` 和 `episode.json`，将各镜头事实与来源写入 `evidence`。新一期使用新 `episode_id`；同一期修改递增 `revision`，保留往期成片。
4. 写逐字稿并安排分镜。围绕“孩子提问题 → 作出选择 → 动手测试 → 观察结果 → 修改或提出新问题”按实际进展取舍。使用 **AI 引导，孩子思考，共同实现**，保留尚未解决的问题。
5. 选场景库布局，按需修改本期复制的渲染器；不要把小车或农场强行套进其他课题。用 `video_pipeline.py PROJECT validate` 和 `stills` 检查。模板占位文字不能进入交付。
6. 导出逐字稿，调用 `mimo_tts.py PROJECT`，再用 `video_pipeline.py PROJECT align` 对齐。脚本按请求指纹判断缓存；文本、模型、音色、指令或窗口改变时重新合成相应片段。超时先缩短文案或调整镜头，变速最多1.2倍，不截断句尾。
7. 用 `video_pipeline.py PROJECT build` 导出。仅改旁白时用 `--picture` 复用已检查画面，并比较视频包哈希；画面或时间线变化时重新渲染。旁白期间压低配乐，保留观察停顿。SRT 句内时间是近似对齐，不宣称逐字精度。
7a. 烧录字幕按 [字幕规范](references/subtitles.md) 执行：默认卡拉OK逐字点亮亮金样式（无底框），逐字计时按字符权重对齐配音实测时长，禁用深色底框，交付前抽帧验证每页可读且不与页面文案重叠。
8. 用 `video_pipeline.py PROJECT check` 做本地检查，查看各场景、翻页、片尾并实际试听。环境不能试听时只报告已做的时长、峰值、字幕和画面检查，不声称听过。不要默认使用云端ASR、声线克隆、其他服务或公开视频平台。
9. 用 `video_pipeline.py PROJECT package` 打包。交付MP4、逐字稿、MP3/WAV、SRT和可重建源文件ZIP。按指定位置保存；未指定时按当前环境的持久化文件流程保存。修改同一期保持文件身份及版本；新一期创建新文件。仅在明确要求时更新Drive、分享或发布。
10. 写本期 `release.json`，记录来源、版本、检查和实际保存位置，供后续继续。不得保存密钥、签名链接或儿童私人身份。展示视频并简短说明本期变化，附配音和逐字稿链接。

## 命令

用实际读取的 skill 目录作为 `<skill-root>`，不要依赖旧对话的 scratch 路径。

```bash
python3 <skill-root>/scripts/new_episode.py week-03 --output /absolute/workdir --kind course-update
python3 <skill-root>/scripts/video_pipeline.py /absolute/workdir/week-03 validate
python3 <skill-root>/scripts/video_pipeline.py /absolute/workdir/week-03 stills
python3 <skill-root>/scripts/mimo_tts.py /absolute/workdir/week-03 --dry-run
# MIMO_API_KEY 由当前执行环境提供，不写真实密钥进文件或示例。
python3 <skill-root>/scripts/mimo_tts.py /absolute/workdir/week-03
python3 <skill-root>/scripts/video_pipeline.py /absolute/workdir/week-03 align
python3 <skill-root>/scripts/video_pipeline.py /absolute/workdir/week-03 build
python3 <skill-root>/scripts/video_pipeline.py /absolute/workdir/week-03 check
python3 <skill-root>/scripts/video_pipeline.py /absolute/workdir/week-03 package
```

没有密钥时可复用完全匹配的缓存配音；新配音缺少密钥或接口不可用时继续完成其他环节，明确未完成状态，不用其他服务冒充MiMo。

## 素材

`assets/engine` 包含原创绘本图元、定稿Logo、带许可的中文字体和可编辑场景库；`assets/templates/lesson-input.md` 为每期记录模板。完整V12历史动画源文件的Library身份为 `libfile_58685cf8efe4819197b2f68f7f36c266`，需要时先定位当前版本再取出，不假定旧文件名永远有效。
