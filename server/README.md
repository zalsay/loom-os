# Loom OS OTA 发布服务

这是 Loom OS Runtime OTA v1 的 Go 参考实现，仅依赖 Go 标准库。运行和构建需要 Go 1.22 或更新版本。

## 功能

- 按 Loom OS 版本规则解析和排序版本，区分 stable、rc、beta、dev；
- 按开发板和渠道挑选比当前版本更新、且符合 bootstrap 版本要求的发布；
- `GET /v1/loom-os/releases/latest`：有更新时返回 `200` 和清单，无更新时返回 `204`；
- `GET /files/<board>/<version>/<path>`：只提供发布清单列出的文件；
- 发布时计算文件实际大小和 HTTPS URL，以临时目录写入后发布，拒绝覆盖已有版本。
- 开发日志（显式启用）：设备主动上传 App `print`、崩溃和 Runtime 错误；按设备 ID 查询最近 200 条。

该参考服务没有账号、数据库、发布签名、文件完整性校验或管理界面。开发日志接口采用单独的共享令牌，仅供受控开发环境使用。

## 目录与代码

- `main.go`：HTTP 接口和命令入口。
- `release.go`：版本、清单验证及发布目录读取。
- `publish.go`：发布工具。
- `release_test.go`：版本、清单、接口、文件边界与发布测试。
- `debug.go`、`debug_test.go`：开发日志写入、查询和令牌验证。

发布目录示例：

```text
release-data/
└── loom-os/
    └── esp-mosaico/
        └── 0.1.1/
            ├── manifest.json
            ├── main.lua
            ├── core/
            ├── system/
            └── update/
```

## 构建和测试

在 `server` 目录运行：

```bash
go test ./...
go build -o release-server .
```

## 发布版本

清单模板须包含规范的 `files[].path` 列表。发布命令会重新计算每个文件的 `size`，并根据公开地址生成 `url`：

```bash
go run . publish \
  -store-root ./release-data \
  -source-root ./loom-os-0.1.1 \
  -manifest ./release-manifest.json \
  -public-base-url https://updates.example.com
```

目标版本目录已存在时命令会失败。修订已发布的内容需要使用新版本号。

## 启动服务

```bash
go run . serve -root ./release-data -host 127.0.0.1 -port 8080
```

也可以运行构建后的 `./release-server serve ...`；`LOOM_OS_RELEASE_ROOT` 可设置默认发布目录。生产环境应在反向代理上提供 HTTPS，设备端默认拒绝普通 HTTP。

设备查询示例：

```text
GET /v1/loom-os/releases/latest?board=esp-mosaico&channel=stable&current=0.1.0&bootstrap=0.1.0
```

版本优先级以 [`update/VERSIONING.md`](../update/VERSIONING.md) 为准；接口结构见 [`update/SERVER_API.md`](../update/SERVER_API.md)。

## 开发版远程日志

开发日志默认关闭。为 server 配置长度至少 32 字符的随机令牌，并通过 HTTPS 反向代理访问；日志数据保存在 `LOOM_OS_DEBUG_ROOT`（默认 `<release-root>/debug-logs`），每台设备保留最近 200 条。

```sh
export LOOM_OS_DEBUG_TOKEN="$(openssl rand -hex 32)"
go run . serve -root ./release-data -host 127.0.0.1 -port 8080
```

在设备 DATA 根目录下创建 `loom-os/state/remote-debug.json`，填入同一个令牌及实际的 HTTPS server 地址。此文件仅放在设备上，不要提交到 GitHub；将其删除或设为 `enabled: false` 即停止上报，配置在下次启动时生效。

```json
{
  "enabled": true,
  "channel": "dev",
  "device_id": "mosaico-dev-01",
  "server_url": "https://debug.example.com",
  "token": "填入与LOOM_OS_DEBUG_TOKEN相同的随机令牌"
}
```

server 地址须加入 ESP-Claw 的 HTTP 域名许可名单，设备还需要 Loom OS 的非阻塞网络适配器。当前仓库未提供经真机验证的适配器；缺少适配器时设备会保留最多 80 条待发日志，但无法上传。开发日志捕获 Loom OS App/Service 的 `print`、App 崩溃和部分 Runtime 错误，不包含 ESP-Claw 固件日志；设备断电前未成功上传的日志不会保留。

从 server 查询：

```sh
curl -H "Authorization: Bearer $LOOM_OS_DEBUG_TOKEN" \
  'https://debug.example.com/v1/loom-os/devices/mosaico-dev-01/logs?limit=100'
```

设备使用同一令牌向该地址 `POST` `{"session":"1","entries":[{"seq":1,"level":"INFO","source":"runtime","message":"boot"}]}`；成功返回 `204`。接口限制单次 16 条、32 KiB，server 只保留最近 200 条，并按设备启动会话与序号去重。读取和上传都需要令牌；响应禁止缓存。日志可能含应用主动打印的数据，只在开发环境使用，并妥善保管 server 日志目录和令牌。
