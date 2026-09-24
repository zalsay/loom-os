-- Loom OS update/release_client.lua
-- Minimal client for the canonical Loom OS Runtime release service.


local json = require("json")
local http = require("system.net.http_client")
local errors = require("core.errors")
local runtime_version = require("core.runtime_version")


local M = {}


local CHANNEL = {
    stable = true,
    rc = true,
    beta = true,
    dev = true,
}


local function validate_board(board)
    return type(board) == "string"
       and board:match("^[a-z0-9][a-z0-9%-]*$") ~= nil
       and #board <= 64
end


local function validate_base_url(url)
    return type(url) == "string" and url:sub(1, 8):lower() == "https://"
end


local function trim_slash(url)
    return (url:gsub("/+$", ""))
end


local function build_url(options)
    if not validate_base_url(options.base_url) then
        return nil, errors.new("E_INVALID_ARG", "release server base_url must use HTTPS")
    end
    if not validate_board(options.board) then
        return nil, errors.new("E_INVALID_ARG", "invalid release board")
    end
    if not CHANNEL[options.channel] then
        return nil, errors.new("E_INVALID_ARG", "invalid release channel")
    end
    if not runtime_version.parse(options.current_version) then
        return nil, errors.new("E_VERSION", "invalid current Runtime version")
    end
    if not runtime_version.parse(options.bootstrap_version) then
        return nil, errors.new("E_VERSION", "bootstrap_version is required and must be valid")
    end


    return trim_slash(options.base_url)
        .. "/v1/loom-os/releases/latest"
        .. "?board=" .. options.board
        .. "&channel=" .. options.channel
        .. "&current=" .. options.current_version
        .. "&bootstrap=" .. options.bootstrap_version
end


function M.latest(options)
    options = options or {}


    local url, url_err = build_url(options)
    if not url then return nil, url_err end


    local response, http_err = http.get(url, {
        timeout_ms = options.timeout_ms or 15000,
        max_body_bytes = options.max_body_bytes or 65536,
        accept_status = {
            [200] = true,
            [204] = true,
        },
    })
    if not response then return nil, http_err end


    if response.status == 204 then
        return {
            available = false,
            current_version = options.current_version,
        }
    end


    local ok, release = pcall(json.decode, response.body or "")
    if not ok or type(release) ~= "table" then
        return nil, errors.new("E_PROTOCOL", "release server returned invalid JSON")
    end


    local parsed, manifest_err = runtime_version.validate_manifest(release)
    if not parsed then
        return nil, errors.new("E_VERSION", "release server returned invalid manifest", {
            cause = manifest_err,
            version = release.version,
        })
    end


    if release.board ~= options.board then
        return nil, errors.new("E_VERSION", "release board does not match device", {
            expected = options.board,
            actual = release.board,
        })
    end


    if release.channel ~= options.channel then
        return nil, errors.new("E_VERSION", "release channel does not match request", {
            expected = options.channel,
            actual = release.channel,
        })
    end


    local newer, compare_err = runtime_version.is_newer(
        release.version,
        options.current_version
    )
    if newer == nil then
        return nil, errors.new("E_VERSION", "failed to compare Runtime versions", {
            cause = compare_err,
        })
    end
    if not newer then
        return nil, errors.new("E_VERSION", "release server returned a non-newer version", {
            current = options.current_version,
            candidate = release.version,
        })
    end


    local cmp, bootstrap_err = runtime_version.compare(
        options.bootstrap_version,
        release.min_bootstrap
    )
    if cmp == nil then
        return nil, errors.new("E_VERSION", "failed to compare bootstrap versions", {
            cause = bootstrap_err,
        })
    end
    if cmp < 0 then
        return nil, errors.new("E_VERSION", "release requires a newer bootstrap", {
            current = options.bootstrap_version,
            required = release.min_bootstrap,
        })
    end


    return {
        available = true,
        release = release,
        current_version = options.current_version,
    }
end


return M