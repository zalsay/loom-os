-- Loom OS api/ui.lua
-- Minimal safe LVGL proxy for v0.1 foreground Apps.

local errors = require("core.errors")

local M = {}

local SAFE_CONSTRUCTORS = {
    "object",
    "container",
    "label",
    "button",
    "bar",
    "slider",
    "arc",
    "scale",
    "checkbox",
    "switch",
    "dropdown",
    "roller",
    "keyboard",
    "textarea",
    "list",
    "table",
    "image",
    "line",
    "spinner",
    "buttonmatrix",
    "calendar",
    "canvas",
    "chart",
    "imagebutton",
    "led",
    "menu",
    "spangroup",
    "spinbox",
    "tabview",
    "tileview",
    "window",
}

local function readonly(data, label)
    return setmetatable({}, {
        __index = data,
        __newindex = function()
            error((label or "value") .. " is read-only", 2)
        end,
        __pairs = function() return pairs(data) end,
        __metatable = "locked",
    })
end

local function make_lv_proxy(lvgl)
    local proxy = {}

    for _, name in ipairs(SAFE_CONSTRUCTORS) do
        local ctor = lvgl[name]
        if type(ctor) == "function" then
            proxy[name] = function(parent, opts)
                if parent == nil then
                    error("Loom OS App widgets require an App-owned parent", 2)
                end
                return ctor(parent, opts)
            end
        end
    end

    return readonly(proxy, "ctx.ui.lv")
end

function M.new(lvgl, app_layer, width, height, resources)
    if type(lvgl) ~= "table" or app_layer == nil then
        return nil, errors.new("E_INVALID_ARG", "lvgl and app_layer are required")
    end

    local root = lvgl.container(app_layer, {
        x = 0,
        y = 0,
        w = width,
        h = height,
        bg_opa = 0,
        border_width = 0,
        pad = 0,
    })

    if resources and type(resources.add) == "function" then
        resources:add("ui_objects", root, function(obj)
            local ok, valid = pcall(function() return obj:is_valid() end)
            if ok and valid then
                obj:delete()
            end
            return true
        end)
    end

    return {
        root = root,
        lv = make_lv_proxy(lvgl),
    }
end

return M
