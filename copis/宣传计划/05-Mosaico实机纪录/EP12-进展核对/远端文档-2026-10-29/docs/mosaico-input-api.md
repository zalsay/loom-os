# Mosaico 屏幕点击接口（本地实现，尚未部署）

## 原生入口：不依赖 Runtime 已经运行

2026-10-27 新增 `GET /api/loom/native/status` 与
`POST /api/loom/native/control`。前者仅返回当前 `boot_id`、尺寸、触摸通道
与 bootstrap 提交状态，不公开令牌或路径，也不表示 Runtime UI 健康。
后者复用 `DATA/loom-os-runtime/control.json` 中已配对、enabled=true 的
四字符令牌与正整数 epoch；无有效配置时拒绝，不新增无鉴权启动入口。

请求体示例（令牌仅作格式占位，不可当作实际凭据）：

```json
{"token":"xxxx","id":"1","boot_id":"实际状态接口返回值","action":"runtime.start","params":{}}
```

`input.tap` 使用同一封装，参数为 `{"x":120,"y":240,"hold_ms":32}`。
`device.restart` 的 params 为 `{}`，使用现有正常重启回调，仅在当前任务
明确授权重启时调用；返回 `restart_requested_not_verified`，必须再观察
断线恢复、新 boot_id 及 Runtime 健康，不能把 HTTP 接受当作重启完成。
原生请求 ID 单独递增，与 Runtime 模块控制的 ID 空间分离；绑定当前
boot_id、授权 epoch，ID 在硬件调用前消耗，失败也不允许同 ID 再执行。
最多512字节 JSON，严格字段/整数/屏幕范围检查，5次令牌失败锁定30秒。
每次操作重新读凭据并在执行前再核对撤销/轮换；不提供路径、eval、批量、
长按悬挂、远程配对或关闭真实触摸门槛。仅用于隔离可信 LAN，不提供 TLS。

`runtime.start` 只提交固件固定的稳定 bootstrap，与开机 hook 共享每次
设备启动最多一次的提交门闩；失败/返回不明也不自动重试，不替换活动 job。
必须已经完成 Claw 启动及 DATA recovery，不能早于固件初始化执行。
返回 `submitted_not_ui_ready` 不表示 Runtime 已启动成功。

原生点按直接使用已有 touch mux，不依赖 Runtime 的 LVGL indev；设计上可
供消费同一 mux 的出厂 GSP/Works 页面使用。返回 `injected_not_verified`
只表示注入和释放排队，必须另看画面/状态证明目标按钮触发，尚未真机验证。
Lua 的 `loom_touch.tap` 继续保留原有 LVGL 注册门槛，不借原生入口绕过
Runtime 启动的 `require_touch=true`。

首次部署仍需：新固件 → 可信渠道部署稳定 bootstrap/可启动 Runtime →
启用 opt-in autostart → 一次本机配对。配对完成后令牌可跨重启保存，
日常启动/点按无需每个动作人工确认。原生入口不能凭空部署缺失 Runtime，
也不能在没有凭据时替代首次配对；现有 HTTP 公共文件接口禁止写入
`loom-os-runtime`，不得通过放松路径保护来完成 provision。

调用侧入口 `tools/loom_native.py` 从既有0600配对凭据读取令牌，不接受命令行
token；固定已知目标10.0.0.129，不跟随重定向、代理或自动重试。
必须指定正在正式双路录像的 `--live-session`，每次 GET/POST 前核对两PID。
`--id` 是原生接口独立递增 ID；`status`、`runtime.start`、`input.tap`、
`device.restart` 为明确动作，不执行任意 Lua。此工具的存在不是设备部署授权。

## Runtime 内模块接口（已有本地实现）

复用已配对的 Runtime `POST /api/lua/loom_control/control`，不另开无鉴权端口。
请求 JSON 沿用 `token`、递增字符串 `id`、`module`、`action`、`params`。
例如模块 `input`，动作 `tap`，参数 `{"x":120,"y":240,"hold_ms":32}`。
`input.status` 返回是否具备注入后端及当前 Runtime UI 尺寸，不会点击。

- `x/y` 为与本机 `touch tap` 命令一致的逻辑像素整数，从零开始，必须在实际显示范围内；默认按住32ms，允许16–250ms。
- 原生 `loom_touch.tap` 使用 `esp_lcd_touch_mux` 的独占 begin/inject/end。成功获取会话后，注入或释放失败均尝试 cancel；begin 失败不取消其他生产者的会话。
- 只提供完整单击，不提供悬空的 down/move，也不提供批量、循环或自动重试。复用已有鉴权、撤销 epoch 和 Runtime 内单调请求 ID；配对后不需要每次人工确认。请求超时或失败后先观察，不能换新 ID 盲重试。
- `accepted=true / completion=injected_not_verified` 只表示注入及释放已排队，不证明 LVGL 已消费，更不证明目标按钮执行；控制端必须核对后续画面/状态。
- 本节的 Runtime 模块接口仅在 Loom Runtime 已运行且控制服务启用时可用；不能用于首次启动 Runtime。上方新原生入口用于解决这项依赖，仍须新固件部署及真实验证。
- 当前设备的只读模块列表没有 `loom_touch`。本轮没有上传、部署、运行或刷写；只上传 Lua 不能添加原生 C 绑定。必须先在新 build ID 编译包含新头文件的固件，审阅备份/刷写与重启范围，再经用户授权部署。旧77文件候选与审批不能复用为新版部署凭证。
- 这是屏幕注入，不是 Lua `touch`（电容传感器）模块；不使用 BLE HID，也不需要额外一块 ESP32。

2026-10-27 最近一次现场HTTP检查（session167）：`/api/status`为200，`/api/lua-modules`为200，新`/api/loom/native/status`为404；不能说三个GET均200。用户确认设备已接线且亮屏，宿主USB/串口枚举无匹配不等于物理未连接，也不能单独确定线材或固件原因。

2026-10-27 session172已完成ESP-IDF整固件编译/打包/检查，产物为
`firmware/artifacts/2026-10-27-native-control-01/`，不是设备当前固件。
18项overlay、22项产物摘要及归档七个二进制独立复核通过；新接口与boot
符号存在于实际链接ELF。未刷写、安装Runtime、配对、点按或验证重启自启。
现场仍需可验证USB数据通道、备份与精确更新范围授权；完整官方归档是initial
安装包，不能直接作为只更新app/ui_apps/system的刷写范围。
