## 除非特别说明，否则不要在开发中使用chrome tool 做验证

# 本项目执行规则：不使用子代理

- 本规则仅适用于 `/Users/sisu/Documents/dev/loom-os` 及其子目录，不修改全局配置或其他项目规则；在本项目中覆盖全局的任务委托要求。
- 所有实现、修复、配置、诊断、审查和测试均由当前主 Agent 直接完成，不创建、续接或派发任何子代理任务，也不调用 `$luna-worker` 或其他代理委托 skill。
- 不通过独立模型 CLI、WorkBuddy 或其他代理服务代为执行本项目任务；用户后续明确更改此规则前，保持单 Agent 工作方式。
- 主 Agent 自行检查实际改动、运行测试、核对证据及剩余风险；此前委托留下的代码和报告只作为待核验材料，不直接当作完成证据。
- 现有 Otty 复用、双路同步录制、设备操作授权和素材归档要求保持不变；历史记录中的 Luna/委托描述仅记载当时发生的事实，不授权未来继续委托。

# 本地摄像头与 Mosaico 操作记录

本文记录 2026-10-16 至 2026-10-17 会话中针对用户自有 TP-Link 摄像头和 Loom OS 小屏设备的现场观察与安全操作方式。地址、固件、临时文件和网络权限可能变化；执行前重新检查，不把临时取帧文件当作持久记录。

## 设备与网络

- 摄像头：TP-Link `TL-IPC43G-ZOOM-DUAL`，固件 `1.0.1 Build 210420 Rel.79658n`，本次地址 `10.0.0.13`。
- 已观察到本机获准访问局域网后 TCP `80`、`2020`、`554` 可达。授权前连接立即报 `No route to host`；这不代表 IP 错误。若再次发生，先检查 macOS 当前应用的“本地网络”权限、接口、路由和 ARP，不扫描其他主机。
- ONVIF Device 与本次媒体/PTZ 服务地址：
  - `http://10.0.0.13:2020/onvif/device_service`
  - `http://10.0.0.13:2020/onvif/service`
- ONVIF SOAP 1.2 请求在 `Content-Type` 中指定对应 `action`。以下函数依次接收 XML、服务地址、Action URI；不使用代理，每次请求设置短超时：

```sh
onvif_post() {
  curl --noproxy '*' --connect-timeout 3 --max-time 5 -sS -i \
    -H "Content-Type: application/soap+xml; charset=utf-8; action=\"$3\"" \
    --data-binary "$1" "$2"
}

onvif_post '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><tds:GetDeviceInformation xmlns:tds="http://www.onvif.org/ver10/device/wsdl"/></s:Body></s:Envelope>' \
  'http://10.0.0.13:2020/onvif/device_service' \
  'http://www.onvif.org/ver10/device/wsdl/GetDeviceInformation'

onvif_post '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><trt:GetProfiles xmlns:trt="http://www.onvif.org/ver10/media/wsdl"/></s:Body></s:Envelope>' \
  'http://10.0.0.13:2020/onvif/service' \
  'http://www.onvif.org/ver10/media/wsdl/GetProfiles'

onvif_post '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><tptz:GetStatus xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"><tptz:ProfileToken>profile_1</tptz:ProfileToken></tptz:GetStatus></s:Body></s:Envelope>' \
  'http://10.0.0.13:2020/onvif/service' \
  'http://www.onvif.org/ver20/ptz/wsdl/GetStatus'

onvif_post '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><trt:GetStreamUri xmlns:trt="http://www.onvif.org/ver10/media/wsdl"><trt:StreamSetup><tt:Stream xmlns:tt="http://www.onvif.org/ver10/schema">RTP-Unicast</tt:Stream><tt:Transport xmlns:tt="http://www.onvif.org/ver10/schema"><tt:Protocol>RTSP</tt:Protocol></tt:Transport></trt:StreamSetup><trt:ProfileToken>profile_1</trt:ProfileToken></trt:GetStreamUri></s:Body></s:Envelope>' \
  'http://10.0.0.13:2020/onvif/service' \
  'http://www.onvif.org/ver10/media/wsdl/GetStreamUri'
```

- 2026-10-19：用户提供的实际账号凭据通过 ONVIF WS-Security `UsernameToken PasswordDigest` 认证后，`GetDeviceInformation`、`GetProfiles`、PTZ `GetStatus(profile_1)` 均为 HTTP 200；设备信息为 TP-Link `TL-IPC43G-ZOOM-DUAL`、固件 `1.0.1 Build 210420 Rel.79658n`，PTZ 状态为 idle、`Error=0`。同一凭据请求 Imaging `GetStatus(raw_vs1)` 返回 HTTP 400 / `ter:NotAuthorized`（Authority failure）；此结果仅表示该 Imaging 请求未获授权，不代表其他 ONVIF 操作或凭据整体失败。本轮只读，未移动、变焦或复位。
- 2026-10-19 本次复查时，无认证的设备信息、视频配置和 PTZ 状态请求均返回 `NotAuthorized`；此前 2026-10-16/17 的无认证成功仅是历史观察，不代表当前认证策略。实际凭据仅保存在本地 [.secrets/tp-link-onvif.md](.secrets/tp-link-onvif.md) 文档中（`.secrets/` 已由 `.gitignore` 忽略）；公开文档不得复制密码。正确摘要生成方式：先调用 `GetSystemDateAndTime`，以响应中的 `UTCDateTime` 构造 `Created`，生成随机 `Nonce`，并按 `Base64(SHA1(Nonce 原始字节 + Created UTF-8 + password UTF-8))` 计算 `PasswordDigest`。不要将凭据拼入 URI、命令行或日志；认证失败时停止，不猜密码。
- 本次 profile：`profile_1` (`mainStream`，H.264 1280×720)；`profile_2` (`minorStream`，H.264 640×480)。PTZ 配置 token 为 `PTZTOKEN`，节点 token 为 `PTZNODETOKEN`。这是本次响应中观察到的 ONVIF 标识，不是登录凭据；重新使用前先 `GetProfiles` 核实。
- `GetStreamUri` 对 `profile_1` 返回 `rtsp://10.0.0.13:554/stream1`。`GetSnapshotUri` 返回 HTTP 500 / SOAP `ter:ActionNotSupported`，不是认证错误。

## 获取一张当前画面

- 观察当前画面或验证 Mosaico 屏幕时，默认仅抓一帧；禁用音频，不保存连续录像。可先请求 `GetStreamUri` 获得当前 URI；不要假设地址永久不变。
- 先使用本机已有的 `ffmpeg`；缺少时，以下命令从官方 PyPI 下载适合本机的 `imageio-ffmpeg` wheel，仅解压到私有临时目录，不安装全局 Python 包、不改项目依赖。示例使用 RTSP over TCP、仅视频轨道、单帧和 5 秒 socket timeout；外层 Python `timeout=10` 限定取帧总运行时间：

```sh
(
  set -eu
  camera_frame_dir="$(mktemp -d /tmp/loom-camera.XXXXXX)"
  camera_ffmpeg="$(command -v ffmpeg || true)"
  if [ -z "$camera_ffmpeg" ]; then
    python3 -m pip --isolated download --no-deps --only-binary=:all: \
      --index-url https://pypi.org/simple --dest "$camera_frame_dir" imageio-ffmpeg
    for camera_wheel in "$camera_frame_dir"/imageio_ffmpeg-*.whl; do
      unzip -q "$camera_wheel" 'imageio_ffmpeg/binaries/ffmpeg-macos-*' -d "$camera_frame_dir"
    done
    for camera_binary in "$camera_frame_dir"/imageio_ffmpeg/binaries/ffmpeg-macos-*; do
      camera_ffmpeg="$camera_binary"
      break
    done
    chmod 700 "$camera_ffmpeg"
  fi
  python3 -c 'import subprocess,sys; subprocess.run([sys.argv[1], "-hide_banner", "-loglevel", "warning", "-rtsp_transport", "tcp", "-timeout", "5000000", "-allowed_media_types", "video", "-i", "rtsp://10.0.0.13:554/stream1", "-an", "-frames:v", "1", "-update", "1", "-y", sys.argv[2]], timeout=10, check=True)' \
    "$camera_ffmpeg" "$camera_frame_dir/frame.jpg"
  file "$camera_frame_dir/frame.jpg"
  sips -g pixelWidth -g pixelHeight "$camera_frame_dir/frame.jpg"
  printf '%s\n' "$camera_frame_dir/frame.jpg"
)
```

- 命令结束后用图像查看工具打开实际输出文件，检查 Mosaico 屏幕是否清楚；不能只凭取流成功就声称看到了屏幕内容。
- 本次曾在临时目录得到 1280×720 JPEG；`/tmp/onvif-frame.aLTkdy/camera.jpg` 只是本次会话临时证据，不能依赖该路径长期存在。

## PTZ 云台控制

- 设备通过 `GetCapabilities` 声明 PTZ 服务；`GetNodes` 响应支持绝对/相对/连续云台空间，Pan/Tilt 绝对范围 `[-1,1]`，绝对 Zoom 范围 `[0,1]`，速度幅值范围 `[0,1]`，连续 Pan/Tilt 与 Zoom 的有符号速度范围 `[-1,1]`；节点最多 8 个预置位、无 Home 支持。相对 Zoom 的本次声明范围是 `[0,1]`，不要自行改写成负值范围。
- 只在用户已要求移动的范围内执行，无需重复确认。先用 `GetStatus` 保存当次位置，单轴、小幅操作；无论请求成功、失败或超时，都在 `finally` 中发送 `Stop`，然后核对状态与稳定后的新单帧。测试后恢复当次基线，不把下表中的历史位置当作以后固定的回位目标。
- 精细转动和变焦优先使用 `AbsoluteMove`：传入 `ProfileToken=profile_1`、`Position/tt:PanTilt` 的目标 `x/y`、`Position/tt:Zoom` 的目标 `x`，并显式设置 `Speed/tt:PanTilt x="0.05" y="0.05"` 和 `Speed/tt:Zoom x="0.05"`；Action 为 `http://www.onvif.org/ver20/ptz/wsdl/AbsoluteMove`。本次验证了 Pan 基线附近 `±0.015`、Tilt 基线附近 `±0.01`、Zoom `0 → 0.05 → 0`。这些是归一化坐标，不是角度或变焦倍数；小速度值也不保证运动幅度与时间成比例。
- `GetConfigurationOptions`（`ConfigurationToken=PTZTOKEN`）实测返回 PTZ timeout 范围 `PT1S` 至 `PT600S`，默认值为 180 秒。不要沿用旧的 `PT0.3S` 示例。连续移动必须显式设置 `PT1S` 看门狗，并通过独立于请求响应的主机计时器约 0.25 秒后发送 `Stop`，最终再补发 `Stop`；不要等待默认超时，也不要把以下请求模板当作完整安全执行器。
- 连续俯仰实测在 `y=+0.05`、约 0.26 秒后停止时，绝对 Tilt 从 `0.683333` 降至 `0.614815`（变化 `-0.068518`），超过本次 `0.05` 保护阈值。测试立即中止剩余连续移动并回位，后续改用小幅绝对定位。不要从连续速度的正负号直接推断绝对坐标方向，也不要重用该脉冲作为精细俯仰步长。

```sh
# 连续水平移动请求模板；须由带独立 Stop 计时器和 finally 清理的执行器调用。
onvif_post '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><tptz:ContinuousMove xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"><tptz:ProfileToken>profile_1</tptz:ProfileToken><tptz:Velocity><tt:PanTilt xmlns:tt="http://www.onvif.org/ver10/schema" x="0.05" y="0"/></tptz:Velocity><tptz:Timeout>PT1S</tptz:Timeout></tptz:ContinuousMove></s:Body></s:Envelope>' \
  'http://10.0.0.13:2020/onvif/service' \
  'http://www.onvif.org/ver20/ptz/wsdl/ContinuousMove'

# 移动请求后立即调用 Stop；若请求错误，也应停止并核对状态。
onvif_post '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><tptz:Stop xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"><tptz:ProfileToken>profile_1</tptz:ProfileToken><tptz:PanTilt>true</tptz:PanTilt><tptz:Zoom>true</tptz:Zoom></tptz:Stop></s:Body></s:Envelope>' \
  'http://10.0.0.13:2020/onvif/service' \
  'http://www.onvif.org/ver20/ptz/wsdl/Stop'
```

- 连续变焦可使用同一 `ContinuousMove` 请求，将 `Velocity` 中的 `tt:PanTilt` 替换为 `<tt:Zoom xmlns:tt="http://www.onvif.org/ver10/schema" x="0.05"/>`；仍需上述看门狗、独立 `Stop` 和画面复核。连续变焦模板尚未实测，本次放大与缩小验证使用的是绝对定位。
- 2026-10-16 仅执行只读 PTZ 查询；2026-10-17 执行了下列移动与恢复，控制请求在本次会话中无认证成功。若之后要求认证，使用用户提供的正确凭据；不猜密码。没有测试最大行程、最大变焦倍数、预置位、Home、配置变更、重启或登录。

### 2026-10-17 控制实测结果

当次基线为 Pan `0.002563`、Tilt `0.683333`、Zoom `0`。以下结果同时核对了 HTTP/SOAP 响应、位置反馈与稳定后的实际画面；每步均发送停止请求，每轴测试结束后回位。

| 功能 | 目标与位置反馈 | 画面验证 |
| --- | --- | --- |
| 水平正向 / 反向 | 绝对 Pan 基线 `±0.015`，到达 `0.017427` / `-0.012301` | 取景向两侧变化 |
| 俯仰正向 / 反向 | 绝对 Tilt 目标 `0.693333` / `0.673333`，到达 `0.692593` / `0.674074` | 取景上下变化 |
| 放大 / 缩小 | 绝对 Zoom 目标 `0.05`，到达 `0.050073`，再恢复 `0` | Mosaico 在画面中明显放大后恢复 |
| 停止 / 回位 | 最终 Pan `0.002563`、Tilt `0.683333`、Zoom `0` | 原取景恢复；PanTilt / Zoom 均 `idle`，`Error=0` |

- 临时证据目录为 `/private/tmp/loom-camera.bv0azJ/stage3/`，含请求 XML、原始响应、状态 JSON 和各状态单帧；最终状态文件为 `final-after-operator-stop-settled-pan.state.json`，最终画面为 `frame-pan-return-baseline-settled-stream1.jpg`。这些是临时现场证据，不依赖其长期存在，也不把设备读取或转动成功当作 Mosaico 真机验收通过。

### 2026-10-19 带认证的 PTZ 变焦复测

- 使用本地凭据与 WS-Security `UsernameToken PasswordDigest`，重新确认 `GetProfiles`、`GetConfigurationOptions`、`GetStreamUri` 和 PTZ `GetStatus` 均 HTTP 200，绝对 Zoom 范围为 `[0,1]`。这次只用 `AbsoluteMove` 的 `tt:Zoom` 单轴位置与 `Speed/tt:Zoom x="0.05"`，未设置 Pan/Tilt 目标，也未调用 Imaging 对焦。
- 本次实际基线为 Pan `0.036904`、Tilt `0.681481`、Zoom `0.211473`。复测 Zoom `0.211473 → 0.259115 → 0.211473` 成功，放大、恢复各请求后均发送 `Stop`；最终 Pan/Tilt 保持原值、两轴 idle、`Error=0`。主 Agent 实际打开前、中、后三张 RTSP 单帧，确认 Mosaico 放大后恢复原取景；屏幕文字仍模糊，不能将变焦成功当作对焦问题已解决。
- 首次请求目标 `0.251473` 时实际稳定在 `0.259115`，因目标容差检查未通过而标记 FAIL，随后已恢复基线；按观察到的实际落点补测才通过。须保留这一偏差记录，不假设任意小数 Zoom 目标都能精确到达，也不把这些历史值当作未来回位坐标。
- 当次临时证据目录 `/tmp/loom-ptz-zoom.63ilwu/`：根目录 `result.json` 为首次未达目标的记录；`verified-step/result.json` 为补测通过及回位记录，配套 `baseline.jpg`、`zoom-changed.jpg`、`restored.jpg` 已实际查看。这些临时路径不保证长期存在。该次 RTSP 取帧使用设备声明的 Basic 认证，同一用户凭据只在内存中读取，未放入 URI、命令参数或日志。

## 小屏设备 Mosaico

- 用户确认摄像头当前画面中的白/浅色外壳小屏设备、屏幕上方橙色圆形细节及 USB 线连接设备，是 Mosaico；摄像头是外置观察工具，不是 Mosaico 本身。后续通过相机观察屏幕时，重新构图并只抓取需要的单帧。
- 仓库板级文件 [`boards/mosaico.lua`](boards/mosaico.lua) 标识 ESP-Mosaico V1.0；清单记录 480×480 显示配置。它是项目声明的配置，不能当作现场测量结果，也不能据此推断当前设备的 IP、端口、SSH 或控制通道。
- 当前 [`README.md`](README.md) 将 Loom OS 标为 0.1.1 集成候选，并注明 Mosaico 真机验收待完成；按 [Mosaico Patch 01–08 真机清单](Mosaico-Patch01-08-Device-Checklist.md) 执行 C01–C10 并记录固件、Runtime、设备日志和结果。主机测试通过或相机画面可见，都不能替代真机验收或证明串口/网络控制链路可用。

### USB 连接与按键

- 2026-10-17 在 macOS `MacBookAir10,1` 上，Mosaico 原生 USB 成功枚举为 Espressif VID `303a` / PID `0020`、USB-OTG，AppleUSBACM/CDC 驱动已绑定；当时出现 `/dev/cu.usbmodem101` 与 `/dev/tty.usbmodem101`，`lsof` 未见占用。这是一次历史枚举，不保证端口编号或当前连接状态；重用前先重新枚举。此处是原生 USB，不是 CP210x/FTDI 桥，无需盲装桥接芯片驱动。
- Type-C 连接须用数据线；官方 FAQ 确认 USB-C 到 USB-C 数据线可用，不把这一说明当作本次线缆规格的现场记录。按住 `BOOT` 上电会进入 ROM 下载模式，随后松开；ROM 没有应用界面，屏幕黑属于正常现象，不代表普通应用调试或 Vibe 已启动。退出手动 BOOT 可松开按键后正常关机再开机；若要用复位操作，须在当前任务授权范围内。
- 按键位置先核对实物丝印和对应版本官方背图：以本次核对的 V1.0 背图为例，主板背面朝向操作者、Type-C 朝下时，`BOOT` 在接口右侧、`POWER` 在左侧；从正面看左右相反。`POWER` 短按会切换开关状态，不是无副作用的唤醒键；`AI` 是另一个按键。V1.0/V1.2 以实物版本丝印确认，仓库板型声明不能替代现场确认。

### 只读检查与复位边界

先在本机检查 USB 和串口枚举；仅对这次确认存在的端口查占用，不扫描其他主机、不猜 IP：

```sh
date
ioreg -p IOUSB -w 0
ioreg -r -c IOSerialBSDClient -l -w0 | rg 'IOCalloutDevice|IODialinDevice'
# 仅当本次枚举确认该端口时才检查；端口编号可能变化
/usr/sbin/lsof -nP /dev/cu.usbmodem101
```

- 没有 USB 节点本身不能证明设备关机；普通应用须有 CDC 支持才会提供 USB 串口。本机曾成功原生 CDC 枚举，故后续应把 USB 链路问题与固件 CDC 行为分开排查。
- 2026-10-17 曾在私有临时 venv 使用 esptool 5.6.0；该版本要求 Python ≥3.10，系统 Python 3.9 不满足，实际使用 bundled Python 3.12。临时 venv 路径 `/private/tmp/mosaico-esptool.4tZBoM/venv/bin/python` 不保证存在；复用时先找可用 Python ≥3.10，再在私有临时环境隔离工具，不要照抄临时绝对路径为永久入口。
- 已验证的只读 ROM 握手命令为 `python -m esptool --chip esp32s31 --port /dev/cu.usbmodem101 --baud 115200 --before no-reset --after no-reset --no-stub --connect-attempts 2 read-mac`，并由外层进程设置 20 秒超时；这里的 `python` 必须指向已准备好的隔离工具环境，不默认指向 macOS 系统 Python。仅在用户授权且重新确认设备处于 ROM 模式及端口后复用；该次返回 S31 rev0.0、USB-OTG 和 `Staying in bootloader`，无需记录完整 MAC。ROM 握手不等于普通固件或屏幕健康。
- **esptool 默认操作后会 hard-reset。** 使用 esptool 做只读 ROM 检查时，显式使用 `--before no-reset --after no-reset --no-stub`，不要依赖默认值。复位会改变运行态，只有当前任务明确包含重启/启动授权时才执行，并先说明影响。约 10:45 用户询问能否启动屏幕后，主 Agent 对同一 `read-mac` 使用 `--after hard-reset`，实际执行了一次重启，输出 `Hard resetting with a watchdog...`；该次 S31 USB-OTG 官方复位路径借 watchdog 执行全系统复位，之后 USB 节点/串口消失。该序列未刷写、擦除 Flash、烧 eFuse 或上传 stub。不要把此次状态变化无证据归因于自动待机，也不要说“没有重启过”或仅凭串口消失宣称应用启动成功。

### 历史结果与息屏判断

- 10:51 与 11:08 的后续只读检查未发现 USB 节点；用户现场确认此前曾亮屏。现有证据不能判定后续黑屏或失联的原因。不要只凭黑屏/USB 失联推断复位、待机、关机或恢复出厂；需要 uptime、BootID、reset reason 或实际日志佐证。
- 本次核对的是官方 `esp-mosaico-claw` 固定 commit `1b7388b26523d74a36b2a9e4ec3df8c838053bbb` 的源码快照，项目版本为 0.4.0；这不代表本地下载的 0.5.0 或现场固件版本。该快照中 Hub 主页前台默认 30 秒息屏，可选 0/10/30/60/120/300 秒，0 表示禁用；触摸可唤醒。该路径只暂停/恢复 UI 面板，不包含重启或关闭 USB 的逻辑，也未见插 USB 时免息屏逻辑。现场固件和配置未知，配置可能已变更。息屏不等于芯片深睡、关机或恢复出厂；不要为验证息屏自动复位或刷机。
- 芯片睡眠模式另见 ESP-IDF 文档；不能从息屏源码推断设备进入了深睡。Vibe 维护模式与 ROM BOOT 不同：官方模式说明中 AI 键上电入口要求设备已有相应固件；Type-C 原生 OTG 也不等于扩展连接器上的外接 USB/串口路径。未连接扩展 USJ/UART；USJ 左侧 H2 为 GPIO33 D− / GPIO34 D+，UART 右侧 H1 为 GPIO58 TX / GPIO59 RX，连接时须按实物版本指南核对，不要混作 Type-C 引脚。
- 固件下载记录：官方 0.5.0 构建日期 2026-10-16，本地文件 `/Users/sisu/Downloads/ESP-Mosaico/0.5.0/ESP-Mosaico-Claw_v0.5.0.bin`，大小 16,703,488 字节，SHA-256 `bd45c135034d50cd9d0d36cfbe5219c2e760274d27d87a0087ec4bc38206b10e`（本地计算，记录见 `DOWNLOAD-RECORD.md`）。本次仅下载，未烧录；该 hash 不是官方签名或发布 hash 校验，最新版本会变化。连接或启动请求不等于授权刷写；官方更新页提示可能清除数据，更新前备份并取得用户明确要求。

### 网络入口与官方资料

- 官方应用文档说明，出厂应用 Web 控制台地址从设备 `Settings/Network/AI Model` 或 Guide 读取；配网后用设备在同一 LAN 的实际 IP。未配网时，`192.168.4.1` 是连接设备热点后的官方 AP 网页入口，不是本次已验证地址。不要因此改主机 Wi-Fi、猜局域网 IP 或扫描网络。此前未验证网络控制链路；2026-10-17 后续只读访问结果如下。
- 2026-10-17 用户提供 Mosaico 当前 IP 为 `10.0.0.129`，随后实际访问 [`http://10.0.0.129/`](http://10.0.0.129/) 返回 HTTP 200，页面标题为 `ESP-MOSAICO Settings`；[`GET /api/status`](http://10.0.0.129/api/status) 同样返回 HTTP 200。上述两个入口在本次请求中未要求账号密码，无需执行登录提交；这不代表所有接口或未来固件均无认证。地址可能因 DHCP 变化，复用前重新确认；与 TP 摄像头 `10.0.0.13` 区分。
- 当次状态响应确认 `wifi_connected=true`、`ip=10.0.0.129`、`wifi_mode=sta_only`、`ap_active=false`、`storage_base_path=/nand`。响应未提供固件版本、uptime 或 BootID，不能由此判断版本、是否曾重启或充电不息屏补丁是否生效。网页可访问不等于 Lua 写入、Runtime 部署或真机验收已经通过；本次没有修改配置、写文件、调用重启或刷机。
- 复查仅使用短超时的只读请求，例如 `curl --noproxy '*' --compressed --connect-timeout 3 --max-time 6 -sS -D - http://10.0.0.129/api/status`。首页本次使用 gzip 响应，读取页面时同样加 `--compressed`。若之后返回 401/403 或出现登录页面，停止并请用户提供真实凭据，不猜默认密码；不要把连接检查扩展为配置修改、重启或网络扫描。
- 硬件与连接：[ESP-Mosaico 文档总入口](https://docs.espressif.com/projects/esp-dev-kits/zh_CN/latest/esp32s31/esp-mosaico/index.html)、[V1.0 指南](https://docs.espressif.com/projects/esp-dev-kits/zh_CN/latest/esp32s31/esp-mosaico/user_guide_v1.0.html)、[V1.2 指南](https://docs.espressif.com/projects/esp-dev-kits/zh_CN/latest/esp32s31/esp-mosaico/user_guide.html)、[主板背面图](https://docs.espressif.com/projects/esp-dev-kits/zh_CN/latest/esp32s31/_images/esp-mosaico-coreboard-back.png)、[ESP32-S31 串口连接说明](https://docs.espressif.com/projects/esp-idf/zh_CN/latest/esp32s31/get-started/establish-serial-connection.html)。串口指南中的通用 USJ/GPIO 说明不应误作 Type-C 引脚定义。
- 应用、固件与 Vibe：[应用指南](https://mosaico.espressif.com/zh/guide/)、[控制面板](https://mosaico.espressif.com/zh/guide/chat-coding/)、[FAQ](https://mosaico.espressif.com/zh/guide/faq/)、[固件更新](https://mosaico.espressif.com/zh/firmware-update/)、[官方出厂源码](https://github.com/esp-mosaico/esp-mosaico-claw)、[Vibe 工作区](https://github.com/esp-mosaico/esp-mosaico-vibe)、[设备模式说明](https://github.com/esp-mosaico/esp-mosaico-vibe/blob/main/docs/device-modes.md)。BOOT 是 ROM 下载入口，此时 ESP-Iris 未运行，不能直接使用依赖 ESP-Iris 的 Vibe 应用控制命令；`recover` 会写入基底固件，不是只读连接或退出 BOOT 命令，不得以排查连接为由擅自执行。
- 工具与芯片参考：[esptool 复位及禁用 stub 选项](https://docs.espressif.com/projects/esptool/en/latest/esp32s31/esptool/advanced-options.html)、[watchdog 复位限制](https://docs.espressif.com/projects/esptool/en/latest/esp32s31/troubleshooting.html#watchdog-reset-limitations)、[ESP32-S31 睡眠模式](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s31/api-reference/system/sleep_modes.html)、[息屏 UI 源码](https://github.com/esp-mosaico/esp-mosaico-claw/blob/1b7388b26523d74a36b2a9e4ec3df8c838053bbb/components/mosaic_ui/mosaic_ui.c)、[息屏超时默认值源码](https://github.com/esp-mosaico/esp-mosaico-claw/blob/1b7388b26523d74a36b2a9e4ec3df8c838053bbb/components/app_system_config/app_system_config.c)。

## Loom OS live 开发与同步录制（Otty × Codex）

本节用于用户明确要求的 live 开发与同步素材采集。开发目标来自真实需求，视频记录过程与证据，不为拍摄制造代码改动、设备状态或成功结果。详细流程见[开发同步录制工作流](copis/宣传计划/05-Mosaico实机纪录/开发同步录制工作流.md)、[Otty-Codex 开发同步录制](copis/宣传计划/05-Mosaico实机纪录/Otty-Codex开发同步录制.md)和[2026-10-16 测试记录](copis/宣传计划/05-Mosaico实机纪录/Otty-Codex测试/测试记录-2026-10-16.md)。

### 每次执行双路录像与独立归档（2026-10-17 补充）

- 2026-10-29 session203真机部署条件只读核对：原Otty703同pane、Safari4621及QT5714静音FaceTime三路，3GET/0POST/设备修改0；10.0.0.129 status200/Wi-Fi正常，lua-modules200未列loom_touch/loom_security，native/status404，固件版本/boot_id未知。ioreg未枚举Espressif/USB-OTG或USB串口，不推断关机/未插线/坏线，未开串口/ROM握手。现有22产物及三update镜像独立大小SHA/候选分区容量核对通过，但不是现场分区读回；安全状态/所需完整备份/刷写授权未核，deployment_ready=false，无上传/Lua执行/Runtime/点按/重启/刷机/eFuse。六MP4完整及独立解码/摘要/30fps静音/328pins及18最终帧实际复核通过，29,933,676B；短测8.17/8.10/8.20秒、正式90.17/90.07/90.17秒，本轮六MOV核验后删净释放171,842,652B不可直接恢复/历史不动。Otty细字PARTIAL，Safari旧202 g2停止页非本轮执行，相机实体Works旧Preflight非Runtime验收。QT预览正常关闭/打开面板仍在，原Otty空闲/Safari保留，发布pending。下一步先核当前数据链/USB模式，若需ROM或重启另授权，再只读确认现场分区/安全状态/备份后明确更新范围，不自动刷写/盲按POWER或BOOT/重跑旧Check。见203验收。

- 2026-10-29 session202（主机原始UTC为10-28，时钟未改）：独立有界HTTP序列不再等模型逐屏门闩；原Otty703同pane实际36Python/9Node/6类host Lua检查通过，Safari4621只刷新/Connect各一次，13HTTP中12成功/原生input.tap真实E_UNSUPPORTED。六次DOM合成点按经官方队列/真实WASM LVGL，空白零事件、Counter2/2/2、Settings/Home至4/4/4、g2重置后Counter1/1/1/1、两Stop取消exit1均通过；五阶段正式MP4实际核133.433/138.106/142.812/148.717/153.197秒。原自动结果visual_pending不覆盖，FINAL.REVIEW独立追加视频通过；200/201旧失败不改。321pins/六tracked/七模块/四WASM资产/生产保护保持，实体操作0，无代理/Chrome/commit/push。六MP4共16,341,234B，短测8.00/8.07/8.03及正式300.13/300.10/300.03秒，完整及独立解码/SHA/30fps静音、18最终帧＋5关键帧实际复核通过；本轮六MOV核验后删净释放273,761,015B不可直接恢复/历史不动。Otty细字PARTIAL，相机实体Works旧Preflight非模拟UI，代码准备非全程编码录像，发布pending。18763无监听/相关进程退出、QT5642预览正常关闭/打开面板仍在，原Otty空闲/Safari g2停止页保留。模拟闭环补齐后不再为录像重复演示；下一目标核真机数据通道/分区/备份/精确更新范围，刷写和重启另授权。完整Runtime/生产HTTP/物理触摸/真实重启自启尚未验收。见session202验收。

- 200/201媒体终验：12MP4完整及独立解码/大小SHA/30fps无音轨、310/317pins和每轮18最终抽帧、额外5个Safari关键帧实际复核完成。200首次启动失败、201点按与Settings/Home成立但STEP3超时均保留，不回填自动通过。正式均约360秒，共190,682,028B；本轮12MOV核验后删净释放1,316,778,958B不可直接恢复、历史媒体不动。201正式104.4285/229.891/290.626/350秒明确录到Counter2/Settings/Home/清理；Otty细字PARTIAL，相机实体Works非模拟UI。复核工具单LF比较失败原样留档，resume精确核验后完成，不改产品/原结果。18763无监听及相关进程退出、QT5586预览正常关闭/打开面板仍在、原Otty空闲与Safari停止页保留；发布pending。下一关去掉模型逐屏交接门闩，自动有限模拟序列后按正式录像核验，第二实例/原生input浏览器重检/完整Runtime/真机自启未验收。

- 2026-10-28 session200–201：独立HTTP模拟输入v2实际可用。200错误assert无返回值set_title导致start失败，原件保留；v2只修此调用。201原Otty703同pane29Python/9Node/6类host Lua契约通过，Safari4621刷新/Connect各一次后7HTTP/5次合成DOM点按，经官方队列/真实WASM LVGL回调得到空白零事件、两次Counter2/2/2、Settings/Home各一次、最终4/4/4，主Agent真实CUA核对，未手点目标。派生HTML仅capture/release两处isTrusted guard，不改WASM/生产main/require_touch/七模块/六tracked或旧199/200输入，不fake loom_touch。300秒逐屏交接在STEP3超时，verification_failed保留，自动Stop/cleanup initialized=false/exit1/Run恢复/Stop禁用；迟到Home观察不回填OK/GUI.DONE。原生input浏览器重检与第二实例未执行。下一关有界自动序列＋阶段时间点＋事后实际Safari MP4验收，不把模型往返当每步执行门闩；不重跑旧Check或擅自真机部署/重启。两轮三路有限静音录像含Safari、原Otty及QT5586 FaceTime预览，媒体终态以200/201验收为准，代码准备不冒充全程编码录像，发布pending。实体HTTP/USB/上传/点按/重启/刷机/eFuse/生产数据0，无子代理/Chrome/commit/push；仍非完整Runtime/生产HTTP/实体触摸/重启自启验收。

- 2026-10-28 session199最终收尾：local_HTTP_real_dispatch_GUI_verified及独立控制/GUI/bundle验收通过，原17Python文案错误明确以16Python/2Node/3CJK日志更正，原件不改。六MP4完整及独立解码/大小SHA/30fps无音轨/302pins、最终18帧及Safari额外四关键帧均实际复核；设置/Home/g2标题/Stop完整处于正式片内。正式三路均600.07秒，短测8.03/8.03/8.07秒，213,157,477B；本轮六MOV核验后删净释放1,027,061,496B不可直接恢复、历史媒体不动。Otty细字PARTIAL，相机实体Works旧Preflight非模拟UI，中文方框限制保留，代码准备不冒充全程编码录像，发布pending。18763无监听、录制/转码/独立验证进程退出，QT5191预览正常关闭/打开面板仍在，原Otty空闲及Safari停止页保留。下一关显式simulation-only的HTTP坐标输入/真实事件闭环，仍非完整Runtime/生产HTTP/物理触摸/自启验收；下段开发阶段“MP4尚在终验”为此前快照，详见199验收。

- 2026-10-28 session199开发阶段：本机HTTP→Safari固定guest信箱→真实core.control_modules.dispatch已端到端观察，16Python/2Node/3CJK回归通过；冻结runner及说明误写17不改原件，以日志及独立验收更正。12HTTP中11成功、input.tap真实E_UNSUPPORTED，设置/Home/g2标题/Stop清理由主Agent实际CUA核对并在520秒内交接，非仅queued收据；runtime.restart只重建Lua state，不是实体重启。合成Settings不写配置，未载CJK字体的Launcher中文方框保留；Stop清理后exit1/Run恢复/Stop禁用，无当前可见active-screen旧警告。原Otty703同pane实际执行，Safari4621刷新/Connect各一次；三路短测九帧及正式600秒自然结束，MP4尚在终验，QT5191静音预览已正常关闭。独立临时256bit控制/浏览器内存能力仅保护loopback模拟，不替换生产四字符配对；不mock原生HTTP/thread/touch，不改生产main/require_touch、七模块/六tracked/四WASM资产。实体HTTP/USB/上传/点按/重启/刷机/eFuse/生产数据0，无子代理/Chrome/commit/push。下一关显式simulation-only的HTTP坐标输入与可观测闭环，完整Runtime/真机接口/自启仍未验收；媒体终态见199最终验收。

- 2026-10-28 session197–198修复版Safari实测：用户动作时明确允许后，197在原Safari4621刷新加载本地派生WASM 3e5c3ae2709845dd3d4f0b288045da61759a6a1686b7d69c29deb7294236e12e；显示合同/exit0、25次init/load/process/deinit/重复deinit/25PASS/exit0，实际日志无旧active-screen警告。197 start#3/#4与198沿用同实例start#5/#6均实际核空白无回调/两次按钮2/2/2/Stop一次、中文设置可读/Demo/Back/设置/Home各一次/PASS1/1/1/1/字体删除/cleanup/正常exit0。固定源码Stop经luaL_error后清理返回1，取消1非正常0，不改产品或旧197全0预期；旧hosted commit未知。两轮GUI观察文件均晚于270/145秒期限未消费，原gui_not_verified/超时保留，不回填自动通过。生产main/require_touch/五模块/六tracked/原官方资产不变，实体操作0，无代理/Chrome/commit/push。
- 197/198三路含Safari真实录屏、原Otty703同pane真实执行、QT5030 FaceTime静音预览；12MP4独立完整解码/大小SHA/30fps无音轨及每轮18最终帧实际复核完成，290/295pins保持。正式197 Safari/Otty/相机300.03/300.00/300.00秒，198为180.00/180.00/180.07秒；12片135,750,674B，对应MOV核验后删净释放1,061,278,172B不可直接恢复、历史不动。Safari实际时间轴明确197只覆盖刷新/显示/25循环，198覆盖点按取消，中文导航过程只有真实CUA证据、未被正式片覆盖，不能称全流程录下。Otty细字PARTIAL，相机实体Works旧Preflight非模拟UI；发布pending。录制/转码退出、18763无监听、QT预览正常关闭/打开面板仍在，Otty空闲/Safari start#6 PASS停止页保留。下一开发关完整Runtime/HTTP控制隔离适配，另设合理有限GUI/录像预算并及时交接，不为凑片重复测试/擅自真机部署或重启；仍非S31/设备HTTP/物理触摸/重启自启验收。详见197/198验收与docs/mosaico-emulator.md；下方“Safari待加载/警告未修”为历史阶段。

- 2026-10-28 session193–196媒体最终收尾：四轮24个MP4（三路短测＋正式）均完成完整及独立解码日志、大小SHA/参数/原固定输入核验与每轮18个最终抽帧实际复核。194/195失败原样保留，196仅主机生命周期PASS、未加载新Safari构建；Safari已录屏但仍是旧189停止页。194/195/196核验后各删对应六MOV，净释放1,353,977,522/1,147,939,125/370,881,510B不可直接恢复、历史媒体不动。Otty细字PARTIAL，相机后期暗不可验UI；共用pane时段可能重叠，不称互斥/帧同步。录制/转码进程退出、18763无监听、QT4903预览已关但打开面板仍在、原Otty空闲及Safari旧停止页保留。下一关动作时确认后新三路录屏加载本地派生WASM，仍不操作真机，隐私发布pending；下方191–196“媒体收尾中”为早期快照。详见194/195/196验收。

- 2026-10-28 session191–196屏幕释放修复：191清单KeyError/192包装SyntaxError/193Python3.9版本拒绝/194Lua TLS失败/195首任务内部符号链接检查及二次Lua夹具状态误判均保留，不覆盖旧证据。SDK私有Emscripten6.0.13已就绪，同官方Lua5.4.8地址直连成功且TLS保持，仅子进程去代理；LVGL9.5.0。固定62aaeed源码独立副本只修默认screen保存/restore-before-cleanup/stop清指针，不造fallback/跳过deinit/隐藏WARN/改生产保护。195完成1096项真实模拟器构建，196独立新测试对象/JS/WASM只将luaL_dostring逻辑OR折叠错误码改为load/pcall保留真实状态，类型/文本断言不放宽；原版expected_active预期失败，修复版105循环heap5576一致、RAW/flag/默认缺失/active/double stop＋真实Lua正常30/异常30/heap1541616一致通过，无active-screen WARN，12文件检查测试通过。新四资产9,458,893B及本地派生manifest在wasm-lifecycle-check-01/runtime，独立大小SHA/WASM.validate不instantiate/280pins通过，原六tracked/官方四资产保持。Safari未刷新/加载新构建，仍旧189 start#3停止页，不能称GUI警告已消失或Runtime/HTTP/物理触摸/自启通过，实体操作0、无子代理/Chrome/commit/push。原Otty703同pane真正执行，新三路含Safari真实录屏、静音；193六MP4277pins/完整及独立解码/18帧三联图已终验，删对应六MOV净释放1,346,339,089B不可直接恢复/历史不动；194–196本段快照媒体收尾中，终态见各验收。Otty细字PARTIAL，相机早期Works旧Preflight、后期偏暗不可验UI，不推断关机/复位；重复录制可能时间重叠且共用pane，不声称互斥/帧同步。下一关动作时确认后新三路ready内Safari加载派生WASM测25次生命周期及原点击/中文导航，不重演实体开机，隐私发布pending。见196验收与docs/mosaico-emulator.md；下方“未修/emcc未安装”为历史阶段。

- 2026-10-28 session188–189独立全流程补录：188冻结不存在的185/FINAL.REVIEW.json时录制前失败，原件保留；189修封装引用，原Otty703同pane实际执行，Safari4621＋Otty＋QT4846静音窗口三路短测九帧后正式360秒。录像内实际刷新Safari得到新WASM，start#1显示合同/色块TEST/exit0，start#2空白不计数/两次按钮事件2/2/2/Stop一次，start#3中文Launcher/Demo/Back/设置/Home各一次/PASS1/1/1/1/字体删除/exit0。正式Safari350/359秒明确包含最终清理与退出，纠正此前仅凭GUI.DONE写入时刻推断“尾段未录到”；320秒交接确实超时，原gui_not_verified/exit1及迟到文件/超时说明保留，不回填自动通过。备用190仅准备未启动。六MP4（三正式各360.00/360.03/360.03秒＋三短测）独立完整解码/大小SHA/30fps无音轨及最终实际18帧、15个Safari关键帧完成；本轮六MOV核验后删，净释放678,320,514B不可直接恢复，旧媒体不动。269/旧187256/185230pins及六tracked不变；Otty细字PARTIAL，相机实体Works旧Preflight非模拟UI。active-screen警告未修，SIM Settings为合成英文面板、非生产设置写入；这是新应用级演示，不是实体开机/完整Runtime/HTTP输入/重启自启验收，不冒充旧历史原片。QT预览正常关闭、Safari停止及原Otty空闲保留、18763无监听/相关进程退出，隐私发布pending。实体操作0，无新下载/安装/子代理/Chrome。见[189验收及MP4](copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-safari-full-replay-189/验收记录.md)；下一开发关仍是独立修模拟器清理生命周期，不继续为录片重复演示。

- 2026-10-28 Safari媒体补录：按用户要求，仅录当前session187同一start#4中文Launcher/PASS1/1/1/1停止终态，不刷新/Run/点击/启服务/真机操作。补录01窗口本地化匹配失败、录制前停止并保留；02精确核CG4621，8秒短测源三帧实际审查后才正式录20秒，最终两MP4为20.03/8.00秒、1332×854/H.264/30fps/静音，完整解码/独立复解/摘要及最终实际六帧通过。本轮两MOV核验后删、净释放2,763,469B不可直接恢复；旧媒体不动。269补录输入、187原256及185原230pins一致，原结果不回填；原Otty703同pane实际执行并空闲保留、Safari原停止画面保留、录制/转码进程退出、18763无监听。这是事后留存结果，不是182/183/185历史点击视频，184/186未运行guest不造画面；各旧session只新增关联说明，不复制冒充原片。实体操作0，无新下载/安装/代理/Chrome；本轮仅用户指定Safari补录，不启相机双路。全片隐私终审及发布pending。见session187/Safari补录说明.md、Safari补录-02/验收记录.md；下方“Safari没录像”保留为原执行时的历史事实。

- 2026-10-28 session186–187字体/交接：186因测试临时路径/var符号链接被严格helper拒绝而verification_failed/0.543秒，原输入/结果/日志保留，无本轮bundle/服务/guest运行；后续旧241仅canonical字体测试和观察器日志两项预期变化，两份旧源快照精确匹配，其余239不变。187新独立CJK helper用官方同包Fusion Pixel（Noto实际cmap缺“设/置/中/文”），有界复制到WASM guest独占scratch，size24/cache96加载，完整shutdown后删除；不挂主机字体/生产存储，不改五真实模块、main/require_touch或官方四资产。31Python＋8场景CJK Lua＋5原entry＋原UI回归PASS，Safari沿用同一runtime/start#4，中文设置可读、Demo/Back/设置/Home各一次、PASS1/1/1/1、自动exit0/Run恢复/Stop禁用，实际CUA绑定观察在120.089秒内被消费，loom_font_ui_verified_with_upstream_warning/256pins不变；旧185230/六tracked保持。active-screen警告仍在，固定源码定位sim close缺设备release已有的restore-before-cleanup顺序，hosted build未知，未重编/改官方资产/跳过deinit/隐藏警告，emcc未安装。下一关独立源码/工具环境修生命周期及重复init/deinit测试，再派生WASM/新manifest/新双路GUI回归；不覆盖原件，不把本轮当完整Runtime/S31/设备HTTP/物理触摸/重启自启验收。实体HTTP/USB/上传/点击/重启/刷写/eFuse/生产数据操作0，单主Agent无Chrome。原Otty703同pane真实执行；八MP4独立完整解码/大小SHA/30fps静音及各正式实际六帧完成，正式各360/360秒，对应八MOV核验后删净释放1,197,393,588B不可直接恢复/历史不动。细字PARTIAL，相机偏暗/实体Works旧Preflight非模拟UI，Safari仅CUA AX/截图没录像。QT4747预览关闭、Otty空闲保留、18763无监听、相关进程退出、发布pending。目录按会话2026-10-28，主机实际UTC2026-10-27原样保留/不改时钟。见186/187验收、Safari实际观察、字体诊断和docs/mosaico-emulator.md；下方184–185是历史阶段。

- 2026-10-27 session184–185最小Loom UI：新增固定五真实模块打包与独立模拟入口，生产main/require_touch=true不改，先真实验证E_UNSUPPORTED再仅模拟入口display-only，touch_available=nil/touch_registered=false，无假loom_touch。184因新测试误断言Launcher callback返回true而host_checks_failed，原失败源/SHA及结果保留；仅修测试为核真实导航队列，旧220pins中该一项预期变化、其余219不变。185的13Python＋5场景Lua＋原UI回归/bundle准备/仅语法通过，230pins/旧204/六tracked/官方四资产不变。Safari沿用182同一runtime/start#3，实际单击Demo/Back/设置/Home各一次，480×480真实页面切换、PASS1/1/1/1、自动exit0/Run恢复；设置中文方框与active-screen清理警告未修。200秒自动任务先超时，原ui_deadline_not_verified/task-failed/200.399秒保留，后写GUI观察未消费，不能称整轮门控通过或全部动作在正式录像内。原Otty703真正执行、非代理/镜像；八MP4独立全解码/大小SHA/参数及各正式实际六帧完成，正式184为360.00/360.00秒、185为240.00/240.00秒，30fps静音。八MOV校验后删，净释放1,318,386,398B不可直接恢复、历史不动；细字PARTIAL，相机实体Works旧Preflight非模拟UI。Safari仅CUA AX/截图、没录像或本地截图文件。QT4700预览关闭、原Otty空闲保留、18763无监听、相关进程退出，发布pending。实体HTTP/USB/上传/点击/重启/刷写/eFuse/生产数据操作0；不是完整Runtime/设备HTTP输入/自启验收。下一关核字体、清理生命周期及GUI观察接收时序，不重跑旧Check/放宽生产保护。见184/185验收、Safari实际观察与docs/mosaico-emulator.md；下方182–183是前一阶段。

- 2026-10-27 session182–183：用户明确允许Safari本地执行181固定官方WASM/JS。182实际公开display_contract返回DISPLAY_CONTRACT_OK/exit0，480×480色块与TEST可见；随后260秒窗口到期，ui_deadline_not_verified/task-failed保留，未执行点击夹具。183新双路沿用同一runtime，只加载独立合成LVGL，空白点击无回调，两次按钮单击各pressed/released/clicked一次、最终2/2/2；Stop一次后FINISHED 2/2/2、exit0、Run恢复/Stop禁用，有active screen was deleted清理警告保留。application_ui_verified/381.364秒，不代表生产Loom/S31/HTTP/物理触摸/自启通过。198/204pins、旧两归档/六tracked/四资产不变，无新下载安装/实体/eFuse/生产数据操作、不改保护。原Otty703真正执行录制/限时loopback服务，非代理；Safari仅CUA观察、未录视频，不能拿Otty/相机视频冒充模拟UI。八MP4独立完整解码/大小SHA/参数及各正式实际六帧完成，182正式300.00/300.00秒、183正式600.00/599.97秒、30fps静音；八MOV核验后删，净释放2,116,757,821B不可直接恢复、历史不动；细字PARTIAL，相机Works旧Preflight。QT4626预览正常关闭、原Otty空闲保留、18763无监听、Safari保留停止画面，发布pending。下一关先做Loom最小模块官方API适配/隔离模拟，不绕require_touch或重复旧Check；整机触摸/NAND阻塞仍在。见182/183验收、Safari实际观察及docs/mosaico-emulator.md。下方180–181未执行为历史准备阶段。

- 2026-10-27 session180–181应用级模拟准备：核固定esp-emu实际help仅I2C register-file/ACK读回，未找到完整CST触摸/NAND配置入口，不重跑179必失败镜像，不绕外设/保护。发现官方ESP-Claw Lua/LVGL WASM模拟及CI发布地址simulator.esp-claw.com；180新helper21隔离测试＋官方1Node测试PASS，但data单次30秒下载超时、preparation_failed原样保留。181只复制已核三文件并GET一次缺失data，12.790秒完成四件套9,465,029B、JS/data大小/连续内部布局一致、WebAssembly.validate通过；未instantiate/运行guest，prepared_not_run。hosted build commit未知、未本地编译/验官方签名，本地SHA只固定下载副本。175/185pins、两归档/六tracked不变，无实体设备/生产密钥/eFuse操作；Runtime/UI/点击/自启仍未验收。tools/mosaico_web_sim.py仅127.0.0.1、四文件白名单、冻结内存内容、拒Host/Origin/路径穿越/POST，CSP和Permissions-Policy阻外网/相机麦克风；本轮服务仅合成测试短暂开随机loopback端口，无18763常驻服务。原Otty703同pane只镜像非UI工具真实日志、QT4528静音预览；八MP4独立完整解码/大小SHA/参数及各正式实际六帧完成，180正式180.00/180.03秒、181正式120.00/120.00秒、30fps/静音，八MOV校验后删，合计净释放750,668,327B不可直接恢复、历史不动；细字PARTIAL，相机实体Works旧Preflight不是模拟UI。原Otty空闲保留、预览关闭、发布pending。下一关先取得浏览器运行新下载官方代码的确认，再新双路session用Safari/WebKit测公开/合成Lua显示与点击，保持应用级和整机/真机边界；不自动加载生产数据或放宽require_touch。见180/181验收、独立结果/媒体复核和docs/mosaico-emulator.md。

- 2026-10-27 session179公开HMAC夹具：新独立helper仅接受合成336B基线，固定SDK公开key1–32放KEY1/BLK5（compact byte144），S31 purpose bit101宽5/HMAC_UP8，仅增该key读写及用途写保护，不改固件/HMAC/鉴权/require_touch。22定向测试PASS，无重编；25秒真实ROM模拟已见eFuse HMAC key ID1/block5 validated，即真实esp_hmac_calculate返回OK，但未比较guest digest/不证明生产认证。随后触摸I2C未发现、NAND厂商0xff，main.c:1130 main_install_touch_mux失败，13abort/13模拟复位，Runtime/HTTP/UI/点击未启动，application_entered_then_failed。113pins/原22与派生11归档/六tracked不变，无实体设备/真实eFuse/生产密钥操作。pristine336B不变，runtime348B=原前缀+12零，不能回灌严格夹具。原Otty703同pane镜像非UI模拟日志、QT4493静音预览；四MP4独立完整解码/大小SHA/参数及实际六帧通过，正式120.03/119.97秒、短测8.03/8.03秒，30fps/无音轨，对应四MOV校验后删，净释放359,839,598B且不可直接恢复、历史不动。末帧文字PARTIAL，相机实体Works/旧Preflight不是模拟UI；Otty空闲保留、预览关闭、相关进程退出，发布pending。下一关核官方触摸/NAND模型，完整协议而非ACK/stub或跳过外设，不反复运行必失败输入；0xB4是配置8位地址、实际7位0x5A，LCD driver create不等于可见渲染。见179验收/独立结果复核/docs/mosaico-emulator.md；下方178 HMAC用途阻塞为旧轮结果。

- 2026-10-27 session178合成eFuse：官方固定make-efuse工具生成S31 rev0.0/本地管理模拟MAC基线，严格helper按固定SDK USER_DATA=BLK3 bit0/文件byte80仅改byte81为1（模型v1.0，不是现场版本），密钥/purpose/安全位全零。14定向测试PASS/无skip；不重编、复用177镜像新副本25秒真实ROM启动，Hardware version v1.0通过，随后main.c:1126的trial_auth_validate_hmac_efuse_key因block5/ID1的purpose0非HMAC_UP返回0x103、13次abort/模拟SW_CPU_RESET，application_entered_then_failed。HMAC计算尚未到达，Works/HTTP/Runtime/点按未启动；保护未禁用，真机HTTP/USB/上传/重启/刷写/eFuse读取烧写0，无真实身份/密钥导入。101pins/原22归档/派生11归档/六tracked前后不变，任务26.432秒未超95秒。pristine336B保存不变，但官方退出保存runtime为348B（前336B相同+12零字节）；raw changed_bytes=[]只是共同前缀，不是全文件不变，不将348B直接回灌严格夹具。原Otty703同pane镜像非UI工具真实日志，QT4464静音预览；正式120.03/120.00秒、短测均8.00秒，四MP4独立完整解码/大小SHA/参数及实际六帧完成，30fps/无音轨；对应四MOV校验后删、净释放360,868,882B且不可直接恢复，历史不动。末帧细字PARTIAL，相机Works/旧Preflight/Stopped，无新Runtime镜头；原Otty空闲保留、预览关闭、相关进程退出，发布pending。下一关先核官方HMAC模拟测试/独立本地测试身份方案，保持真实计算、隔离生产Trial服务，不用生产密钥或禁用保护，不反复运行必失败的夹具；LCD/触摸/NAND仍未验收。见178验收、独立结果复核与docs/mosaico-emulator.md；下方177板型阻塞是旧轮结果。

- 2026-10-27 session175–177隔离模拟：独立source/SDK/build只关闭USB_CDC_AUTO_INIT并保留UART，Board Manager USB原已有init_skip=true；175因新SDK路径未登记S31目标而exit127/未编译，176官方登记后整固件编译exit0/253.232秒，但宿主误用系统Python缺elftools，原preparation_failed保留/未模拟。177用现有隔离Python3.12接续核验/打包/25秒真实ROM启动，不重编；已进入真实Starting app并注册114资源，随后BSP从模拟eFuse USER_DATA读板型0x0000，不支持而abort/14次模拟SW_CPU_RESET，分类application_entered_then_failed。USB门槛越过不等于Works/HTTP/Runtime/点按健康，HMAC尚未到达。派生11产物标simulation_only/do_not_flash，原22归档/manifest、76冻结pins及六tracked不变；无实体设备HTTP/USB/上传/点按/重启/刷写/eFuse读取烧写。非UI终端执行，原Otty703同pane仅镜像真实日志，不冒充Otty shell执行。三轮12MP4独立完整解码/大小SHA/参数及各正式实际六帧通过，正式175为599.97/600.00秒、176为600.00/600.00秒、177为120.00/120.00秒，均30fps/无音轨；对应12MOV校验后删，分别净释放1,683,607,761/2,025,117,873/368,447,018B（共4,077,172,652B），不可直接恢复，历史不动。Otty末帧细字PARTIAL，相机Works/旧Preflight/Stopped，无Runtime镜头；原Otty空闲保留、QT4417预览关闭、相关进程退出，发布pending。下一关核固定S31字段布局及官方--efuse的336字节格式，制作仅模拟合成板型fixture，不读/烧真机eFuse、不导入身份密钥、不绕HMAC/鉴权/require_touch；LCD/触摸/NAND模型未验收。详见175–177验收、177独立结果复核及docs/mosaico-emulator.md；下方173–174“未进真实主体”仅为旧轮结果。

- 2026-10-27 session173–174本机模拟：173官方下载25秒超时/attempts=[]失败保留，续传并核官方SHA后174以esp-emulator0.51.0实际运行build01七段合并副本25秒。真实ROM/bootloader/16MB PSRAM/FreeRTOS通过，但USB DWC2 ID断言→TinyUSB5秒超时0x107→usb_console.c:329的__wrap_app_main abort，4次模拟SW_CPU_RESET，真实应用主体/Works/HTTP/Runtime未启动；Calling app_main只是包装入口，raw app_started/panic_seen=false及exit0误判不作验收，以174独立结果复核blocked_before_real_app_main为准，不复用该marker扫描。无实体设备HTTP/USB/上传/重启/刷写；原22产物/manifest、合并镜像前后、六tracked pins不变。非UI终端执行模拟器，原Otty703同pane只镜像同一日志，不冒充在Otty shell执行。两轮八MP4独立完整解码/大小SHA/参数及各正式实际六帧通过，正式173为180.03/180.00秒、174为120.00/120.00秒，30fps/无音轨；对应八MOV校验后删、净释放727,307,898B不可直接恢复，历史不动。174末帧文字PARTIAL，实体相机Works/旧Preflight，无Runtime镜头；原Otty空闲保留、QT4378关闭、相关进程退出、发布pending。下一关独立模拟专用配置关闭USB_CDC_AUTO_INIT/保留UART并核Board Manager残余USB初始化，不改真机保护、不把软件stub当硬件验收；本轮未改固件/重编译。见173/174验收与174独立结果复核。

- 2026-10-27 session172终验：新build01原生控制固件已完成ESP32-S31整机编译/链接/打包/检查，exit0，521.986秒未超530秒预算。仅构建子进程去代理＋已验签GSPC0.9，TLS/签名保持开启；18 overlay/22产物/官方归档7 BIN与实际ELF原生路由/boot符号独立复核通过，产物`firmware/artifacts/2026-10-27-native-control-01/`、manifest SHA `7bd74f11d0b5d1f17d682d92dfe95185090e50b788248a39d5a0ee1f435e8acd`。37旧冻结输入在任务后通过，随后仅修docs/mosaico-input-api.md的“三GET均200”为200/200/404并补新构建事实；后核36项一致/仅此文档预期变化，六tracked未变，不回写旧inputs。无本轮设备HTTP/上传/执行/点按/重启/刷写/启用自启，USB/串口仍无枚举；下一关有效数据连接→现场只读分区/安全状态/必要备份→精确三分区更新范围及刷写授权，initial官方全量包不可直接作为update。可信bootstrap/Runtime初装和一次配对仍待完成，不再点旧Check。原Otty703/QT4277双路正式600.03/600.01秒自然结束，四MP4独立完整解码/大小SHA/参数及正式实际六帧通过，删对应四MOV净释放2,059,861,421B、不能直接恢复，历史素材未动；正式MP4为600.03/600.00秒，30fps/无音轨。Otty中末成功可读，相机Works/旧Preflight，无新功能证据。原Otty空闲保留、预览关闭、录制/转码/独立验证完成，发布pending；详见172验收/产物独立复核/部署范围草案。下方169–172续接段的“172仍在录/终态待补”为当时快照，现以本段为准，不重复构建或刷写。

- 2026-10-27 session169–172续接：169在BSP Git TLS下载失败，170在官方GSPC0.9清单Python TLS EOF失败，均exit2且未进入C编译；两轮各四MP4独立完整解码/摘要/参数及实际六帧终验已完成，删对应MOV分别净释放1,664,343,291/1,615,509,562B。171正常curl HTTPS固定官方下载＋保留内建Ed25519验签成功，GSPC0.9置项目私有cache，同build01却再次BSP Git TLS失败exit2；四MP4独立完整解码/摘要/参数及实际六帧终验完成，删对应四MOV净释放1,353,591,668B，均不能直接恢复。Otty中帧结果可读、末帧PARTIAL，相机变暗但仍Works/旧Preflight，无新功能证据。172复用原Otty703/QT4277，新短测实际六帧后仅构建子进程去代理＋已验签GSPC续接同build01，configure已通过/整固件终态待补，仍在600秒双路。直连与继承代理的只读Git诊断都曾成功，不断言代理是唯一根因。37冻结输入未改，旧GSPC0.8不替代0.9，不降低TLS/签名；无设备请求/上传/点按/运行/重启/刷写/启用自启。09:50 USB/串口无枚举，不据此推断关机或物理断线。隐私发布pending。详见169/170/171验收；下方165–169“169仍在构建”为历史快照。

- 2026-10-27 session165–169：用户将优先目标改为原生HTTP启动Runtime、点按及后续重启自启，停止沿旧Check反复人工点击路线。主Agent独立实现`GET /api/loom/native/status`、`POST /api/loom/native/control`（runtime.start/input.tap/device.restart）及`tools/loom_native.py`；复用已配对四字符token/epoch、当前boot_id/独立递增ID、执行前消耗、动作前撤销重核、错误令牌冷却，固定bootstrap与开机hook共享每boot一次提交attempt，不提供任意Lua/path/eval/自动重试。165仅短测等待审阅超时；166首轮11项中两错误保留，167修正后11Python及7组Lua全部PASS/无skip，含真实C编译执行/临时Git overlay，仅定向host证据。设备只读三个GET分别200/200/404，loom_touch/loom_security未列出，USB/usbmodem无匹配但不推断物理断线或关机；无上传/运行/点击/重启/刷写/启用自启。168新build01在530秒源码子模块下载预算处退出124、未进入整固件编译；169正在新双路内用旧build04固定提交的Git对象种子加速同一新build，不复制旧产物/工作树脏改动，不改旧cache，构建终态待补。165–168的14个本轮MP4均独立完整解码/大小SHA/参数及实际六帧复核完成，校验后删对应14MOV，净释放1,997,922,117B，不能直接恢复，历史素材未动；166/167末帧文字PARTIAL，168超时可读，相机均Works/旧Preflight，无新功能证据。169仍在录，原Otty703/QuickTime4277保留，发布pending。首次使用仍需新固件、可信provision固定bootstrap/Runtime及一次本机配对；公共文件路径保护不放宽。原生注入/提交/重启请求accepted分别不等于按钮执行/UI健康/重启完成；下一关以新构建终态和USB/备份/明确刷写范围为准，不要求点旧作品。详见167/168验收与`docs/mosaico-input-api.md`；下方160人工Check路线为历史阶段。

- 2026-10-27 session160：用户在限定“只上传77文件、逐项精确读回、不运行/重启”后回复继续，主Agent复用原Otty703与新QuickTime4167静音预览、新双路短测/实际六帧后，生产runtime_manual_upload首次实连通过。固定149候选343a39c9b2f4，16新目录/77文件305,283B，299请求（206GET/93POST）全HTTP200、逐项精确读回、launcher最后，exit0/uploaded_not_run，无重试或待定attempt。独立核163live输入/455旧公开pins/六tracked/六源码快照/73当前源/require_touch=true不变，私有正文未读，无运行/点击收据/旧报告/安装/HTTP控制/自启/重启/USB/刷机；本轮未重跑61测试。任务02:52:39.774–02:56:38.002 UTC，238.228秒、接近但未超240秒预算，未临时扩大。正式两MP4为300.03/300.00秒、短测均8.00秒，30fps/无音轨，四输出独立完整解码/大小SHA/参数及正式实际六帧通过；校验后删本次四MOV，净释放677,457,168B、不可直接恢复，历史素材未动。Otty末帧77/299/未运行结果可读，相机实体可见但屏幕偏暗、UI文字不可确认，无新标题/运行证据。原Otty空闲保留、预览关闭，本轮录制/转码PID退出，隐私发布pending。下一关只请用户看Works Installed全分页确认Loom Runtime Check 343a39可见，暂不点击；全分页缺标题时另授权一次正常重启，不重传。单次人工运行与GET-only接收另授权/新双路，新80GET精确基线与challenge后才提示点一次，不复用旧反馈或旧Backup/Preflight/Check。详见`2026-10-27-ep04-runtime-upload-160/验收记录.md`与`正式六帧人工复核.md`；下方159“下一关首次只上传”为历史阶段，不能据此重复上传。

- 2026-10-27 session158–159：Runtime live薄驱动组合离线通过，下一关为另授权的首次只上传。主Agent新增固定HTTP/fsync journal/冻结输入与双路guard/真正异步1.5秒macOS inspector/scope授权及单次真实反馈收据链；journal attempt后再次核录像预算，生产入口不接受host/transport/clock/inspect/candidate覆盖。158因110秒封装超时exit1、只前19项通过，失败日志/审批/源码快照保留，残留worker准确核对后停止；159只修测试封装，完整上传/接收/片尾预算三集成仍使用完整guard，61Node（18新live）/0fail/skip/cancel＋两Lua全PASS，154原故障位置PASS，实际inspector三次801.961/191.916/174.586ms通过。455公开pins（431小文件＋24历史媒体）、六tracked/149候选343a39的77文件与73当前源/require_touch=true均不变，两私有输入排除/正文未读。真实设备请求0，无真实授权/点击收据，上传/Runtime/UI/安装/HTTP/自启not_run。两轮默认八MP4独立完整解码/SHA/参数及各正式六帧完成后删本次八MOV，净释放991,308,579B；正式158为180.03/180.03秒、159为300.03/300.07秒，30fps/无音轨。159Otty中帧结果可读、末帧缺字PARTIAL，相机Works/旧Preflight，无新运行证据；原Otty703空闲保留、QT4030预览关闭，本轮录制/转码/失败worker退出，隐私发布pending。旧素材/审批/收据不改，MOV不能直接恢复。下一关新session/真实只上传授权/新双路和冻结审批，使用生产runtime_manual_upload写新namespace/逐项读回/launcher最后，模糊POST不重试，不用旧stage run；Works可见、必要重启、单次人工运行与接收各自另授权，不自动重启或执行，不再泛加mock关卡。详见`2026-10-27-ep04-runtime-live-driver-retest-159/验收记录.md`及`tools/mosaico-runtime-manual-live.md`；下方157“live薄驱动待接入”为历史阶段。

- 2026-10-27 session155–157：Runtime IO适配层离线通过，仍不可直接部署。主Agent新增固定目标/77文件路由HTTP、0600独占/fsync/readback journal与冻结输入/双PID/时限/当前窗口guard及15测试，无CLI。155误pin录制器动态文档、156误把历史视频送入2MiB小文件列表，两轮测试前失败证据保留；157只修验收封装，43Node/0skip＋两组Lua及77文件组合mock/154原故障位置PASS，设备0请求。423公开pins重核（24历史MP4迁移单独审阅、399小文件进逐请求guard），两私有输入排除/正文未读、六tracked与149候选343a39/require_touch=true不变。三轮默认12MP4完整校验后删本次12MOV，独立完整解码/SHA/参数通过、各正式六帧复核完成，净释放583,488,024B；正式90.00/90.07、90.03/90.00、60.00/59.97秒，无音轨/30fps。157中帧结果可读、末帧缺字PARTIAL，相机Works/旧Preflight，无Runtime证据。原Otty703空闲保留、QT3980预览关闭、录制/转码PID退出，隐私发布pending。下一关仍需不可替换live薄驱动、异步实时窗口inspector/真实scope与点击收据组合离线验收，再另授权只上传，不能用旧stage run；本轮同步Swift检查不是逐请求硬2秒inspector验收。详见`2026-10-27-ep04-runtime-io-adapters-final-157/验收记录.md`与`后续接入边界.md`；下方152“适配器待实现”为历史阶段。

- **2026-10-26 本次用户另行授权历史 MOV 清理（已完成）**：365个旧MOV/37,322,226,308B全部转为相邻MP4，逐项输入输出完整解码、媒体参数及删除前双指纹校验通过后删除MOV；输出共1,195,858,103B，净释放36,126,368,205B，失败0/跳过0，全项目复扫剩余MOV 0。中断前完成172项；用户“继续跑完”后在`resume-01/`完成剩余193项，原中断清单原样保存在`manifest.interrupted.json`，唯一1,048,624B中断partial在替代MP4独立验证后另行清理。主Agent再次独立重算全部365输出大小/SHA、核对原片缺失/主清单指纹/原中断快照/六既有tracked不变，全部通过；批处理、复核、FFmpeg及本批次caffeinate进程均已退出。批次为`批量转码/2026-10-26-0757-old-mov-cleanup/`，合并逐文件映射见`manifest.json`，复核见`independent-verification.json`、`resume-finalization.json`及`结束复核.md`。旧session/setup/收据/pins/验收文档未回填，历史“原片保留”描述仅为当时快照；后续新任务须另审本批次原MOV→MP4路径/指纹迁移，不伪造原片、不回填旧pins或把有损MP4当原MOV。删除不能直接撤销，全片隐私审查/发布仍pending。本批次是下方“历史素材不追溯”的一次明确授权例外，不授权未来任意清理。无设备/网络/新录像操作，Runtime进度不变。

- **2026-10-26 用户更新：后续录制默认生成 MP4，不长期保存 MOV 原片。** 新 setup 省略 `preserve_screen_source` 或设为 `false`；不得为留证擅自设为 `true`。`tools/live_capture.py` 在结束并通过媒体验证后，自动后台转换本次正式及 preflight 的 Otty MOV、QuickTime 预览窗相机 MOV；逐个完整解码、时长/尺寸/帧率/体积及输入输出指纹校验通过后删除对应 MOV。失败保留对应原片和错误，不因任务测试失败就跳过有效录像转码。AVFoundation/TP 已直接输出 MP4，不重复编码。此规则覆盖下方历史“保留原始 MOV”的后续默认行为；历史 session/冻结 setup/收据/原片不追溯修改或批量清理。用户另行明确要求保留原片时才使用保留选项；发布仍须人工复核并保持 pending。

- 默认 MP4 已实测（session153–154）：153 的历史批处理测试因 Otty PATH 缺 rg，38PASS/1ERROR 的真实日志保留；154 仅补本次测试 PATH，生产代码未变，39 项含实际合成编码/解码/清理全 PASS、无skip。两轮均省略保留开关，自动转码正式+短测双路，共八 MP4；逐项完成后删本次八 MOV，主 Agent 对八输出独立完整解码/指纹/媒体参数及正式每轮六帧复核，净释放217,501,797B，历史素材未动、既有六tracked不变。Otty中帧结果可读、末帧PARTIAL；相机Camera/Open/Done，无设备请求或Runtime进展。原Otty703空闲保留、QuickTime3921预览关闭、录制及转码PID退出，隐私发布pending。详见`2026-10-26-ep04-default-mp4-retest-154/验收记录.md`；152的Runtime下一关不变。

- 最新Runtime传输核心（2026-10-26 session150–152）：新增独立`mosaico_runtime_manual_transport.mjs`及15测试，无CLI/默认网络适配器。150因macOS临时目录非canonical导致15hookFailed、151因path.join提前折叠符号链接导致1FAIL；均保留审批/日志/源码快照/原片。仅修两条测试夹具、不放宽生产guard，152新双路内28Node/无skip＋两组Lua全PASS，77POST故障位置/77读回故障位置均通过，设备0请求。主Agent独立核375pins/六tracked/原253/147公开证据/148–151失败证据不变、生产核心与150逐字节相同、149真实候选343a39的77文件本地核对及73源与当前仓库一致；未读私有正文。协议核心上传新namespace/逐项读回/launcher最后，接收80GET基线/120秒确认窗口/先confirm再35秒settle/最多3报告GET，COMPLETED及READY不等于Runtime/UI成功，require_touch=true。真实HTTP adapter与durable journal/双路/冻结输入/真实收据live驱动尚未实现和验收，不能直接部署，也不能用旧stage run补位；下一关先离线接入这些驱动，再另授权只上传。150/151/152正式原MOV120.00/120.00、90.02/90.01、90.02/90.00秒自然结束/无音轨/完整解码，主Agent各自独立四摘要及实际六帧完成；Otty中帧结果可读、末帧缺字PARTIAL，相机Camera/Open/Done，无新运行证据。原片全保留/隐私发布pending，预览3834/3860/3878均关闭、原Otty703空闲。上传/Runtime/安装/HTTP控制/自启均not_run。详见`2026-10-26-ep04-runtime-transport-final-152/验收记录.md`及`tools/mosaico-runtime-manual-transport.md`；下方149“上传器待实现”现仅协议核心通过，live适配器仍待接入。

- 最新Runtime独立候选（2026-10-25 session148–149）：147绑定Lua备份通过后，仅离线准备`Loom Runtime Check 343a39`/nonce343a39c9b2f4，不重复Backup/Preflight或旧Check。148的13项测试/入口13场景PASS，但Node24默认spec导致TAP证据解析失败/exit1，失败日志和120秒原片保留；149固定TAP，新双路ready内13Node/无skip、两组Lua、73冻结源仅编译、实际新候选入口13场景均PASS，设备请求0、网络guard自检1/意外联网0。主Agent另核manifest/73源/重渲染三产物/253pins（含六既有tracked、147真实收据/备份媒体及148失败证据）不变；未读私有备份正文。新入口只单次调用新validator、无旧导出器，保留require_touch=true；73源/66模块尚未在设备验证，Runtime/安装/HTTP/自启not_run。149正式原MOV90.01/90.00秒、148为120.00/120.01秒，均自然结束/无音轨/完整解码/主Agent独立四MOV摘要及正式实际六帧完成；149Otty中帧关键结果可读、末帧缺字/PARTIAL，相机Works5 ITEMS/旧Backup，无新运行证据。原片保留/全片隐私发布pending，两个预览均关闭/原Otty703空闲，本次录像PID不存在。当前仅本地候选，77文件受限上传器/接收器仍待实现和mock验收，禁止用旧stage的run模式（会请求Agent）；之后另授权新双路只上传/精确读回、launcher最后，Works可见后另准备单次人工点击，不自动重启/重传。详见`2026-10-25-ep04-runtime-manual-prepare-149/验收记录.md`及`tools/mosaico-runtime-manual-check.md`；下方147“下一关准备”为此前阶段。

- 最新备份验收（2026-10-25 session147）：用户真实“点了”，主Agent14:16:58 UTC首次核对；14:17:27.668596在155pins/新双路gate/两PID/期限有效后独占发布0600/单link/129B真实CLICKED，SHAb4240f0562ce2e8aa588e4e6458a8237fa932d25b88dcd59d7bdae0a5d66f65c，不回填物理触摸时刻。原实例14:17:28.703115公开confirm_click接受后35秒settle，报告COMPLETED再完整output，总7GET全200/0POST、14:18:05.426 exit0/backup_download_verified。绑定Lua90189B，SHA72583b153875d0481f26e8ceb6499488a399557506e952a380d3a318d8a22fa9；接收器fsync/完整读回后，主Agent再独立完整私有读回、0700/0600/单link/155pins/原确认指纹通过，Git忽略、正文未公开。只是一份绑定Lua备份，不是整机或全部Runtime，不保证不可变快照；旧060785根因仍未知，Runtime/validator/安装/自启未运行，不再点Backup/Preflight、不重置槽/重传/重启。正式两原MOV600.01/600.01秒自然结束、差0.001秒、无音轨/完整解码/主Agent独立四MOV摘要与实际正式六帧完成；Otty本轮结果可读，相机Works5 ITEMS/新Backup/Stopped，无抽帧独立触摸过渡证据。原片保留，全片隐私/发布pending；预览3659已关闭/打开面板仍在，原Otty空闲、本次录像PID已不存在。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-owned-backup-receive-147/验收记录.md`及正式六帧复核；下方147等待/无CLICKED为成功前快照，145超时与原片保持不变。

- 最新重试等待（2026-10-25 session147）：用户“再来一次”，145确认窗口超时/task-failed、无CLICKED/接收结果、仅5基线GET；原片480.01/480.02秒自然结束、无音轨/完整解码/主Agent独立四MOV摘要及实际正式六帧已完成，原片保留/隐私发布pending，不补旧收据或断言设备未运行。147新独立、原Otty703/新QuickTime3659 FaceTime静音预览，新短测8.01/8.00秒/实际六帧通过；正式600秒14:10:55.038/.039 UTC起、14:10:57.097 ready。本轮49Python＋147封装7场景＋两组Lua全PASS/无skip、意外联网0；155pins/旧137/六tracked/145最终证据一致。5GET全200，身份/公开入口一致、report/output各64B精确PENDING，14:10:59.486304 backup_click_ready。尚无147CLICKED/运行后GET/备份成功；只点新Loom Backup 1c4343一次并立即确认，提示北京时间22:17前，理论确认截止22:17:59.486304/14:17:59.486304 UTC，晚到不补收据/不再点。14:11:42主Agent复核双路gate/两PID/155pins、剩552.47秒。唯一147进程先公开confirm_click再35秒settle、最多再2GET，不恢复145/复用141、不重置槽/重传/重启/清理或执行Runtime。正式原片仍在录/终验待补/全片隐私发布pending；只对应一个绑定Lua文件，旧根因/完整备份/Runtime仍未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-owned-backup-receive-147/验收记录.md`及续接说明；下方145等待已过期。

- 最新单次Backup等待（2026-10-25 session145）：用户在新标题可见后“继续”，当前主Agent独立复用Otty703/原pane、新QuickTime3607静音FaceTime预览，新8秒短测8.02/8.01秒及实际六帧通过。正式480秒13:58:06.515/.516 UTC启动、13:58:08.594 ready；49Python＋145封装7场景＋两组Lua全PASS/无skip，意外联网0。137pins/六tracked/141确认/142结果及144/146状态一致；5GET全200，身份/公开两文件一致、report/output各64B精确PENDING，13:58:11.084499 backup_click_ready。尚无145CLICKED/运行后GET/备份成功；只单击新Loom Backup 1c4343一次并立即确认，提示北京时间22:02前，理论确认截止22:03:11.084499/14:03:11.084499 UTC，晚到不补收据/不再点。13:58:46主Agent独立复核双路gate/两PID/137pins、剩440.07秒。145现有唯一进程公开confirm_click必须先于35秒settle，之后仅1报告GET/COMPLETED才1输出GET；不沿122私有收据路径、不复用141确认。正式原片仍在录/终验待补/隐私发布pending；无自动点击、重启/重传/重置旧槽、远端source/binding/旧报告读取、清理/USB/配置/Runtime。仅一个绑定Lua源文件，旧根因/完整备份/Runtime未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-owned-backup-receive-145/验收记录.md`及续接说明；下方“145仅计划”为此前快照。

- 最新Works可见性反馈（2026-10-25，144/146录像后）：用户在“只确认`Loom Backup 1c4343`出现、暂不点击”后回复“有了”，记`user_confirmed_visible`。这是用户现场反馈，不是146原片新标题证据，不改写原片Works→Camera/Open/Done及当时未确认可见性的记录；未收到点击/运行确认。本次仅本地文档更新，设备/网络/相机/测试请求0，无新录像、收据、执行、上传或重启。145仍为后续另授权单次备份导出/完整接收计划；准备新双路和5GET精确PENDING基线后才提示点新Backup一次，不提前点、不复用141确认、不重启/重传/重置旧槽。绑定Lua源备份、旧根因和Runtime仍未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-owned-backup-reboot-146/录像后可见性确认.md`。下方“下一步确认标题”为此前阶段，现已由用户确认可见，非授权运行。

- 最新上传并单次重启（2026-10-25 session144/146）：用户明确“上传然后重启”，当前主Agent独立复用原Otty703/原pane，分别新QuickTime3560/3580 FaceTime静音预览、新8秒短测/实际六帧及正式ready。144沿143候选`Loom Backup 1c4343`/nonce1c4343412666，115pins核对后27请求（20GET/7POST），两新目录/五文件全部精确读回、launcher最后，backup_uploaded_not_run；本地私有144 binding未覆盖，源正文未读。144正式两原MOV179.99/179.99秒终验后，146单次POST /api/restart HTTP200接受、两次暂不可达后身份恢复，共9请求（8GET/1POST）；新launcher154B/export.lua20761B前后与144逐字节一致，121pins/六既有tracked/141真实收据/142结果不变，空缓存。无boot_id，保留物理重启因果边界；相机首Works、中末Camera/Open/Done，重启后新标题尚未检查。146正式150.00/150.00秒；两session均自然结束、无音轨/完整解码、主Agent独立重算各四MOV摘要并实际打开正式六帧，Otty本轮中末结果可读，不把旧49测试输出当本轮重跑。原片保留、全片隐私/发布pending；两预览已关闭、QT打开面板仍在、原Otty空闲，所有本次录像PID不存在。没有运行新旧作品/exporter/Runtime、读远端私有binding/report/output/旧报告、再次上传/清理/USB/刷机/配置或自启；源备份/旧根因/Runtime仍未验收。下一步用户仅Done回Works、Installed看全分页确认`Loom Backup 1c4343`可见，暂不点作品、不再重启/重传；145仍只是后续单次导出/完整接收计划，另授权/新双路/新真实确认，不复用141。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-owned-backup-deploy-144/验收记录.md`与`2026-10-25-ep04-owned-backup-reboot-146/验收记录.md`。下方143“未获设备授权/144只是计划”为当时状态，当前仅上传及单次重启授权已执行，不扩大为运行授权。

- 最新备份候选准备（2026-10-25 session143）：用户“机修下一步”按继续下一步，主Agent独立准备全新nonce1c4343412666/标题`Loom Backup 1c4343`，不复用/重置2f3e诊断槽或060785旧失败入口。原Otty703/QuickTime3538新短测及实际六帧后，正式ready内49项Python＋两组Lua内存mock全PASS/无skip，实际新候选入口7场景；两个联网前阻断自检通过、意外联网0/真实设备请求0。公开四产物、私有新0700/0600绑定和部署/接收manifest模板已准备，源指针沿130同一对象但不公开、源正文未读；export.lua20761B除nonce外与旧冻结脚本逐字节一致，未声称修复旧根因。109pins/6tracked/141收据/142真实结果与成片状态未变，空缓存。144/145只是计划，真实session/设备授权/点击收据均未创建，本地私有144候选binding不是已部署。143两原MOV150.00/149.99秒、差0.002秒，无音轨/完整解码/主Agent重算四MOV摘要及正式实际六帧完成；Otty中帧结果可读、末帧缺字/文字保真PARTIAL，相机Works4 ITEMS/旧Preflight/Stopped，无新执行。原片保留、隐私发布pending，预览关闭/打开面板仍在、原Otty空闲，本次录像PID已不存在。下一关另明确授权144只上传新Backup不执行，新双路/27请求/7POST精确读回、launcher最后；先确认Works全分页可见，缺标题再另授权一次重启，不自动重启/重传。之后145单次导出/完整下载另授权与新双路，不复用141确认；COMPLETED＋完整大小/SHA/fsync/私有读回通过才算备份，当前backup_verified=false/Runtime not_run。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-owned-backup-prepare-143/验收记录.md`及部署与验收说明。

- 最新诊断读回（2026-10-25 session141–142）：141用户“点了”的真实收据及480.03/480.06秒双路已终验，未要求重复点击。规范142独立脚本仅改会话路径、100pins/6tracked/141收据及基线成片状态一致，原Otty703/新QuickTime3512新短测及实际六帧通过；正式09:49:27 UTC起、09:49:29 ready内唯一1GET/15秒/512B，HTTP200，同nonce2f3e1201baa7报告120B严格completed/ready/prerequisites_ready，SHA78936a454a94454f50ff4b150d6642baba97bc4795cfb3b1ecf173304c8a9bbd，task_exit0。报告不再PENDING，只证明metadata前置条件；源仅stat、未完整备份/Runtime，旧060785根因仍未知，do_not_click_again=true。没有额外status/旧报告/source/output/binding/重试/自动Lua/上传/重启/清理/USB/配置。142两原MOV89.98/90.02秒、启动差0.001秒，无音轨/完整解码/主Agent重算四原MOV摘要与正式实际六帧完成；Otty中帧结果可读、末帧缺字/文字保真PARTIAL，相机Works4 ITEMS/新Preflight/Stopped，无独立触摸或Running转换证据。原片保留、隐私发布pending；预览正常关闭但打开面板仍在、原Otty空闲、两个本次录像PID已不存在。下一关仅准备并审阅受限完整源备份导出/接收方案，真实新部署/单次导出另获授权与新双路，完整备份验证后再验Runtime；不再点Preflight、不重置旧槽或重跑060785。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-backup-preflight-readback-142/验收记录.md`。下方141/136等待及142尚未创建均为历史快照。

- 141真实点击确认已收到（2026-10-25）：用户“点了”，主Agent首次主机检查09:37:53.424044 UTC，recording/两PID存活/基线及94pins通过，剩余233.758秒；真实CLICKED.json0600/150B/单链接、SHA95926d3197113032e7233d1c64b2e39c26842969dc55e66c3926b92764e3c28d，不回填触摸时刻。当前预览Works4 ITEMS/新Preflight Stopped，不证明成功/Job。不要再点，正式录制继续自然结束/终验待补、运行后GET0。静态接收准备发现旧计划retry-readback-142不符合transport正则，不改141冻结脚本或放宽工具；141媒体验收后另建规范`2026-10-25-ep04-backup-preflight-readback-142`，独立脚本只改PREP/SESSIONS并冻结审批、绑定141真实收据，新双路仅1GET/15秒/512B短报告。142尚未创建，备份/根因/Runtime未验收。见141验收记录更新；下方“尚无CLICKED/等待点击”已过时。

- 当前重试等待（2026-10-25 session141）：用户“现在重来”，136两正式原MOV300.02/300.01秒自然结束、无音轨/完整解码/主Agent重算四SHA及实际正式六帧完成，无CLICKED，不能断言设备未运行；旧预览已关闭/原Otty保留，不补旧收据。141新独立封装仅140的PREP/SESSIONS路径变更，静态AST其余一致/四公开文件字节一致，旧87/114pins及审批、新94pins匹配，未重跑历史测试。原Otty703/新FaceTime预览3487新短测8.01/8.05秒/实际六帧通过，Works4 ITEMS/新Preflight可辨。正式480秒09:33:47.182/.184 UTC起、09:33:49.333 ready，4GET全200，身份/公开两文件匹配、自身67B精确PENDING，09:33:51.211455 preflight_click_ready/task_exit0仅基线；journal顶层计数0未更新，以四events/result4为准、原件保留。尚无141CLICKED/142或运行后读取；当前门槛复核后只点新Preflight一次并立即确认，提示北京时间17:40前，理论共同片尾17:41:47/09:41:47 UTC，晚到不补写/不再点。正式原片仍在录/终验待补，不中断或关预览；141真实收据/媒体验收后142新双路仅1GET/15秒/512B短报告。无重置报告/源正文/output/旧报告/自动Lua/上传/重启/清理/USB/配置，备份/根因/Runtime未验收，隐私发布pending。见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-backup-preflight-retry-click-141/验收记录.md`及续接说明；下方136等待已过期。

- 当前单次Preflight等待（2026-10-25 session136）：主Agent独立，140候选87/主机114pins与审批复核PASS，原Otty703/新QuickTime FaceTime预览3455新短测并实际六帧通过。正式300秒02:26:55.073/.075 UTC启动、02:26:57.292 ready，4GET全200，身份/两公开文件一致、自身67B精确PENDING，preflight_click_ready/task_exit0只表示基线。journal顶层requests=0为未更新继承字段，实际四events/result.requests=4，原证据保留。尚无CLICKED/137/运行后读回；当前双路门槛复核后才请单击Loom Preflight 2f3e12一次并立即确认，理论共同截止02:31:55.073 UTC/北京时间10:31:55，晚到不补收据/不再点。两原片仍在录、终验待补，不打断或关预览。136真实收据及媒体验收后137另建新双路仅1GET/15秒/512B读自身短报告；无自动Lua执行/源正文/output/旧报告/上传/重启/清理/USB/配置，备份/根因/Runtime未验收、隐私发布pending。见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-backup-preflight-click-136/验收记录.md`及续接说明；下方140下一关为此前阶段。

- 最新主机修正与验收（2026-10-25 session138–140）：主Agent独立，138封装26项中两项录像收据反例失败、旧回归两组import错误；139因本卷大小写不敏感导致REVIEWED.json/reviewed.json同名覆盖，在本地冻结检查停止/测试0。失败代码、日志及原片全部保留，135原件不改。140新副本修正录像成功终态/严格退出码/两轨实测片长、解码、无音轨与共同时间窗，主机清单改名HOST-REVIEWED.json并确认不同inode；原Otty703/QuickTime3410新短测及实际六帧后，正式ready内29封装＋37回归全PASS/无skip、Lua内存45场景PASS，真实网络阻断/设备0请求。114主机pins/87候选pins/6tracked前后匹配，真实136/137及授权/点击收据未创建。138/139/140正式两原MOV分别120.00/120.03、120.03/119.99、120.02/119.98秒，均无音轨/完整解码/主Agent重算各四原片SHA并实际打开正式六帧；Otty中帧结果可读、末帧缺字/文字保真PARTIAL，相机Works4 ITEMS/新Preflight可辨，无本轮执行证据。原片保留、隐私/发布pending，预览已正常关闭/打开面板仍在，原Otty空闲，无后台录像。下一关另获单次真机诊断授权，136/137须重新指向140候选及SHA，不用135旧setup；136新双路4GET精确PENDING后才请单击新Preflight并在录像里确认，136自然结束/媒体验收后137新双路只1GET/15秒/512B读同nonce短报告。不要提前点击、重启/重传/再清理或读源/output/旧报告；完整备份/根因/Runtime仍未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-preflight-wrapper-final-host-140/验收记录.md`；下方135静态准备及136/137计划为此前阶段，不授予设备权限。

- 最新静态准备（2026-10-25 session135）：用户仅“继续准备”，主Agent独立准备新Preflight 2f3e12的baseline/readback薄封装、三份公开artifact、readback manifest/审批模板与两份不可直接运行的setup模板。83旧输入＋4新文件共87pins一致，语法静态解析/源码审阅完成；未运行runner/verify_local/测试，设备/相机/网络0，无新录像。目录0700/文件0600，RUN.AUTHORIZED/CLICKED/CLICK.APPROVED均未创建，136/137仅计划未启动。下一关先在原Otty新双路禁网定向验收薄封装，再另获单次执行授权，136新基线4GET/精确PENDING后才请只点一次；真实确认必须在该录像窗口内。137独立新双路只1GET/15秒/512B读同nonce短报告，不套旧60秒二次时效，不读源/output/旧报告/私有binding，不自动运行/重启/重传/删除。准备不等于主机或真机验收，完整源备份/根因/Runtime仍未知。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-25-ep04-preflight-execution-prepare-135/操作说明.md`。

- 2026-10-25 用户确认（session134后续）：主Agent请用户Done返回Works确认新`Loom Preflight 2f3e12`出现及六旧条目消失，用户回复“确认了”，记为`user_confirmed_visible_and_old_entries_absent`。这是用户现场反馈，不是134原片的新画面，不改写原片Camera/Open/Done或当时未确认的结论。仅更新本地文档，设备/相机/测试/作品执行请求0，无新录像，不重启/重传/再删，也不将确认可见当作点击授权。下一关准备新双路及同nonce单次诊断/受限短报告接收，另获执行授权后才请只点新Preflight一次；完整源备份/根因/Runtime仍未验收。

- 最新单次重启（2026-10-24 session134）：用户在“需确认重启刷新Works”后回复“继续”，主Agent直接复用原Otty、新QuickTime FaceTime预览窗3369与新短测/实际六帧；正式150秒ready内6元数据fixture/精确路由自检PASS，21请求（20GET/唯一1POST /api/restart），19次200、两次暂不可达后身份恢复，task exit0。新Preflight两文件前后与130冻结字节一致，六旧目录前后均无launcher且辅助项元数据不变；无boot_id，不单凭200证明物理重启。83pins/6tracked/122旧收据journal/133六私有恢复入口一致；未运行/重传/再删/读旧Lua报告或源/output/USB/刷机/配置。两正式原MOV150.01/150.00秒、差0.001秒，无音轨/完整解码/主Agent重算四原片SHA/实际正式六帧通过；相机首Works、中末Camera/Open/Done（末段变暗仍可辨），重启后Works/新标题尚未验证。原片保留、全片隐私/发布pending；QT预览关闭/打开面板在，原Otty空闲，无后台录像。下一关用户点Done回Works，Installed看全分页，只确认`Loom Preflight 2f3e12`与六旧条目消失，暂不点作品，不再重启/重传/清理；新诊断执行另获授权与新双路。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-preflight-refresh-reboot-134/验收记录.md`；下方133“待授权重启”为此前阶段，完整备份/根因/Runtime仍未验收。

- 最新部署与旧Works入口清理（2026-10-24 session129–133）：当前主Agent独立完成；129日志目录权限保护/设备0请求，130新nonce`2f3e1201baa7`、`Loom Preflight 2f3e12`两目录六文件30请求/8POST全部精确读回、launcher最后，另1GET旧目录清单，未运行。131辅助文件保护4GET/0DELETE，132旧Check脚本size_mismatch保护9GET/0DELETE，不推断具体类型/值或改动根因；失败原片/冻结版本保留。133收窄只删六个旧launcher：新双路ready内15项禁网测试PASS，43请求（37GET/6DELETE）全200，先私有0700/0600/fsync/逐字节恢复备份再删除，旧Lua/报告/目录与出厂/新Preflight保留；83pins/45旧输入/6tracked及122旧收据/journal一致。未运行/重启/读旧报告或源/output/刷机/配置。133两原MOV120.00秒、差0.001秒，无音轨/完整解码/重算四原片SHA/正式实际六帧通过，Otty结果可读，相机仍Works9 ITEMS/3/3/旧Check Stopped，磁盘移除不等于界面刷新。原片保留、隐私/发布pending；QT预览关闭/打开面板在，原Otty空闲。下一关另经用户确认单次正常重启刷新Works，不再清理/重传，不点击作品；完整备份/根因/Runtime未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-old-works-cleanup-133/验收记录.md`；下方128“未部署”为此前阶段。

- 最新离线传输验收（2026-10-24 session128）：当前主Agent独立新增preflight受限传输/接收器、15项Python多矩阵测试及合同3文件，旧42输入不变；原Otty新双路ready内5组Lua＋147Python全PASS/无skip，真实网络阻断、设备请求0，45冻结输入/6tracked/122收据与失败journal一致。部署合同新两目录/六文件、30请求/8POST、launcher最后，readback独立1GET/15秒/512B，仅新nonce短报告，无执行/源正文/output/旧报告或重启路由；本轮仅mock、未部署。两原MOV119.99/120.03秒、差0.001秒，无音轨/完整解码/主Agent重算四原片SHA及正式六帧完成；Otty中帧147项OK/PASS可读，末帧字形缺损/文字保真PARTIAL，相机Works9 ITEMS/3/3/旧Check Stopped，不证明新诊断执行。原片保留、全片隐私/发布pending；QT预览关闭但打开面板在、原Otty空闲。下一关另获明确部署授权，准备新nonce独立session/私有binding/指纹审阅及新双路，只上传不自动执行；Works可见与单次执行/短报告读回分离，不再点060785/旧Slot/Diag/Check、不重置PENDING/盲重读旧报告/重传/自动重启。非原子CAS/bootstrap边界保留，现场根因/完整备份/Runtime仍未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-backup-preflight-transport-host-128/验收记录.md`；下方127“传输未实现”为此前阶段。

- 最新离线启动前诊断（2026-10-24 session127）：当前主Agent独立核对build04 storage/json/system/IO与Works链，未找到明确本地API冲突，现场根因仍未知。新增独立metadata-only preflight Lua/renderer/classifier及测试/合同5文件；自身新role报告先STARTED后固定stage/code，源只stat、backup槽只读、仅写自身诊断报告，不调用exporter/Runtime。原Otty新双路ready内5组Lua（新45场景）＋132Python全部PASS/无skip，真实网络连接阻断、设备请求0，37旧输入/6tracked/122收据与失败journal不变，42项冻结。未部署/新传输尚未实现，不重读旧报告或再点060785/旧Slot/Diag/Check，不重置PENDING/上传/重启/USB/配置。两原MOV119.98/120.01秒、差0.001秒，无音轨/完整解码/重算SHA/实际六帧完成；Otty中帧结果可读、末帧字形缺损/文字保真PARTIAL，相机Works9 ITEMS/3/3/旧Check Stopped，无新执行证据。原片保留、隐私/发布pending，QT预览关闭但打开面板在、原Otty空闲，无后台录制。下一关仅准备新诊断受限传输/接收器的离线验收，新增nonce部署/单次执行另经明确授权与新双路；非原子CAS与bootstrap无法写报告边界保留，完整备份/Runtime仍未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-backup-preflight-host-127/验收记录.md`；下方126“下一关离线诊断”为此前阶段。

- 最新只读恢复（2026-10-24 session124–126）：当前主Agent独立新增恢复器并在124原Otty新双路内完成4组Lua＋125Python全PASS/无skip，37输入与6tracked不变；124主审放行等待超时/设备0请求保留。125因artifacts父目录0755触发本地directory_unavailable/设备0请求保留，不在失败实例续跑。126逐层0700、禁网verify_local PASS后，新短测/实际六帧及正式ready内4GET/0POST均200；身份与公开launcher/script逐字节一致，同nonce06078511e788报告64B严格PENDING，终态recovery_not_completed/backup_verified=false/do_not_click_again=true，task exit0仅只读流程完成。未读output/源正文，新私有0B占位非备份；不再次点击/prepare重建PENDING/重传/重启/USB/配置/Runtime，不改122真实收据。124两原MOV240.02/240.00秒、125为120.03/119.99秒、126为119.99/120.00秒，均无音轨/完整解码/主Agent重算SHA与实际正式六帧完成；125末帧及126短测部分字形缺损，文字保真PARTIAL，不称全程可读。126正式中末pending结果可读，相机Works9 ITEMS/3/3/旧Check Stopped，不推断点错。原片保留、隐私/发布pending，QT预览已关闭、打开面板仍在、原Otty空闲，无后台录制。下一关仅离线排查STARTED前入口/前置检查与有界错误回传；PENDING不能证明未执行或根因，不盲重读/重跑同nonce，新增入口/执行另获授权。完整备份/Runtime仍未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-recover-126/验收记录.md`；下方旧“准备GET-only恢复”为完成前阶段。

- session123主机时序修复（2026-10-24）：当前主Agent直接修复接收器，新增confirm_click单次接受阶段；首次真实收据仍≤60秒，接受后另以60秒单调预算覆盖35秒settle及完整接收，持续核对不可变收据/gate/pins，不靠改旧时间或移除保护。原Otty新短测/实际六帧通过，正式ready内4组Lua＋109项Python全PASS、无skip，含40.020秒交接＋35秒settle集成；34冻结输入中3项授权更新，其余31项及6项既有tracked改动不变、pycache空。真实设备请求/作品运行/源正文/备份读取/上传/重启/USB/配置/Runtime均0，122真实收据/task/失败原片不变；设备既有结果仍未知，不再要求用户点击。正式原MOV179.99/180.01秒自然结束、启动差0.002秒，主Agent重算SHA/无音轨/完整解码技术PASS、实际六帧复核完成；Otty中帧可读、末帧字形明显缺损，文字保真PARTIAL，不称全程可读；相机三帧Works9 ITEMS/3/3/旧Check Stopped可辨，无新Backup执行独立证据。原片保留，隐私/发布pending；预览已关闭、打开面板仍在、原Otty空闲，无后台录制。下一关独立审阅GET-only恢复本nonce已有结果，不重建prepare/PENDING、不重跑/改收据/重传/重启。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-receive-host-123/验收记录.md`；下方旧“先修时序”为完成前阶段。

- session122正式收尾（2026-10-24，覆盖下行“仍在录”）：任务仍click_receipt_stale/task-failed，仅5GET/0POST、无执行后报告/输出读取。用户点击已确认，不再要求点击。两原MOV480.01/480.03秒自然结束、启动差0.001秒，无音轨/完整解码/主Agent重算SHA及实际正式六帧PASS；Otty中帧确认接受可读、末帧部分字缺损，相机三帧Works9 ITEMS/3/3/旧Check Stopped，无新Backup点击/运行独立证据、有人员局部入镜。原片/失败journal/真实0600收据/私有0B占位保留，发布/全片隐私pending；34输入未变、pycache空，生产代码/真实设备未再操作。QuickTime预览关闭、打开面板仍在、未确认进程退出，原Otty空闲、无后台录制。下一关独立修复并集成验收“40秒确认交接＋35秒等待/二次60秒过期”时序，再审阅新GET-only会话只恢复本nonce已有结果；不重跑/重置/改旧收据/重传/重启。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-receive-122/点击后诊断.md`和验收/素材复核，完整备份/Runtime仍未验收。

- 最新点击后停止（2026-10-24 session122）：用户窗口内“点了”，主Agent17:02:22.707核对当前gate/截止/双路PID，真实时间收据0600不覆盖发布，17:03:02.727742被接受；35秒无网络等待后，receive_once二次60秒时效检查触发click_receipt_stale，17:03:37.862 exit1。约40.020秒确认交接＋35秒等待导致主机时序失败，不是设备运行失败证据。仍仅5GET/0POST，无执行后报告/output读取或完整下载，backup_verified=false，34输入未变/pycache空；点击后单次预览仍Works9 ITEMS/3/3/旧Check Stopped，无新Backup执行画面，不推断点错。不能再次点/重调receive/重置槽/改receipt时间/重传/重启。下一关先独立修复并集成验收时序，再审阅新GET-only会话只读本次已有结果，不重新运行。正式480秒双路仍待自然结束/终验，原片/失败journal/真实收据/私有占位保留，发布pending，完整备份/Runtime未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-receive-122/点击后诊断.md`；下方122“等待确认”为之前阶段。

- 当前Backup等待（2026-10-24 session122，覆盖下方121等待快照）：121确认窗口超时，task exit1、5GET/0POST、无CLICKED/receive；已补两原MOV300.00/299.99秒无音轨/完整解码/重算SHA/实际正式六帧，34输入未变，失败原片保留，不能据无确认证明设备未执行。用户再次“再来一次”，主Agent独立122仅把确认窗口延长至300秒、正式录制480秒，起始剩余门槛470/435秒，生产保护未变。新短测7.98/8.03秒无音轨/解码/六帧PASS，原Otty/QuickTime预览新双路16:59:33.295/.296启动、16:59:35.334 ready；4情形等待自检PASS，5GET精确PENDING基线PASS。确认截止北京时间17:04:36.180588，17:00:05双路PID活着、click_confirmed=false、CLICKED不存在。仅真实本轮确认后按122续接写0600不覆盖收据、35秒等待及一次报告/可选输出，总≤7GET/0POST；不补旧收据、不第二次点/重置槽/重传/重启。正式原片在录/终验待补，原片保留、全片隐私/发布pending，完整备份/Runtime未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-receive-122/续接操作说明.md`及验收；QT预览/原Otty为本122保留。

- 当前单次Backup等待（2026-10-24，session121）：用户“再来一次”，主Agent直接新独立准备并复用原Otty/QuickTime FaceTime预览，8.03/7.99秒短测无音轨/完整解码/实际六帧PASS。正式300秒16:44:35.093/.094启动、16:44:37.177 ready后4情形等待自检PASS，34旧输入冻结；仅5GET/0POST均200，身份/两公开入口一致、report/output精确PENDING。16:44:37.573825进入backup_click_ready、确认截止北京时间16:47:37.573825；16:45:03复核双路PID活着、click_confirmed=false、CLICKED不存在。尚无点击/完整备份，只有真实“点了”才按121续接核对当前gate、0600不覆盖收据、35秒等待及一次报告/可选输出，总≤7GET。状态改变/超时即停，不第二次点、不补120收据、不重传/重启。正式原片仍在录/终验待补，原片保留、发布pending；QT预览/原Otty暂保留。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-receive-121/续接操作说明.md`及验收记录；下方121“准备”为放行前阶段。

- 最新续接（2026-10-24，session120终验/121准备）：120在16:12:40确认窗口超时、task exit1，只有5GET基线，未收到CLICKED或执行receive，不据此证明设备未点击；两正式原MOV300.01/300.00秒无音轨、完整解码/主Agent重算SHA与实际正式六帧复核通过，34输入未变、pycache空，原片/失败journal保留，发布pending。用户随后“再来一次”，主Agent直接准备独立121，复用原Otty/QuickTime FaceTime预览、无新窗口或委托。121必须新短测六帧/正式ready及5GET精确PENDING后才安排一次点击；状态改变立即停止，不重置槽/重传/重启，不补120收据。完整备份/Runtime仍未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-receive-121/续接操作说明.md`及120终验；下方120“仍在录/等待点击”为超时前快照。

- 当前单次Backup等待（2026-10-24，session119–120）：用户“运行”授权一次新`Loom Backup 060785`及受限接收。119因主Agent提前创建日志目录与录制器独占mkdir冲突，在录制前失败、设备0请求，保留不复用；120改正准备顺序、原Otty新双路短测8.02/8.01秒无音轨/完整解码/六帧PASS。正式300秒北京时间16:09:38开启、16:09:40 ready后4情形本地等待自检PASS，34旧输入未变；仅5GET/0POST均200，身份/两个公开入口一致、report/output精确PENDING。16:09:40.960889进入backup_click_ready，确认截止16:12:40.960889，click_confirmed=false；主Agent核对双路PID/当前journal/截止与无收据后才请用户只点新Backup一次。尚未确认点击/运行/完整备份；不预造CLICKED、不再重启/重传或点旧入口。收到真实“点了”必须先查本session续接说明与live gate，0600暂存后不覆盖发布收据，35秒无网络等待后仅一次报告/可选一次完整输出接收，总≤7GET。超时停止，不补造/重演。正式录像尚在录、终验待补，原片保留/发布pending；QT预览和原Otty此刻保留运行。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-receive-120/续接操作说明.md`与验收记录；下方118“等待执行授权”为授权前历史。

- 最新接收链离线验收（2026-10-24 session118：当前主Agent独立新增Backup报告/完整下载接收器、23项测试与合同，原Otty新双路ready内4组Lua＋97项Python全部PASS、无skip，31旧＋3新共34项冻结输入未变；真实设备/源正文/报告/输出/上传/点击/重启/Runtime请求0。严格同nonce规范报告、≤7GET、≤128KiB下载及大小/SHA/fsync/本地完整读回/私有权限保护仅通过host/mock，不代表真实备份。正式原MOV180.02/180.00秒、启动差0.001秒，无音轨/完整解码/主Agent重算SHA与正式六帧PASS；Otty结果可读，相机Works9 ITEMS/3/3/旧Check Stopped可辨，有局部人员，未见新Backup标题/点击。原片保留，全片隐私/发布pending；QT预览关闭、打开面板仍在，原Otty空闲保留。下一关独立准备真实接收task/manifest与单次执行授权，新双路ready及5GET精确PENDING基线后才请只点`Loom Backup 060785`一次；不要提前点击、重传/重启或复用旧Slot/Diag/Check。完整备份/Runtime仍未验收。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-receive-host-118/验收记录.md`与`tools/mosaico-owned-backup-receive.md`；下方117“尚无接收器”为历史阶段。）

- 最新可见性反馈：2026-10-24，session117录像后，用户回复“出现了”，确认Works中的`Loom Backup 060785`（nonce `06078511e788`）可见，记为`user_confirmed_visible`。这是用户现场反馈，不是117原片的新标题证据，不改写原片中Camera/Open/Done或当时可见性未验证的结论；未收到点击/执行确认，完整备份和Runtime仍未验收。本次仅本地文档与既有传输工具静态核对，设备/网络/相机/测试/执行请求0，无新录像，不再重启/重传。现有`mosaico_owned_backup.py`仅支持渲染/上传，尚无配套的完整报告严格分类与有界下载/hash接收；下一关先离线准备并验证这条接收链，另建新双路执行session，ready且单次执行获授权后才请用户只点新Backup一次。不要点旧Slot/Diag/Check或提前点Backup。详见117[录像后确认](copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-reboot-117/验收记录.md)。下方117“等待返回Works”为反馈前状态。

- 最新一次正常重启（2026-10-24 session117：用户确认Works两页均无Backup并授权一次正常重启；主Agent直接在原Otty新双路ready内9请求（8GET/唯一1POST /api/restart），HTTP200接受、两次暂不可达后身份恢复。Backup launcher154B/export.lua20761B前后与116冻结文件逐字节一致，task exit0。无boot_id，不单凭200证明物理重启；相机首帧Works8 ITEMS/2/2，中末帧Camera/Open/Done，重启后新标题仍未验证。无私有binding/原始源正文/output/report/旧报告读取，无新旧作品/exporter/validator/Runtime执行、上传/刷机/USB/清理/配置/自启。正式原MOV149.99/150.01秒、启动差0.001秒，无音轨/完整解码/主Agent重算SHA与正式六帧通过；Otty末帧部分字缺损，原片保留、全片隐私/发布pending。QT预览已关闭、打开面板仍在，原Otty空闲保留。下一关只点设备Done回Works看全分页，确认`Loom Backup 060785`可见、暂不点作品，不再重启/重传；单次执行与完整下载hash另准备，完整备份/Runtime仍未完成。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-reboot-117/验收记录.md`；下方115–116下一步为重启前历史阶段。）

- 最新备份入口部署（2026-10-24，session115–116）：当前主Agent直接完成，未创建/续接子代理。115截断fixture冲突而失败、设备0请求，失败原片/日志保留；修正fixture不放宽生产保护，116在原Otty新双路ready内4组Lua＋74项Python全PASS、无skip，31项冻结输入（25旧＋6本轮）未变，嵌入exporter与114逐字节一致。新nonce `06078511e788`、标题`Loom Backup 060785`，27请求（20GET/7POST），两新目录/五文件逐字节读回、launcher最后、journal七项verified，exit0/backup_uploaded_not_run。仅安全读取旧本地私有binding生成新binding，未读设备源正文/旧报告，未运行新旧作品/exporter/validator/Runtime、重启/刷机/USB/清理/配置/自启。116两原MOV180.02/179.99秒、115两原MOV360.00/360.03秒，均无音轨/完整解码/重算SHA/正式六帧复核通过，原片保留、不改写115任务失败。116 Otty末帧部分字符缺损，相机三帧Works8 ITEMS/2/2/V2可辨，无新Backup可见证据。全片隐私/发布pending；QT预览关闭、打开面板仍在，原Otty空闲。下一关只检查Works全部分页确认新标题、暂不点击；若仍缺标题另获授权一次正常重启，不重复上传/点旧入口。单次执行和同nonce完整下载/hash核验另准备；完整备份/Runtime未完成。详见`EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-deploy-116/验收记录.md`与115失败记录；下方“未部署”为历史阶段。

- session114终验补充（2026-10-24，覆盖下行的“素材待补”阶段状态）：4组Lua＋60项Python全部PASS、旧25项输入未变，新独立归属槽导出器只经host/mock验收、未部署。正式Otty179.98秒/相机180.00秒、启动差0.001秒，两原MOV无音轨、完整解码及主Agent重算SHA一致。正式六帧已实际打开：Otty中帧60项OK/最终PASS可读、末帧部分字符缺损，相机三帧Works/8 ITEMS/2/2/V2可辨，不声称全程清晰/全片隐私合格。两原片保留、发布pending；已关闭QuickTime录影预览，打开面板仍在，原Otty空闲保留。用户要求本项目不用子代理，活动任务已中断，后续主Agent直接修正/审阅/冻结/测试，无续接或新派发；历史Luna产物不当完成证据。设备/网络/USB/真实源读取/上传/点击/重启/Runtime0，完整备份与Runtime仍未验收。下一关由主Agent直接准备新nonce入口及受限预分配/传输的离线验收，不重跑旧Slot/Diag/Check、不放宽unknown保护。详见[114完整验收](copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-host-114/验收记录.md)。

- 最新主机修复（2026-10-24，session114，正式素材终验待补）：新增独立归属槽exporter、mock测试和合同文档，先正面验证两个固定槽普通文件/大小/nonce/role/PENDING，不依赖stat缺失错误码；unknown继续拒绝、源只读、输出固定，STARTED后失败不清理/重试。旧exporter/loader/helper/pins及25项旧输入不变。原Otty新双路ready内4组Lua＋60项Python全PASS、无skip，task exit0；真实设备/网络/USB/源正文/上传/点击/重启/Runtime0。准备早期有Luna静态输入；用户追加本项目禁用子代理后已中断活动任务，后续修正/审阅/冻结/测试由主Agent直接完成，不再派发，历史委托不作为继续授权。仅主机修复，未部署；SHA来自源块，目标仅大小验证，非原子CAS，不能保证并发/别名/同尺寸修改/reload重试安全。下一关由主Agent准备新nonce入口与受限预分配/传输并离线验收，不重复旧Slot/Diag/Check，不读取旧报告或放宽unknown保护。双路180秒原片待自然结束/终验，发布pending。详见[114验收记录](copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-backup-host-114/验收记录.md)。

- 最新单次回读与终验（2026-10-24，session113）：用户回复“点了”；主Agent在北京时间10:26:23.551截止前核对click-ready与双路进程，10:25:46.988创建CLICKED，等待3秒后仅调用一次schema2 read_result。共5GET（4基线均200/verified＋1回读889B）、0POST，task exit0；classification=completed但报告partial。missing_probe实际仅nil/string两项返回，第三项未返回、detail_code other/state unknown；source为已知90189B普通文件，两residual存在性/大小未知。该项两值与本地build04三值不同，不推广到其他路径/旧执行或推断固件、ENOENT、残留不存在、完整根因。10:26单帧Works/8 ITEMS/2/2、V2 Stopped；无独立Running过渡/点击事件。两原MOV300.00/300.03秒、启动差0.001秒，无音轨、完整解码、主Agent重算SHA通过；实际打开正式六帧，Otty中帧结果可读、末帧部分字符缺损，相机三帧Works/V2可辨，有局部人员入镜，不称全程文本清晰或隐私已审。原片保留、全片隐私审查/发布pending；QT预览已关闭、打开面板仍在，原Otty空闲保留。无源正文/私有binding/旧4323d2报告读取，无exporter/validator/Runtime主动执行、上传、重启、刷机/USB。下一关离线设计两值错误接口的安全兼容和可观测性，不把unknown当缺失、不放宽覆盖保护；不重复点V2/旧Slot/Diag/Check。根因/完整备份/Runtime仍未完成。详见[session113验收记录](copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-owned-probe-v2-readback-113/验收记录.md)。

- 最新录像后反馈与可复用经验（2026-10-24，session112之后）：用户回复“有了，这个问题好几次了，你需要记住要重启”，确认 Works 中 `Loom Slot V2 c37907`（nonce `c3790771bee8`）可见，记为 `user_confirmed_visible`。这是录像结束后的现场反馈，不是112原片拍到的内容，也不证明点击作品、诊断执行或 Runtime 成功；session112验收中的“可见性未验证”保留为反馈到来前的状态。此次观察到，Mosaico HTTP 新作品文件上传及精确读回不保证 Works 注册表热刷新；若读回精确一致且检查 Works 全部分页仍缺标题，可优先安排一次经用户授权的正常重启刷新，不反复重传或重跑旧入口。重启不是所有上传的强制要求，也不保证未来固件都需要；无授权不得重启。live仍须复用原Otty并满足新双路ready；重启后Done返回Works只确认标题、不点作品；运行另行授权。详见112[录像后确认](copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-v2-slot-reboot-112/验收记录.md)。

- 最新重启检查（2026-10-24，session111–112）：用户明确“重启试试”；111只短测后审阅等待超时、设备0请求，失败原片/日志保留。112由Luna受限静态准备、主Agent实际代码/指纹审阅冻结，原Otty新双路ready内9请求（8GET/唯一1POST /api/restart），HTTP200/ok=true、两次暂不可达后身份恢复；V2 launcher/script重启前后与110冻结文件逐字节一致，task exit0。接口无boot_id，不单凭HTTP200证明物理重启。相机首帧Works7 ITEMS/2/2，中末帧及结束单帧Left port/Camera/Photo/Video/Open/Done；重启后V2可见性未验证，下一关用户Done回Works看全部分页，仅确认Loom Slot V2 c37907、不点击作品；不再次重启/重传。无诊断/旧Check/exporter/validator/Runtime主动执行，无私有binding/源正文/result槽/旧4323d2报告读取，无上传/publish/刷机/USB/清理/设置/自启变更。112两原MOV150.02/150.00秒、启动差0.001秒，无音轨、完整解码/原片SHA/正式六帧复核PASS，原片保留，隐私审查/发布pending；QT录影预览已关闭、打开面板仍在，原Otty空闲保留。根因/完整备份/Runtime仍未验证。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-24-ep04-v2-slot-reboot-112/验收记录.md`；下方旧下一步保留历史。

- 最新部署（2026-10-23，session110）：按Luna审阅与本session闸门任务，主Agent实际逐行审阅/核对指纹后，在原Otty新双路ready内完成全新schema2诊断上传。nonce `c3790771bee8`、显示名`Loom Slot V2 c37907`；24请求（18GET/6POST），两个新目录/四文件逐字节回读，launcher最后，journal六项verified、终态slot_uploaded_not_run。独占空pycache_prefix＋禁写字节码避免旧.pyc脱离源码SHA，未改生产工具。只安全读取本地已审阅binding转schema2，不读设备源正文；没有诊断/旧新作品点击、旧4323d2报告、exporter/validator/Runtime、重启/刷机/USB/清理/设置/自启/网络扫描。109主机测试未重跑，不冒充本轮测试。两原MOV359.99/360.08秒，启动差0.001秒，无音轨、完整解码/原片SHA复核PASS；主Agent实际打开正式六帧，Otty结果可读，相机环境暗但三帧主页亮屏可辨，小字泛光，无Works标题证据。原片保留，全片隐私审查/发布pending；QuickTime录影预览已关闭、打开面板仍在，原Otty空闲保留。下一关先请用户进入Works看全部分页，仅确认`Loom Slot V2 c37907`可见、暂不点击；若无则按缓存边界另行准备，不自动重传或重启。单次执行/同nonce独立读回须新双路门槛与授权，不复用旧c38050/Diag/Check。现场stat契约、根因、完整源备份和Runtime仍未验证。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-23-ep04-owned-probe-v2-deploy-110/验收记录.md`；下方“尚未部署/下一步上传”为历史阶段。

- 最新离线验收（2026-10-23，session108–109）：按Luna委托并经主Agent实际审阅，新增独立schema2传输器与测试，deploy仅全新nonce目录/四文件、launcher最后、≤24请求/90秒；readback独立≤1 GET/15秒、完整≤8192字节并用真实v2分类器。每请求同session/窗口/双路门槛、SHA pins、私有binding0700/0600/symlink保护、失败准确计数/独占journal，不调用v1 owned deploy或改helper全局。108父审阅超时未测试，失败原片/日志保留；109在原Otty新双路ready内冻结后，3组Lua及60项Python（原43+新17，多失败矩阵）全部PASS、无skip，19旧文件摘要不变。109两原MOV600.01秒、启动差0.001秒，无音轨、完整解码/正式六帧/原片SHA复核PASS；108两路600.00/600.01秒技术复核也PASS，不改写任务失败。原片保留，发布pending；QuickTime录影预览已关闭、打开面板仍在，未确认进程退出，原Otty空闲保留。设备/真实网络/USB/私有源读取/上传/点击/重启/Runtime均0，新诊断尚未部署，现场根因/完整备份/Runtime未验证。下一关准备并审阅全新nonce的v2部署会话/渲染指纹/受限私有binding，新双路仅上传、不自动执行或重启；Works可见/单次执行/同nonce读回分离，不用host109门槛，不复用旧c38050/Diag/Check或请求旧4323d2。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-23-ep04-stat-v2-tools-final-109/验收记录.md` 与 `tools/mosaico-owned-probe-v2.md`；下方旧下一步保留历史。

- 最新离线验收（2026-10-23，session105–107）：Luna实现、主Agent实际审阅冻结七个独立schema2文件，新增stat返回项数/前三项类型/第三项结构与白名单code摘要，保留unknown/ENOENT和归属门槛；v1七文件摘要不变。105/106父审阅超时未测试，失败原片/日志保留；105两测试mtime晚于其录像结束约9秒，不补称全程在录。107在原Otty新双路ready后，三组Lua及43项Python（含16种stat形态/10种归属失败）全部PASS、无skip，设备/网络/上传/点击/重启/Runtime均0。两原MOV300.10/299.99秒、启动差0.001秒，无音轨、完整解码/六帧/原片SHA复核PASS，原片保留，发布pending；QuickTime录影预览已关闭但空白打开面板仍在，未确认进程退出，原Otty空闲保留。新诊断尚未部署、现场根因/完整备份/Runtime仍未验证。下一关先准备v2新nonce受限上传/接收工具并离线验收，不复用v1部署器或旧c38050/Diag/Check，不请求旧4323d2、不自动重启。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-23-ep04-stat-contract-final-107/验收记录.md`；以下旧下一步保留历史。

- 最新离线诊断（2026-10-23，session104）：Luna定向分析、主Agent复核本地build04实际storage绑定/manifest与Lua链；本地stat失败明确返回nil/message/detail三项，exists只报stat成功布尔值，未发现目标绑定本地改动。现场103的第二项string/other既兼容旧两值，也兼容第三项未知/非白名单code，不能据此确认现场契约、ENOENT或根因；unknown/partial是保守判定。exporter遇目标缺失不可确认会destination_check_failed，旧loader又丢弃具体错误码，是候选失败路径而非现场已证实根因。本轮仅本地静态/文档，设备/网络/相机/项目测试0，无新录像，未改代码/旧档案或重跑/上传/重启。下一关离线补有界返回项数/第三项类型/规范化code，同步schema、净化、严格分类和SHA pins后在原Otty新双路验收；不放宽ENOENT/归属保护，不重复点c38050/旧Diag/Check、不请求旧4323d2。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-23-ep04-stat-contract-diagnosis-104/操作说明与诊断.md`；现场根因/完整源备份/Runtime仍未验证。

- 最新终验（2026-10-23，session103）：用户反馈00:29单击新Slot，Running→Stopped；已存同noncejournal显示32个GET均200，4基线PASS＋28轮询，第28次约00:29:13从pending读到completed，task_exit0，报告partial。source为regular_file/90,189B；missing_probe第二返回类型string、detail_code other/state unknown，两个residual的exists_known/size_known均false，不推断缺失、零字节或根因；source元数据不等于已导出/备份。未采到STARTED或独立点击事件，不精准绑定job。主Agent复核冻结摘要与原片SHA、既有完整解码/无音轨日志，实际打开正式六帧：Otty结果可读，相机首/中可辨Works/Slot，末帧暗无可读屏幕，不推断睡眠/关机，也不冒充全程可读。两MOV300.00/300.02秒、启动差0.001秒，原片保留、全片隐私审查/发布pending。当前本轮设备新请求0、未重跑/上传/重启；已关闭残留QuickTime预览，原Otty空闲保留，未操作更新提示。详见session103验收记录第7节。下一关先离线核对storage.stat错误返回兼容，不重复点Slot/旧Diag/Check，不请求旧4323d2；根因/Runtime仍未验证。下方“执行中”为完成前历史快照。

- 执行中（2026-10-23，session103）：用户要求继续后，用Luna静态准备GET-only接收器、主Agent实际审阅并冻结；原Otty＋新QuickTime预览窗8秒短测两路无音轨/完整解码/六帧复核通过，正式300秒两路于00:26:51启动，00:26:53 both_ready。内存自测PASS、4基线GET200，身份/Slot两文件摘要/canonical PENDING匹配，已发SLOT_CLICK_READY并请用户只点Loom Slot c38050一次；目前尚无点击或结果确认，Runtime未验证。接收最晚约00:30:38截止，截止后不要补点；录像约00:31:51自然结束，正式媒体/六帧终验仍待完成，预览暂保留供录制。不要重启/重传或点旧Diag/Check/请求旧4323d2。详见session103执行中状态；后续先检查该session日志和录制状态，不能重复触发。

- 最新反馈（2026-10-23，session102录像后）：用户回复“出现了”，确认上一轮目标 `Loom Slot c38050` 在Works可见，记 `user_confirmed_visible`；这是用户现场反馈，非102原片拍到标题，不改写原录像/六帧结论，不代表已点击、诊断执行或Runtime通过。本轮仅文档同步，设备/相机/测试/执行请求0，无新录像；不重启、重传、请求旧4323d2报告或点旧Diag/Check。下一关先准备新有限双路录像和同nonce结果接收，另获单次执行授权后、ready内才请用户只点新Slot一次。详见session102验收记录跟进；下方“可见性未验证/Done返回”为历史阶段。

- 最新续接（2026-10-22，session101–102）：用户明确要求重启。101交接未稳定/摘要错误，未放行正式门槛而超时，设备0请求、失败保留。102主Agent修正摘要、完整审阅后独立预检，在原Otty正式双路ready内5组内存自测PASS，10请求（9 GET/唯一1 POST /api/restart），HTTP200接受、两次暂不可达后恢复，两公开Slot文件前后逐字节一致。未主动运行Lua/诊断/旧Check/exporter/validator/Runtime，未重传/publish/刷写/清理/改设置或自启，不再重启。接口无boot_id；相机首帧Works、中末帧与当前预览为Left port/Camera/Photo/Video、Open/Done，支持重启观察但重启后Works/Slot可见性仍未验证。下一关请用户Done返回Works，只确认Loom Slot c38050可见，暂不点击。102两路150.03/150.00秒原MOV无音轨、完整解码及六帧PASS，启动差0.002秒，原片保留、发布pending；预览已关闭，原Otty空闲保留。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-22-ep04-slot-reboot-102/验收记录.md`；下方旧下一步均为历史。

- session100 媒体终验补充（2026-10-22）：Otty149.99秒、QuickTime相机预览窗150.00秒原MOV均无音轨、完整解码及主Agent六帧复核PASS，启动差0.001秒，原片保留，发布pending；预览已关闭，原Otty空闲保留，无后台录制。文件重传PASS但Works仍6 ITEMS、第2/2页无新Slot，未运行或重启。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-22-ep04-owned-probe-reupload-100/验收记录.md`。

- 最新续接（2026-10-22，session98–100）：用户要求重新上传同一Loom Slot c38050。98预检等待审阅超时、99正式录制内本机动态模块导入失败，均设备0请求，失败原片/日志保留。100修正标准导入后，在原Otty＋QuickTime预览窗独立正式双路ready内5组内存自测PASS，13请求（11 GET/2 POST）重传同字节diagnose.lua和launcher，launcher最后，前后四文件精确核对，私有0700/0600备份已核验；binding/result只读仍PENDING。上传后相机仍Works6 ITEMS、第2/2页两旧作品、没有Slot，第一页未直观检查，tab高亮过曝不猜字样；重传不代表注册或运行。未运行Lua/诊断/旧Diag/Check/exporter/validator/Runtime，未重启、刷写、清理、publish或改设置/自启。100正式媒体自然结束与终验另见该次记录，发布pending。下一关注册刷新通道或另获用户授权的单次正常重启，不再自动重传/点击。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-22-ep04-owned-probe-reupload-100/任务验收.md`；下方旧下一步保留历史。

- 最新反馈与诊断（2026-10-22，session97）：用户明确Works没有Loom Slot，记user_reported_not_visible；不把96上传读回当注册/可见。仅本地静态源码诊断，设备/网络/测试/执行/相机均0，无录像。Luna查快照并补查已有build04子模块，主Agent复核：registry foreach只读内存，reload/publish才扫盘；Works每秒刷新但只读registry，HTTP上传不通知reload。最可能是新作品尚未注册刷新，现场固件未知仍非已确认根因。清单静态规则未发现问题；另需确认Installed全部分页（每页4项、order90可能在后页），不能以Recent没有判断。下一关先核对tab/页数/ITEMS，暂不点击；若仍缺失，准备已上传ID的publish_app调用通道或另经授权的单次重启验证，不自动重启/重传/改配置。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-22-ep04-slot-visibility-diagnosis-97/诊断记录.md`；以下“先确认出现”是历史阶段。

- 最新续接（2026-10-22，session96）：新作品 `Loom Slot c38050`（nonce c380504c30c0）已在原Otty与QuickTime相机预览窗正式双路ready后单次上传/精确读回，24请求（18 GET/6 POST），2新目录与4文件核对通过，launcher最后写入，终态slot_uploaded_not_run，报告槽PENDING。本次没有执行诊断/旧Check/exporter/validator/Runtime、重启、刷写、清理或改Debug/设置/自启，也未请求旧4323d2报告。94只预检后等待超时，设备请求0，失败保留；96独立预检，没有覆盖94。96两路149.99/150.01秒原MOV无音轨、完整解码/六帧复核通过，启动差0.001秒，原片保留、预览已关闭、原Otty空闲保留，发布pending。设备画面仍Camera/Open/Done；下一关请用户Done返回Works，只确认新标题可见，暂不点击。新鲜录制/接收门槛通过后才安排一次物理点击，不自动重启/重传。PENDING不证明可执行，STARTED至多证明启动写副作用；根因/Runtime仍未验证。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-22-ep04-owned-probe-deploy-96/验收记录.md`；以下旧“下一步”均为历史阶段。

- 最新续接（2026-10-22，session93/95，94准备中）：93主机17项中2FAIL，失败日志及两路原MOV保留；Luna仅修测试fixture规范路径/断言，生产门控未放宽。95原Otty正式双路ready内17项新传输+31项回归全部PASS，两路119.99/120.03秒原MOV无音轨、完整解码/六帧复核通过，原片保留，发布pending。设备请求/上传/执行仍0。新nonce c380504c30c0仅本机渲染，94只静态准备受限上传，不运行/点击/重启；必须先冻结94脚本与95验收指纹、重新独立双路门控后才能上传。旧4323d2/旧Check/报告不重试。95验收见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-22-ep04-owned-probe-transport-accept-95/验收记录.md`。以下旧“下一步”保留为历史阶段。

- 当前续接点（2026-10-22，session91–93）：用户已要求继续诊断，采用全新 nonce 的主机预置归属报告槽，不依赖历史stdout或现场stat第三值ENOENT。session92在原Otty+QuickTime预览窗正式双路ready内通过10项Python、新入口Lua失败矩阵及原probe回归；两路120秒原MOV无音轨、完整解码/六帧复核通过，原片保留、预览已关闭、原Otty保留。设备HTTP/WS/上传/执行均0，旧4323d2报告不再请求、旧Diag/Check不重跑。新入口只支持单操作者单次点击，非原子CAS；STARTED至多证明启动写副作用，不能证明probe运行。session93正在静态准备新上传/有界结果接收工具的离线验收，尚未测试/部署；候选nonce仅本地准备。下一关先完成工具审阅及离线验证，再另建受限部署session，不能提前点击或重启。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-22-ep04-owned-probe-accept-92/验收记录.md`；下方旧“下一步”保留为历史阶段。

- 当前停止点（2026-10-21，session90，仅本地静态排查）：Luna 源码证据经主 Agent 阅读和关键实现复核，未找到可确认的已结束 Works stdout/error 历史回读合同。`/api/logs/status` 只返回开关，`/ws/logs` 仅实时推送，不回放；现场固件未知。诊断结果正常输出可能达16KiB，本地日志行缓冲384字节，不能假定连接后可完整接收。设备HTTP/WS/测试/执行均0，无本轮录像；只打开过QuickTime预览，已关闭，原Otty保留。89报告404仍为NOT_VERIFIED，不重试旧报告或新Diag/旧Check。下一关先取得新nonce独立受限诊断方案的用户方向确认，并验证可靠输出接收链；不得直接上传/执行、改Debug或重启。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-diag-log-read-90/操作说明与验收.md`；下方“准备历史日志读取/单击”为历史计划，以本条为准。

- session89媒体终验：Otty60.03秒、QuickTime相机预览窗60.01秒原MOV，无音轨、完整解码及六帧复核通过、启动差0.001秒；原片保留，预览已关闭，原Otty空闲保留，发布pending。任务仍为同nonce报告404/NOT_VERIFIED。验收记录：`EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-diag-readback-89/验收记录.md`。

- 当前续接状态（2026-10-21，session87–89）：87离线自测失败；88修正后自测PASS但120秒点击等待超时，均设备请求0。用户随后明确回复“点了”，不补写88迟到确认、不再要求或执行点击。89新正式双路ready内自测PASS，只GET `/api/status` 200和同nonce `4323d2f2cd46` 的诊断报告404即停（not_found，2请求）。没有取得报告、现场stat合同或根因，不能从Stopped/404推断成功、缺失或stdout_only。下一关准备受限读取本次已有日志，不重跑新Diag/旧Check/exporter/validator/Runtime，不重启、重传、刷机或清理。87/88原片已通过无音轨、完整解码/六帧复核；89终验另见本次记录，发布pending。以下旧“下一步单击”是历史阶段，不可重复执行。

- 用户已明确要求：live 执行时同步开启 TP 摄像头录像和 Otty 窗口录屏；每次执行一个独立项目文件夹，并保存本次操作说明。这里的 TP 录像指 RTSP 视频流在电脑本地落盘，不擅自更改 SD 卡录像计划、摄像头配置或云台。
- 当前任务边界内可录制有限时长的设备视频，默认两路均无音频；普通非 live 画面查询仍默认单帧。执行结束停止，不延伸为后台、全天监控或自动发布。
- 使用 `tools/live_capture.py`，参考[双路录制操作说明](tools/live-capture.md)。两路短测均完成文件/解码/首中末画面验收后，才能开始正式录制；确认所选相机已输出首帧进度且 Otty 录制计时已启动，再自动运行任务。任一路失败不得声称双路同步成功。
- 当前新 live session 使用本次现场枚举并明确配置的 Mac 摄像头（AVFoundation）；须设置 `camera_source: "avfoundation"` 并记录当次 video index/name、video_size 和 framerate，只输入视频 `index:none`，无音频、不访问网络或请求 ONVIF/RTSP。不得固定永久 index、自动选择或切换相机。历史 TP 操作记录保留原样；仅未设置 `camera_source` 的旧 setup 仍按 TP RTSP 兼容路径执行。
- 2026-10-20 session76 的 Mac 摄像头预检失败：TCC 日志明确指出当前 Otty 缺少 `com.apple.security.device.camera` entitlement，系统禁止授权弹窗，正常 requestAccess 返回 false。不是用户漏点“允许”；不得反复取帧、重签 Otty、重置 TCC 或绕过拒绝。没有 Mac 画面/双路素材，设备结果任务未派发。若需要改用 macOS Terminal 仅承载相机采集，先取得用户确认，开发与录屏仍复用原 Otty；获准后重新做相机正常授权、构图和独立 session 双路预检，不把此路径预先视为成功。
- session77：用户已允许 Terminal 相机采集，但桌面控制接口明确禁止操作 `com.apple.Terminal`；不换 API/输入技术绕过。QuickTime 正常“新建录影”的 FaceTime高清相机预览可见 Mosaico Works，未点击录制，查看后已关闭预览；菜单仅见内置麦克风，无“无音频”选项。没有保存相机文件或双路录像，未请求设备。仅捕获 QuickTime 预览窗口图像且不录音轨的替代方案仍待用户确认、实现和独立预检，不把预览截图当成正式素材或脚本结果。
- session78 起用户已确认 QuickTime 预览窗口无声采集方案：仅对实际核对的 QuickTime Player `录影` 预览窗口用系统窗口录像保存 `MAC-camera.mov`，同时单独录原 Otty；不点击 QuickTime 自身录制按钮，不传录音参数。此用户授权仅新增相机预览这一目标窗口，不允许全桌面/区域或其他窗口，不更改权限/签名。两路真实媒体无音轨、完整解码及六帧复核仍是放行门槛，未通过则不执行设备任务。原生相机流与预览窗口录制必须在 metadata 中区分；保留原始 MOV，不能冒充原生 AVFoundation 流或帧级同步。
- session78 实测：QuickTime预览窗与原Otty双路8秒短测、120秒正式素材均自然导出、无音轨、完整解码及首中末六帧复核通过；两路正式原MOV保留，发布pending，结束关闭预览。正式录制ready后仅做3个GET：状态200、loader报告200、导出报告404即停；loader为`export_failed`、exporter_calls=1、validator_calls=0，未获得缺失源文件/新validator结果。报告无底层错误码，不猜原因；不要再次点击旧一次性Check或把Stopped当成功。下一步先补受限诊断并定位导出失败。详见session78验收记录，未执行重启、刷机、安装、boot或自启。
- 2026-10-21 session80：Mac本地分叉已读取核对；独立只读元数据模块 `tools/mosaico_export_probe.lua` 通过原Otty正式双路中的Lua契约、38项Python和旧exporter回归，设备请求0。模块尚未上传/运行，缺少单次设备入口和受限结果回传；不能把主机PASS当作根因或Runtime通过。旧loader丢弃exporter第二错误码；本机build04绑定支持stat三值，但现场固件未知。下一关先审阅独立设备探针，不重跑旧Check或清理残留。session79未释放正式门槛而超时，只有预检；失败与原片保留。
- session80媒体验收：两路正式约120秒原MOV自然导出、无音轨、完整解码及首中末六帧复核通过；QuickTime相机预览已关闭，原Otty保留。只做主机测试，最新真机结果仍为session78；发布pending。
- 2026-10-21 session81/83/84 主机验收失败均保留日志与原片，修正后 session85 通过诊断 Works 入口 Lua、13项 Python 入口/传输测试及基础 probe Lua；设备请求0。session85 两路正式约60秒原MOV无音轨、完整解码及六帧复核通过。新入口内联独立元数据模块，仅读私有固定binding、不读源内容或执行旧exporter/validator/Runtime。已有结果任一正面证据即停；仅结构化stat第三值ENOENT且无矛盾时复查后尝试一次写报告。该写入非原子exclusive-create，stdout_only没有持久防重保证，所以只单击一次，不宣称多次点击安全。
- session82 已在原Otty与QuickTime预览窗正式双路ready后上传新 `Loom Diag 4323d2`：nonce `4323d2f2cd46`，新目录 `/nand/apps/loom_diag_4323d2f2cd46`、私有binding `/nand/inbox/d_4323d2f2cd46-binding.json`，预期结果 `/nand/inbox/d_4323d2f2cd46-result.json`。21个受限请求，5个POST均核对（2新目录+3新文件），三文件逐字节回读一致，launcher最后写入；终态 `diagnostic_entry_uploaded_not_run`。未运行诊断、旧Check、validator、Runtime或重启/刷写/自启；新入口是否出现在Works尚未确认。下一关用户在Works单击新入口一次，再在新双路session受限读回同nonce报告；若stdout_only且结果404即停止，另准备受限日志读取，不能重跑入口。现场固件stat合同与根因仍未知。
- session82媒体验收：Otty 119.99秒、QuickTime相机预览窗120.02秒，均无音轨、完整解码及正式首中末六帧复核通过；原MOV保留，启动差0.002秒，不声称帧级同步。预览已关闭，原Otty保留；完整隐私审查/发布pending。验收记录位于 `EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-export-probe-deploy-82/`。
- 从本次起统一存放 `copis/宣传计划/05-Mosaico实机纪录/EPxx-主题/执行记录/<session_id>/`，其中 `原始素材/OTTY-screen.mov`、`原始素材/MAC-camera.mp4`（旧 session 可保留 `TP-camera.mp4`）、`preflight/`、`日志/`、`session.json`、`操作说明.md` 归属于同一次执行。每次唯一目录，拒绝覆盖旧原片；历史目录保留原样，旧录屏没有相机原片时明确记为未录。
- 记录两路主机时间和启动差；这是并行记录，不声称帧级同步。最终两路均验收文件大小、时长、分辨率、帧率、轨道、完整解码和首中末抽帧。正式画面人工复核与公开脱敏仍单独记录，未完成时发布保持 pending。
- `screencapture -V` 让其自然结束导出，不以 Ctrl-C 当成可保存的停止方式。录像时长必须覆盖任务预算；长任务另开合理时长的新 session，不偷偷切换未录制窗口或无限录制。

- 2026-10-21 session86：用户确认后，在原 Otty 与 QuickTime 预览窗正式双路 ready 内执行 10 个受限请求（9 GET、唯一 POST 为一次 `/api/restart`）。离线自测通过，POST HTTP 200，设备两次短暂不可达后恢复；诊断 launcher/script 重启前后逐字节一致。接口无 boot_id/uptime，不声称 Boot ID 变化。首帧 Works，重启后中/末帧与结束单帧为 `Left port / Camera / Photo / Video`、Open/Done；尚未观察重启后 Works，不能认定新入口已显示或确认注册失败根因。本次未运行 Lua、旧 Check、validator 或 Runtime，也未重传/刷写/清理/改自启。下一关用户点 Done 返回 Works 并检查后页，暂不点作品；不再重复重启。session86两路150.01/150.00秒原MOV无音轨、完整解码与六帧复核通过，启动差0.001秒，发布pending；预览已关闭、原Otty保留。详见 `EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-diag-reboot-86/验收记录.md`。

- session86 录像结束后，用户回复“出现了”，现场确认 Works 已显示 `Loom Diag 4323d2`。状态为 `user_confirmed_visible`，不是session86原片拍到的条目，也不证明已执行。此跟进设备请求0；不再重启或重传，下一关另行确认单次诊断并准备新双路录像，ready后只点新入口一次，旧Check不点。

### 开发目标与直接执行

- 开工前读取 `copis/宣传计划/05-Mosaico实机纪录/` 下的宣传计划及对应集拍摄计划；每集只回答一个与真实开发有关的问题。
- 沿用 EP02 上电、EP03 适配、EP04 Runtime、EP05 硬件、EP06 权限、EP07 OTA、EP08 课程这条顺序；仅选择与当前事实和代码节点匹配的一集。
- 遵循本文件的单 Agent 执行规则。Otty 是用户已授权 live 任务的执行/可视通道，由当前主 Agent 直接准备和执行命令，不派发子代理或独立模型 CLI 任务。
- 用户已要求把 live 需求交给 Otty 中的 Codex 时，由 Agent 自动传递完整功能需求；不得要求用户再手动粘贴提示词。
- 执行上下文须自包含：目标与验收条件、仓库路径和分支、执行前脏状态、允许修改的文件、禁止事项、安全与审批边界、测试命令/预期、共享 `session_id` 和 `episode_id`。
- 主 Agent 验收实际 diff、运行输出和相应测试；不以执行者自称完成作为证据。未执行或未通过的检查须明确记为未验证或失败。
- 不盲目使用 YOLO、bypass 或扩大文件权限。提交、推送、刷机、复位及其他改变设备状态的操作，只能在用户明确授权范围内进行。

### Otty 自动派发边界

- 2026-10-16 的历史验证使用 `/Applications/Otty.app/Contents/MacOS/otty-cli`，以 `open <repo> --command '<codex绝对路径> exec --json --ephemeral --sandbox read-only --color never "<任务>"' --title ...` 新建任务 pane 并自动派发；只读探针曾返回 `OTTY_DISPATCH_OK`、`OTTY_SYNC_RECORDING_OK`。这是历史记录，不是当前新建窗口/面板的操作指引。
- 以上是历史模板，不代表当前安装、版本、权限或录制能力；用户当前要求优先复用上次执行保留的 Otty 窗口和可用 pane，不得自动新建窗口。每次先检查当前 Otty CLI 的 `help`、可执行路径与当前 Codex 的绝对路径/版本；不得固化历史 `node-v24` 路径。`--ephemeral` 仅用于 `codex exec`。
- 构造 `--command` 时按 shell 规则正确引用和转义提示词，避免变量展开、命令替换及元字符执行；不把未经处理的外部文本直接拼入命令字符串。
- 写任务必须明确合适的 sandbox、审批策略及文件范围；只读探针命令不能当成开发命令或开发完成证据。
- 记录可取得的 Otty window/pane、Codex thread/session 标识；缺失就写“未记录”，不可推测。`pane list`、`pane capture` 及终端文本只证明可见状态/文本，不证明已有视频。
- 默认 `ipc-allow-send-keys=false` 时，`pane run` / `pane send-text` 会被拒绝。遇拒绝即停止该路径，不反复重试；不擅自开启全局开关、安装 hook 或重启现有用户窗口。
- 每次复用上一执行保留的同一 Otty 窗口及其中可用 pane，不自动新建窗口，也不以新窗口规避 pane 输入限制。当前记录的窗口 `w_7495DBEB-0E12-4457-9F67-F4FF4D338B6E`、pane `p_1a14a2f26ff_f`、标题 `Loom EP02 IDF62 20261017-16` 只是本次参考值，不保证后续仍存在；每次须重新核对窗口、pane、标题和任务归属。主 Agent 负责按当前授权检查并关闭无关旧窗口，同时保留上次执行窗口供复用。
- 若保留窗口或 pane 缺失、不可用，或 `pane run` / `pane send-text` 被拒绝，先停止该输入路径；只有在同一窗口内存在已授权且经核对的正常 UI 输入/启动路径时才可使用。否则如实报告无法复用并等待处理，不得另开窗口、改全局配置或要求用户手动粘贴任务来绕过限制。

### 目标窗口录制与权限

- 只录选定的 Otty 窗口，不录整个桌面或无关窗口；默认不录系统音频或麦克风。
- Otty 的 `w_UUID` / `p_UUID` 与 macOS `CGWindowID` 不同。按 Otty 进程、窗口标题和 pane 所属任务核对真实目标窗口后，才能选择对应 `CGWindowID`。
- `screencapture -x -l <CGWindowID> -v -V <seconds> <绝对输出.mov>` 使用前须检查当前系统帮助并做短时实测；2026-10-17 已有自然结束并验收的 `.mov`，但不能据历史成功跳过本次权限及素材核验。
- 逐项确认窗口捕获工具及实际录制调用宿主所需权限。Accessibility 可读或截图成功，不等于 Screen Recording 获准，更不等于录像成功。
- 遇权限拒绝，走系统正常授权流程；不得绕过权限、持续重试或擅自退回全屏/区域录制。不可用时停止录制并报告，开发与素材结果分开说明。
- 历史权限恢复后曾仅有窗口截图；2026-10-17 后续已完成实际 `.mov` 验收，记录见 EP02 对应 session。后续仍须验证当次实际录制。

### 开始、派发和素材验收

- 正式任务前先做短录屏验证：目标文件真实存在且非零；用 `ffprobe` 或等效工具核验时长、分辨率、帧率及媒体轨道；抽看起始、中段、末段，确认只含目标窗口、画面可读且非黑屏，并无敏感信息。
- 正式派发前核对并复用上一执行保留的 Otty 窗口及可用 pane，确认目标 ID 稳定；不可用时停止并报告，不得新建窗口替代。`open --command` 仅作历史派发路径记录，不用于新建本次窗口，也不能同时充当“窗口已准备”和“录制已就绪”的证据。
- 若无法在已核对的保留窗口内开始任务，先确认同一窗口内是否有已授权且可验证的启动路径；没有则停止并报告。任何启动门闩/等待信号都必须先只读探测并验证可中断且有有限超时，使正式命令暂不执行；确认该窗口已在录后再释放。具体方式未验证前不得假称可用。
- 不得因为正式任务已经启动而切换到未录制的新窗口；仍须自动派发，不要求用户人工粘贴提示词。
- 只有录制器准备就绪并确认正在录制后，才自动派发正式任务，避免漏掉初始提示词和第一次事件。结束后再次核验录制文件及其内容；短测不能替代正式素材验收。
- 若目标窗口录制不可用、文件未生成或核验失败，标记录制未通过/待验证，不宣称同步录制完成；不得为补录像重演首次上电、故障或其他不可重复事件，也不得额外刷机。
- 真机镜头与 Otty 窗口录屏分开保存并关联同一个 `session_id`。本文件既有相机安全边界继续适用；用户已授权本节所述每次 live 执行的有限双路录像，除此之外仍默认单帧，不扩展成全天监控。

### 同步记录、隐私与成片真实性

- 每次记录共享的 `session_id`、`episode_id`、本集问题事实卡、`git_before`/`git_after`、分支和前后 dirty 清单。
- 记录真实设备、Runtime、固件版本；未知时写“未知/未记录”。同时记 Otty/Codex 身份与版本、window/pane/thread/session 标识、公开任务摘要、完整测试命令及 PASS/FAIL 输出、实际 diff、原片文件名和时间点。
- 仅在相关时记录设备日志及 OTA `state.json`；录制前检查目标窗口只显示本任务所需内容，并清理或遮挡密钥、Wi-Fi、账号、序列号、儿童信息和私人上下文。公开记录不复制这些内容，发布前再次检查并脱敏。
- 新执行统一保存于 `copis/宣传计划/05-Mosaico实机纪录/EPxx-主题/执行记录/<session_id>/`（详见上方独立归档规则）。历史 `{原始素材,代码证据,设备信息,后期}` 目录保留，不覆盖或移动既有原片；剪辑使用副本，补拍须显式标注。
- 主机测试通过不等于真机验收；计划、终端文本或截图不等于视频；视频存在也不等于内容已验收。将验证通过、失败和未验证分别报告。
- 宣传主版为 9:16、45–60 秒，预告版 15–20 秒；原始 coding 录屏不直接等同成片。旁白体现“AI 引导、孩子思考、共同实现”，准确区分人的决策、AI 建议和实际验证。
- 未完成人工画面与音频检查时，发布状态保持 `pending`。不自动登录、上传、发布、评论或监控平台。
