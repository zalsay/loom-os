# 图片生成 API

## 定位

`generate-image.mjs` 负责生成**无文字的全新底图**；`render-cover.mjs` 负责统一遮罩和中文排版。两者分开执行，先审看底图，再做封面。

- **原图合成**：不调用图片 API，直接使用用户图片，像素内容不重画。
- **参考图生图**：`mode=reference`，以 multipart/form-data 上传 `reference`，请求 `POST <base>/images/edits`。模型参考图片和提示词生成新图，不保证逐像素保留主体或事实。
- **提示词生图**：`mode=prompt`，以 JSON 请求 `POST <base>/images/generations`。可以直接描述配色，也可以给 `palette` 色值。
- **仅参考配色**：提示词模式增加 `paletteImage`，在本地提取五组主要色彩，仅把色值写进提示词，**不上传这张图**。色彩接近是模型指令，不是色差或构图一致性保证。

只支持 OpenAI Images 兼容的同步端点与 `data[0].b64_json` / `data[0].url` 响应。不声称支持 Gemini 原生接口、异步任务轮询或任意服务商的私有格式；兼容服务的模型、尺寸、quality 和参考图支持必须另行确认。示例协议基于 OpenAI Images 常用结构；此环境访问官方 API 文档返回 403，尚未对指定服务进行真实付费联调。

## 环境变量

| 变量 | 用途 |
| --- | --- |
| `IMAGE_API_BASE_URL` | API 基址，默认 `https://api.openai.com/v1`，兼容服务通常填其 `/v1` 基址，而非完整 generations 路径；也支持 `OPENAI_BASE_URL` 回退 |
| `IMAGE_API_KEY` | API 密钥，也支持 `OPENAI_API_KEY` 回退；仅从环境读取，不写入任务、日志或生成记录 |
| `IMAGE_MODEL` | 必填，指定该服务实际支持的图片模型；脚本不擅自选择或切换模型 |
| `IMAGE_DOWNLOAD_HOSTS` | URL 返回方式的图片下载主机白名单，逗号分隔、精确主机名匹配；默认只允许 API 主机，CDN 必须显式列出 |

网络请求只使用 HTTPS，本机开发的 localhost/127.0.0.1/::1 API 端点例外。图片下载仅 HTTPS，不跟随跳转，绝不携带 API Authorization。服务返回未授权的 CDN 地址时，先确认可信域名，再配置白名单，不自动放宽。

密钥应通过当前环境的凭据管理方式注入。不要读取、打印或复用聊天模型的私有配置，不在聊天里索要真实密钥，也不要提交包含凭据的命令或文件。

## 调用

将示例任务复制到本次独立目录，填写提示词及输出路径。所有任务路径相对任务 JSON；不要改写共享示例或覆盖历史成品。

```bash
# 只检查配置、提取配色并展示安全请求预览，不联网，不收费，不写图片。
node <skill-root>/scripts/generate-image.mjs /absolute/path/generation.json --dry-run

# 确认服务/模型、上传授权与可能费用后，才真正请求。
node <skill-root>/scripts/generate-image.mjs /absolute/path/generation.json

# 审图后，在封面任务的 image 字段引用生成的 PNG。
node <skill-root>/scripts/render-cover.mjs /absolute/path/cover-job.json --validate
node <skill-root>/scripts/render-cover.mjs /absolute/path/cover-job.json
```

`--dry-run` 缺少密钥/模型时仍展示请求结构，`ready=false` 和 `missing` 列出未配置项；不能把 dry-run 成功称为 API 已验证。真实调用缺少这些变量会在联网前报错。

## 两种任务示例

### 参考图生成

```json
{
  "mode": "reference",
  "reference": "./reference.webp",
  "prompt": "以参考图的草甸绿、浅薄荷绿和暖白为主色，重新生成一幅乡野共居主题的自然风景。中下部一辆小巴停在草地上，远处是起伏的山丘。不要复刻原海报的文字或品牌。",
  "size": "1024x1536",
  "quality": "medium",
  "output": "./background-v001.png"
}
```

### 提示词 + 相似配色

```json
{
  "mode": "prompt",
  "paletteImage": "./reference.webp",
  "palette": ["#C8DDD1", "#718C32", "#E8E7CE"],
  "prompt": "春日草甸、低缓山丘与一辆暖白色小巴，自然摄影质感，绿色为主、暖白点缀。主体置于中下部，上方预留干净的标题空间。",
  "size": "1024x1536",
  "output": "./background-v001.png"
}
```

只给提示词、不参考任何本地图时，省略 `paletteImage`；配色可写在提示词内，也可以使用 `palette`。

字段：`prompt`、`output` 必填；`mode` 默认 prompt；`reference` 只允许 reference 模式；`paletteImage` 两种模式均可用，仅在本地取色；`palette` 最多八个 `#RRGGBB`。显式色值优先，再补取色结果，总计最多八个。未知字段报错。

`size` 允许 `1024x1024`、`1024x1536`、`1536x1024`、`auto`；默认竖向 `1024x1536`。这是 API 生成尺寸，不是最终封面的 1080×1440；后续按已确认封面比例等比裁切。`quality` 可省略或选 auto/low/medium/high，是否受服务支持需实际确认。`timeoutMs` 默认 180000，范围 1000–600000。每次请求一张，无自动重试；超时也可能已被服务计费，核实服务端状态后再手动决定是否重试。

## 请求与返回

提示词模式发送 JSON：`model`、`prompt`、`n=1`、`size`、可选 `quality`。参考图模式发送同名表单字段及单个 `image` 文件字段，不手工设置 multipart Content-Type。脚本自动补充“无文字/Logo、水印，无模糊，上方留标题区”的底图约束；遮罩和文字不交给图片模型。

默认不发送 `response_format`，因为不同图片模型支持不同；优先解析 `b64_json`。URL 响应仅从可信白名单主机下载。图片会实际解码，再保存为 PNG；返回非图片、HTTP 错误、异常尺寸、超大响应时停止，不将失败响应当作 PNG。

成功写入 PNG 和同名 `.generation.json`，记录模型、实际提示词、配色、输入哈希、输出哈希和 AI 生成属性。不保存密钥、原始请求文件字节、base64 或服务返回的签名图片 URL。任何输入和既有输出都不覆盖；记录中 `visualApproved=false`，生成成功不等于用户批准。

## 审核与安全

- 新增 API 方法不代表当前已授权把所有用户图片发送到外部。真实执行前确认服务商、费用和参考图上传授权，尤其是人物、儿童、设备屏幕和非公开素材。纯提示词/本地取色可避免原图外传。
- 参考模式输出是 AI 生成的相似场景，不是原图记录，不把它冒充真实活动、实际地点、课程成果或真实设备状态。保留 AI 来源记录；按实际发布平台要求另做声明。
- 图片中文字或 Logo 仍可能偶发出现，必须用图像工具查看，不能承诺 prompt 能绝对保证无字。失败时先调整提示词或经用户确认再请求，不自动循环计费。
- 生成后延续用户裁定：上部仅半透明遮罩，无模糊；底部不遮罩、不压暗。以主标题和金色副标题结束，默认不再加一句小字尾句。
- 本次开发只进行 mock API 测试和本地流程验证；真实服务联通性、具体模型效果与实际计费未验证。
