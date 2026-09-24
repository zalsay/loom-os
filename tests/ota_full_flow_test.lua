return function(update, storage, base)
    local root = storage.join_path(base, "clawos-runtime")
    local initial = storage.join_path(root, "releases", "0.1.0")
    storage.mkdir(initial)
    storage.write_file(storage.join_path(initial, "main.lua"), "return true")
    assert(update.provision("0.1.0"))
    local source = "return { version='0.1.1' }"
    local release = { schema=1, product="clawos", board="esp-mosaico", channel="stable",
        version="0.1.1", release_id="clawos:esp-mosaico:0.1.1", min_bootstrap="0.1.0",
        entry="main.lua", files={{path="main.lua",url="https://example.test/main.lua",size=#source}} }
    local backend = { download = function(url, path, options)
        assert(url:sub(1,8) == "https://" and options.size == #source)
        storage.write_file(path, source)
        return true
    end }
    assert(update.install(release, backend))
    assert(update.status().pending_version == "0.1.1")
    assert(update.confirm_boot({version="0.1.1"}))
    assert(update.status().active_version == "0.1.1")
    return release
end
