return {
    on_create = function(ctx)
        local root, lv = ctx.ui.root, ctx.ui.lv
        root:set_flex({ flow = "column", main = "start", cross = "start" })
        lv.label(root, { text = "Loom OS Diagnostics" })
        local info = ctx.system.info()
        lv.label(root, { text = "Board: " .. tostring(info.board or "unknown") })
        local display = info.display or {}
        lv.label(root, { text = "Display: " .. tostring(display.width) .. "x" .. tostring(display.height) })
        local battery, battery_err = ctx.system.battery()
        lv.label(root, { text = "Battery: " .. tostring(battery and battery.percentage or
            (battery_err and battery_err.code or "unavailable")) })
        local names = {}
        for _, sensor in ipairs(ctx.sensor.list()) do names[#names + 1] = sensor.id end
        lv.label(root, { text = "Sensors: " .. (#names > 0 and table.concat(names, ", ") or "driver unavailable") })
    end,
}
