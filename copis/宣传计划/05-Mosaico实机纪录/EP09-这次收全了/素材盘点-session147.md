# EP09 素材盘点（2026-10-26）

## 素材来源与完整性

- **session147**（2026-10-25，绑定 Lua 备份接收通过）：双路原片 `OTTY-screen.mov`（441M，600.01s）/ `MAC-camera.mov`（947M，600.01s）保留在远端 `i.meetlife.com.cn:~/Documents/dev/loom-os/copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-owned-backup-receive-147/原始素材/`，**未做任何修改或删除**。
- **session152**（2026-10-26，Runtime 传输核心离线验收）：`OTTY-screen.mov`（24M，90.0s）已拉回本地 `剪辑/素材/tty152.mov`，用于片尾"下一关"背板。
- 六帧复核图（两 session 各 3 帧）在 `剪辑/素材/帧-复核/`。

## 远端转码说明

- 远端无 ffmpeg（历史批量转码工具 `tools/batch_compress_mov.py`、`compress_otty_recording.py` 依赖的 ffmpeg 已不在；且二者会删除原片，不符合 session 证据保留规则，未直接使用）。
- 本次方案：远端临时安装静态 ffmpeg 9.0 ARM（`/tmp/ffmpeg9/ffmpeg`，来自 osxexperts.net），按 `compress_otty_recording.py` 定稿参数（`fps=30, libx264 veryfast, crf26, yuv420p, +faststart, -an`）**定点抽段**，输出到 `批量转码/2026-10-26-ep09-147-segments/`，原片零改动。
- 试过 `avconvert PresetHEVC1920x1080` 整片转码：中间产物超过原片体积（码率失控），已放弃并清理。

## 已拉回本地的片段（`剪辑/素材/147-segments/`）

| 文件 | 源 | 源时间窗 | 时长 | 大小 | 用途 |
| --- | --- | --- | --- | --- | --- |
| tty-early.mp4 | OTTY 147 | 0–12s | 12s | 2.1M | 49 测试滚动 + BACKUP CLICK READY |
| tty-click.mp4 | OTTY 147 | 385–440s | 55s | 1.3M | 点击确认（≈7.6s）/ 结果行（≈45s）/ exit=0 |
| tty-end.mp4 | OTTY 147 | 590–600s | 10s | 349K | 空闲末态（备用） |
| cam-w1.mp4 | 相机 147 | 60–68s | 8s | 120K | 设备端（干净，备用） |
| cam-w2.mp4 | 相机 147 | 300–308s | 8s | 123K | 设备端 Works 列表（成片采用） |
| cam-w3.mp4 | 相机 147 | 540–548s | 8s | 116K | **有人臂入镜，弃用** |
| 帧-cam/ 帧-tty/ | — | 1/5s、1/10s 调查帧 | — | ~4M | 时间轴核对与隐私排查 |

合计约 4.2M（远端产出 ≤10M 要求达成；全量 1.4G 原片未传输）。

## 关键时间轴（tty-click 段内）

- seg 0–7s：BACKUP CLICK READY 等待态
- seg ≈7.6s：真实点击 → CLICK_CONFIRMATION_ACCEPTED（主机接收确认时刻）
- seg 7.6–43s：35 秒保护期 + settle（成片快进，标注条声明）
- seg ≈45s：BACKUP RESULT `backup_verified: true, bytes: 90189, sha256: 72583b15…` 
- seg ≈50s：任务结束 exit=0

## 隐私核验

- [x] cam-w2（成片采用段）无人脸/人员局部
- [x] cam-w3 有人臂入镜 → 弃用并记录
- [x] 终端画面无密钥/Wi-Fi/账号；SHA 与 nonce 为公开摘要
- [ ] 发布前按《发布文案.md》事实边界做最后人工复核
