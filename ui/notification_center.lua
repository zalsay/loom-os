-- Loom OS ui/notification_center.lua
-- Minimal system-owned notification banner renderer.

local notifications = require("core.notifications")

local M = {}
local current = nil

local function remove_current()
    if current and current.root and current.root:is_valid() then
        current.root:delete()
    end
    current = nil
end

local function show(ui_state, item)
    remove_current()

    local lv = ui_state.lvgl
    local width = math.max(120, ui_state.width - 24)
    local root = lv.container(ui_state.screen, {
        x = 12,
        y = ui_state.status_height + 8,
        w = width,
        h = 72,
        bg_color = "#202830",
        border_width = 1,
        pad = 8,
    })
    root:set_flex({ flow = "column", main = "start", cross = "start" })

    lv.label(root, {
        text = item.title or "Loom OS",
        text_color = "#ffffff",
    })
    lv.label(root, {
        text = item.message,
        text_color = "#ffffff",
        long_mode = "wrap",
        w = width - 16,
    })

    current = { id = item.id, root = root }
end

function M.process(ui_state)
    for _, action in ipairs(notifications.drain_actions()) do
        if action.type == "show" then
            show(ui_state, action.item)
        elseif action.type == "dismiss" and current and current.id == action.id then
            remove_current()
        end
    end
end

function M.clear()
    remove_current()
end

return M
