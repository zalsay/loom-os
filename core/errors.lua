-- Loom OS core/errors.lua
-- Stable error objects shared by the v0.1 core and App API wrappers.

local M = {}

M.codes = {
    E_INVALID_ARG = true,
    E_PERMISSION = true,
    E_NOT_FOUND = true,
    E_EXISTS = true,
    E_BUSY = true,
    E_IO = true,
    E_UNSUPPORTED = true,
    E_TIMEOUT = true,
    E_CANCELLED = true,
    E_LOAD = true,
    E_CRASH = true,
    E_VERSION = true,
    E_INVALID = true, E_START = true,
    E_APP_MANIFEST = true, E_APP_ID = true, E_APP_VERSION = true,
    E_APP_ENTRY = true, E_APP_PATH = true, E_APP_PACKAGE = true,
    E_APP_FILES = true, E_APP_VERSION_EXISTS = true,
    E_APP_NOT_PENDING = true, E_APP_STATE = true, E_APP_ROLLBACK = true,
    E_AUTHOR_FILE = true, E_AUTHOR_PATH = true, E_AUTHOR_CONTENT = true,
    E_AUTHOR_DRAFT = true, E_AUTHOR_OPERATION = true, E_AUTHOR_FILES = true,
    E_AUTHOR_DUPLICATE = true, E_AUTHOR_ENTRY = true,
    E_AUTHOR_ID_CHANGE = true, E_AUTHOR_NOT_FOUND = true,
    E_AUTHOR_NOT_VALID = true, E_VALIDATE_SOURCE = true,
    E_VALIDATE_REQUIRE = true, E_VALIDATE_DYNAMIC_CODE = true,
    E_VALIDATE_LUA = true, E_PERMISSION_APPROVAL = true,
    E_AGENT_FORMAT = true,
}

function M.new(code, message, detail)
    if type(code) ~= "string" or not M.codes[code] then
        code = "E_IO"
    end
    return {
        code = code,
        message = tostring(message or code),
        detail = detail,
    }
end

function M.wrap(code, message, detail)
    if type(detail) == "table" and detail.code and detail.message then
        return detail
    end
    return M.new(code, message, detail)
end

function M.from_exception(code, err, detail)
    return M.new(code or "E_IO", tostring(err), detail)
end

function M.is_error(value)
    return type(value) == "table"
        and type(value.code) == "string"
        and type(value.message) == "string"
end

return M
