local json = require("json")
local http = require("system.net.http_client")
local client = require("update.release_client")


local function release(version, channel, board, min_bootstrap)
    return {
        schema = 1,
        product = "clawos",
        board = board or "esp-mosaico",
        channel = channel or "stable",
        version = version,
        release_id = "clawos:" .. (board or "esp-mosaico") .. ":" .. version,
        entry = "main.lua",
        min_bootstrap = min_bootstrap or "0.1.0",
        files = {
            {
                path = "main.lua",
                url = "https://updates.example.com/clawos/" .. version .. "/main.lua",
                size = 100,
            },
        },
    }
end


local mode = "no_update"


http.set_adapter({
    request = function(options)
        assert(options.url:match("^https://updates%.example%.com/v1/clawos/releases/latest"))
        assert(options.url:find("bootstrap=0.1.0", 1, true))
        if mode == "no_update" then
            return { status = 204, body = "" }
        elseif mode == "new" then
            return { status = 200, body = json.encode(release("0.1.1")) }
        elseif mode == "equal" then
            return { status = 200, body = json.encode(release("0.1.0")) }
        elseif mode == "wrong_board" then
            return { status = 200, body = json.encode(release("0.1.1", "stable", "other-board")) }
        elseif mode == "bootstrap" then
            return { status = 200, body = json.encode(release("0.1.1", "stable", "esp-mosaico", "0.2.0")) }
        end
        error("unknown test mode")
    end,
})


local base = {
    base_url = "https://updates.example.com",
    board = "esp-mosaico",
    channel = "stable",
    current_version = "0.1.0",
    bootstrap_version = "0.1.0",
}


local result = assert(client.latest(base))
assert(result.available == false)


mode = "new"
result = assert(client.latest(base))
assert(result.available == true)
assert(result.release.version == "0.1.1")


mode = "equal"
assert(client.latest(base) == nil)


mode = "wrong_board"
assert(client.latest(base) == nil)


mode = "bootstrap"
assert(client.latest(base) == nil)


local missing_bootstrap = {
    base_url = base.base_url,
    board = base.board,
    channel = base.channel,
    current_version = base.current_version,
}
assert(client.latest(missing_bootstrap) == nil)


http.set_adapter(nil)
print("release_client_test: PASS")