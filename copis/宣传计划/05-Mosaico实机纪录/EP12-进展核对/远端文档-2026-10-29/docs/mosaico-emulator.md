# Mosaico S31 本机模拟

本机已安装官方 esp-emulator 0.51.0；这是 ESP32-S31 early-bring-up 模拟，不是 Mosaico 全外设/屏幕模拟器。模拟结果不能替代真机 C01–C10、Runtime、HTTP或点按验收。

## 最新：转向真机部署条件，只读核对完成（session203）

不再重复模拟演示。本轮只向 `10.0.0.129` 发出三个 GET：status200、lua-modules200但未列出loom_touch/loom_security、native/status404；Mac未枚举Espressif/USB-OTG或USB串口。这不证明关机、未接线或坏线，应用CDC行为仍未知。未开串口、ROM握手、上传、执行Lua、点按、重启或刷写。

现有22件产物和三项update镜像已独立校验，本地候选分区能容纳镜像；不是设备分区读回。现场布局/安全状态/刷写所需备份及精确授权尚未核验，deployment_ready=false。下一步先确认数据链与USB模式；如需ROM/重启，先取得当次授权，再只读确认和备份，不自动刷写或按POWER/BOOT。

原Otty同pane、Safari及静音相机预览三路短测＋正式已归档六MP4，共29,933,676B，30fps无音轨/完整及独立解码/大小SHA/328pins及18最终帧复核通过。本轮六MOV核验后删净，净释放171,842,652B不可直接恢复，历史不动。Safari是202旧停止页非本轮执行，Otty细字PARTIAL，相机Works非Runtime验收；QT预览已关/原Otty空闲，发布pending。见[203只读结果与录像](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-29-ep04-native-readiness-203/验收记录.md)。完整Runtime、生产HTTP、实体触摸与重启自启仍未验收。

## 最新：自动 HTTP 点按与正式视频闭环通过（session202）

新增独立[有界序列helper](../tools/mosaico_sim_pointer_sequence.py)及7项失败即停测试，不改固定v2/bridge或生产保护。
原Otty实际36Python/9Node/6类host Lua检查通过；Safari只刷新/Connect一次，自动13HTTP完成六次合成点按，
空白零事件、Counter2、Settings/Home、原生input拒绝、第二Lua实例计数重置与Stop全部核验。
没有逐屏STEP.OK/GUI.DONE等待、无重试。HTTP通过只写visual_pending；主Agent实际查看正式MP4五阶段后独立追加视频通过，原200/201失败不改。

六MP4完整及独立解码/大小SHA/30fps静音/321pins、18最终帧＋5额外关键帧通过，16,341,234B；
正式300.13/300.10/300.03秒，本轮六MOV核验后删净释放273,761,015B不可直接恢复，历史不动。
Otty细字PARTIAL，相机实体Works非模拟UI；QT5642预览已关、18763无监听、相关进程退出，发布pending。
这是接口→DOM→官方输入队列→真实WASM LVGL→页面结果的**模拟闭环**；不是原生loom_touch、完整Runtime、生产HTTP、实体重启或开机自启。
下一实际目标转向核真机部署条件，不为录像重复模拟；刷写和重启另授权。
见[202验收与Safari录像](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-29-ep04-sim-http-pointer-202/验收记录.md)。环境日期10-29与原始主机UTC10-28分别保留。

## 前一阶段：HTTP 坐标输入已触发真实 LVGL 事件，自动交接仍超时（session200–201）

媒体终验已完成：两轮12MP4共190,682,028B，完整及独立解码/大小SHA/30fps静音、310/317pins、36最终帧及5个Safari关键帧实际核验；对应本轮MOV核验后删除，净释放1,316,778,958B不可直接恢复，历史不动。201正式片确实包含Counter2/Settings/Home/超时清理。QT预览已关、原Otty空闲/Safari停止页保留、18763无监听及相关进程退出。见[200失败验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-sim-http-pointer-200/验收记录.md)、[201点按及超时验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-sim-http-pointer-201/验收记录.md)。

新增[显式模拟输入 v2](../tools/mosaico-sim-pointer-v2.md)。200在start时错误断言无返回值set_title而失败，原件保留；独立v2仅修此错误。201原Otty实际跑29Python＋9Node＋6类host Lua契约通过，Safari只刷新/Connect一次，之后7条真实loopback HTTP完成5次合成DOM点按：空白零目标事件、Counter两次2/2/2、Settings与Home各一次，最终Counter2/4/4/4。主Agent实际CUA观察成立，目标按钮没有手点。

派生HTML仅对capture/release增加两处isTrusted判断，随后仍走官方输入队列和真实WASM LVGL read callback；不直接写队列或调用回调。固定WASM/七模块/六tracked/生产main与require_touch不改，无fake loom_touch。诊断Home/Settings为英文面板，不写配置。

整轮仍为verification_failed：300秒逐屏观察交接在STEP3超时，模拟器自动Stop/cleanup initialized=false/exit1/Run恢复/Stop禁用。迟到Home观察独立留档，不回填OK/GUI.DONE。原生input浏览器重检与第二实例未执行；不是生产HTTP、完整Runtime、物理触摸或开机自启验收。下一关应有界自动跑序列并记录阶段时间点，结束后核正式Safari MP4，不再把模型往返变成每步执行门闩。两轮三路MP4的最终媒体结果见各session验收；代码准备不称全程编码录屏，发布pending。

## 前一阶段：本机 HTTP 已调用真实控制模块并观察到 UI（session199）

新增[独立应用模拟 HTTP 适配](../tools/mosaico-sim-control.md)：loopback HTTP → Safari桥接 → WASM固定内存信箱 → 真实 `core.control_modules.dispatch`。不改生产main/require_touch、HTTPworker/配对、七模块源或既有四WASM资产，不 mock loom_touch/thread。固定官方模拟 HTTP 仅占位且 thread 缺 stop/queue_delete，故本轮不是生产 HTTP worker 或完整 Runtime 运行。

原Otty703同pane实际跑16Python＋2Node＋3CJK回归全过，12条真实HTTP请求中11成功、原生input.tap按预期 E_UNSUPPORTED。Safari4621实际只刷新/Connect各一次，之后由接口驱动：设置合成面板 → Home → runtime.restart请求后重建g2 Lua state → 新标题 `Loom HTTP PASS g2` → Stop/cleanup initialized=false/exit1；Run恢复、Stop禁用、当前可见日志无旧active-screen警告。主Agent实际观察并在520秒预算内交接，未重复让用户确认点击。冻结runner/说明误写17Python，原件保留，以原始日志16项及独立验收更正。未载CJK字体，Launcher中文按钮方框不算中文通过。

三路Safari/Otty/QuickTime5191静音预览短测九帧通过，正式均600.07秒自然结束；六MP4完整及独立解码/大小SHA/30fps无音轨、302pins和最终18帧实际复核通过。另实际核最终Safari MP4的84.123/113.869/140.8755/213.497秒，确认设置/Home/g2/停止过程均录下。六片213,157,477B，本轮六MOV核验后删净释放1,027,061,496B不可直接恢复，历史媒体不动；Otty细字PARTIAL，相机实体Works旧Preflight非模拟UI，代码初稿准备不冒充全程编码录像，发布pending。QT预览已正常关闭，原Otty空闲/Safari停止页保留、18763无监听及相关进程退出；实体HTTP/USB/上传/点按/重启/刷机/eFuse/生产数据/commit/push均0。控制及浏览器侧用本轮独立临时256bit内存能力，仅本机模拟，不替换生产四字符令牌方案；不向LAN提供服务。见[199验收与MP4](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-sim-http-control-199/验收记录.md)。

下一关做显式simulation-only的HTTP坐标输入与事件观测闭环；保持生产input.tap不支持的真实结果，不伪造loom_touch成功。原生固件、完整Runtime、生产配对、实体触摸及开机自启仍待分别验收。详见session199的GUI观察和最终验收；下文197–198为前一阶段。

## 前一阶段：修复版Safari实际回归无旧警告，交接超时及录像缺口保留（session197–198）

用户明确允许后，197实际刷新Safari加载本地派生WASM（SHA `3e5c3ae2709845dd3d4f0b288045da61759a6a1686b7d69c29deb7294236e12e`）。显示合同、25次init/load/process/deinit/重复deinit均通过且exit0；真实按钮空白无回调/两次2/2/2，中文设置可读、Demo/Back/设置/Home各一次、PASS1/1/1/1、字体清理/正常exit0。198沿用同一实例再次核按钮取消及中文导航。可见日志均无旧active-screen删除警告，Run恢复/Stop禁用。不是仅主机测试或旧停止画面。原四资产、六tracked、生产main/require_touch与五模块不改，实体操作0。

固定源码Stop会luaL_error("script stopped")，run_file保留错误、完成清理再返回1；这是取消合同，不是正常exit0。197冻结runner沿用旧hosted全0预期，原失败保留，198按本地源码区分取消1/正常0，没有改产品错误处理。两轮GUI.DONE均晚于270/145秒期限，result仍gui_not_verified/超时；实际CUA观察不能回填自动门控通过，构建时manifest中的browser_executed=false也不回写，新GUI事实独立归档。

两轮12个MP4（三路短测＋正式）完整及独立解码/大小SHA/30fps无音轨、每轮18最终帧实际复核与290/295pins保持通过，共135,750,674B；对应MOV核验后删除、净释放1,061,278,172B不可直接恢复，历史素材不动。正式197 Safari/Otty/相机300.03/300.00/300.00秒，198为180.00/180.00/180.07秒。实际时间轴确认197录到刷新/显示/25循环，198录到点按取消；**本轮中文导航过程有CUA实际观察，但未被正式视频覆盖，不称完整全流程片**。相机是实体Works旧Preflight非模拟UI，Otty细字PARTIAL，发布pending。见[197验收与Safari视频](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-sim-lifecycle-safari-197/验收记录.md)、[198验收与Safari视频](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-sim-stop-navigation-198/验收记录.md)。

原Otty703同pane真实执行后空闲保留，Safari保留start#6 PASS停止页，QT5030预览正常关闭/打开面板仍在，18763无监听/相关录制转码进程退出。下一开发关为最小模拟扩展到完整Runtime/HTTP控制隔离适配，另设足够有限GUI/录像预算并及时落盘观察；不为录片继续重复测试，也不自动部署/重启实体。不代表完整Runtime、S31硬件、设备HTTP输入、物理触摸或重启自启通过。

## 前一阶段：屏幕释放修复主机回归通过、Safari当时待加载（session191–196）

媒体收尾补充：193–196 的 24 个 MP4 均已完成完整解码、独立文件/日志/参数/输入核验与各 18 个最终抽帧复核。194/195 原失败保持，196 主机 PASS 不改为 GUI PASS。194/195/196 分别净释放 1,353,977,522 / 1,147,939,125 / 370,881,510 B；对应 MOV 核验后删除、不可直接恢复，历史媒体未动。Safari 录屏真实存在但画面仍是旧 189 停止页；所有录制/转码进程已退出，18763 无监听。各 session 验收文档记载具体时长与内容边界；下文“其余媒体收尾”为终验前快照。

已在固定官方源码的独立副本修复模拟display_service释放顺序：保存默认screen，满足非RAW及restore标志时先恢复有效默认screen，再调用Lua cleanup，stop清指针。没有跳过deinit、构造fallback或隐藏WARN；生产main/require_touch、五模块、真机和原下载四资产不动。项目私有Emscripten6.0.13/LVGL9.5.0/Lua5.4.8，195完成模拟器四件套编译；196真实LVGL/Lua A/B负对照及循环回归通过，见[196构建验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-sim-lifecycle-status-196/验收记录.md)。

原版expected_active断言预期失败，修复版105次会话heap5576/5576、RAW/flag/默认缺失/active及double stop通过；真实Lua正常30/异常30次退出heap1541616/1541616、无active-screen警告，12项文件检查测试通过。新四资产9,458,893B，manifest位于`firmware/.build-cache/wasm-lifecycle-check-01/runtime/manifest.json`，标记本地派生/原hosted commit未知/未验上游签名/浏览器及真机未验证。独立摘要/大小/WASM.validate及280pins通过，不instantiate。

191清单字段KeyError、192包装SyntaxError、193Python3.9不满足版本、194Lua TLS失败、195首任务符号链接检查及第二次夹具状态误判的原失败均保留。Lua下载最终同官方地址直连且保持TLS；仅新构建子进程去代理。官方源码唯一内部CLAUDE.md→AGENTS.md原样保留，不允许外部链接。Lua夹具v2仅修luaL_dostring逻辑OR折叠错误码，保留原状态/文本断言，不放宽产品逻辑。

本轮新三路含Safari真实录屏，仍是旧189 start#3停止画面，未刷新/加载新派生软件，不能把主机PASS说成Safari警告消失或完整Runtime/HTTP输入/重启自启通过。193六MP4已独立及18帧三联图终验，其余素材在本段快照时收尾，终态见各验收记录。下一步仅在动作时确认后，新三路录屏ready内加载新构建做真实25次生命周期＋原点击/中文导航回归；不操作真机。

## 独立冷启动及可测功能补录（2026-10-28，session188–189）

已新增[6分钟Safari完整补录及三路素材验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-safari-full-replay-189/验收记录.md)。这是新演示，不补造历史第一次；“冷启动”仅指Safari刷新重建官方WASM实例，不是实体/固件开机。新start #1显示合同/色块TEST/exit0；#2空白不增加计数、两次按钮事件2/2/2、Stop一次/exit0；#3中文Launcher、Demo/Back/设置/Home各一次、PASS1/1/1/1、字体删除/清理/自动exit0。设置面板为合成英文/no configuration writes；中文仅Launcher入口核可读。active-screen警告未修，完整Runtime、HTTP输入、硬件及重启自启仍未验收，下一开发关不变。

原320秒GUI交接超时，result仍gui_not_verified/exit1、迟到文件未消费。事后实际回看最终MP4的350/359秒已包含退出，故纠正先前“尾段未录到”的时间推断，见[视频索引与补充](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-safari-full-replay-189/视频复核补充.md)；视频覆盖与自动门控分开。188录制前冻结引用失败保留，190备用仅准备未执行，不再重复演示。

原Otty703同pane真实执行，Safari/Otty/QuickTime相机预览三路静音：正式360.00/360.03/360.03秒、短测8.03/8.13/8.10秒，六MP4均H.264/30fps，独立完整解码/大小SHA、最终实际18帧及15个Safari关键帧通过；六MOV核验后删，净释放678,320,514B不可直接恢复，历史不动。269/旧256/230pins和六tracked不变，无生产代码/官方资产变更、实体操作0。相机是实体Works旧Preflight非模拟UI，Otty细字PARTIAL；QT4846预览已关闭、Safari停止/原Otty空闲保留、18763无监听、相关进程退出，发布及全片隐私终审pending。

## Safari 结果事后补录（2026-10-28）

按用户要求，已将当前保留的 session187 start #4 中文 Launcher / PASS1/1/1/1 停止终态录为[正式 MP4（20.03秒）及短测 MP4（8秒）](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-loom-font-simulator-187/Safari补录说明.md)。两片均1332×854/H.264/30fps/静音，完整解码、独立复解、SHA及实际六帧通过；本轮两个MOV核验后删、净释放2,763,469B且不可直接恢复。首轮录制前窗口匹配失败保留，第二轮独立归档。没有刷新/Run/点击/启动服务/真机操作，旧结果及256/230pins不变，原Otty空闲保留、18763无监听。

这是事后留存结果，不是此前点击过程；182/183/185的历史Safari录像无法补回，184/186无本轮guest执行，各目录只新增关联说明，不复制187片冒充历史原片。下方原记录“Safari未录像”仍是原执行时事实；补片不改变旧失败/超时、清理警告或Runtime未验收结论，发布仍pending。

## 当前结果：中文与有界观察交接通过，清理警告未修（session186–187）

186因macOS临时路径/var符号链接被严格helper拒绝，首组四测试三过一错误，verification_failed/0.543秒；没有新bundle/服务/guest运行，原失败保留。187修测试canonical路径，并另用新CJK helper加载官方同包Fusion Pixel：原Noto实际cmap缺“设/置/中/文”，font_load成功不足以证明中文。Fusion 5,159,320B在WASM guest内有界复制到独占scratch，通过官方API加载size24/cache96，完整shutdown后删除；不挂主机/生产字体或存储，不改五模块/生产main/强触控策略/官方四资产。

187实际31Python、8场景CJK Lua、5场景原entry及原UI回归全过。新bundle24,026B、SHA `57edb6a0495d8ce6c90c16f959a963e1630d8ffea82434b34b7d10132495211f`。Safari同一runtime/start#4，只Run一次，中文“设置”可读，Demo/Back/设置/Home各一次、PASS1/1/1/1、自动exit0/Run恢复/Stop禁用；字体删除和CLEANUP initialized=false实际出现。真实CUA观察后写本次绑定记录并在120.089秒被消费，result=loom_font_ui_verified_with_upstream_warning，不再晚到补成功。256输入/旧185230/六tracked/四资产保持；186旧241仅两项后续预期变化且旧源精确快照保留。

**active-screen删除警告仍存在，未修。** 固定官方模拟close直接cleanup，而设备release先restore default screen；hosted确切build未知，仅定位解释。未跳过deinit/隐藏警告/改下载二进制，本机无emcc。下一关独立源码与Emscripten环境中修restore生命周期、重复init/deinit回归及派生WASM后再GUI验证，不覆盖官方原件。不是完整Runtime、S31/HTTP点按/物理触摸或重启自启验收，实体操作0。

两轮八MP4独立完整解码/大小SHA/参数与各正式实际六帧完成，正式各360.00/360.00秒、30fps静音；对应八MOV核验后删，净释放1,197,393,588B、不可直接恢复，历史不动。原Otty703真实执行/同pane保留，细字PARTIAL，相机偏暗但实体Works旧Preflight可辨，不是模拟UI。Safari仅本会话CUA AX/截图、没录像；QT4747预览关闭、Otty空闲、18763无监听、相关进程退出，发布pending。见[186失败验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-loom-font-simulator-186/验收记录.md)、[187验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-28-ep04-loom-font-simulator-187/验收记录.md)、[字体与观察工具](../tools/mosaico-loom-font-sim.md)。

## 前一阶段：最小 Launcher/导航已观察，自动交接超时（session184–185）

新增[独立打包工具及说明](../tools/mosaico-loom-ui-sim.md)，固定嵌入真实 `core.errors/core.ui_runtime/core.navigation/api.nav/ui.launcher`，不含生产 main/bootstrap、硬件、HTTP、存储或自启。原源文件字节不改，只有嵌入时去 navigation 的 BOM。先用真实 `require_touch=true` 验证 E_UNSUPPORTED，再仅非生产模拟入口使用现有 display-only 选项；无假 loom_touch，生产 main 的强触控策略不变。

184因新测试误断言 Launcher 回调返回true而失败，原失败源和结果保留；仅修测试为调用后核真实导航队列。185实际13项Python、5场景Lua、原UI回归、bundle准备及仅编译语法全部通过。bundle为22,493B，SHA `88a5603d8d79003c64c8287d59089b8664ebc45245abcf25bae7bc5f04756e4a`；230输入、旧204输入、六tracked和官方四资产不变。

Safari沿用182同一已运行官方实例，Run一次（start#3），实际480×480画布完成 Demo → Back → 设置 → Home，各一次，真实页面切换及 PASS1/1/1/1，自动exit0、Run恢复/Stop禁用。示例App和设置面板为合成内容，不是生产App隔离/设置写入测试。**中文设置标签显示方框，退出仍有active-screen删除警告；均未修复。**

**自动整轮失败仍保留。** 200秒任务先以 `ui_deadline_not_verified`/200.399秒结束，session为task-failed；GUI记录写得晚、未被任务消费。实际GUI观察成立，不等于整轮自动门控通过，更不能断言全部GUI动作处于正式录像期限内。不补成功result或重跑点击。下一关先核字体/清理生命周期及有界GUI观察接收时序，再接完整Runtime模块。

两轮八MP4独立完整解码/大小SHA/参数及正式实际六帧已完成：184正式360.00/360.00秒、185正式240.00/240.00秒，30fps静音；对应八MOV校验后删、净释放1,318,386,398B不可直接恢复、历史不动。原Otty703实际执行，细字PARTIAL，相机仍实体Works/旧Preflight；Safari只有本会话CUA AX/截图，无视频或本地截图文件。预览关闭、原Otty空闲保留、18763无监听、相关进程退出，发布pending。实体操作0；不是完整Runtime/S31/设备HTTP点击/物理触摸/重启自启验收。见[184失败验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-loom-ui-simulator-184/验收记录.md)、[185验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-loom-ui-simulator-185/验收记录.md)、[Safari实际观察](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-loom-ui-simulator-185/Safari实际观察.md)。

## 前一阶段：Safari应用级显示与点击（session182–183）

用户明确允许后，182在Safari本地执行181固定官方WASM/JS，公开`display_contract.lua`返回`DISPLAY_CONTRACT_OK`/exit0，实际看到480×480色块与TEST。两条重复open的INVALID_STATE是contract预期拒绝。182随后超过260秒服务期限，原`ui_deadline_not_verified`/task-failed保留，合成点击没有在该轮执行。

183新双路录制内沿用同一已启动页面，只加载独立合成LVGL fixture。实际画布显示标题/蓝色按钮/计数；空白画布点击不累加，两次按钮单击各产生一次pressed→released→clicked，最终2/2/2。Stop一次后`FINISHED 2/2/2`、exit0、Run恢复/Stop禁用；有`lv_obj_delete: the active screen was deleted lv_obj_tree.c:86`清理警告，保留而未宣称无警告。183 `application_ui_verified`、381.364秒；UI证据来自主Agent直接CUA AX/截图，不是guest自动回传或设备收据。

这是**公开官方应用级模拟运行成功，不是生产Loom Runtime、S31整机/Works/NAND/HMAC、设备HTTP输入、物理触摸或重启自启通过**。没有改固件或保护；198/204冻结输入、原两归档/六tracked/181四资产不变，实体操作0、没有新下载/安装。下一步将Loom最小显示/启动模块与官方绑定做接口适配，再在隔离内存环境验证；不直接加载生产数据或放宽require_touch。

两轮八MP4独立完整解码/大小SHA/参数及各正式实际六帧完成：182正式300.00/300.00秒，183正式600.00/599.97秒，30fps/无音轨；对应八MOV校验后删，净释放2,116,757,821B、不可直接恢复，历史不动。原Otty703真正执行录制和loopback服务；Safari没有被录成视频，截图仅在本会话CUA工具结果，不能拿Otty/相机视频冒充模拟UI录像。相机仍实体Works/旧Preflight，Otty细字PARTIAL；QuickTime4626预览已正常关闭，原Otty空闲保留。18763服务已关闭，Safari保留已停止画面，发布pending。见[182验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-web-simulator-ui-182/验收记录.md)、[183验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-web-simulator-click-183/验收记录.md)及[Safari点击原始观察](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-web-simulator-click-183/Safari点击观察.md)。

## 独立应用级路径准备记录（历史session180–181）

固定esp-emu的实际`--help`确认`--i2c-dev`只提供寄存器存储/ACK/读回；官方也明确没有真实设备行为。未找到完整NAND器件模型配置入口，不以“未找到”断言实现绝对不存在，更不把ACK当CST9217触摸报告/释放验证。保留179失败，不再反复启动同一镜像。

官方ESP-Claw另有[Lua/LVGL应用级模拟器](https://github.com/espressif/esp-claw/blob/62aaeed7de8f3055615448620dd00ed39fd6af13/tools/lua_lvgl_web_sim/README.md)与[网页入口说明](https://github.com/espressif/esp-claw/blob/62aaeed7de8f3055615448620dd00ed39fd6af13/pages/simulator/README.md)。固定[官方CI](https://github.com/espressif/esp-claw/blob/62aaeed7de8f3055615448620dd00ed39fd6af13/.gitlab/ci/simulator.yml)声明生产发布域名`https://simulator.esp-claw.com`。这是Lua/LVGL/display与模拟触摸路径，不是S31整机、出厂Works、NAND/HMAC/设备HTTP或重启自启验收；官方mock不能证明接线/硬件行为。

当前没有Docker/Emscripten，本轮未本地编译。180已运行新helper的21项主机隔离测试和官方1项Node引导测试，全部PASS；公开运行时下载在最后data包30秒超时，失败证据完整保留。181新目录仅复制三个已核代码文件并重新GET一次缺失data，12.790秒完成：

| 公开产物 | 字节 | SHA-256 |
| --- | ---: | --- |
| HTML | 30,365 | `b964aa9b20244c322dab1ec1777e837c6bf9d953e378488e8ad74ee841d6042d` |
| JS | 87,072 | `ed0885a9e0eaae34e18fd59f43580d91e68a31a3148b0449c3f1fe588bb42426` |
| WASM | 3,139,152 | `e2cef52626ace6a895fdc9259c13e792c5fc9231ccf3ae6fe7a6b2df0decc545` |
| DATA | 6,208,440 | `52c3c183035626cc0ce553379a8b69623b0ca3fd966181666e2e1659fe3621e2` |

四文件共9,465,029B；data与下载JS声明大小及三个连续内部文件区间一致，WASM只做`WebAssembly.validate`结构校验，**未instantiate/执行guest、Lua或浏览器界面**。下载版实际build commit未知，不能声称与固定源码匹配；hosted HTML/资产已有和固定源码不同的内容。TLS及本地SHA固定副本不是官方签名/可复现构建证明。下载manifest SHA为`ed6ecd6a26a8982bbb5bfbe6e13db2cea77834c128d5a75fb10ee11b1de0b30f`。

工具[`tools/mosaico_web_sim.py`](../tools/mosaico_web_sim.py)提供`fetch/verify/serve`：serve只监听127.0.0.1:18763、有界1–1800秒，启动前逐项校验后只在内存服务四文件和不自动运行guest的索引；无repo目录列表、任意文件/POST上传，拒错误Host/Origin、符号链接/路径穿越。CSP限制外部网络，Permissions-Policy禁止相机/麦克风/定位等，不挂生产文件。浏览器兼容性及实际CSP下的WASM启动仍未验证。本轮仅合成host测试短暂开随机loopback端口，无18763常驻服务。

取得运行新下载官方代码的用户确认后，另建新live session，使用Safari/WebKit（不用Chrome），从公开显示合同和合成点击fixture开始，再审查如何挂载Loom模块；不改生产`require_touch=true`、不将模拟触摸等同真机触摸。本地有界服务准备命令（从项目根执行，当前尚未启动）：

```sh
python3 tools/mosaico_web_sim.py serve 'copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-web-simulator-complete-181/official-runtime' --seconds 600
```

180/181独立复核175/185冻结输入、原22/派生11归档及六tracked未变；无实体设备/真实eFuse/生产密钥操作。两轮八MP4已独立完整解码/指纹/参数及各正式实际六帧复核，180正式180.00/180.03秒、181正式120.00/120.00秒，30fps静音。对应八MOV校验后删，合计净释放750,668,327B、不可直接恢复，历史不动。相机仍是实体Works旧Preflight，不是模拟UI；细字PARTIAL，预览关闭、原Otty空闲保留、发布pending。见[180失败与测试验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-web-simulator-prepare-180/验收记录.md)和[181准备完成验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-web-simulator-complete-181/验收记录.md)。

## 两套固件必须分开

- 真机候选：`firmware/artifacts/2026-10-27-native-control-01/`，22项原归档及manifest不改。
- 模拟派生源码/SDK/构建：`firmware/.build-cache/builds/2026-10-27-simulation-uart-01/`，独立复制，不复用旧CMake build/cache或绝对路径生成代码。
- 模拟配置仅关闭 `CONFIG_USB_HS_CONSOLE_USB_CDC_AUTO_INIT`，保留UART。Board Manager的USB设备已`init_skip: true`，不额外关闭鉴权/HMAC/require_touch，不mock外设健康。
- 模拟派生11项产物已归档到 `firmware/artifacts/2026-10-27-simulation-uart-01/`，manifest标注`simulation_only`及`do_not_flash`。不能拿此包刷真机。

## 工具环境

SDK复制到新路径后，官方工具以SDK路径登记安装目标；应执行本地SDK的 `tools/idf_tools.py install --targets esp32s31`，复用已安装的S31工具。未登记会回落到所有芯片，错误地要求Xtensa/ULP等工具。核旧登记项不变，只新增新SDK路径，不安装所有目标来掩盖问题。

构建及ELF验证均使用已有隔离Python：`firmware/.build-cache/idf-tools/python_env/idf6.2_py3.12_env/bin/python`。系统Python3.9没有`elftools`；不要为此全局安装依赖。构建子进程可去代理，TLS与工具签名保持开启，GSPC复用已验签0.9.0私有cache。

## 启动与结果边界

按派生构建的`flasher_args.json`七段地址用esptool **merge-bin**生成独立镜像，不能调用flash/monitor。只用公开默认内容，不导入实体NVS、Wi-Fi、配对令牌、私有备份或真机eFuse；仅允许有明确来源和逐字节检查的合成模拟夹具。

运行参数固定真实ROM、25秒、`--net user,restrict=yes,dns=127.0.0.1`；无hostfwd/TAP/vmnet，不保存guest flash。前后核镜像摘要，模拟复位不称实体设备复位。

`Calling app_main()`可能只是USB wrapper；exit0也可能只是模拟器达到timeout。至少核真实应用`Starting app`，并同时核assert/ESP_ERROR_CHECK/abort/复位。`tools/mosaico_emulator_outcome.py`对入口只给`application_entered_unverified`，从不自动给Runtime/HTTP/UI或硬件通过。

session174为USB DWC2断言/TinyUSB超时，阻塞于真实main前。175为新SDK目标登记缺失/未编译；176整固件编译成功，但宿主ELF校验用了系统Python而失败，未启动模拟器。177用隔离Python接续核验/打包/25秒ROM启动，不重编：已见真实`Starting app`和114资源注册，随后BSP从eFuse USER_DATA读到板型0x0000，返回NOT_SUPPORTED并abort/14次模拟复位，分类`application_entered_then_failed`。Works/HTTP/Runtime未启动，后续HMAC尚未到达。

session178已完成合成模拟板型fixture并实际运行，未重编译。固定S31 SDK的USER_DATA=BLK3 bit0，官方[make-efuse.py固定布局](https://github.com/espressif/esp-emulator/blob/61d71cef2b1f13a936173c6d282a52c093137d6a/tools/make-efuse.py)对应word20/byte80。官方工具生成silicon rev0.0和本地管理模拟MAC基线，helper严格核基线并只改byte81为1（板型0x0100/v1.0）；不代表真机版本。密钥/purpose/安全配置全零，14项定向测试通过。25秒ROM模拟已见Hardware version v1.0，越过板型检查；随后main.c:1126的trial_auth_validate_hmac_efuse_key因key block5/key ID1的purpose0而拒绝（期望HMAC_UP、0x103），13次abort/模拟复位。尚未进行HMAC计算，Works/HTTP/Runtime/点按未启动。分类application_entered_then_failed，不以exit0当成功。

注意：--efuse在退出时会保存状态；本次输入及pristine336B，保存的runtime348B，前336B相同且追加12个零字节。raw changed_bytes=[]仅比较共同前缀，不表示文件整体不变。原始336B夹具单独保留，348B不直接回灌严格夹具工具、不截断或改旧证据。101pins、原22/派生11归档及六tracked不变，真机操作0。四MP4独立终验/实际六帧通过，对应MOV校验后删，净释放360,868,882B、不可直接恢复；原Otty空闲保留、相机预览关闭，发布pending。见[178验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-s31-emulator-efuse-178/验收记录.md)及[独立结果复核](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-s31-emulator-efuse-178/独立结果复核.json)。

session179已按固定SDK公开测试key（字节1–32）生成新独立严格夹具。KEY1=BLK5，S31 purpose bit101宽5/HMAC_UP8；compact文件KEY1=byte144，仅增该key读写及用途写保护。旧board-only helper不放宽，22定向测试PASS。固件/保护未改、无重编，25秒真实ROM模拟已见`eFuse HMAC key ID 1 in block 5 validated`，真实`esp_hmac_calculate()`返回ESP_OK；未读/比较guest digest，不称bit-for-bit或生产服务认证通过。

本轮随后在触摸和NAND失败：No LCD touch on I2C、NAND manufacturer 0xff，main.c:1130的main_install_touch_mux失败，13次abort/模拟复位，仍application_entered_then_failed。Works/HTTP/Runtime/点按未启动，LCD driver create不证明有可见屏幕。113pins/原22/派生11归档及六tracked不变，无实体设备/eFuse/生产密钥操作。pristine336B不变、runtime348B为前缀相同+12零，不回灌。四MP4独立终验/实际六帧通过，MOV校验后删，净释放359,839,598B；原Otty保留、相机预览关闭，发布pending。见[179验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-s31-emulator-hmac-179/验收记录.md)和[独立结果复核](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-s31-emulator-hmac-179/独立结果复核.json)。

下一关核官方S31触摸/NAND模型：板配置8位0xB4被驱动转为7位0x5A，CST9217/9220需真实寄存器/报告/释放语义，不能只给ACK或通用填充值当健康。NAND不是启动NOR镜像，需要独立器件和页/缓存/坏块/文件系统语义。模型不足时与独立host/LVGL测试明确分开，不以stub、跳过外设或空目录宣称整机/真机通过；不反复运行本轮必失败输入。

175–177的12个MP4已完成独立完整解码、大小/SHA、媒体参数与各正式六帧复核，对应MOV校验后删除（净释放4,077,172,652B，不可直接恢复），历史素材未动。终端细字PARTIAL，实体相机Works不是模拟UI；原Otty空闲保留、预览关闭、相关进程退出，隐私发布pending。见[177功能与素材验收](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-s31-emulator-uart-177/验收记录.md)、[独立结果复核](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-s31-emulator-uart-177/独立结果复核.json)及[独立媒体验证](../copis/宣传计划/05-Mosaico实机纪录/EP04-LoomRuntime上传与验证/执行记录/2026-10-27-ep04-s31-emulator-uart-177/独立媒体验证.json)。

每轮遵循AGENTS的原Otty复用、新双路短测/实际六帧门控、独立归档及默认MP4规则。非UI工具启动模拟器时，Otty仅镜像同一原始日志，应如实记录执行位置。源码准备不冒充全程Otty编码录像；发布保持pending。

官方来源：[esp-emulator 0.51.0](https://github.com/espressif/esp-emulator/releases/tag/v0.51.0)、[Mosaico源码](https://github.com/esp-mosaico/esp-mosaico-claw)。当前源码/SDK固定提交及归档摘要见原build01 manifest，不随“latest”漂移。
