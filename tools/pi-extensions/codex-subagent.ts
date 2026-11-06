// Pi agent extension: delegate read-only tasks to Codex CLI with model fallback.
import { spawn, execFileSync } from "node:child_process";
import { StringDecoder } from "node:string_decoder";
import { homedir } from "node:os";
import { delimiter, join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const MAX_TASKS = 4;
const MAX_BYTES = 64 * 1024;

// Read macOS system proxy at launch, preserving explicit environment overrides.
function childEnvironment(): NodeJS.ProcessEnv {
  const env = { ...process.env };
  env.PATH = [env.PATH, join(homedir(), ".local", "bin"), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"].filter(Boolean).join(delimiter);
  if (process.platform !== "darwin") return env;
  try {
    const info = execFileSync("/usr/sbin/scutil", ["--proxy"], { encoding: "utf8", timeout: 3000, stdio: ["ignore", "pipe", "ignore"] });
    const field = (key: string) => info.match(new RegExp(`^\\s*${key}\\s*:\\s*(.*?)\\s*$`, "m"))?.[1];
    for (const [key, upper, lower] of [["HTTP", "HTTP_PROXY", "http_proxy"], ["HTTPS", "HTTPS_PROXY", "https_proxy"]]) {
      const host = field(`${key}Proxy`), port = field(`${key}Port`);
      if (field(`${key}Enable`) !== "1" || !host || !port || !/^[a-zA-Z0-9.:-]+$/.test(host) || !/^\d{1,5}$/.test(port) || Number(port) < 1 || Number(port) > 65535) continue;
      const address = host.includes(":") ? `[${host}]` : host;
      const value = env[upper] || env[lower] || `http://${address}:${port}`;
      env[upper] ||= value; env[lower] ||= value;
    }
    const exceptions = info.match(/ExceptionsList\s*:\s*<array>\s*\{([\s\S]*?)\}/)?.[1];
    const entries = exceptions ? [...exceptions.matchAll(/^\s*\d+\s*:\s*(.+?)\s*$/gm)].map((m) => m[1].replace(/^\*\./, ".")).filter((v) => v !== "<local>") : [];
    const noProxy = env.NO_PROXY || env.no_proxy || entries.join(",");
    if (noProxy) { env.NO_PROXY ||= noProxy; env.no_proxy ||= noProxy; }
  } catch { /* No system proxy available: preserve existing environment. */ }
  return env;
}
const DEFAULT_TIMEOUT = 300_000;
const MAX_TIMEOUT = 600_000;

type Result = {
  status: "success" | "error" | "timeout" | "cancelled";
  response: string;
  error: string;
  exitCode: number | null;
  threadId?: string;
  model?: string;
  effort?: string;
  startedWork?: boolean;
  fallbackFrom?: string;
};

function clipped(text: string): string {
  const bytes = Buffer.from(text, "utf8");
  if (bytes.length <= MAX_BYTES) return text;
  return bytes.subarray(0, MAX_BYTES).toString("utf8") + "\n[output truncated]";
}

function runCodex(task: string, cwd: string, timeoutMs: number, model: string, effort: string, signal?: AbortSignal): Promise<Result> {
  return new Promise((resolve) => {
    if (signal?.aborted) {
      resolve({ status: "cancelled", response: "", error: "Cancelled before starting", exitCode: null });
      return;
    }
    // The prompt travels via stdin, not through a shell or process arguments.
    const args = ["exec", "--json", "--sandbox", "read-only", "--ephemeral", "--skip-git-repo-check", "-m", model, "-c", `model_reasoning_effort="${effort}"`, "-C", cwd, "-"];
    const proc = spawn(process.env.CODEX_BIN || "codex", args, {
      cwd,
      stdio: ["pipe", "pipe", "pipe"],
      env: childEnvironment(),
    });
    let response = "";
    let stderr = "";
    let pending = "";
    let threadId: string | undefined;
    let eventError = "";
    let stopped: "timeout" | "cancelled" | undefined;
    let startedWork = false;
    let finished = false;
    const decoder = new StringDecoder("utf8");
    const readLine = (line: string) => {
      if (!line.trim()) return;
      try {
        const event = JSON.parse(line);
        if (event.type === "thread.started" && typeof event.thread_id === "string") threadId = event.thread_id;
        if ((event.type === "item.started" || event.type === "item.completed") && event.item?.type && !["agent_message", "reasoning"].includes(event.item.type)) startedWork = true;
        if (event.type === "item.completed" && event.item?.type === "agent_message" && typeof event.item.text === "string") {
          response = clipped(event.item.text);
        }
        if (event.type === "turn.failed" || event.type === "error") {
          eventError = clipped(String(event.error?.message ?? event.message ?? "Codex reported an error"));
        }
      } catch {
        eventError = "Codex returned invalid JSONL output";
      }
    };
    const consume = (text: string) => {
      pending += text;
      const lines = pending.split("\n");
      pending = lines.pop() || "";
      for (const line of lines) readLine(line);
      if (Buffer.byteLength(pending, "utf8") > 1024 * 1024) {
        eventError = "Codex JSON event exceeded the 1 MiB limit";
        proc.kill("SIGTERM");
      }
    };
    let killTimer: ReturnType<typeof setTimeout> | undefined;
    const stop = (reason: "timeout" | "cancelled") => {
      if (finished || stopped) return;
      stopped = reason;
      proc.kill("SIGTERM");
      killTimer = setTimeout(() => proc.kill("SIGKILL"), 2_000);
    };
    const timer = setTimeout(() => stop("timeout"), timeoutMs);
    const abort = () => stop("cancelled");
    signal?.addEventListener("abort", abort, { once: true });
    proc.stdout.on("data", (chunk: Buffer) => consume(decoder.write(chunk)));
    proc.stderr.on("data", (chunk: Buffer) => { stderr = clipped(stderr + chunk.toString("utf8")); });
    proc.stdin.on("error", () => { /* close/error provides the final result */ });
    proc.on("error", (error) => { eventError = clipped(error.message); });
    proc.on("close", (exitCode) => {
      finished = true;
      clearTimeout(timer);
      if (killTimer) clearTimeout(killTimer);
      signal?.removeEventListener("abort", abort);
      consume(decoder.end());
      if (pending.trim()) readLine(pending);
      const status = stopped ?? (exitCode === 0 && !eventError && response ? "success" : "error");
      const error = stopped ? `Codex ${stopped}` : eventError || (exitCode !== 0 ? stderr : "") || (!response ? "Codex returned no final message" : "");
      resolve({ status, response, error: clipped(error), exitCode, threadId, model, effort, startedWork });
    });
    proc.stdin.end(task);
  });
}

async function runWithFallback(task: string, cwd: string, timeoutMs: number, signal?: AbortSignal): Promise<Result> {
  const first = await runCodex(task, cwd, timeoutMs, "gpt-6-astra", "medium", signal);
  const unavailable = /(?:model[^\n]*(?:not found|not available|unavailable|not supported|does not exist|not accessible)|(?:unknown|unsupported) model)/i.test(first.error);
  if (first.status !== "error" || first.startedWork || first.response || signal?.aborted || !unavailable) return first;
  const fallback = await runCodex(task, cwd, timeoutMs, "gpt-6.1-sol", "high", signal);
  return { ...fallback, fallbackFrom: "gpt-6-astra" };
}

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "codex_subagent",
    label: "Codex Subagent",
    description: "Run one or up to four independent read-only Codex tasks. Defaults to gpt-6-astra/medium; falls back to gpt-6.1-sol/high only on a pre-execution model-unavailable error.",
    parameters: Type.Object({
      task: Type.Optional(Type.String({ description: "One self-contained task" })),
      tasks: Type.Optional(Type.Array(Type.String(), { description: "Independent tasks, maximum four", minItems: 1, maxItems: MAX_TASKS })),
      timeoutMs: Type.Optional(Type.Number({ description: "Per-task timeout, 1000–600000 ms", minimum: 1000, maximum: MAX_TIMEOUT })),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      const single = typeof params.task === "string" && params.task.trim().length > 0;
      const multiple = Array.isArray(params.tasks) && params.tasks.length > 0;
      if (single === multiple || (multiple && (params.tasks!.length > MAX_TASKS || params.tasks!.some((task) => typeof task !== "string" || !task.trim())))) {
        return { content: [{ type: "text", text: "Provide exactly one nonempty task or 1–4 nonempty tasks." }], details: {}, isError: true };
      }
      const timeout = params.timeoutMs ?? DEFAULT_TIMEOUT;
      if (!Number.isFinite(timeout) || timeout < 1000 || timeout > MAX_TIMEOUT) {
        return { content: [{ type: "text", text: "Invalid timeoutMs." }], details: {}, isError: true };
      }
      const tasks = single ? [params.task!] : params.tasks!;
      const results = await Promise.all(tasks.map((task) => runWithFallback(task, ctx.cwd, timeout, signal)));
      const text = results.map((result, i) => `Task ${i + 1} [${result.status}] model=${result.model ?? "not started"} effort=${result.effort ?? "unknown"}${result.fallbackFrom ? ` fallback-from=${result.fallbackFrom}` : ""}${result.threadId ? ` thread=${result.threadId}` : ""}\n${result.response || result.error || "(no response)"}${result.response && result.error ? `\nError: ${result.error}` : ""}`).join("\n\n");
      return { content: [{ type: "text", text }], details: { results }, isError: results.some((result) => result.status !== "success") };
    },
  });
}
