# Mosaico 真机验收清单：Loom OS Patch 01–08

日期：2026-09-24。记录每项的固件版本、Runtime 版本、设备序列号、日志和 PASS/FAIL。先在测试设备上备份 `loom-os/` 与 `loom-os-runtime/`。

## 前置条件

- [ ] 将 `provision/runtime_files.lua` 的 60 个运行时文件打包；逐项核对文件存在和 Lua 语法。新装设备运行一次 `provision/install_initial.lua`，安装 0.1.1 集成候选；已有 0.1.0 设备通过 Runtime OTA 发布 0.1.1，不重跑初始安装。
- [ ] 运行 `tests/runtime_provision_check.lua`，确认 active、last_good 与 release 路径。
- [ ] 固件提供 `storage`、`json`、`lvgl`、`gpio`、`board_manager`；记录 Mosaico LCD、触控及系统时钟实测值。
- [ ] 明确是否已有经过验证的 soil.moisture Lua 驱动、非阻塞 HTTPS 适配器、Agent 结构化输出提供者。未接入时对应 API 必须返回 `E_UNSUPPORTED`，不得报告假成功。

## Patch 01 / 02 / 04：Service 与诊断

- [ ] 在 Launcher 启动 Hardware Diagnostics；显示 ESP-Mosaico、480×480、已注册传感器；没有电池/传感器驱动时显示不可用，不能编造读数。
- [ ] 安装 AI Farm 后启动 `soil-monitor`；服务 Context 不含 `ui/nav`，关掉 App 后服务和定时器仍运行；手动停止后资源释放。
- [ ] 重启后验证 manifest 的 `autostart=true` 服务能启动；pending 候选不得在健康确认前自动运行。
- [ ] 连续启动/关闭 20 次，检查定时器、UI、内存与 crash 日志；普通 App 无法访问未声明的 Service。

## Patch 03：Runtime OTA

- [ ] C01 初始 0.1.0 active；C02 HTTPS 获取与版本门禁；C03 下载后逐文件大小校验。
- [ ] C04 staging 文件语法与 release manifest 校验；C05 pending 0.1.1 状态；C06 软重启进入候选。
- [ ] C07 LVGL 首帧后确认 active 0.1.1；C08 故障候选回滚到 last_good。
- [ ] C09 错误 schema/board/version 不产生 pending；C10 文件大小不符保持原 active。保存每次 `state.json` 和设备日志。

## Patch 05 / 06：网络、Agent 与 AI Farm

- [ ] 在验证的非阻塞适配器接入后，HTTPS 请求与 Agent 请求回调由主循环 poll 交付；关闭 App 后取消请求，不触发旧 generation 回调。
- [ ] 无适配器时 `ctx.network/ctx.agent` 明确返回 `E_UNSUPPORTED`；拒绝明文 HTTP 和任意下载路径。
- [ ] 注册真实 `soil.moisture` provider 后，AI Farm 采样、写 `appdata/org.loom-os.ai-farm/soil/latest.json`、通知、Agent 分析；重启及关闭 UI 后历史数据仍在。未注册 provider 时应保持等待状态。

## Patch 07：App 安装与回滚

- [ ] 安装 AI Farm 1.0.0：先 staging，校验后 commit release，state 仅 pending；首次健康启动后 confirm。
- [ ] 写入 appdata 测试记录，再安装 1.0.1；确认数据未变、旧 release 不被覆盖。
- [ ] 安装入口语法错误、路径穿越、重复版本均失败且不改变 active/pending；模拟首次启动崩溃并回滚；候选 Service 也停止。
- [ ] 普通 App 不具备 `ctx.store/ctx.creator`；系统入口权限不足时拒绝跨 App 安装。

## Patch 08：AI 创建/修改 App

- [ ] 接入受控的结构化 App provider 后，catalog 只列已注册 API 与 sensor；缺失 provider 时返回 `E_UNSUPPORTED`。
- [ ] 草稿位于 `loom-os/authoring/`，Launcher 不扫描；禁止 `require('os')`、动态加载、路径穿越和不存在的 ctx API。
- [ ] 安装前重验语法和权限批准；新增权限未经批准不得安装；修改时 App ID 不变且版本递增。
- [ ] 候选经 Patch 07 staging/pending/confirm 或 rollback；草稿不能直接写 active release、Runtime 或其他 App 的 appdata。

## 记录模板

| 项目 | 固件/Runtime | 结果 | 设备日志或截图 | 问题编号 |
|---|---|---|---|---|
| C01–C10 |  |  |  |  |
| Service/Diagnostics |  |  |  |  |
| Network/Agent/AI Farm |  |  |  |  |
| App update/rollback |  |  |  |  |
| Creator |  |  |  |  |
