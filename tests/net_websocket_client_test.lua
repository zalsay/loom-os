local ws = require("system.net.websocket_client")

local emitted
ws.set_backend({
    connect = function(options, emit)
        emitted = emit
        local handle = { connected = true }
        function handle:send_text(text)
            self.last_text = text
            return true
        end
        function handle:send_binary(data)
            self.last_binary = data
            return true
        end
        function handle:is_connected()
            return self.connected
        end
        function handle:close()
            self.connected = false
            return true
        end
        return handle
    end,
})

local conn = assert(ws.connect({ url = "wss://example.test/ws" }))
local opened = false
local message
conn:on("open", function() opened = true end)
conn:on("message", function(v) message = v end)

emitted("open")
emitted("message", "hello")
assert(opened == true)
assert(message == "hello")
assert(conn:is_connected())
assert(conn:send_json({ type = "ping" }))
assert(conn:close())

print("net_websocket_client_test: PASS")
