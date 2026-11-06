# Local CLI agents

This Host plugin registers `run_cli_agent`, a model-facing tool that invokes one of three local coding-agent CLIs without shell interpolation.

## Configuration

The bundle config contains editable defaults for every CLI:

```yaml
models:
  codex: gpt-6.1-sol--high
  agy: gemini-3.8-flash--high
  claude: haiku-5-5--high
```

The shared `--high` suffix is normalized per CLI. Codex receives the base model plus high reasoning effort, Antigravity receives its native `-high` model suffix, and Claude receives the family alias plus `--effort high`.

`executables` contains the absolute path used for each CLI. Their containing directories are appended to the host PATH for subprocess lookup, allowing launchers using `/usr/bin/env node` to find Node installed alongside a CLI. If Node is installed elsewhere, configure a CLI executable path in a directory containing Node or update the host PATH. The other settings bound run time and captured output, and select each CLI's non-interactive permission policy.

## Tool input

- `provider`: `codex`, `agy`, or `claude`.
- `prompt`: task text sent to the selected CLI.
- `model`: optional one-call override of the configured model.
- `cwd`: optional working directory. Relative values resolve from the current DSH session directory.
- `timeout_seconds`: optional per-call timeout, capped by `timeoutMs`.
- `read_only`: optional review mode. It forces Codex read-only sandboxing, restricts Claude to Read/Glob/Grep, and enables Antigravity sandbox plus plan mode.

The tool returns a structured result with the model, working directory, exit code, captured output, duration, timeout state, and truncation or spill details.

## Non-interactive policies

- Codex runs through `codex exec` with the configured sandbox.
- Antigravity runs through `agy --print`; sandboxing defaults to enabled. On macOS, explicit proxy environment variables take precedence; otherwise enabled HTTP/HTTPS system proxies are detected for the agy process, with localhost bypassed. PAC and SOCKS-only configurations are not detected.
- Claude Code runs through `claude --print` with no session persistence and the configured permission mode.

The selected CLI remains responsible for its own authentication, model availability, and tool permissions.
