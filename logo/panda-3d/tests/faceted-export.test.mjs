import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import os from "node:os";
import path from "node:path";
import { verifySourceIntegrity } from "../scripts/export-faceted-standing.mjs";

const script = new URL(
  "../scripts/export-faceted-standing.mjs",
  import.meta.url,
);

test("standalone export refuses to overwrite an existing asset before starting a browser", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "loom-panda-export-"));
  const output = path.join(dir, "existing.glb");
  const preview = path.join(dir, "preview.png");
  try {
    await writeFile(output, "keep this asset");
    assert.throws(
      () =>
        execFileSync(
          process.execPath,
          [fileURLToPath(script), output, preview],
          {
            encoding: "utf8",
            stdio: "pipe",
            timeout: 5000,
          },
        ),
      /already exists/,
    );
    assert.equal(await readFile(output, "utf8"), "keep this asset");
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test("export refuses stale source attribution without writing any assets", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "loom-panda-stale-"));
  try {
    await mkdir(path.join(dir, "src"));
    await writeFile(
      path.join(dir, "src/panda-faceted.js"),
      "// deliberately modified",
    );
    const output = path.join(dir, "out.glb"),
      preview = path.join(dir, "out.png");
    await assert.rejects(verifySourceIntegrity(dir), /source.*changed/i);
    await assert.rejects(readFile(output), { code: "ENOENT" });
    await assert.rejects(readFile(preview), { code: "ENOENT" });
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
