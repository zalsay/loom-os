-- Loom OS ui/launcher.lua
-- Minimal scrollable Launcher for Phase 3/4.

local M = {}
local current_root = nil

function M.show(ui_state, app_records, nav)
    ui_state.app_layer:clean()

    local lv = ui_state.lvgl
    local root = lv.container(ui_state.app_layer, {
        x = 0,
        y = 0,
        w = ui_state.app_width,
        h = ui_state.app_height,
        bg_opa = 0,
        border_width = 0,
        pad = 12,
        pad_row = 10,
        pad_column = 10,
    })
    root:set_flex({
        flow = "row_wrap",
        main = "start",
        cross = "start",
        track = "start",
    })
    root:set_scroll({ dir = "ver", scrollbar = "auto" })

    local settings_button = lv.button(root, {
        text = "设置", w = 138, h = 78,
        bg_color = "#286aa7", text_color = "#ffffff", radius = 12,
    })
    settings_button:on("clicked", function() nav.settings() end)

    for _, record in ipairs(app_records or {}) do
        if record.enabled and record.manifest then
            local button = lv.button(root, {
                text = record.manifest.name,
                w = 138,
                h = 78,
                bg_color = "#26323d",
                text_color = "#ffffff",
                radius = 12,
            })
            button:on("clicked", function()
                nav.open(record.id)
            end)
        end
    end

    if #(app_records or {}) == 0 then
        lv.label(root, {
            text = "No apps installed",
            align = "center",
            text_color = "#c7d0d9",
        })
    end

    current_root = root
    return root
end

function M.root()
    return current_root
end

return M
