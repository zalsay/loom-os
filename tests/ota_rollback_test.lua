return function(update, source_release, storage)
    local release = {}
    for key, value in pairs(source_release) do release[key] = value end
    release.version, release.release_id = "0.1.2", "loom-os:esp-mosaico:0.1.2"
    local backend = { download = function(_, path)
        storage.write_file(path, "return { version='0.1.2' }")
        return true
    end }
    assert(update.install(release, backend))
    assert(update.status().pending_version == "0.1.2")
    assert(update.rollback_pending("candidate crash"))
    assert(update.status().active_version == "0.1.1")
    assert(update.status().pending_version == nil)
end
