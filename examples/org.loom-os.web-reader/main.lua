local html_reader = require("html_reader")

local DEFAULT_URL = "https://example.com"
local function valid_https_url(url)
    if type(url) ~= "string" or #url > 512 or url:find("[%s%c]") then return false end
    local authority = url:match("^https://([^/%?#]+)")
    if not authority then return false end
    local host, port = authority:match("^([%w%.%-]+):(%d+)$")
    if not host then host = authority end
    if not host:match("^[%w][%w%.%-]*[%w]$") or not host:find("%.") then return false end
    if port and (tonumber(port) < 1 or tonumber(port) > 65535) then return false end
    return authority == host or port ~= nil
end
local SAMPLE_HTML = [[
<!doctype html>
<html lang="zh">
<head><title>网页阅读器示例</title><style>body { color: red; }</style></head>
<body>
  <h1>欢迎使用 Loom OS 网页阅读器</h1>
  <p>这是一个<em>静态 HTML</em>页面。标题、段落、列表和链接会变成可滚动的 LVGL 文字。</p>
  <h2>支持的内容</h2>
  <ul><li>中文与英文文字</li><li>HTML 实体，例如 &amp; 和 &#9733;</li></ul>
  <p><a href="https://example.com">示例链接</a>；图片显示替代文字：<img alt="示意图" src="image.png"></p>
  <script>window.alert("This script is not executed");</script>
</body>
</html>
]]

return {
    on_create = function(ctx, args)
        args = args or {}
        local lv, root = ctx.ui.lv, ctx.ui.root
        root:set_style({ bg_color = "#101820", bg_opa = 255, pad = 18, pad_row = 10 })
        root:set_flex({ flow = "column", main = "start", cross = "start" })
        root:set_scroll({ dir = "ver", scrollbar = "auto" })

        lv.label(root, {
            text = "网页阅读器", w = 420, text_color = "#ffffff",
        })
        local load_button = lv.button(root, {
            text = "加载 HTTPS 页面", w = 210, h = 48,
            bg_color = "#286aa7", text_color = "#ffffff",
        })
        local status = lv.label(root, {
            text = "本地 HTML 示例", w = 420, text_color = "#9db8cb",
        })
        local rendered = {}
        local pending, generation = nil, 0

        local function clear_page()
            for _, widget in ipairs(rendered) do
                if widget:is_valid() then widget:delete() end
            end
            rendered = {}
        end

        local function render(html)
            local page, err = html_reader.parse(html)
            if not page then
                status:set_text("无法显示：" .. tostring(err))
                return false
            end
            clear_page()
            if page.title ~= "" then
                rendered[#rendered + 1] = lv.label(root, {
                    text = page.title, w = 420, text_color = "#86cdfa",
                })
            end
            for _, block in ipairs(page.blocks) do
                local color = "#e7edf1"
                if block.kind:match("^h[1-6]$") then color = "#8bd4ff"
                elseif block.kind == "li" then color = "#c7e7cb"
                elseif block.kind == "quote" then color = "#b6b1dd"
                elseif block.kind == "rule" then color = "#647484" end
                rendered[#rendered + 1] = lv.label(root, {
                    text = block.text, w = 420, text_color = color,
                })
            end
            status:set_text(page.truncated and "页面过长，已截取部分内容" or
                ("已显示 " .. tostring(#page.blocks) .. " 个文本块"))
            return true
        end

        render(type(args.html) == "string" and args.html or SAMPLE_HTML)

        load_button:on("clicked", function()
            local url = type(args.url) == "string" and args.url or DEFAULT_URL
            if not valid_https_url(url) then
                status:set_text("请输入有效的 HTTPS 地址")
                return
            end
            generation = generation + 1
            local request_generation = generation
            if pending then ctx.network.cancel(pending); pending = nil end
            status:set_text("正在加载 " .. url)
            local id, err = ctx.network.request({
                method = "GET", url = url, max_body_bytes = 32768,
            }, function(response, request_err)
                if request_generation ~= generation then return end
                pending = nil
                if request_err or not response or response.status ~= 200
                    or type(response.body) ~= "string" then
                    status:set_text("加载失败：" .. tostring(request_err and request_err.code
                        or response and response.status or "无响应"))
                    return
                end
                render(response.body)
            end)
            if not id then
                status:set_text("网络不可用：" .. tostring(err and err.code or "E_UNSUPPORTED"))
            else
                pending = id
            end
        end)

        return true
    end,
}
