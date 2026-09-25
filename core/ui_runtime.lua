-- Loom OS core/ui_runtime.lua
-- Owns the single LVGL runtime, root screen, App layer and system bar.


local board_manager = require("board_manager")
local lvgl = require("lvgl")
local errors = require("core.errors")


local M = {}


local state = {
    initialized = false,
    touch_registered = false,
}


local function init_device(name, required)
    local call_ok, result, err = pcall(board_manager.init_device, name)
    if not call_ok then
        if required then
            return nil, errors.new("E_IO", "board_manager.init_device failed", {
                device = name,
                cause = tostring(result),
            })
        end
        return false
    end
    if result ~= true then
        if required then
            return nil, errors.new("E_IO", "board device init failed", {
                device = name,
                cause = err,
            })
        end
        return false
    end
    return true
end


function M.init(options)
    options = options or {}
    if state.initialized then
        return state
    end


    local display_device = options.display_device or "display_lcd"
    local touch_device = options.touch_device or "lcd_touch"


    local display_ok, display_err = init_device(display_device, true)
    if not display_ok then return nil, display_err end


    local params_ok, panel_handle, io_handle, width, height, panel_if =
        pcall(board_manager.get_display_lcd_params, display_device)


    if not params_ok or not panel_handle or not width or not height then
        return nil, errors.new("E_IO", "display parameters are unavailable", {
            device = display_device,
        })
    end


    if options.expected_width and width ~= options.expected_width then
        return nil, errors.new("E_VERSION", "unexpected display width", {
            expected = options.expected_width,
            actual = width,
        })
    end
    if options.expected_height and height ~= options.expected_height then
        return nil, errors.new("E_VERSION", "unexpected display height", {
            expected = options.expected_height,
            actual = height,
        })
    end


    local ok, init_err = pcall(lvgl.init,
        panel_handle,
        io_handle,
        width,
        height,
        panel_if,
        {
            buffer_lines = options.buffer_lines or 40,
            tick_ms = options.tick_ms or 5,
            task_period_ms = options.task_period_ms or 10,
        }
    )
    if not ok then
        return nil, errors.new("E_IO", "lvgl.init failed", { cause = tostring(init_err) })
    end


    local touch_required = options.require_touch ~= false
    local touch_init, touch_init_err = init_device(touch_device, touch_required)
    if not touch_init and touch_required then
        pcall(lvgl.deinit)
        return nil, touch_init_err
    end


    if touch_init then
        local touch_ok, touch_handle = pcall(board_manager.get_lcd_touch_handle, touch_device)
        if touch_ok and touch_handle then
            local reg_ok, reg_result = pcall(lvgl.indev_register, "touch", touch_handle)
            state.touch_registered = reg_ok and reg_result ~= false
        elseif touch_required then
            pcall(lvgl.deinit)
            return nil, errors.new("E_IO", "touch handle is unavailable", {
                device = touch_device,
            })
        end
    end


    local screen = lvgl.create_screen()
    screen:set_style({ bg_color = options.bg_color or "#101418" })


    local status_h = options.status_height or 32
    local app_h = height - status_h


    local app_layer = lvgl.container(screen, {
        x = 0,
        y = status_h,
        w = width,
        h = app_h,
        bg_opa = 0,
        border_width = 0,
        pad = 0,
    })
    app_layer:set_scroll({ dir = "none" })


    local system_bar = lvgl.container(screen, {
        x = 0,
        y = 0,
        w = width,
        h = status_h,
        bg_color = options.system_bar_color or "#182028",
        border_width = 0,
        pad = 4,
    })


    local title = lvgl.label(system_bar, {
        text = "Loom OS",
        align = "left_mid",
        x = 8,
        text_color = "#ffffff",
    })


    screen:load()


    state.initialized = true
    state.lvgl = lvgl
    state.screen = screen
    state.app_layer = app_layer
    state.system_bar = system_bar
    state.title = title
    state.width = width
    state.height = height
    state.app_width = width
    state.app_height = app_h
    state.status_height = status_h
    state.display_device = display_device
    state.touch_device = touch_device


    return state
end


function M.clear_app_layer()
    if state.app_layer then
        state.app_layer:clean()
    end
end


function M.process_events(ms)
    return lvgl.process_events(ms or 20)
end


function M.set_title(text)
    if state.title and state.title:is_valid() then
        state.title:set_text(text or "Loom OS")
    end
end

function M.set_theme(theme)
    if not state.initialized then return false end
    local light = theme == "light"
    state.screen:set_style({ bg_color = light and "#f5f7fa" or "#101418" })
    state.system_bar:set_style({ bg_color = light and "#d8e5f0" or "#182028" })
    state.title:set_style({ text_color = light and "#142638" or "#ffffff" })
    return true
end


function M.shutdown()
    if not state.initialized then
        return true
    end


    if state.touch_registered then
        pcall(lvgl.indev_unregister, "touch")
    end
    pcall(lvgl.deinit)


    if state.touch_device then
        pcall(board_manager.deinit_device, state.touch_device)
    end
    if state.display_device then
        pcall(board_manager.deinit_device, state.display_device)
    end


    state = {
        initialized = false,
        touch_registered = false,
    }
    return true
end


function M.state()
    return state
end


return M
