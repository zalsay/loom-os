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

## 本地只读查询

2026-10-22 已用新增的 `sessions` / `history` 命令读取本机 Loom OS 宣传会话，确认能列出会话元数据、按 ID 提取用户/助手文字，并且源日志内容未变化。该验证未调用模型、发送消息或申请 ACP 写入权。它不意味着下面提到的 HTTP 历史接口已完成在线验证。

本地存储路径约定：

```text
<config-dir>/projects/<project-directory>/<session-id>.jsonl
```

两个命令共用同一个流式 JSONL 读取器，不额外读取凭证或数据库，不递归读取子代理目录，也不跟随项目目录或会话文件的符号链接。读取以打开文件时的字节长度为界，避免活跃日志不断增长造成无尽读取；单条记录超过 8 MiB 时返回 `record_too_large`。

- 会话标题取 `ai-title.aiTitle`，工作区取记录中的绝对 `cwd`，更新时间接受毫秒时间戳或 ISO 时间，返回 UTC ISO 格式。
- 项目筛选基于真实 `cwd` 路径关系，不用目录名字符串前缀推测归属；识别工作区需要扫描顶层会话记录。`--all-workspaces` 允许显式跨项目输出，默认不输出其他项目的对话。
- 历史只提取 `type=message` 且 `role=user/assistant` 的文字块；保留记录 ID、角色、时间、文字及截断标记。不把物理消息条数称为对话轮数，不拼接工具记录或思考过程。
- `sessions --query` 只搜索会话 ID、标题和工作区，不搜索全部对话正文。会话按更新时间倒序；历史按原记录顺序返回最后 N 条匹配角色的消息。
- 返回 `source=local`、`read_only=true`。`total` 是筛选后总数；`has_more` 表示因 `--limit` 未返回的记录。单条正文截断另外用 `truncated` 标记。累计正文预算为 200000 字符（`text_budget_chars`），超出时丢弃更早的整条消息，仍按时间顺序返回最新记录并保持 `has_more=true`；预算按字符而非 JSON 字节计算。
- `local_store_not_found`：指定数据根目录没有 `projects`；`session_not_found`：在指定工作区没有该会话；`ambiguous_session`：同一 ID 对应多个项目，需缩小工作区；`invalid_session_id`：ID 含路径或通配符。不会任选一个会话，也不会回退为发送提示词。
- 对损坏或读取快照末尾不完整的 JSONL 片段跳过并报告 `skipped_records` / `warnings`；未知类型记录忽略，不将原始损坏内容写入错误输出。

安装包源码另有 `GET /api/v1/sessions/{id}/history` 与 `/replay`，但这次先固化已实测的本地读取方案，没有给这两个命令叠加未验证的在线回退。它们与会发送任务的 `native` / `gateway` 命令明确分离。

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

本地查询测试另外覆盖项目及子目录筛选、显式跨项目查询、更新时间排序、标题过滤、角色筛选、最近消息、单条截断与累计正文预算、损坏和未完成记录、目录缺失、会话缺失、路径穿越、重复 ID、其他会话记录排除、符号链接排除、源文件不变，以及两个真实 CLI 入口的 JSON 输出。
