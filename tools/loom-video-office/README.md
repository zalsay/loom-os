# 织界统一办公动画框架

从 EP22 办公场景 v010 提取的可复用 Three.js + FFmpeg 管线。**2026-11-09 用户确认后续实机纪录统一采用此框架**；不影响历史已锁版视频。框架本身不配音、不生成事实、不上传平台、不操作设备。

默认画面：原版 header/footer + 左右两个无标题真实录制窗口 + 熊猫侧后方办公桌 + MacBook 示意滚屏 + 观察者由远到近及轻微步伐 + 常驻 **含AI生成视频**。模型、材质、窗口位置集中维护，不再每期复制长脚本。

## 环境

- Node.js 20+，已安装的 Three.js / Playwright，Chrome 或 Playwright Chromium，FFmpeg/ffprobe（生成标题/烧字幕需要 libass）。
- 现有项目依赖：`logo/panda-3d/node_modules`，配置可换路径；不自动安装或下载。
- 模型由配置指定，默认使用用户提供的 `logo/panda-3d/assets/panda-faceted-standing.glb`；不会修改原始 GLB。
- macOS 自动选已安装 Chrome；跨机器用 `CHROME_PATH`、`FFMPEG`、`FFPROBE` 指定已有程序。字体请在目标机安装 Hiragino Sans GB 或合适中文替代；不要把缺字当完成。
- 与 showlab/Code2Video 的 Manim 教学框架、OpenSenseNova 的 code-video 项目不是同一个实现；这里是项目本地可重建的办公动画框架，不声称运行过上述完整上游管线。

## 三个动作

在项目根目录运行（或加 `--root /项目路径`）：

```bash
# 先检查素材时长、裁切边界、输出及参数
node tools/loom-video-office/render.mjs <当集配置.json> --validate

# 预览三维场景：首、中、尾三帧（此时窗口是占位；实录/header/footer 在最终 FFmpeg 阶段合成）
node tools/loom-video-office/render.mjs <当集配置.json> --preview

# 正式渲染：逐帧动画 → 双实录与品牌头尾合成 → 全片解码 → 指纹记录
node tools/loom-video-office/render.mjs <当集配置.json>

node --test tools/loom-video-office/tests/config.test.mjs
```

本机 PATH 不含 Homebrew 时，命令前加 `PATH="/opt/homebrew/bin:$PATH"` 并用 `/opt/homebrew/bin/node`。

可直接运行的本集配置：
[office-ep22-v011.json](../../copis/宣传计划/05-Mosaico实机纪录/EP22-一千多项测试都过了打包还是失败/剪辑/office-ep22-v011.json)。

## 下一集需要换什么

复制配置，不复制渲染器。所有文件路径均相对 **项目根目录**，不是 JSON 所在目录；也接受绝对路径。

| 配置项 | 含义 |
| --- | --- |
| `schemaVersion` | 固定 1；不兼容版本拒绝 |
| `episode`、`duration` | 本期期号、秒数（2–120 秒，30fps 对齐） |
| `outputDir`、`outputName` | 当期新修订输出目录、MP4 文件名 |
| `model` | 已授权的原始 GLB |
| `cameraVideo`、`terminalVideo` | `path`、源 `start` 秒、`crop:[x,y,w,h]`、`masks:[[x,y,w,h],…]` |
| `audio` | 已混好且通过本集审核的完整音轨文件、`start`；可读 MP4 的音轨，不自行变速/自动合成 |
| `header` | 两行标题 `lines`（自动写 ASS）**或** `source:{path,start,crop}` 复用本集已有头部，不复用另一集标题 |
| `footer` | `kind:"image"` / `"video"`、`path`、可选源 `crop` / `start` |
| `subtitleAss` | 可选。只包含旁白字幕的已校对 ASS，1080×1920 坐标；不能夹带旧标题。省略表示不烧录字幕，绝不算字幕验收通过 |
| `camera` | `from/to/lookFrom/lookTo`、`holdStart/travelDuration`、`gaitHz/gaitStrength`；默认后方走近，`gaitStrength:0` 关闭步伐 |
| `scrollRowsPerSecond` | MacBook 示意代码滚屏速度，默认 1.55 |
| `pixelRatio` | 默认 1（720×1280 渲染后合成 1080×1920）；1.5 原生覆盖最终像素，耗时增加 |

固定布局由 `config.mjs` 的 `LAYOUT` 定义并与模板配套：1080×1920 / 30fps，header 高 280，footer 从 1688 开始；实录窗口位于 `[51,320,464,264]` 和 `[564,320,464,264]`。场景下移 82 CSS 像素（成片 123px），窗口不随镜头运动。**不要每集为填空擅改布局。**

### 使用新标题和图片 footer

```json
{
  "header": {"lines": ["本集主标题", "本集副标题"]},
  "footer": {"kind": "image", "path": "品牌底部装饰.png"}
}
```

其余字段从可运行配置继承。上述只是字段示例，不是一份完整可渲染配置。

## 输出与安全

输出目录含 MP4、`frames/`、`render-manifest.json`（配置、布局、来源 SHA、源场景 SHA、实际探测结果）、`config.resolved.json`。最终 MP4 或帧目录已存在则停止；失败后使用新修订目录，检查失败日志，不覆盖旧样片。不静默复用旧帧，不删除文件，不接管用户浏览器；临时服务仅绑定回环地址，结束时关闭。

真实录制先遮挡再裁切；遮挡坐标逐期确认。框架只能检查数值边界，不能判断每行是否包含隐私。素材正在下载时不要渲染；先核对大小/SHA、全片解码。输出解码成功不等于全片隐私、字幕或听感通过。

## 制作与交付约定

1. 先依据当期真实记录定脚本；不得把电脑端通过画成真机通过，不推断黑屏状态。
2. 本框架只解决合成和动画；旁白/TTS、逐句听检、字幕对齐走项目原流程，不按字数估时间冒充精确同步。
3. 保留常驻「含AI生成视频」。屏幕内移动色行是示意，不是伪造的日志。此标注不替代发布平台要求的 AI 声明。
4. 完整每集仍交付 **成片＋系列封面＋agy 生成的文案文档**，一次性交用户确认。试片验收不等于发布授权。
5. 本次改造没有自动更新既往锁版视频，也没有提交/推送 GitHub。

## 验证范围

基础测试覆盖跨集参数、固定窗口、禁用步伐、错误时长/裁切、输出覆盖防护；另外以 EP22 22 秒实录做端到端重渲。测试通过不保证任意新素材都正确，换集必须重新核验。
