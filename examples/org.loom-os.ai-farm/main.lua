return {
    on_create = function(ctx)
        local root, lv = ctx.ui.root, ctx.ui.lv
        root:set_flex({ flow = "column", main = "start", cross = "start" })
        lv.label(root, { text = "AI Farm" })
        local reading = lv.label(root, { text = "Waiting for soil sensor" })
        local function refresh()
            local data = ctx.storage.read_json("soil/latest.json")
            if data then reading:set_text("Soil: " .. tostring(data.value)) end
        end
        refresh()
        ctx.timer.every(5000, refresh)
        if not ctx.service.status("soil-monitor") then
            local started, err = ctx.service.start("soil-monitor")
            if not started then
                lv.label(root, { text = "Monitor: " .. tostring(err and err.code or "unavailable") })
            end
        end
    end,
}
