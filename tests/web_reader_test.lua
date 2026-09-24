package.path = "examples/org.loom-os.web-reader/lib/?.lua;" .. package.path

local reader = require("html_reader")
local page = assert(reader.parse([[
<!doctype html><html><head><title>A &amp; B</title><style>.x { display: none }</style></head>
<body><!-- comment --><h1>Hello &#9733;</h1>
<p>One <strong>two</strong> <a HREF="https://example.com/a?x=1&amp;y=2">link</a><br>next</p>
<ol><li>First</li><li>Second</li></ol>
<img alt="Picture" src="https://example.com/img.png">
<script>window.alert("must not run");</script></body></html>
]]))
assert(page.title == "A & B")
assert(page.blocks[1].kind == "h1" and page.blocks[1].text == "Hello ★")
assert(page.blocks[2].text:find("https://example.com/a?x=1&y=2", 1, true))
assert(page.blocks[3].text == "1. First" and page.blocks[4].text == "2. Second")
assert(page.blocks[5].text == "[图片：Picture]")
for _, block in ipairs(page.blocks) do
    assert(not block.text:find("window.alert", 1, true))
    assert(not block.text:find("display: none", 1, true))
end
local plain = assert(reader.parse("<p>1 < 2 and 3 > 1 &unknown; &#x4E2D;</p>"))
assert(plain.blocks[1].text == "1 < 2 and 3 > 1 &unknown; 中")
assert(reader.parse(string.rep("x", 32769)) == nil)
local many = assert(reader.parse(string.rep("<p>paragraph</p>", 100)))
assert(#many.blocks == 80 and many.truncated)
local long_title = assert(reader.parse("<title>" .. string.rep("中", 1000) .. "</title>"))
assert(long_title.truncated and #long_title.title <= 2051)

local function widget(parent, opts)
    local value = { text = opts and opts.text or "", valid = true, children = {} }
    if parent then parent.children[#parent.children + 1] = value end
    function value:set_style() end
    function value:set_flex() end
    function value:set_scroll() end
    function value:set_text(text) self.text = text end
    function value:is_valid() return self.valid end
    function value:delete() self.valid = false end
    function value:on(event, callback)
        assert(event == "clicked")
        self.click = callback
    end
    return value
end

local root = widget()
local button, network_call
local ctx = {
    ui = {
        root = root,
        lv = {
            label = widget,
            button = function(parent, opts)
                button = widget(parent, opts)
                return button
            end,
        },
    },
    network = {
        request = function(options, callback)
            assert(options.url == "https://example.com/page")
            assert(options.max_body_bytes == 32768)
            network_call = callback
            return 7
        end,
        cancel = function() return true end,
    },
}
local app = dofile("examples/org.loom-os.web-reader/main.lua")
assert(app.on_create(ctx, { url = "https://example.com/page" }))
local old_heading = root.children[4]
assert(old_heading.text == "网页阅读器示例")
button.click()
assert(network_call)
network_call({ status = 200, body = "<title>Online</title><h2>Loaded</h2><p>It works</p>" })
assert(not old_heading:is_valid())
local found = false
for _, child in ipairs(root.children) do
    if child.valid and child.text == "Loaded" then found = true end
end
assert(found, "HTML response was not rendered")
network_call = nil
ctx.network.request = function() error("invalid URL reached network adapter") end
local previous_children = #root.children
assert(app.on_create(ctx, { url = "https://example.com@evil.test/" }))
local invalid_status = root.children[previous_children + 3]
button.click()
assert(network_call == nil)
assert(invalid_status.text == "请输入有效的 HTTPS 地址")
ctx.network.request = function() return nil, { code = "E_UNSUPPORTED" } end
previous_children = #root.children
assert(app.on_create(ctx, { url = "https://example.com/page" }))
local unavailable_status = root.children[previous_children + 3]
button.click()
assert(unavailable_status.text == "网络不可用：E_UNSUPPORTED")
print("web_reader_test: PASS")
