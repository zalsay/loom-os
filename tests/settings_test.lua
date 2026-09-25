local files, values, next_json = {}, {}, 0
package.preload.storage = function()
    return {
        join_path = function(a, b) return a .. "/" .. b end,
        exists = function(path) return files[path] ~= nil end,
        read_file = function(path) return files[path] end,
        write_file = function(path, data) files[path] = data; return true end,
    }
end
package.preload.json = function()
    return {
        encode = function(value)
            next_json = next_json + 1
            local key = "@json:" .. next_json
            values[key] = value
            return key
        end,
        decode = function(text) return assert(values[text]) end,
    }
end

local settings = require("core.settings")
local state = "state/settings.json"
assert(settings.configure({state="state"}))
assert(settings.snapshot().theme == "dark")
local changed, err = settings.set_brightness(70)
assert(changed == nil and err.code == "E_UNSUPPORTED" and files[state] == nil)
changed, err = settings.set_volume(120)
assert(changed == nil and err.code == "E_INVALID_ARG")
assert(settings.set_theme("light"))
assert(values[files[state]].theme == "light")

local applied, secrets = {}, {}
local hooks = {
    theme = function(theme) applied.theme = theme; return true end,
    display = { set_brightness = function(value) applied.brightness = value; return true end },
    audio = { set_volume = function(value) applied.volume = value; return true end },
    wifi = {
        status = function() return {connected=true, ssid="Classroom", ip="192.168.1.8"} end,
        connect = function(ssid, password) secrets.ssid, secrets.password = ssid, password; return true end,
    },
}
assert(settings.configure({state="state"}, hooks))
assert(applied.theme == "light")
assert(settings.set_brightness(65))
assert(settings.set_volume(0))
assert(settings.snapshot().brightness == 65 and settings.snapshot().volume == 0)
assert(settings.wifi_status().ssid == "Classroom")
assert(settings.connect_wifi("Classroom", "password123"))
assert(secrets.password == "password123" and values[files[state]].password == nil)
assert(settings.connect_wifi("Classroom", "short") == nil)
assert(settings.configure({state="state"}, hooks))
assert(applied.brightness == 65 and applied.volume == 0)

package.preload.system = function()
    return { info = function() return {wifi_ssid="Classroom", wifi_rssi=-48} end,
        ip = function() return "192.168.1.8" end }
end
local native_wifi = require("system.settings_status").wifi_status()
assert(native_wifi.connected and native_wifi.ssid == "Classroom" and native_wifi.ip == "192.168.1.8")

local widgets = {}
local function widget(parent, opts)
    local value = { text = opts.text or "", style = opts, children = {} }
    widgets[#widgets+1] = value
    if parent then parent.children[#parent.children+1] = value end
    function value:set_style(style) for k, v in pairs(style) do self.style[k] = v end end
    function value:set_flex() end
    function value:set_scroll() end
    function value:set_text(text) self.text = text end
    function value:clean() self.children = {} end
    function value:on(name, callback) assert(name == "clicked"); self.click = callback end
    return value
end
local layer = widget(nil, {})
local nav = {home = function() applied.home = true end}
local ui = { app_layer = layer, app_width=480, app_height=448,
    lvgl = {container=widget,label=widget,button=widget} }
local screen = require("ui.settings").show(ui, settings, nav)
assert(screen and #screen.children > 6)
local found_wifi, found_theme = false, false
for _, child in ipairs(screen.children) do
    if child.text:find("Classroom", 1, true) then found_wifi = true end
    if child.text == "切换深色 / 浅色主题" then child.click(); found_theme = true end
end
assert(found_wifi and found_theme and settings.snapshot().theme == "dark")

local launcher = require("ui.launcher")
local launcher_root = launcher.show(ui, {}, {settings = function() applied.open_settings = true end})
for _, child in ipairs(launcher_root.children) do
    if child.text == "设置" then child.click() end
end
assert(applied.open_settings)

local navigation = require("core.navigation")
navigation.set_handler(function(action) applied.action = action.type; return true end)
assert(require("api.nav").new().settings())
assert(navigation.process_next())
assert(applied.action == "settings")
print("settings_test: PASS")
