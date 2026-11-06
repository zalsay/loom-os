import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const asset = new URL("../assets/panda-faceted-standing.glb", import.meta.url);

test("delivered standing GLB is self-contained and retains source and emblem metadata", async () => {
  const bytes = await readFile(asset);
  assert.equal(bytes.subarray(0, 4).toString(), "glTF");
  assert.equal(bytes.readUInt32LE(4), 2);
  assert.equal(bytes.readUInt32LE(8), bytes.length);
  const jsonLength = bytes.readUInt32LE(12);
  assert.equal(bytes.subarray(16, 20).toString(), "JSON");
  const gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString());
  const model = gltf.nodes.find(
    (n) => n.extras?.assetVariant === "faceted-standing",
  );
  assert.equal(model?.extras?.sourceProject, "loom-web");
  assert.equal(
    model?.extras?.sourceCommit,
    "b7b9418d419fa45186f5e88ec53eaf274b5a8e92",
  );
  assert.equal(model?.extras?.rooftopPose, undefined);
  assert.ok(
    (model.translation?.[1] ?? model.matrix?.[13]) > 0 &&
      (model.translation?.[1] ?? model.matrix?.[13]) < 0.01,
    "source is lifted minimally to ground the feet",
  );
  for (const name of [
    "head",
    "torso",
    "arm-left",
    "arm-right",
    "paw-left",
    "paw-right",
    "foot-left",
    "foot-right",
    "tail",
  ])
    assert.ok(
      gltf.nodes.some((n) => n.name === name),
      `${name} is present`,
    );
  assert.ok(
    !gltf.nodes.some((n) =>
      /^forearm-|^shin-|^knee-|studio floor/.test(n.name || ""),
    ),
  );
  const emblem = gltf.nodes.find((n) => n.name === "loom-emblem");
  assert.equal(emblem?.children?.length, 104);
  assert.equal(emblem.extras?.source, "LoomOS-panda-ink-clean.svg");
  assert.ok(
    (gltf.images || []).every((image) => Number.isInteger(image.bufferView)),
  );
  assert.ok(
    (gltf.buffers || []).every((buffer) => !buffer.uri),
    "no remote or separate buffers",
  );
});

test("all exported floating-point vertex normals are finite and unit length", async () => {
  const bytes = await readFile(asset);
  const jsonLength = bytes.readUInt32LE(12);
  const gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString());
  const chunkOffset = 20 + jsonLength;
  assert.equal(
    bytes.subarray(chunkOffset + 4, chunkOffset + 8).toString("ascii"),
    "BIN\0",
  );
  const binaryStart = chunkOffset + 8;
  let checked = 0;
  for (const mesh of gltf.meshes || []) {
    for (const primitive of mesh.primitives || []) {
      if (primitive.attributes.NORMAL === undefined) continue;
      const accessor = gltf.accessors[primitive.attributes.NORMAL];
      const view = gltf.bufferViews[accessor.bufferView];
      assert.equal(accessor.componentType, 5126);
      assert.equal(accessor.type, "VEC3");
      assert.equal(accessor.sparse, undefined);
      for (let i = 0; i < accessor.count; i++) {
        const offset =
          binaryStart +
          (view.byteOffset || 0) +
          (accessor.byteOffset || 0) +
          i * (view.byteStride || 12);
        const normal = Math.hypot(
          bytes.readFloatLE(offset),
          bytes.readFloatLE(offset + 4),
          bytes.readFloatLE(offset + 8),
        );
        if (!Number.isFinite(normal) || Math.abs(normal - 1) > 0.001)
          assert.fail(
            `Invalid normal in ${mesh.name || "mesh"} at index ${i}: ${normal}`,
          );
        checked++;
      }
    }
  }
  assert.ok(checked > 10000);
});
