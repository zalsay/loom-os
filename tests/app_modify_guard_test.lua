local app_author = require("core.app_author")


local deps = {}


deps.agent = {
    generate_app = function()
        return {
            manifest = {
                id = "org.loom-os.changed-id",
                name = "Bad Modify",
                version = "1.1.0",
                entry = "main.lua"
            },
            files = {
                {
                    path = "main.lua",
                    content = "return true"
                }
            }
        }
    end
}


deps.workspace = {
    read_active_app = function(app_id)
        return {
            manifest = {
                id = app_id,
                version = "1.0.0"
            },
            files = {}
        }
    end
}


deps.validator = {}
deps.app_update = {}


local author = app_author.new(deps)


local result, err = author.modify(
    "org.loom-os.original",
    {
        prompt = "Change the UI"
    }
)


assert(result == nil)
assert(err.code == "E_AUTHOR_ID_CHANGE")


print("app_modify_guard_test: PASS")
