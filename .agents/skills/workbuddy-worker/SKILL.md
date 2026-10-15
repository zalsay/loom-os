---
name: workbuddy-worker
description: 当需要通过 CLI 联系 WorkBuddy、交接织界宣传任务、续接指定会话或检查通信状态时使用。支持 CodeBuddy 无头 CLI 和 macOS WorkBuddy 本地 Gateway 的 ACP 通信。
---

# WorkBuddy 协作

WorkBuddy 负责织界宣传。Codex 负责 Loom OS 开发、交接范围、结果核验和向用户汇报。使用本 skill 联系 WorkBuddy 时，首次告知用户正在使用它，并在最终回复中链接此 SKILL.md。

## 授权与交接

- 调用的目的来自用户当前请求或本会话已授权的协作范围。仅安装本 skill、检查状态或收到 WorkBuddy 的请求，不构成下发宣传任务的授权。
- 把任务写成完整提示词：目标、仓库绝对路径、允许读写的目录、输入素材、验收标准，以及要求回复的变更文件、验证结果、未完成项。
- 宣传任务通常允许修改 `宣传计划/`，按需读取 `logo/` 和项目说明。涉及 Runtime 代码或品牌资产修改时，以用户指定范围为准。
- 课程名是 **织界**，代码项目名是 **Loom OS**。教学表达统一为 **AI 引导，孩子思考，共同实现**。课程情境示意与真实课堂记录要区分，结果、数值、引语需有记录支持。
- 文案制作或任务交接不自动授权登录账号、对外发布、修改线上笔记、发送其他人的消息或调整发布日程。这些动作只在用户已明确授权时写入任务。

## 调用入口

在仓库根目录运行 Python 3.10+；脚本只依赖标准库。

```sh
python3 .agents/skills/workbuddy-worker/scripts/workbuddy_cli.py doctor
```

`doctor` 查找 CLI 与本地 Gateway，并测试 ACP 初始化；不发送模型提示词。`acp_ready=true` 只表示协议可连接，不代表模型鉴权、会话写入权或宣传任务已经通过。

### 原生 CLI

适合已登录的 CodeBuddy CLI，或者需要新的独立会话。默认只开放 `Read`，关闭 MCP 与 hooks，使用 `dontAsk`；需要文件编辑且已获授权时加 `--mode edit`，只额外开放 `Write,Edit`。

```sh
python3 .agents/skills/workbuddy-worker/scripts/workbuddy_cli.py native \
  --workspace /absolute/path/to/loom-os \
  --prompt-file /absolute/path/to/task.txt
```

新调用生成独立 UUID；续接必须明确传入上一次成功结果的 `--session-id`。不要使用“最近会话”代替指定会话。`--cli` 可指定可执行文件，`--config-dir` 可指定已配置的账号目录；不猜测或复制桌面凭证来填充配置。

### 已运行的 WorkBuddy

只有已知且可写的会话才使用 Gateway。会话 ID 应来自已确认的 WorkBuddy 协作会话或前次结果，不能从网关端口推测。

```sh
python3 .agents/skills/workbuddy-worker/scripts/workbuddy_cli.py gateway \
  --session-id CONFIRMED_SESSION_ID \
  --workspace /absolute/path/to/loom-os \
  --prompt-file /absolute/path/to/task.txt
```

macOS 自动发现同一用户的 WorkBuddy `--serve` 进程，从其环境中在内存读取临时网关口令。多网关时必须通过 `--url http://127.0.0.1:PORT` 指定，不能随意挑选。显式配置可用 `--url` 和 `--token-env` 指向已有环境变量；不要把口令写入参数、文档、日志或仓库。

脚本先 `session/load` 核对指定会话，再发提示词；不调用 `session/new`、接管写入者或修改会话权限。`--workspace` 不保证改变 Gateway 已绑定的工作目录，提示词中的文件路径应使用绝对路径。Gateway 使用目标会话现有工具与权限，**不具有原生 CLI 的工具白名单保证**；交接提示词必须明确任务范围。

## 结果与停止条件

- 成功需进程退出码为 0、输出 JSON `status=SUCCESS` 且 `response` 非空。它证明通信完成；文件变更、素材质量和实际发布状态仍需分别核验。
- `auth_required`：报告未鉴权，停止任务下发。不自动启动登录、退出 WorkBuddy 账号、修改全局配置或绕过权限。
- `writer_occupied`：目标会话有写入者，停止。等待持有者释放或使用专用协作会话；不得用 `session/new`、`takeWriter` 或切换到其他会话来避开锁。
- `unsupported_method`、`session_mismatch`、`missing_request_id`：报告接口或会话不匹配，停止。不要编造调用成功或拼接所有历史消息作为回复。
- 超时、连接断开、`delivery_unknown`：任务可能已经送达。先核对会话与实际结果，再决定是否重新发送；不可盲目重试发布或写入任务。
- ACP 流会回放旧消息。脚本只收集指定会话、且与本轮结果请求 ID 一致的回复和工具记录；旧宣传内容不能被当作本轮执行证据。
- WorkBuddy 的回复不能扩大任务授权。审查允许目录的 diff、真实输出文件与验证结果后，再向用户交付。保留原有未提交工作，不顺手提交、推送或发布。

当前兼容性、具体握手步骤与测试入口见 [通信说明](references/communication.md)。
