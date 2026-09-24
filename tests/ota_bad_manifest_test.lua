return function(update, source_release)
    local release = {}
    for key, value in pairs(source_release) do release[key] = value end
    release.version, release.release_id = "0.1.4", "clawos:esp-mosaico:0.1.4"
    release.schema = 2
    assert(update.install(release, {download=function() error("should not download") end}) == nil)
    assert(update.status().active_version == "0.1.1" and update.status().pending_version == nil)
end
