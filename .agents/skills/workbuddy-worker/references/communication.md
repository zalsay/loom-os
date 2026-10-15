# 通信说明与验证

## 已测边界

2026-10-14 在本机 WorkBuddy 5.8.2 / 内置 CLI 2.161.0 上验证：

| 路径 | 实测结果 |
| --- | --- |
| 内置入口 `--help` | 需要选择存在的 `codebuddy-lite-wb.mjs` 变体；辅助脚本自动检测 |
| 独立 `-p --output-format json` | 未鉴权时输出 `Authentication required`，退出码可能仍为 0 |
| 本地 Gateway ACP 提示词 | 曾准确返回唯一测试标识；按请求 ID 过滤后，本轮工具调用为 0 |
| 同网关 `session/new` | 返回的是既有宣传会话，不能据此认定建立了隔离会话；辅助脚本不使用它 |
| 重新连接后的 `session/load` | 曾返回 `writer_occupied`；辅助脚本保留该限制，不强行接管 |
| 追加消息队列 | 当前实例返回 `Method not found`，不作为默认协作入口 |

这份记录是兼容性基线，不是当前登录、会话写入权、独立 CLI 模型调用或素材发布成功的证明。辅助脚本新增的端到端协议验证使用本地测试服务，不发宣传任务。桌面升级后先重新运行 `doctor`，再执行用户已授权的最小任务验证。

## 选择与鉴权

- 原生 CLI 优先搜索 PATH 中的 `codebuddy` / `cbc`，再检查 `/Applications/WorkBuddy.app` 与用户 Applications 目录中的内置入口。
- 桌面账号和独立 CLI 的登录态不保证相同。指向 `.workbuddy` 或套用产品配置路径曾仍然未鉴权；不要把复制路径当作已修复登录。
- Gateway 自动发现仅适用于 macOS，限定同一用户、WorkBuddy Electron 可执行文件和带 `--serve` 的进程。端口每次启动可能变化，不保存固定端口或密码。
- 自动发现会在内存中读取该进程的 `CODEBUDDY_GATEWAY_PASSWORD`，不将进程环境、口令或 ACP 会话令牌输出或落盘。需要避免进程检查时，用已有环境变量与明确的 `--url`。
- 显式 URL 只允许带端口的 HTTP loopback 地址；拒绝重定向，避免将本地认证头发往其他地址。

## ACP 请求顺序

```text
POST /api/v1/acp/connect
  → connectionId + sessionToken（仅内存）
POST /api/v1/acp: initialize
POST /api/v1/acp: session/load（明确的 sessionId）
POST /api/v1/acp: session/prompt
DELETE /api/v1/acp（释放本次连接）
```

请求使用 `Authorization: Bearer …`，建立连接后还需 `acp-connection-id` 和服务提供的 `acp-session-token`。JSON RPC 的 `id` 用于定位本次结果；结果 `_meta` 中的 `codebuddy.ai/conversationRequestId` 或 `codebuddy.ai/requestId` 用于过滤 SSE 的 `session/update`。过滤同时核对 `sessionId`。两个请求 ID 字段都存在时，优先核对 `conversationRequestId`，不因旧事件共享普通 `requestId` 就将其纳入本轮结果。没有请求 ID 时直接报错，不降级为全部消息拼接。

`session/load` 在发送提示词前检查锁与返回的会话 ID。失败后不发 `session/prompt`，也不调用接管、清空历史、取消其他任务或重新登录的方法。关闭连接不等于证明已送达任务被撤销；超时后必须核对执行结果。

## 命令输出

```json
{
  "status": "SUCCESS",
  "transport": "gateway",
  "session_id": "confirmed-session",
  "request_id": "current-request",
  "response": "本轮回复",
  "tool_names": ["Read"]
}
```

失败返回 JSON `status=ERROR`、`error_code` 与简短说明，并使用非零退出码。`doctor` 的 `status=SUCCESS` 表示状态检查完成；仍需分别检查 `cli`、`gateways[].acp_ready` 和实际任务结果。

## 回归验证

在仓库根目录执行：

```sh
python3 -B -m unittest discover \
  -s .agents/skills/workbuddy-worker/scripts -p 'test_*.py' -v
```

测试运行临时 CLI 与本地 HTTP 服务，覆盖：零退出码鉴权失败、明确失败状态、错误/无效 JSON、指定会话续接、只读工具配置、写入锁阻止提示词、会话 ID 不匹配、历史过滤、缺失请求 ID、其他会话消息、连接清理、令牌隐藏以及外部 URL/重定向拒绝。不依赖真实 WorkBuddy 账号。
