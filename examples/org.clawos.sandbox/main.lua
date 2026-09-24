local greeting = require("greeting")

return {
    on_create = function(ctx, args)
        assert(io == nil)
        assert(os == nil)
        assert(debug == nil)
        print(greeting.text(ctx.app.name))
    end,
}
