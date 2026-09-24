return {
    on_create = function(ctx, args)
        local lv = ctx.ui.lv
        local root = ctx.ui.root


        root:set_flex({
            flow = "column",
            main = "center",
            cross = "center",
        })


        lv.label(root, {
            text = "Hello Loom OS",
            text_color = "#ffffff",
        })


        local home = lv.button(root, {
            text = "Home",
            w = 160,
            h = 48,
        })


        home:on("clicked", function()
            ctx.nav.home()
        end)
    end,
}