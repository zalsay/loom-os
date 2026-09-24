# 网页阅读器示例

`org.loom-os.web-reader` 将单个静态 HTML 页面转成可滚动的 LVGL 文字视图。启动后先显示内置示例；点击“加载 HTTPS 页面”读取 `main.lua` 中的 `DEFAULT_URL`，也可在启动参数传入 `url` 或 `html`。

支持标题、段落、换行、列表、引用、预格式文字、链接文字及 HTTPS 地址；图片显示 `alt` 替代文字。页面中的脚本、样式、嵌入内容不会执行，也不会下载外部资源。页面上限 32 KiB、80 个文本块，每块最多 2 KiB。

在线加载需要设备提供 loom-os 的非阻塞网络适配器，并为目标域名配置 ESP-Claw `http_allowlist`。App 清单已声明 `network.enabled`；没有适配器时，内置示例仍可查看，加载操作会显示 `E_UNSUPPORTED`。当前例子没有地址栏；修改 `DEFAULT_URL` 即可固定要显示的单个网页。

在仓库根目录运行 `texlua tests/web_reader_test.lua` 检查 HTML 解析与 App 展示流程。设备端 LVGL 字体、滚动和联网能力仍需在 Mosaico 真机上验证。

这是受限的静态网页阅读器，不包含 CSS 排版、JavaScript、表单、图片解码或通用浏览器导航。
