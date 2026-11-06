import path from "node:path";
import { performance } from "node:perf_hooks";

const name = "local-agent-cli";
const inject = ["tools", "subprocess", "workingDirectory"];
const PROVIDERS = ["codex", "agy", "claude"];

const DEFAULT_CONFIG = Object.freeze({
  models: {
    codex: "gpt-6.1-sol--high",
    agy: "gemini-3.8-flash--high",
    claude: "haiku-5-5--high",
  },
  executables: {
    codex: "/opt/homebrew/bin/codex",
    agy: "/Users/yingzhang/.local/bin/agy",
    claude: "/opt/homebrew/bin/claude",
  },
  timeoutMs: 600000,
  maxOutputBytes: 4194304,
  maxOutputChars: 24000,
  codexSandbox: "workspace-write",
  claudePermissionMode: "acceptEdits",
  agySandbox: true,
});

const TOOL_PARAMETERS = {
  type: "object",
  additionalProperties: false,
  properties: {
    provider: {
      type: "string",
      enum: PROVIDERS,
      description: "Local CLI to invoke.",
    },
    prompt: {
      type: "string",
      description: "Complete task instructions for the selected CLI.",
    },
    model: {
      type: "string",
      description: "Override the configured model for this call only.",
    },
    cwd: {
      type: "string",
      description: "Working directory. Relative paths resolve from the current DSH session directory.",
    },
    timeout_seconds: {
      type: "number",
      description: "Per-call timeout in seconds, capped by the plugin's timeoutMs setting.",
    },
    read_only: {
      type: "boolean",
      description: "Use the CLI's most restrictive non-interactive review mode. Set true for review-only tasks.",
    },
  },
  required: ["provider", "prompt"],
};

const TOOL_OUTPUT_SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    provider: { type: "string", enum: PROVIDERS },
    model: { type: "string" },
    cliModel: { type: "string" },
    reasoningEffort: { oneOf: [{ type: "string" }, { type: "null" }] },
    cwd: { type: "string" },
    exitCode: { oneOf: [{ type: "integer" }, { type: "null" }] },
    signal: { oneOf: [{ type: "string" }, { type: "null" }] },
    timedOut: { type: "boolean" },
    readOnly: { type: "boolean" },
    durationMs: { type: "integer" },
    stdout: { type: "string" },
    stderr: { type: "string" },
    stdoutTruncated: { type: "boolean" },
    stderrTruncated: { type: "boolean" },
    stdoutSpillPath: { type: "string" },
    stderrSpillPath: { type: "string" },
  },
  required: [
    "provider",
    "model",
    "cliModel",
    "reasoningEffort",
    "cwd",
    "exitCode",
    "signal",
    "timedOut",
    "readOnly",
    "durationMs",
    "stdout",
    "stderr",
    "stdoutTruncated",
    "stderrTruncated",
  ],
};

function resolveConfig(config = {}) {
  return {
    ...DEFAULT_CONFIG,
    ...config,
    models: { ...DEFAULT_CONFIG.models, ...config.models },
    executables: { ...DEFAULT_CONFIG.executables, ...config.executables },
  };
}

function validateConfig(config) {
  for (const provider of PROVIDERS) {
    if (config.models[provider].trim().length === 0) {
      throw new Error(`local-agent-cli: models.${provider} must be non-empty`);
    }
    if (config.executables[provider].trim().length === 0) {
      throw new Error(`local-agent-cli: executables.${provider} must be non-empty`);
    }
  }
  for (const field of ["timeoutMs", "maxOutputBytes", "maxOutputChars"]) {
    if (!Number.isSafeInteger(config[field]) || config[field] <= 0) {
      throw new Error(`local-agent-cli: ${field} must be a positive safe integer`);
    }
  }
  if (!["read-only", "workspace-write", "danger-full-access"].includes(config.codexSandbox)) {
    throw new Error("local-agent-cli: codexSandbox is invalid");
  }
  if (!["manual", "acceptEdits", "auto", "dontAsk", "plan"].includes(config.claudePermissionMode)) {
    throw new Error("local-agent-cli: claudePermissionMode is invalid");
  }
  if (typeof config.agySandbox !== "boolean") {
    throw new Error("local-agent-cli: agySandbox must be a boolean");
  }
}

function readArgs(raw) {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
    throw new Error("run_cli_agent arguments must be an object");
  }
  if (!PROVIDERS.includes(raw.provider)) {
    throw new Error("provider must be codex, agy, or claude");
  }
  if (typeof raw.prompt !== "string" || raw.prompt.trim().length === 0) {
    throw new Error("prompt must be a non-empty string");
  }
  if (raw.model !== undefined && (typeof raw.model !== "string" || raw.model.trim().length === 0)) {
    throw new Error("model must be a non-empty string when provided");
  }
  if (raw.cwd !== undefined && (typeof raw.cwd !== "string" || raw.cwd.trim().length === 0)) {
    throw new Error("cwd must be a non-empty string when provided");
  }
  if (raw.timeout_seconds !== undefined && typeof raw.timeout_seconds !== "number") {
    throw new Error("timeout_seconds must be a number when provided");
  }
  if (raw.read_only !== undefined && typeof raw.read_only !== "boolean") {
    throw new Error("read_only must be a boolean when provided");
  }
  return raw;
}

function resolveModel(provider, selection) {
  const qualified = /^(.*?)--(low|medium|high|xhigh|max)$/.exec(selection);
  const base = qualified?.[1] ?? selection;
  const effort = qualified?.[2];

  if (provider === "agy") {
    return {
      model: effort === undefined ? base : `${base}-${effort}`,
      effort,
    };
  }
  if (provider === "claude") {
    const familyAlias = /^(haiku|sonnet|opus)(?:-\d+-\d+)?$/.exec(base);
    return {
      model: familyAlias?.[1] ?? base,
      effort,
    };
  }
  return { model: base, effort };
}

async function agyProxyEnvironment(ctx, cwd, signal) {
  if (process.platform !== "darwin") return {};
  const proxyEnv = {};
  for (const key of ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"]) {
    if (process.env[key] !== undefined) proxyEnv[key] = process.env[key];
  }
  if (proxyEnv.HTTP_PROXY || proxyEnv.http_proxy || proxyEnv.HTTPS_PROXY || proxyEnv.https_proxy || proxyEnv.ALL_PROXY || proxyEnv.all_proxy) {
    return proxyEnv;
  }

  let text;
  try {
    const handle = ctx.subprocess.spawn({
      argv: ["/usr/sbin/scutil", "--proxy"],
      cwd,
      stdio: { stdin: "ignore", stdout: { maxBytes: 16384 }, stderr: { maxBytes: 4096 } },
      graceMs: 500,
      signal,
    });
    const outcome = await handle.done;
    if (outcome.exitCode !== 0) return proxyEnv;
    text = handle.collected.stdout?.readFrom(0).text ?? "";
  } catch (error) {
    if (signal.aborted) throw error;
    return proxyEnv;
  }

  const value = (key) => text.match(new RegExp(`^\\s*${key}\\s*:\\s*(.+?)\\s*$`, "m"))?.[1];
  for (const [name, prefix] of [["HTTP_PROXY", "HTTP"], ["HTTPS_PROXY", "HTTPS"]]) {
    const host = value(`${prefix}Proxy`);
    const port = value(`${prefix}Port`);
    if (value(`${prefix}Enable`) !== "1" || !host || !/^\d+$/.test(port ?? "")) continue;
    // Do not accept credentials, URL syntax, or shell metacharacters in host.
    if (!/^[A-Za-z0-9.:-]+$/.test(host) || Number(port) < 1 || Number(port) > 65535) continue;
    const address = host.includes(":") && !host.startsWith("[") ? `[${host}]` : host;
    proxyEnv[name] = `http://${address}:${port}`;
  }
  if (proxyEnv.HTTP_PROXY || proxyEnv.HTTPS_PROXY) {
    const entries = new Set((proxyEnv.NO_PROXY ?? proxyEnv.no_proxy ?? "").split(",").map((item) => item.trim()).filter(Boolean));
    for (const host of ["localhost", "127.0.0.1", "::1"]) entries.add(host);
    proxyEnv.NO_PROXY = [...entries].join(",");
  }
  return proxyEnv;
}

function invocation(provider, resolvedModel, prompt, config, readOnly) {
  switch (provider) {
    case "codex":
      return {
        argv: [
          "exec",
          "--skip-git-repo-check",
          "--sandbox",
          readOnly ? "read-only" : config.codexSandbox,
          "--color",
          "never",
          "--model",
          resolvedModel.model,
          ...(resolvedModel.effort === undefined
            ? []
            : ["--config", `model_reasoning_effort="${resolvedModel.effort}"`]),
          "-",
        ],
        stdin: prompt,
      };
    case "agy":
      return {
        argv: [
          "--model",
          resolvedModel.model,
          ...(readOnly
            ? ["--sandbox", "--mode", "plan"]
            : config.agySandbox ? ["--sandbox"] : []),
          `--print=${prompt}`,
        ],
        stdin: undefined,
      };
    case "claude":
      return {
        argv: [
          "--print",
          "--output-format",
          "text",
          "--model",
          resolvedModel.model,
          ...(resolvedModel.effort === undefined ? [] : ["--effort", resolvedModel.effort]),
          "--permission-mode",
          readOnly ? "dontAsk" : config.claudePermissionMode,
          ...(readOnly ? ["--tools", "Read,Glob,Grep"] : []),
          "--permission-prompts",
          "none",
          "--no-session-persistence",
        ],
        stdin: prompt,
      };
    default:
      throw new Error(`Unsupported CLI provider: ${provider}`);
  }
}

function clipOutput(text, maxChars) {
  if (text.length <= maxChars) return text;
  const marker = "\n\n[... output truncated; see spillPath for the captured stream ...]\n\n";
  const available = Math.max(0, maxChars - marker.length);
  const headLength = Math.floor(available * 0.4);
  const tailLength = available - headLength;
  return `${text.slice(0, headLength)}${marker}${text.slice(-tailLength)}`;
}

function readOutput(reader, maxChars) {
  if (reader === undefined) {
    return { text: "", truncated: false };
  }
  const captured = reader.readFrom(0);
  const clipped = captured.text.length > maxChars;
  return {
    text: clipOutput(captured.text, maxChars),
    truncated: captured.lossy || clipped,
    spillPath: captured.spillPath,
  };
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

function renderResult(value) {
  const status = value.timedOut
    ? `timed out after ${value.durationMs} ms`
    : `exited with code ${value.exitCode ?? "null"}${value.signal ? ` (${value.signal})` : ""}`;
  const modelLabel = value.model === value.cliModel
    ? value.model
    : `${value.model} (CLI: ${value.cliModel})`;
  const effortLabel = value.reasoningEffort === null ? "" : `, effort ${value.reasoningEffort}`;
  const sections = [`${value.provider} using ${modelLabel}${effortLabel} ${status}.`];

  if (value.stdout.length > 0) {
    sections.push(`stdout:\n${value.stdout}`);
  }
  if (value.stderr.length > 0) {
    sections.push(`stderr:\n${value.stderr}`);
  }
  if (value.stdout.length === 0 && value.stderr.length === 0) {
    sections.push("The CLI produced no output.");
  }
  if (value.stdoutTruncated || value.stderrTruncated) {
    sections.push("Captured output was truncated.");
  }

  return [{ type: "text", text: sections.join("\n\n") }];
}

function apply(ctx, rawConfig) {
  const config = resolveConfig(rawConfig);
  validateConfig(config);

  ctx.tools.register({
    name: "run_cli_agent",
    description:
      "Run one local coding-agent CLI non-interactively with a prompt. Choose codex, agy, or claude; each has a configured default model. Set read_only for reviews that must not modify files. Otherwise the CLI may edit files in cwd under its own non-interactive permission policy.",
    parameters: TOOL_PARAMETERS,
    output: {
      schema: TOOL_OUTPUT_SCHEMA,
      render: (_args, value) => renderResult(value),
      presentationMeta: (_args, value) => ({
        provider: value.provider,
        model: value.model,
        cliModel: value.cliModel,
        reasoningEffort: value.reasoningEffort,
        cwd: value.cwd,
        exitCode: value.exitCode,
        timedOut: value.timedOut,
        readOnly: value.readOnly,
      }),
    },
    timeoutMs: config.timeoutMs,
    async execute(rawArgs, exec) {
      const args = readArgs(rawArgs);
      const prompt = args.prompt.trim();
      if (exec.agent === undefined) throw new Error("run_cli_agent requires an owning agent session");
      if (exec.signal.aborted) throw new Error("run_cli_agent was cancelled");

      const provider = args.provider;
      const model = args.model?.trim() || config.models[provider];
      const resolvedModel = resolveModel(provider, model);
      const readOnly = args.read_only === true;
      const sessionCwd = await ctx.workingDirectory.ensure(exec.agent, exec.signal);
      const cwd = args.cwd ? path.resolve(sessionCwd, args.cwd) : sessionCwd;

      const requestedTimeout = args.timeout_seconds === undefined
        ? config.timeoutMs
        : Math.round(args.timeout_seconds * 1000);
      if (!Number.isFinite(requestedTimeout) || requestedTimeout <= 0) {
        throw new Error("timeout_seconds must be a positive number");
      }
      const timeoutMs = Math.min(requestedTimeout, config.timeoutMs);
      const request = invocation(provider, resolvedModel, prompt, config, readOnly);
      // GUI-launched hosts can have a system-only PATH. Append explicitly
      // configured executable directories so /usr/bin/env can find runtimes.
      const extraPath = Object.values(config.executables)
        .filter((command) => path.isAbsolute(command))
        .map((command) => path.dirname(command));
      const basePath = process.env.PATH || "/usr/bin:/bin:/usr/sbin:/sbin";
      const childEnv = {
        PATH: [...new Set([...basePath.split(path.delimiter).filter(Boolean), ...extraPath])].join(path.delimiter),
        ...(provider === "agy" ? await agyProxyEnvironment(ctx, cwd, exec.signal) : {}),
      };
      const executable = await ctx.subprocess.resolveExecutable(
        config.executables[provider],
        childEnv,
        exec.signal,
      );

      const controller = new AbortController();
      let timedOut = false;
      const forwardAbort = () => controller.abort(exec.signal.reason);
      exec.signal.addEventListener("abort", forwardAbort, { once: true });
      const timer = setTimeout(() => {
        timedOut = true;
        controller.abort(new Error(`run_cli_agent timed out after ${timeoutMs} ms`));
      }, timeoutMs);
      const startedAt = performance.now();

      try {
        const handle = ctx.subprocess.spawn({
          argv: [executable, ...request.argv],
          cwd,
          env: childEnv,
          stdio: {
            stdin: request.stdin === undefined ? "ignore" : { data: request.stdin },
            stdout: {
              maxBytes: config.maxOutputBytes,
              spill: { maxBytes: config.maxOutputBytes * 2 },
            },
            stderr: {
              maxBytes: config.maxOutputBytes,
              spill: { maxBytes: config.maxOutputBytes * 2 },
            },
          },
          graceMs: 2000,
          signal: controller.signal,
        });

        let outcome;
        let processError;
        try {
          outcome = await handle.done;
        } catch (error) {
          processError = error;
        }

        const stdout = readOutput(handle.collected.stdout, config.maxOutputChars);
        const stderr = readOutput(handle.collected.stderr, config.maxOutputChars);
        const durationMs = Math.round(performance.now() - startedAt);

        if (exec.signal.aborted) {
          throw exec.signal.reason instanceof Error
            ? exec.signal.reason
            : new Error("run_cli_agent was cancelled");
        }
        if (timedOut) {
          return {
            provider,
            model,
            cliModel: resolvedModel.model,
            reasoningEffort: resolvedModel.effort ?? null,
            cwd,
            exitCode: null,
            signal: null,
            timedOut: true,
            readOnly,
            durationMs,
            stdout: stdout.text,
            stderr: stderr.text,
            stdoutTruncated: stdout.truncated,
            stderrTruncated: stderr.truncated,
            ...(stdout.spillPath === undefined ? {} : { stdoutSpillPath: stdout.spillPath }),
            ...(stderr.spillPath === undefined ? {} : { stderrSpillPath: stderr.spillPath }),
          };
        }
        if (processError !== undefined) {
          throw new Error(`Failed to run ${provider}: ${errorMessage(processError)}`);
        }

        return {
          provider,
          model,
          cliModel: resolvedModel.model,
          reasoningEffort: resolvedModel.effort ?? null,
          cwd,
          exitCode: outcome.exitCode,
          signal: outcome.signal,
          timedOut: false,
          readOnly,
          durationMs,
          stdout: stdout.text,
          stderr: stderr.text,
          stdoutTruncated: stdout.truncated,
          stderrTruncated: stderr.truncated,
          ...(stdout.spillPath === undefined ? {} : { stdoutSpillPath: stdout.spillPath }),
          ...(stderr.spillPath === undefined ? {} : { stderrSpillPath: stderr.spillPath }),
        };
      } catch (error) {
        if (timedOut) throw new Error(`run_cli_agent timed out after ${timeoutMs} ms`);
        throw error;
      } finally {
        clearTimeout(timer);
        exec.signal.removeEventListener("abort", forwardAbort);
      }
    },
    presentCall(rawArgs) {
      const provider = rawArgs && typeof rawArgs.provider === "string" ? rawArgs.provider : "local";
      const cwd = rawArgs && typeof rawArgs.cwd === "string" ? rawArgs.cwd : undefined;
      const mode = rawArgs && rawArgs.read_only === true ? " (read-only)" : "";
      return {
        card: "terminal",
        title: `Run ${provider} CLI${mode}`,
        cwd,
      };
    },
    isConcurrencySafe(rawArgs) {
      return rawArgs?.read_only === true;
    },
  });
}

export { apply, inject, name };
