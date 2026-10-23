# EP07 v007 独立 Reviewer 证据归档

来源：reviewer 只读复核临时目录（2026-10-22 17:07–17:11），2026-10-23 09:18 由 claude 复制归档；原文件未改。

| 文件 | 大小 | SHA-256 |
| --- | ---: | --- |
| `full-frame-samples.png` | 1,258,981B | `93081b0f54533060a23a20be8c5536e1669e77c3cee76d4db544438959b9a1ae` |
| `three-stages-comparison.png` | 1,196,281B | `21087ec8c9761b41a8ea2005b1d86ba0b129e9d7a1e14fa7812afa007492309e` |
| `gold-scan.json` | 4,364B | `788dbf2ed58bd36e0fc3898db5ac86af4cbaacbe49bf271ab9db955f1c1f8663` |
| `gold-scan-annotation-and-source.json` | 333B | `f4a714ac6a1e1da698b85d3240aaad800ab9259877bb2a982b3ef5efe9d6c1a4` |

## 复跑 recipe（reviewer 2026-10-22 原始执行口径）

- **对象**：`产物/EP07-我传完了还没跑-竖版-v007.mp4`（md5 `68981a0b10cfb25200c3f9c2e5fdffba`）。
- **解码**：RGB24 全片解码 **735 帧**（`frame_index/30 = t`）；通道先转 `int16` 再比较，避免 uint8 溢出。扫描前统一 `crop=1080:792:0:608`（取终端区）。
- **严格金色阈值**（三套标注判据）：`R>=180, G>=120, B<=160, R>=G+15, G>=B+25`。
- **三套空间子 ROI 与有效时段**（半开区间，**成片全局坐标**；先 `crop` 的话 y 需减 608：oldlog `10–64`、focus `0–60`、pending `627–687`）：

| 标注 | 子 ROI（x × y） | 有效时段 |
| --- | --- | --- |
| oldlog-label（含「说明」小标） | `[220,860) × [618,672)` | `0 ≤ t ≤ 6.2` |
| focus-mask | `[0,1080) × [608,668)` | `6.2 ≤ t ≤ 10.2` |
| PENDING bar（含「说明」小标） | `[240,840) × [1235,1295)` | `10.28 ≤ t ≤ 16.37` |

- **原始暖色解释（第二层检查）**：比较基线是 **`剪辑/历史-v006/EP07-我传完了还没跑-竖版-v006.mp4` 同帧**（md5 `164c75bb8c7b31880f23a3b631823a58`），**不是未经剪辑的相机/OTTY 原 MOV**——两版走相同取样/裁切/zoom 链，同帧坐标才可比。
  - 宽松暖色 mask：`R>=120, G>=90, B<=180, R>=G+3, G>=B+10`。
  - 在 v006 同帧的宽松暖色 mask 上做 **±3px（7×7 方邻域）** 膨胀，匹配 v007 剩余严格金色像素；未匹配 `0`。
  - 该检查只证“剩余暖色来自源内容”，**不替代**三套标注子 ROI 各自的严格金色 0 结论。
- **不要混称两套 mask**：`gold-scan.json` 里的 `new_gold_unmatched_total: 2245` 是早期 **±2px 严格 mask 初筛**；最终结论来自上述 **宽松暖色 mask**，二者口径不同。
- 完整统计原文件保留在 JSON 中；本 README 只补复跑口径，**JSON 原字节未改**。

## 结论

- 三套标注层有效时段、各自子 ROI 内：可见严格金色像素 **总计 0、单帧最大 0**（`gold-scan-annotation-and-source.json`）。
- 源内容暖色解释后仍未匹配：**0**（`remaining_gold_without_source_warm_match_3px: 0`）。

## 2026-10-23 Reviewer 独立复跑记录

reviewer 按本 README 的 recipe 独立复跑，结果由 claude 单写者复制归档（新增文件，**不覆盖**上方 4 个原件）：

| 文件 | 大小 | md5 | SHA-256 |
| --- | ---: | --- | --- |
| `reviewer-rerun-2026-10-23.json` | 3,679B | `1b1aa7f534254637dad6787a4acf6c2f` | `b9fdcce297348e4cb03c1be4db5a3b1817abe0418f36b98a0c141fb73c00b06b` |

复跑摘要（详见 JSON）：

- 全解码 `rc=0`、stderr 0B；ffprobe `N=735`、`24.500000s`、`30/1`、音频 1057 包；ADTS 与 PCM 双指纹均与原记录一致。
- 三套子 ROI 有效帧数：oldlog 187、focus 121、pending 183（与时间窗按 30fps 推导一致）。
- 严格金色总数/单帧最大：三套均 **0 / 0**；源暖色未匹配 **0**。
- `video_sha256` = `ef576874afa49e5514959db1bff278aa7dbe74a2d53cd6930c206d30c9dd8baf`，与定版一致（成片未变）。
- 归档 4 原件的 SHA-256 复列于 JSON，与上表一致。

## 使用边界

- 证据只证明技术层面的颜色/解码/帧数结论，不替代人工试听、全片隐私复核与发布授权。
- 终端原文的黄色提示符（如「🌙 via」）属于原始录屏内容，不在标注层清零范围内，不得改动或删除。
