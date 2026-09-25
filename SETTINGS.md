# Loom OS 系统设置

启动器内置“设置”入口，由 `ui/settings.lua` 显示，`core/settings.lua` 验证并保存设置。普通 App 不会收到直接修改系统设置的 API。深浅主题在系统层立即生效，保存在 DATA 根目录下的 `loom-os/state/settings.json`。

## Wi-Fi

设置页通过 ESP-Claw 的原生 `system.info()` 和 `system.ip()` 读取 SSID、连接状态和 IP（前提是固件编入 `system` Lua 模块）。当前 Mosaico 固件尚无经验证的 Lua Wi-Fi 配置绑定，设置页会引导用户连接设备热点，在 ESP-Claw Web Console（`http://esp-claw.local/` 或设备的 IP）配置 SSID/密码，随后重启。Loom OS 不把 Wi-Fi 密码写入 `settings.json` 或 App 数据。未来固件提供受控连接接口后，系统可调用 `settings.connect_wifi(ssid, password)`；需要同时补齐可读取输入内容的受支持 LVGL 控件绑定和现场测试。

## 屏幕与声音

主题无需设备驱动。亮度、音量的 5–100% 与 0–100% 控件仅在提供者可用时出现；未接入时显示明确说明，不保存虚假的硬件值。屏幕亮度必须由 Mosaico 面板驱动或固件提供控制方法。音量应接入持有共享音频输出对象的系统服务，避免设置页另开 codec 与播放服务争用设备。

将经过真机验证的提供者作为 `settings.configure(paths, hooks)` 的第二参数注入：

```lua
{
  theme = ui_runtime.set_theme,
  display = { set_brightness = function(percent) ...; return true end },
  audio = { set_volume = function(percent) ...; return true end },
  wifi = {
    status = function() return { connected = true, ssid = "...", ip = "..." } end,
    connect = function(ssid, password) ...; return true end,
  },
}
```

设备回调应尽快返回，Wi-Fi 连接不能阻塞 LVGL 主循环。`theme` 与只读 Wi-Fi 状态当前已接入 `main.lua`；其他回调等待固件绑定和 Mosaico 真机验证。系统不会把这些写操作暴露给普通 App。

在仓库根目录运行 `texlua tests/settings_test.lua`。真机需要检查：主题切换与重启恢复；无提供者时的界面状态；接入后的亮度/音量实际变化和重启恢复；Wi-Fi 连接、失败回退，以及密码不落入 loom-os 的文件或远程日志。
