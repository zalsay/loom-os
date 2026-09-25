-- System Settings screen. Hardware changes stay behind core.settings providers.
local M = {}

function M.show(ui, settings, nav)
    ui.app_layer:clean()
    local lv = ui.lvgl
    local light = settings.snapshot().theme == "light"
    local root = lv.container(ui.app_layer, {
        x = 0, y = 0, w = ui.app_width, h = ui.app_height,
        bg_color = light and "#f5f7fa" or "#101820",
        border_width = 0, pad = 16, pad_row = 10,
    })
    root:set_flex({ flow = "column", main = "start", cross = "start" })
    root:set_scroll({ dir = "ver", scrollbar = "auto" })

    local width = math.max(180, ui.app_width - 40)
    local labels = {}
    local function label(text, muted)
        local widget = lv.label(root, { text = text, w = width,
            text_color = light and (muted and "#43596a" or "#142638") or
                (muted and "#c5d5e2" or "#ffffff") })
        labels[#labels + 1] = { widget = widget, muted = muted }
        return widget
    end
    local status = lv.label(root, { text = "", w = width,
        text_color = light and "#175480" or "#9bd3ff" })
    local function message(ok, err, success)
        status:set_text(ok and success or (err and err.message or "设置失败"))
    end

    local back = lv.button(root, { text = "返回桌面", w = 160, h = 44 })
    back:on("clicked", function() nav.home() end)

    label("Wi-Fi")
    local wifi_label = label("正在读取网络状态", true)
    local function refresh_wifi()
        local info = settings.wifi_status()
        if not info then
            wifi_label:set_text("连接设备热点后打开 http://esp-claw.local/ 配置 Wi-Fi；若无法解析，请使用设备显示的 IP。更改后重启设备。")
        elseif info.connected then
            wifi_label:set_text("已连接：" .. tostring(info.ssid or "Wi-Fi") ..
                (info.ip and "  " .. tostring(info.ip) or ""))
        else
            wifi_label:set_text("未连接；可通过 ESP-Claw Web Console 配网。")
        end
    end
    local refresh = lv.button(root, { text = "刷新网络状态", w = 180, h = 44 })
    refresh:on("clicked", refresh_wifi)
    refresh_wifi()

    label("屏幕")
    local theme = lv.button(root, { text = "切换深色 / 浅色主题", w = 240, h = 44 })
    theme:on("clicked", function()
        local next_theme = settings.snapshot().theme == "dark" and "light" or "dark"
        local ok, err = settings.set_theme(next_theme)
        if ok then
            light = next_theme == "light"
            root:set_style({ bg_color = next_theme == "light" and "#f5f7fa" or "#101820" })
            for _, entry in ipairs(labels) do
                entry.widget:set_style({ text_color = light and
                    (entry.muted and "#43596a" or "#142638") or
                    (entry.muted and "#c5d5e2" or "#ffffff") })
            end
            status:set_style({ text_color = light and "#175480" or "#9bd3ff" })
        end
        message(ok, err, ok and ("主题已设为" .. (next_theme == "dark" and "深色" or "浅色")))
    end)

    local screen = settings.snapshot()
    local brightness = label("", true)
    local function refresh_brightness()
        local current = settings.snapshot()
        brightness:set_text(current.brightness_available and
            ("亮度：" .. (current.brightness and tostring(current.brightness) .. "%" or "设备默认")) or
            "亮度：此固件尚未提供屏幕调节接口")
    end
    refresh_brightness()
    if screen.brightness_available then
        for _, delta in ipairs({ -10, 10 }) do
            local button = lv.button(root, {
                text = delta < 0 and "降低亮度" or "提高亮度", w = 160, h = 44,
            })
            button:on("clicked", function()
                local value = settings.snapshot().brightness or 50
                local ok, err = settings.set_brightness(math.max(5, math.min(100, value + delta)))
                message(ok, err, "亮度已更新")
                refresh_brightness()
            end)
        end
    end

    label("声音")
    local volume = label("", true)
    local function refresh_volume()
        local current = settings.snapshot()
        volume:set_text(current.volume_available and
            ("音量：" .. (current.volume and tostring(current.volume) .. "%" or "设备默认")) or
            "音量：此固件尚未提供共享音频调节接口")
    end
    refresh_volume()
    if screen.volume_available then
        for _, delta in ipairs({ -10, 10 }) do
            local button = lv.button(root, {
                text = delta < 0 and "降低音量" or "提高音量", w = 160, h = 44,
            })
            button:on("clicked", function()
                local value = settings.snapshot().volume or 50
                local ok, err = settings.set_volume(math.max(0, math.min(100, value + delta)))
                message(ok, err, "音量已更新")
                refresh_volume()
            end)
        end
    end
    return root
end

return M
