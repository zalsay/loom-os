# Loom OS

面向 ESP-Claw / Mosaico 的 Lua + LVGL 应用运行时，提供应用启动器、隔离运行环境、系统 API 和 Runtime 更新能力。

> **当前版本状态：0.1.1 集成候选。** 主机侧集成测试已通过；Mosaico 真机验收仍待完成。API、包标识和存储路径已统一采用 loom-os 命名。

## 项目目标

让 Lua 应用能够以图标形式出现在启动器中，并在受控的运行环境内启动、退出和使用设备能力，为 Mosaico 上的课程项目和设备应用提供基础 Runtime。

## 当前进度

- Patch 01–08 已集成到 Lua 源码，主机侧集成序列已通过；Go 版参考 OTA 服务由 GitHub Actions 运行测试。
- 真机验收尚未完成。下一步是按 [Mosaico 真机验收清单](Mosaico-Patch01-08-Device-Checklist.md) 执行 C01–C10，记录固件、Runtime、设备日志和结果。
- 在真机清单通过前，不要将 Patch 01–08 标记为设备验收完成，也不要开始新的功能 Patch。
- 分阶段记录、验证结果和限制见 [开发计划](Loom-OS-Development-Plan.md)。

## 能力概览

| 模块 | 当前能力 |
| --- | --- |
| App Runtime | manifest 校验、应用发现、隔离环境、生命周期和启动器 |
| 系统 API | App 专属存储、定时器、GPIO、传感器、通知和 Service |
| 应用管理 | 分阶段安装、版本化发布、健康确认和失败回滚 |
| Runtime 更新 | 暂存、版本检查、文件大小校验、切换和回滚流程 |
| Network / Agent / Creator | API 与适配器接口已集成；设备端后端仍需验证或接入 |
| OTA 参考服务 | 按板型和版本提供不可变 Runtime 发布文件 |

## 运行环境

设备 Runtime 依赖固件提供 `storage`、`json`、`lvgl`、`board_manager`；使用 GPIO 的应用还需要 `gpio`。具体固件、屏幕和传感器能力以设备实测为准。

主机侧集成测试使用 Lua 5.3；可使用 `texlua` 运行。参考 OTA 服务需要 Go 1.22 或更新版本。

## 主机侧测试

在仓库根目录执行：

```sh
texlua tests/patch01_08_integration_test.lua
texlua tests/web_reader_test.lua
texlua tests/remote_debug_test.lua
(cd server && go test ./...)
```

以上测试用于检查主机侧集成逻辑，不能替代 Mosaico 真机验收。

## 网页阅读器示例

[网页阅读器 App](examples/org.loom-os.web-reader/README.md) 将单个静态 HTML 页面显示为可滚动的 LVGL 文字视图。启动时显示内置页面；在线读取 HTTPS 页面需要设备网络适配器及目标域名许可。支持的 HTML 范围、大小限制和测试方法见示例说明。

## 开发版远程日志

[开发日志配置与查询](server/README.md#开发版远程日志)：开发设备主动向 Go server 上传有上限的 App `print` 和 Runtime 错误，server 可按设备 ID 查询。该功能默认关闭，启用时须配置 HTTPS、令牌及设备网络适配器；设备端接入仍需真机验证。

## 真机安装与验收

先在测试设备上备份 `loom-os/` 和 `loom-os-runtime/`。新装和 OTA 流程、Runtime 文件清单、适配器要求及 C01–C10 步骤见 [真机验收清单](Mosaico-Patch01-08-Device-Checklist.md)。

- 新设备按清单检查初始安装流程。
- 已使用 loom-os 目录和发布协议的 0.1.0 测试设备通过 Runtime OTA 升级，不要重跑初始安装脚本。
- 旧命名设备的存储目录和 OTA 协议与新名称不兼容；先备份 App 数据并完成专门迁移，再测试升级。
- 保存每项验收使用的固件版本、Runtime 版本、设备日志和 PASS / FAIL 结果。

## 已知限制与安全边界

- 当前权限机制是 **App 能力授权**：系统根据 manifest 权限决定是否开放 API；它不是用户登录系统。仓库没有实现账号登录、OAuth、用户会话或 Token 管理。
- Network API 要求 HTTPS 和非阻塞设备适配器。没有适配器时会返回 `E_UNSUPPORTED`。
- Agent、真实土壤湿度传感器和结构化 App 生成服务仍需接入经过验证的设备 Provider；未接入时不应返回假成功。
- 参考 OTA 服务目前不含账号、签名、哈希、数据库状态或管理 API。正式部署前需补齐适合生产环境的发布认证与完整性验证。

## 目录结构

| 路径 | 内容 |
| --- | --- |
| `core/`、`api/` | Runtime 核心、权限检查和 App API |
| `ui/`、`main.lua` | 启动器、系统 UI 和主循环 |
| `system/`、`update/` | 网络与 Agent 后端、OTA 客户端 |
| `provision/` | 初始安装脚本和 Runtime 文件清单 |
| `examples/` | 示例 App 和 Service |
| `tests/` | Lua 集成测试、Runtime 测试和设备 smoke test |
| `server/` | Runtime OTA 参考服务与发布工具 |

## 继续开发

先阅读开发计划和真机验收清单，运行上面的主机测试，再按清单完成 Mosaico 验收。设备行为只有在记录了实际设备证据后才可标记为通过。
