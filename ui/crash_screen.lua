-- Loom OS ui/crash_screen.lua

local M = {}

function M.show(ui_state, app_name, err, nav)
    ui_state.app_layer:clean()
    local lv = ui_state.lvgl

    local root = lv.container(ui_state.app_layer, {
        x = 0,
        y = 0,
        w = ui_state.app_width,
        h = ui_state.app_height,
        bg_opa = 0,
        border_width = 0,
        pad = 20,
    })
    root:set_flex({ flow = "column", main = "center", cross = "center" })

    lv.label(root, {
        text = (app_name or "App") .. " stopped",
        text_color = "#ffffff",
    })
    lv.label(root, {
        text = err and err.message or "Unknown error",
        text_color = "#ffb4ab",
    })

    local restart = lv.button(root, { text = "Restart", w = 150, h = 48 })
    restart:on("clicked", function() nav.reload() end)

    local home = lv.button(root, { text = "Home", w = 150, h = 48 })
    home:on("clicked", function() nav.home() end)

    return root
end

return M
