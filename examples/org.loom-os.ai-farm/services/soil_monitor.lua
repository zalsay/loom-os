return {
    on_start = function(ctx)
        ctx.storage.mkdir("soil")
        local function sample()
            local value = ctx.sensor.read("soil.moisture")
            if not value then return end -- no unverified native driver is assumed
            local measurement = { value = value, timestamp_ms = ctx.system.now_ms() }
            ctx.storage.write_json("soil/latest.json", measurement)
            ctx.notify.show({ title = "AI Farm", message = "Soil reading recorded" })
            ctx.agent.ask("Analyze soil moisture " .. tostring(value), function(result)
                if result and result.text then
                    ctx.storage.write_json("soil/analysis.json", { text = result.text })
                end
            end)
        end
        sample()
        ctx.timer.every(60000, sample)
    end,
}
