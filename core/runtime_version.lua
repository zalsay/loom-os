-- ClawOS core/runtime_version.lua
-- Canonical ClawOS Runtime version parser/comparator.
-- The server and device MUST follow the same rules.


local M = {}


local CHANNEL_RANK = {
    dev = 1,
    beta = 2,
    rc = 3,
    stable = 4,
}


local function parse_uint(text, allow_zero)
    if type(text) ~= "string" or text == "" then return nil end
    if #text > 1 and text:sub(1, 1) == "0" then return nil end
    local value = tonumber(text)
    if not value or value % 1 ~= 0 then return nil end
    if not allow_zero and value < 1 then return nil end
    if allow_zero and value < 0 then return nil end
    return value
end


function M.parse(version)
    if type(version) ~= "string" or version == "" or #version > 32 then
        return nil, "version must be a non-empty string up to 32 characters"
    end
    if version:find("+", 1, true) then
        return nil, "build metadata is not allowed"
    end
    if version:sub(1, 1) == "v" then
        return nil, "v prefix is not allowed"
    end


    local core, prerelease
    local dash = version:find("-", 1, true)
    if dash then
        core = version:sub(1, dash - 1)
        prerelease = version:sub(dash + 1)
        if prerelease == "" then return nil, "empty prerelease is not allowed" end
    else
        core = version
    end


    local maj_s, min_s, patch_s = core:match("^(%d+)%.(%d+)%.(%d+)$")
    if not maj_s then
        return nil, "version core must be MAJOR.MINOR.PATCH"
    end


    local major = parse_uint(maj_s, true)
    local minor = parse_uint(min_s, true)
    local patch = parse_uint(patch_s, true)
    if major == nil or minor == nil or patch == nil then
        return nil, "numeric version fields must not contain leading zeros"
    end


    local channel = "stable"
    local sequence = nil
    if prerelease then
        local kind, seq_s = prerelease:match("^([a-z]+)%.(%d+)$")
        if not kind or not CHANNEL_RANK[kind] or kind == "stable" then
            return nil, "prerelease must be dev.N, beta.N, or rc.N"
        end
        sequence = parse_uint(seq_s, false)
        if not sequence then
            return nil, "prerelease sequence must be an integer >= 1 with no leading zero"
        end
        channel = kind
    end


    return {
        raw = version,
        major = major,
        minor = minor,
        patch = patch,
        channel = channel,
        sequence = sequence,
    }
end


function M.validate_for_channel(version, channel)
    if not CHANNEL_RANK[channel] then
        return nil, "channel must be one of stable, rc, beta, dev"
    end
    local parsed, err = M.parse(version)
    if not parsed then return nil, err end
    if parsed.channel ~= channel then
        return nil, "version suffix does not match release channel"
    end
    return parsed
end


function M.compare(a, b)
    local va, ea = M.parse(a)
    if not va then return nil, ea end
    local vb, eb = M.parse(b)
    if not vb then return nil, eb end


    for _, key in ipairs({"major", "minor", "patch"}) do
        if va[key] < vb[key] then return -1 end
        if va[key] > vb[key] then return 1 end
    end


    local ra = CHANNEL_RANK[va.channel]
    local rb = CHANNEL_RANK[vb.channel]
    if ra < rb then return -1 end
    if ra > rb then return 1 end


    if va.channel ~= "stable" then
        if va.sequence < vb.sequence then return -1 end
        if va.sequence > vb.sequence then return 1 end
    end


    return 0
end


function M.is_newer(candidate, current)
    local cmp, err = M.compare(candidate, current)
    if cmp == nil then return nil, err end
    return cmp > 0
end


function M.release_id(product, board, version)
    return tostring(product) .. ":" .. tostring(board) .. ":" .. tostring(version)
end


function M.validate_manifest(release)
    if type(release) ~= "table" then
        return nil, "release manifest must be a table"
    end
    if release.schema ~= 1 then
        return nil, "release schema must be 1"
    end
    if release.product ~= "clawos" then
        return nil, "product must be clawos"
    end
    if type(release.board) ~= "string" or release.board == "" then
        return nil, "board is required"
    end


    local parsed, err = M.validate_for_channel(release.version, release.channel)
    if not parsed then return nil, err end


    if type(release.release_id) ~= "string" or release.release_id == "" then
        return nil, "release_id is required"
    end
    local expected = M.release_id(release.product, release.board, release.version)
    if release.release_id ~= expected then
        return nil, "release_id must equal " .. expected
    end


    if release.min_bootstrap ~= nil then
        local min_bootstrap, min_err = M.parse(release.min_bootstrap)
        if not min_bootstrap then
            return nil, "invalid min_bootstrap: " .. tostring(min_err)
        end
    end


    return parsed
end


return M