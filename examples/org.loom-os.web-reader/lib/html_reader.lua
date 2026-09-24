-- Small, text-first HTML reader for the Loom OS Web Reader App.
-- No CSS layout, script execution, resource fetching, or native modules.
local M = {}

local MAX_HTML = 32768
local MAX_BLOCKS = 80
local MAX_BLOCK_BYTES = 2048

local named_entities = {
    amp = "&", lt = "<", gt = ">", quot = '"', apos = "'",
    nbsp = " ", mdash = "—", ndash = "–", hellip = "…",
}

local function entities(text)
    return (text:gsub("&([#%w]+);", function(name)
        if named_entities[name] then return named_entities[name] end
        local number = name:match("^#[xX]([%x]+)$")
        if number then number = tonumber(number, 16)
        else
            local decimal = name:match("^#([0-9]+)$")
            if decimal then number = tonumber(decimal, 10) end
        end
        if number and number > 0 and number <= 0x10ffff
            and not (number >= 0xd800 and number <= 0xdfff) then
            local ok, value = pcall(utf8.char, number)
            if ok then return value end
        end
        return "&" .. name .. ";"
    end))
end

local function trim(text)
    return (text:gsub("^%s+", ""):gsub("%s+$", ""))
end

local function attribute(tag, name)
    local _, finish = tag:lower():find("%s" .. name .. "%s*=%s*")
    if not finish then return nil end
    local source = tag:sub(finish + 1)
    local value = source:match('^"([^"]*)"')
        or source:match("^'([^']*)'")
        or source:match("^([^%s>]+)")
    return value and entities(value)
end

local function tag_end(html, start)
    local quote
    for i = start + 1, #html do
        local char = html:sub(i, i)
        if quote then
            if char == quote then quote = nil end
        elseif char == "'" or char == '"' then
            quote = char
        elseif char == ">" then
            return i
        end
    end
end

local block_tags = {
    p = true, div = true, section = true, article = true, header = true,
    footer = true, main = true, tr = true,
}
local ignored_tags = {
    script = true, style = true, noscript = true, iframe = true,
    svg = true, object = true, template = true,
}

function M.parse(html)
    if type(html) ~= "string" then return nil, "HTML must be text" end
    if #html > MAX_HTML then return nil, "HTML exceeds 32 KiB" end

    local blocks, parts = {}, {}
    local kind, title = "p", ""
    local in_head, in_title, in_pre = false, false, false
    local list, number, link = nil, 0, nil
    local truncated = false

    local function flush()
        local content = table.concat(parts)
        parts = {}
        if not in_pre then
            content = content:gsub("[ \t]+", " "):gsub(" *\n *", "\n")
        end
        content = trim(content)
        if content == "" then return end
        if #blocks >= MAX_BLOCKS then truncated = true; return end
        if #content > MAX_BLOCK_BYTES then
            content = content:sub(1, MAX_BLOCK_BYTES)
            local _, invalid = utf8.len(content)
            if invalid then content = content:sub(1, invalid - 1) end
            content = content .. "…"
            truncated = true
        end
        blocks[#blocks + 1] = { kind = kind, text = content }
    end

    local function append(raw)
        if raw == "" then return end
        local content = entities(raw)
        if in_title then
            title = title .. content
        elseif not in_head then
            if not in_pre then content = content:gsub("%s+", " ") end
            parts[#parts + 1] = content
        end
    end

    local lower = html:lower()
    local pos = 1
    while pos <= #html do
        local start = html:find("<", pos, true)
        if not start then append(html:sub(pos)); break end
        append(html:sub(pos, start - 1))

        if html:sub(start, start + 3) == "<!--" then
            local finish = html:find("-->", start + 4, true)
            if not finish then break end
            pos = finish + 3
        else
            local finish = tag_end(html, start)
            if not finish then append(html:sub(start)); break end
            local raw = html:sub(start, finish)
            local name = raw:match("^<%s*/?%s*([%a][%w]*)")
            if not name then
                if not raw:match("^<%s*[!?]") then append(raw) end
                pos = finish + 1
            else
                name = name:lower()
                local closing = raw:match("^<%s*/") ~= nil
                pos = finish + 1

                if ignored_tags[name] and not closing then
                    local close_start = lower:find("</" .. name, pos, true)
                    if not close_start then break end
                    local close_end = tag_end(html, close_start)
                    if not close_end then break end
                    pos = close_end + 1
                elseif name == "head" then
                    in_head = not closing
                elseif name == "title" then
                    in_title = not closing
                elseif not in_head then
                    if name:match("^h[1-6]$") then
                        flush()
                        kind = closing and "p" or name
                    elseif name == "p" or name == "blockquote" or name == "pre" then
                        flush()
                        if name == "pre" then in_pre = not closing end
                        kind = closing and "p" or (name == "blockquote" and "quote" or name)
                    elseif name == "ul" or name == "ol" then
                        flush()
                        if closing then list = nil else list, number = name, 0 end
                    elseif name == "li" then
                        flush()
                        if closing then
                            kind = "p"
                        else
                            kind = "li"
                            if list == "ol" then
                                number = number + 1
                                parts[#parts + 1] = tostring(number) .. ". "
                            else
                                parts[#parts + 1] = "• "
                            end
                        end
                    elseif name == "a" then
                        if closing and link then
                            local href = trim(link)
                            if href:match("^https://") then
                                parts[#parts + 1] = " (" .. href .. ")"
                            end
                            link = nil
                        elseif not closing then
                            link = attribute(raw, "href")
                        end
                    elseif name == "br" then
                        parts[#parts + 1] = "\n"
                    elseif name == "img" then
                        parts[#parts + 1] = " [图片：" .. (attribute(raw, "alt") or "未提供说明") .. "] "
                    elseif name == "hr" then
                        flush()
                        kind = "rule"
                        parts[1] = "────────"
                        flush()
                        kind = "p"
                    elseif name == "td" or name == "th" then
                        if closing then parts[#parts + 1] = "  |  " end
                    elseif block_tags[name] then
                        flush()
                        kind = "p"
                    end
                end
            end
        end
    end
    flush()
    title = trim(title:gsub("%s+", " "))
    if #title > MAX_BLOCK_BYTES then
        title = title:sub(1, MAX_BLOCK_BYTES)
        local _, invalid = utf8.len(title)
        if invalid then title = title:sub(1, invalid - 1) end
        title = title .. "…"
        truncated = true
    end
    return { title = title, blocks = blocks, truncated = truncated }
end

return M
