# Safarier browser tool

Registers `sfa` for the installed Safarier AI CLI. Use `profiles` and `authorize` to inspect environments and permission. If the selected profile is not running, use `launch` with its UUID and optional HTTP(S) URL. Then `connect`, use `observe` to inspect the page, and `release` when finished. Inspect or save screenshots before release because release can clean them up.

Use `{"action":"click-target","target":"Save"}` for JEV semantic click on the current connection without a frame. The CLI sends the target and recognized page text to the configured model, then clicks the selected candidate. Use `observe` to confirm the page effect. The `click` action still uses screenshot coordinates.

For a page upload, first click the page’s upload control. Then call `sfa` with `{"action":"select-file","paths":["/absolute/cover.png","/absolute/page.png"]}` using the same connection. Pass one path per file; multiple files require a chooser that supports multi-selection. This action needs no screenshot frame. `filesSelected` counts the files given to the page; use `observe` to check the upload.

Each requested browser operation is sent once. CLI exit codes, signals, stdout, stderr and parsed JSON are returned to the agent; they do not establish whether a page action achieved its intended effect. Use `observe` for that decision. The agent chooses a suitable frame and screenshot coordinates; this plugin does not impose a latest-frame cache or invalidate frames after input.

A CLI error, non-JSON response, truncated output or transport exception does not poison later explicit calls. The plugin never automatically repeats browser input. Unsupported keys still return the installed CLI's error: removing the historical error barrier does not add support for `Space` or upgrade the installed App.

After a plugin reload, completed `sfa` results in the owning session's history restore its runtime and connection. Incomplete or failed historical calls do not impose a permanent manual-recovery lock. A failed connect can be explicitly retried against the same runtime. `launch` is independent of the control connection and remains available after a failed connect. An explicit connect to the same profile is also forwarded after restoring a historical connection: daemon start and connect are each sent once. A failed start/connect preserves the old route; only success replaces the connection. An existing owned connection must be released before connecting to another profile. A stale socket left by a terminated daemon still returns the CLI error; this plugin does not remove sockets or infer that an uncertain release succeeded.

Release returns the actual CLI receipt. With an owned connection, the daemon is stopped only after the CLI reports all four release fields as true (`inputReleased`, `artifactsCleaned`, `browserRetained`, `manualInteractionEnabled`). Missing fields are reported as `releaseVerified: false` and do not block another explicit call. If release succeeded but daemon cleanup failed, `releaseVerified: true` is returned with the stop failure; the next explicit `release` attempts only daemon cleanup, including after reload. If connect/start failed without obtaining a connection, `release` sends only daemon stop and returns its actual result, without claiming browser release. Successful cleanup clears routing both in memory and on history restoration.

The existing command/argument validation, per-agent serialization and owning session's `danger-full-access` policy requirement remain. The plugin cannot request OS permissions or elevate policy, execute arbitrary shell commands, mutate profiles or close the browser. Only perform browser operations authorized by the user.

Run the scoped plugin tests with:

```sh
node --test plugins/sfa-tool/test.mjs plugins/sfa-tool/test-extra.mjs plugins/sfa-tool/test-recovery.mjs plugins/sfa-tool/test-file-selection.mjs plugins/sfa-tool/test-click-target.mjs
```

The installed DSH profile can link directly to this source directory. A source edit alone does not prove the running Host has loaded it. Use DSH's supported plugin/profile recomposition or restart DSH, then verify the running tool. Source-level tests and direct plugin/CLI integration do not establish in-Host activation.
