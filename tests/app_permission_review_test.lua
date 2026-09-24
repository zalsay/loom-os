local validator = require("core.app_validator")


local v = validator.new({
    lua_check = function()
        return true
    end,


    api_check = function()
        return true
    end,


    board_check = function()
        return true
    end
})


local draft = {
    manifest = {
        permissions = { sensor = {"soil.moisture"}, network = {enabled = true} }
    },
    files = {}
}


local ok, err = v.validate_approval(draft, {
    permissions = {
        "sensor"
    }
})


assert(ok == nil)
assert(err.code == "E_PERMISSION_APPROVAL")


print("app_permission_review_test: PASS")
