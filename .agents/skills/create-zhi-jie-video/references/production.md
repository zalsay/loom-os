# 执行流程

## 工具与工作目录

需要Python 3、numpy、Node.js、`@napi-rs/canvas`、ffmpeg/ffprobe。当前模板固定canvas 0.1.100，先复用当前环境依赖；独立环境可在本期目录执行 `npm install`，不要把node_modules打包。

新建目录后改episode.json。脚本都复制到本期 `tools/`，源文件ZIP可独立继续构建，不依赖skill在旧scratch的位置。

```bash
python3 tools/video_pipeline.py . validate
python3 tools/video_pipeline.py . script
python3 tools/video_pipeline.py . stills
python3 tools/mimo_tts.py . --dry-run
python3 tools/mimo_tts.py .
python3 tools/video_pipeline.py . align
python3 tools/video_pipeline.py . build
python3 tools/video_pipeline.py . check
python3 tools/video_pipeline.py . package
```

配音只使用环境变量密钥。dry-run不发请求、不需要密钥。每期原始配音与对齐记录保留在narration目录。文本或时间线改变后重复相应步骤；build拒绝覆盖已有版本成片。

仅改旁白时：递增revision，准备当前匹配音频并align，然后 `build --picture /absolute/checked-picture.mp4`。该参数只复用画面，新配乐按本期时间线生成，不会混入旧旁白。若要复用其他原创音乐，改本期混音脚本并核实其为单独音乐轨；不要从含旁白的混音里直接叠加新旁白。

## 检查

先看每个场景静帧和翻页帧。检查顶部约100px空白、页眉与标题间距、主体与标题、正文卡片、字幕和片尾是否相撞；在手机尺寸预览，确认中文易读。编码后再看 `out/encoded-check`，检查实际成片。

自动check核对尺寸、fps、帧数、总长、旁白窗口、速度上限、PCM峰值，导出封面与实际视频检查帧，写release.json。它不验证事实或发音。人工查看和实际试听后填写对应状态；不能试听就明确保留pending，并如实交付。

对白时间窗预留翻页与余韵，变速不超过1.2。音乐在旁白期间自动压低。导出H.264/yuv420p/AAC/faststart；SRT作为可选字幕轨，不再叠一层烧录文字遮住纸面字幕。

## 交付与延续

每期交付命名 `Zhi-Jie-<episode_id>-vNNN.mp4` 和对应source.zip，另有逐字稿.md、narration.mp3/wav、narration.srt、poster.jpg。ZIP包含脚本、事实输入、分镜、字稿、Logo、字体许可、原始配音和对齐记录，排除密钥、node_modules、临时输出、日志和成片重复副本。

保存到明确指定的位置，未指定时按环境的持久化流程；不能只提供临时文件链接。保存后更新release.json的saved_locations，记录稳定文件身份，必要时刷新源ZIP。同一期修改保持已有文件身份与版本，新一期创建新身份。不要自动发布、分享或改权限。

后续继续时读取当前课程记录与最近同一期release，保留风格，按本次事实换主题、分镜、字稿和证据。宣传片模板不是必须逐期重复的课程流程。
