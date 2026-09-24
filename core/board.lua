-- ClawOS core/board.lua
local board_manager = require("board_manager")
local errors = require("core.errors")


local M = {}
local current_adapter, current_info
local KNOWN = { mosaico = "boards.mosaico" }


function M.load(id)
    local module_name = KNOWN[id]
    if not module_name then
        return nil, errors.new("E_NOT_FOUND", "unknown ClawOS board adapter", {board=id})
    end
    local ok, adapter = pcall(require, module_name)
    if not ok then
        return nil, errors.new("E_LOAD", "failed to load board adapter", {
            board=id, cause=tostring(adapter)
        })
    end
    local info = {}
    local iok, value = pcall(board_manager.get_board_info)
    if iok and type(value) == "table" then info = value end
    current_adapter, current_info = adapter, info
    return adapter, info
end


function M.detect()
    local ok, info = pcall(board_manager.get_board_info)
    if not ok or type(info) ~= "table" then
        return nil, errors.new("E_IO", "board_manager.get_board_info() failed", {
            cause=tostring(info)
        })
    end
    for id, module_name in pairs(KNOWN) do
        local loaded, adapter = pcall(require, module_name)
        if loaded and type(adapter) == "table" and type(adapter.matches) == "function" then
            local mok, result = pcall(adapter.matches, info)
            if mok and result == true then
                current_adapter, current_info = adapter, info
                return adapter, info, id
            end
        end
    end
    return nil, errors.new("E_UNSUPPORTED", "no ClawOS board adapter matched current board", {
        name=info.name, chip=info.chip, version=info.version
    })
end


function M.current()
    return current_adapter, current_info
end


return M