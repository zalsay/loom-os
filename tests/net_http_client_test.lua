local http = require("system.net.http_client")

local calls = {}
http.set_adapter({
    request = function(options)
        calls[#calls + 1] = options
        return { status = 200, body = '{"ok":true}', bytes = 11 }
    end,
})

local value, response = assert(http.get_json("https://example.test/status"))
assert(value.ok == true)
assert(response.status == 200)
assert(calls[1].method == "GET")

local bad, err = http.get("http://example.test/plain")
assert(bad == nil and err.code == "E_TLS")

print("net_http_client_test: PASS")
