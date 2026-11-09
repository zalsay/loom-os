---
name: loom-motion-graphics
description: 制作织界 LoomOS 实机纪录的统一熊猫办公动画、双实录窗口、镜头推进与屏幕动效。用户提到加动效、Code2Video/code2vedio、熊猫办公桌、摄像机走近或步伐、调整桌椅、设备黑屏、复用视频模板，或制作后续实机纪录 EP 时使用。默认走项目 tools/loom-video-office 的配置式框架，保留原版 header/footer 和含AI生成视频标注；不自动发布。
---

# 织界统一办公动画

## 当前默认（2026-11-09 用户裁定）

后续实机纪录统一复用 **熊猫办公场景＋双实录窗口＋观察者后方慢推进/轻微步伐**。说明条固定为 **含AI生成视频**。此裁定覆盖历史按上下分区摆放动效的默认做法，不自动改动历史锁版成片。

- 模型保留指定低多边形熊猫与白眼；桌椅位置、MacBook 示意逐行上滚保持已确认风格。
- 两个无标题实录窗口固定在上方，header/footer 沿用品牌样式，不跟随镜头晃动。
- 实录与动画明确分开；黑屏不能推断设备未连接、关机或运行状态。
- 不把录屏里的事实改写为动画中的新开发结果，不把示意代码冒充真实日志。

## 入口与操作

从项目根定位 [统一框架说明](../../../tools/loom-video-office/README.md)（实际路径：`tools/loom-video-office/README.md`），读取配置字段与依赖后再运行。**每期复制配置 JSON，不再复制修改整套场景 JS。**

```bash
node tools/loom-video-office/render.mjs <当期配置.json> --validate
node tools/loom-video-office/render.mjs <当期配置.json> --preview
node tools/loom-video-office/render.mjs <当期配置.json>
```

- `--validate`：核对时长、裁切范围、输入与输出，缺依赖立即停止，不自动安装。
- `--preview`：看首中尾三维构图；预览的实录窗口是占位，最终成片必须再审看。
- 渲染：独立新修订目录，遇已有成片/帧目录不覆盖；合成后解码并记录来源 SHA 和配置。
- 设置 `CHROME_PATH/FFMPEG/FFPROBE` 适配已安装环境；不依赖历史 `/tmp` 文件。

## 按集制作

1. 读取当期事实记录、制作 TODO 和用户最新裁定；核准素材来源与授权。
2. 填当期期号、标题、完整时长、两路素材与源时间窗、源坐标遮挡、混好音轨、footer；配置路径均相对项目根目录。
3. 新集标题用 `header.lines`，同一集已确认标题可用 `header.source`；不要把 EP22 字样带进其他集。
4. 可调整 `camera` 镜头与步伐、滚屏速度；镜头减速不改变音轨、角色或实录播放速度。
5. 字幕传入已校准、只含旁白事件的 `subtitleAss`。静音检测/字数推算不等于听检，不宣称自动精确对齐。
6. 检查完整画幅的起止、行进中间、动作过渡和文字边界；AI 标注贯穿，用户指定之前不隐藏。
7. 成片＋系列封面＋**agy** 发布文案一起交用户确认；事实、技术、隐私、听感与发布授权分别记录。画面 AI 标注不替代平台 AI 声明。

## 维护边界

- 输出 MP4、配置和 `render-manifest.json`；额外抽帧写本集 `剪辑/审核证据-*/`。
- 只点亮有事实支持的状态，不能把“构建完成”画成“真机部署完成”。未来真实部署通过时再依据证据改变状态，不写成永远不能点亮。
- 统计必须保持口径（例如 build/pack 合计不能改成全是 pack）。动画中间数字不能作为最终封面数字。
- 本框架是项目自己的 Three.js 实现，不是已安装或验证过上游 Code2Video 全管线。用户参考视频展示的 OpenSenseNova 项目与早期研究的 showlab 同名项目要区分。

## 可选历史工具

仅当用户明确需要二维信息图时，读取 [二维设计参考](references/design.md)、[历史合成说明](references/integration.md)，使用 `scripts/motion_kit.py`。这些是旧路线，不覆盖当前默认办公框架及最新用户裁定。
