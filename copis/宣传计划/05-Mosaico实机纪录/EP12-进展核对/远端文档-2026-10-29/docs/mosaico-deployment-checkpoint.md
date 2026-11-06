# Mosaico 部署检查点（2026-10-21）

最新停止点（session90，静态排查）：所检查本地源码没有可确认的历史 stdout/error 回读入口；`/api/logs/status` 仅开关、`/ws/logs` 仅实时输出，不能取回用户刚才已点击的那次日志。现场固件未知；报告404仍不证明 stdout_only、成功或根因。设备HTTP/WS/测试/执行均0，无本轮录像；QuickTime预览已关闭、原Otty保留。下一步需用户确认全新nonce的独立受限诊断方案，并先验证可靠短/分块输出接收；不重试旧报告、不点旧Diag/Check，不擅自上传/执行、开启Debug或重启。见[session90审阅](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-diag-log-read-90/操作说明与验收.md)。下文“准备历史日志读取/下一步单击”保留为历史阶段，以本段和第0关为准。

session89终验：Otty60.03秒、QuickTime相机预览窗60.01秒，两原MOV均无音轨、完整解码和正式首中末六帧复核通过，启动差0.001秒；原片保留、预览已关闭、原Otty空闲保留，发布pending。设备结果仍为报告404/NOT_VERIFIED，不能被媒体验收升级。见[session89验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-diag-readback-89/验收记录.md)。本轮使用Luna准备最小只读分支，主Agent实际审阅diff、冻结哈希并在原Otty录像内核对自测/两GET证据；没有新增诊断执行。

最新结果（session87–89）：87离线自测失败、设备请求0，修正仅放入88；88自测PASS并请用户单击新Diag，但本地120秒等待超时、设备请求0，随后用户回复“点了”。不补写迟到确认或再要求点击。89在独立双路正式ready后自测PASS，只做两个GET：状态200、同nonce `4323d2f2cd46` 诊断结果404即停（`not_found`）。未取得报告/实际stat合同或底层错误码，不能从Stopped或404推断成功、残留不存在、源丢失或具体根因。下一关是为本次已点击的诊断准备受限日志读取，不再点击新Diag或旧Check，不重启、重传、刷写或清理。见[session88验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-diag-readback-88/验收记录.md)与[session89事实卡](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-diag-readback-89/事实卡.md)。下文“未点击/下一步单击”均为历史阶段，不能再照做。

最新补充（session86录像结束后）：用户回复“出现了”，现场确认 `Loom Diag 4323d2` 已显示在Works；证据为用户反馈，不在session86原片中。可见性为 `user_confirmed_visible`，诊断执行未报告。本次跟进没有设备请求或操作。下一关另行确认后，在新双路录像ready时只点击该新入口一次并受限读取同nonce报告；旧Check不点，不再重启或重传。下文“显示未确认/先返回Works”保留为当时观察。

session86 最新现场状态：用户确认后，在原 Otty 正式无声双路 ready 内仅正常重启一次；10 请求（9 GET、1 POST），`/api/restart` HTTP 200，短暂离线后恢复，两公开诊断文件前后逐字节一致。没有 boot_id/uptime 证据，不宣称 Boot ID 变化。相机首帧 Works，重启后中/末帧及结束单帧为 `Left port / Camera / Photo / Video`、Open/Done，尚未回到 Works；新入口可见性仍未验证，诊断/旧Check/Runtime均未运行。下一步请用户点 Done 返回 Works，检查包括后页的列表，先不点作品；不要再重启或重传。两路150.01/150.00秒原MOV无音轨、完整解码与六帧复核通过，预览已关闭、原Otty保留，发布pending。详见[session86验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-diag-reboot-86/验收记录.md)。

最新进展：session85 的独立诊断 Works 入口与传输契约通过 Lua 入口、13 项 Python 及基础 probe Lua 验收，设备请求0；session81/83/84 的失败日志和原片保留。session82 已向 10.0.0.129 完成 21 个受限请求、5 个 POST（2 目录+3 文件），三个文件逐字节回读一致，launcher 最后写入。终态为 `diagnostic_entry_uploaded_not_run`，作品名 `Loom Diag 4323d2`。上传未运行诊断，Works 是否显示尚未确认；下一步用户返回 Works 单击这个新入口一次，再在独立双路会话读回同 nonce 的受限报告。不要点击旧 Check。入口的 stdout_only 分支没有持久防重保证；报告写入为非原子的检查后写入，不能承诺并发点击安全。详见[session85审阅](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-export-probe-accept-85/主Agent审阅.md)及[探针边界](../tools/mosaico-export-probe.md)。

上述 session85/82 的“下一步单击”是当时计划；当前以 session86 的先确认 Works 可见性、暂不点击为准。以下 session80 为历史状态；最新设备诊断执行结果仍为 session78 的 `export_failed`，session82 只推进了新诊断的上传与读回层。

session82 两路正式原 MOV 自然保存：Otty 119.99秒、QuickTime相机预览窗120.02秒，无音轨、完整解码及六帧复核通过，原片保留。预览已关闭，原 Otty 保留，完整隐私审查/发布 pending。详见[session82验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-export-probe-deploy-82/验收记录.md)。

session80 主机侧续接：已读取 Mac 本地分叉，并新增独立只读元数据探针 `tools/mosaico_export_probe.lua`；原 Otty 的正式双路录制内，新探针 Lua、38项 Python 回归及旧 exporter Lua 全部通过，设备请求0。探针只返回能力/固定状态/封顶大小/白名单错误码，不读写文件内容；旧两值或权限错误不被解释为缺失。它尚无设备入口、未上传/运行，不能推进为真实根因已定位或 Runtime PASS。session79未释放正式门槛而超时，仅保留预检；详见[session80审阅](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-export-probe-host-80/主Agent审阅.md)与[探针边界](../tools/mosaico-export-probe.md)。以下session78仍是最新真机结果。

session80两路正式约120秒原MOV自然导出，无音轨、完整解码及首中末六帧复核通过，QuickTime预览已关闭，原Otty保留，发布pending。见[最终验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-21-ep04-export-probe-host-80/验收记录.md)。

用户已授权部署。当前新固件build04已编译、打包、检查通过，尚未刷写；Runtime新版73项已暂存但未执行验证。session75已在10.0.0.129完成一次受限备份及Check loader上传/精确读回；用户随后已点击并看到 Running → Stopped。session78只读取得loader终态 `export_failed`（exporter_calls=1、validator_calls=0），导出报告GET返回404后停止。缺失文件仍未取得，新validator未运行；不要再次点击旧入口。最近只读USB枚举仍为session73的0，后续需重新确认，不扫描其他主机。

## 下一步的真实关口

0. session90静态排查未找到可确认的历史读取合同；不发无效GET或连接实时日志来冒充历史回读。当前旧诊断输出未取得、根因未知。先请用户确认全新nonce的独立受限诊断方案，再审阅和验证短/分块输出接收、单次执行与录制边界；尚未允许以“取旧日志”为由运行新Lua或开启Debug。旧Diag/Check不再点击，旧报告不重试。

1. 用户已运行session75的一次性Check loader。session78在正式双路录制ready后仅执行GET：`/api/status`、loader报告、导出报告；第三项404即停止，没有请求原始导出字节或validator报告。loader确认 `export_failed`、exporter一次、validator零次，但没有记录底层导出错误码。独立模块及 Works 入口已通过 session80/85 主机验证，session82 新入口上传/精确读回通过；下一关用户在 Works 单击 `Loom Diag 4323d2` 一次，再受限读回同 nonce 报告。若 stdout_only 且结果404即停，不重跑，另行准备受限日志读取。旧loader丢弃exporter第二错误码；本机build04源码支持stat三值不能证明现场固件合同，也不足以定根因。不直接重跑已有报告的一次性入口、不清理未知残留。此时不要进入BOOT下载模式，先完成诊断与文件导出。
2. 将导出的原始字节保存到私有备份，与设备报告的字节数/SHA-256逐一核对。设备只产生导出文件或返回成功文字都不足以完成备份。保留旧Check并在适当录制session恢复入口；清理只限已确认的临时文件。
3. 稳定bootstrap目标固定为 `/nand/loom-os-runtime/bootstrap.lua`。现有 `provision/install_initial.lua` 要求args.source_root、仅复制Runtime清单并写state.json；它不复制bootstrap，且当前Works的args为空，不能直接拿来初装或重跑。应在备份完整、候选bootstrap核验后，以受控本地Works安装链部署固定目标；目标存在则核对并保留，不覆盖未知文件。临时写入、rename、读回及仅语法检查分别记录，不顺带启用自启或改变state.json。
4. 恢复USB后，确认当前端口/ROM状态，读回实际分区并与build04比较，保全必要的旧镜像/配置；再准备具体更新命令。默认包的flash_args含引导与恢复区，不能直接当作本次最小更新范围。不得擦除/eFuse或改用旧包冒充本次产物。
5. 新固件启动后按原样require_touch门槛验收Runtime；健康后再做本机4位一次性码配对、随机4字符token保存及真实HTTP控制。最后才启用开机启动。

## 证据与执行约束

session75：18项Python、两组Lua、diff-check通过。真实部分备份含195个文件共998,943字节，API可见清单251项/196文件且大小稳定；唯一排除文件90,189字节仍无真实原始字节/SHA-256。三项POST均接受并逐字节读回，driver只执行一次、不重试。loader SHA-256 `95be73f07aa8f0500b36c648c0a17fa519e9c9255ece3689c4a004b10c9113de`，终态`loader_uploaded_not_run`。私有binding/原文件名与内容不写入公开记录。session74的mock测试失败与原片单独保留，不倒填成功。

session78只读结果：focused live-capture unittest退出0；设备状态和loader报告可读，导出报告404，公开结果 `NOT_VERIFIED`。loader声明 `runtime_install_requested=false`、`runtime_boot_requested=false`、`restart_requested=false`。原备份manifest保持历史partial不改写；本次私有诊断0600保存，无原文件字节恢复。停止状态不是Runtime成功，404也不单独证明不存在残留导出文件。详见[本次记录](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-20-ep04-mac-camera-readback-78/验收记录.md)。

固件目录 `firmware/artifacts/2026-10-20-runtime-secure-04/`，artifact manifest SHA-256 `6b11412334c4952a1823061377d092bf2560cc674124815aa78954fe42510c7b`。session73保留构建日志、USB结果、双路600秒原片及主Agent抽帧验收。

所有实际主机验证、设备请求、刷写或重启仍复用同一Otty窗口，在有限双路录像内进行。没有可验证的远程Lua执行入口；此前Agent试用额度耗尽。需要本机点击或物理接线时如实交给用户，不用HTTP上传伪装执行成功。公开记录不包含私有文件名、内容、配对码或token；素材全片隐私审查未完成，发布pending。
