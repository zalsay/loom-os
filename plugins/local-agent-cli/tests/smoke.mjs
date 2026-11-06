import { spawn } from "node:child_process";
import process from "node:process";
import { apply } from "../index.js";

const provider = process.argv[2];
if (!["codex", "agy", "claude"].includes(provider)) {
  throw new Error("usage: node tests/smoke.mjs <codex|agy|claude>");
}

let registered;
const fakeCtx = {
  tools: {
    register(definition) {
      registered = definition;
    },
  },
  workingDirectory: {
    async ensure() {
      return process.cwd();
    },
  },
  subprocess: {
    async resolveExecutable(command) {
      return command;
    },
    spawn(spec) {
      const child = spawn(spec.argv[0], spec.argv.slice(1), {
        cwd: spec.cwd,
        env: { ...process.env, ...spec.env },
        stdio: ["pipe", "pipe", "pipe"],
      });
      const stdout = [];
      const stderr = [];
      child.stdout.on("data", (chunk) => stdout.push(chunk));
      child.stderr.on("data", (chunk) => stderr.push(chunk));

      if (typeof spec.stdio.stdin === "object") {
        child.stdin.end(spec.stdio.stdin.data);
      } else {
        child.stdin.end();
      }

      const abort = () => child.kill("SIGTERM");
      spec.signal?.addEventListener("abort", abort, { once: true });
      const done = new Promise((resolve, reject) => {
        child.on("error", reject);
        child.on("close", (exitCode, signal) => {
          spec.signal?.removeEventListener("abort", abort);
          resolve({ exitCode, signal });
        });
      });

      const reader = (chunks) => ({
        readFrom() {
          const text = Buffer.concat(chunks).toString("utf8");
          return { text, nextOffset: Buffer.byteLength(text), lossy: false };
        },
      });

      return {
        done,
        collected: {
          stdout: reader(stdout),
          stderr: reader(stderr),
        },
        terminate: () => child.kill("SIGTERM"),
        waitForExit: () => done.then(() => true),
      };
    },
  },
};

apply(fakeCtx, {});
if (registered === undefined) throw new Error("plugin did not register run_cli_agent");

const controller = new AbortController();
const input = {
  provider,
  prompt: "Reply with exactly OK. Do not inspect or modify any files.",
  timeout_seconds: 180,
  read_only: true,
};
if (process.argv[3] !== undefined) input.model = process.argv[3];
const result = await registered.execute(input, {
  agent: { id: "local-agent-cli-smoke" },
  signal: controller.signal,
});

console.log(JSON.stringify(result, null, 2));
if (result.exitCode !== 0) process.exitCode = 1;
