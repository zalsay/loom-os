# ClawOS Network Foundation


System-only network primitives shared by Runtime OTA, `ctx.network`, Agent streaming and future Store/resource services.


## Layers


```text
ESP-Claw capabilities / future WebSocket binding
                 ↓
system/net adapters
                 ↓
system/net HTTP / download / WebSocket facade
                 ↓
    ┌────────────┼───────────────┐
    ↓            ↓               ↓
Runtime OTA   ctx.network   Agent / Store
```


## Files


- `system/net/errors.lua` — normalized network errors.
- `system/net/http_client.lua` — stable HTTP facade.
- `system/net/adapters/espclaw_http.lua` — `capability` -> `http_request` adapter.
- `system/net/download.lua` — download + declared-size verification.
- `system/net/websocket_client.lua` — stable WebSocket facade/backend contract.
- `system/net/adapters/espclaw_websocket.lua` — explicit unsupported placeholder until a verified generic ESP-Claw Lua WebSocket binding exists.
- `update/runtime_backend.lua` — Runtime OTA download adapter.


## HTTP backend


ESP-Claw's `http_request` Capability supports URL, method, headers, body, timeout, body limits, file save path and file size limits. Its file mode writes a temporary file and renames it to the requested `save_path` only after the request succeeds.


ClawOS therefore does not implement another HTTP/TLS stack.


`system.net.http_client` normalizes this into:


```lua
http.request(options)
http.get(url, options)
http.post(url, body, options)
http.get_json(url, options)
http.download(options)
```


HTTPS is required by default at the ClawOS layer even though upstream `http_request` can also accept plain HTTP.


## Download validation


`system/net/download.lua` performs only the checks required by the current minimal Runtime OTA design:


- HTTPS transport through ESP-Claw `http_request`;
- requested destination;
- maximum file size;
- declared file-size match when `size` is present.


Cryptographic file hashing is intentionally not part of ClawOS v0.1 Runtime OTA.


## WebSocket


The verified ESP-Claw Lua module catalog does not currently list a generic WebSocket client, although ESP-Claw uses WebSocket internally. ClawOS therefore freezes the public system API now and keeps the wire implementation behind a backend:


```lua
local ws = require("system.net.websocket_client")
local conn = assert(ws.connect({ url = "wss://example.com/ws" }))
conn:on("message", function(message) end)
conn:send_text("hello")
conn:send_json({ type = "ping" })
conn:close()
```


A future ESP-Claw native binding only needs to implement:


```lua
backend.connect(options, emit) -> handle
```


where `handle` provides `send_text`, optional `send_binary`, `close`, and `is_connected`.