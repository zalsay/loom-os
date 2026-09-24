local installer = require("core.app_installer")


local ok = installer.validate_package({
    manifest = {
        id = "org.loom-os.bad",
        version = "1.0.0",
        entry = "../escape.lua"
    },
    files = {
        { path = "../escape.lua" }
    }
})


assert(ok == nil)


print("app_bad_package_test: PASS")
