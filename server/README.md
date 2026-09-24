# Loom OS OTA 发布服务

这是 Loom OS Runtime OTA v1 的 Go 参考实现，仅依赖 Go 标准库。运行和构建需要 Go 1.22 或更新版本。

## 功能

- 按 Loom OS 版本规则解析和排序版本，区分 stable、rc、beta、dev；
- 按开发板和渠道挑选比当前版本更新、且符合 bootstrap 版本要求的发布；
- `GET /v1/loom-os/releases/latest`：有更新时返回 `200` 和清单，无更新时返回 `204`；
- `GET /files/<board>/<version>/<path>`：只提供发布清单列出的文件；
- 发布时计算文件实际大小和 HTTPS URL，以临时目录写入后发布，拒绝覆盖已有版本。

该参考服务没有账号、数据库、签名、哈希、管理界面或管理 API。

## 目录与代码

- `main.go`：HTTP 接口和命令入口。
- `release.go`：版本、清单验证及发布目录读取。
- `publish.go`：发布工具。
- `release_test.go`：版本、清单、接口、文件边界与发布测试。

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
