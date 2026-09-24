return function(update, source_release)
    local release = {}
    for key, value in pairs(source_release) do release[key] = value end
    release.version, release.release_id = "0.1.3", "clawos:esp-mosaico:0.1.3"
    local backend = { download = function(_, _, options)
        return nil, {code="E_IO",message="size mismatch",detail={expected=options.size,actual=0}}
    end }
    assert(update.install(release, backend) == nil)
    assert(update.status().active_version == "0.1.1" and update.status().pending_version == nil)
end
