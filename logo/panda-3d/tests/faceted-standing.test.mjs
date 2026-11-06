import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import { createFacetedPanda } from "../src/panda-faceted.js";
import { createPanda, disposePanda } from "../src/model.js";

test("the new faceted variant is independent, upright, and keeps the old mascot unchanged", () => {
  const sculpture = createFacetedPanda();
  const original = createPanda();
  try {
    sculpture.updateMatrixWorld(true);
    assert.equal(sculpture.name, "LoomOS Panda");
    assert.equal(sculpture.userData.rooftopPose, undefined);
    for (const side of ["left", "right"]) {
      const arm = sculpture.getObjectByName(`arm-${side}`);
      const paw = sculpture.getObjectByName(`paw-${side}`);
      const foot = sculpture.getObjectByName(`foot-${side}`);
      assert.ok(arm && paw && foot);
      assert.ok(
        paw.position.y < arm.position.y,
        "arms rest at sides instead of reaching up",
      );
      assert.ok(
        foot.position.y < 0.3 && foot.position.y > 0.1,
        "feet rest below the body",
      );
      assert.equal(sculpture.getObjectByName(`forearm-${side}`), undefined);
    }
    const head = sculpture.getObjectByName("head");
    assert.equal(head.material.flatShading, true);
    assert.equal(head.geometry.index, null);
    assert.ok(
      new THREE.Box3().setFromObject(head).getSize(new THREE.Vector3()).x >=
        2.6,
    );
    assert.equal(sculpture.getObjectByName("tuft"), undefined);
    assert.equal(sculpture.getObjectByName("short-fur"), undefined);
    assert.ok(sculpture.getObjectByName("loom-emblem"));
    assert.ok(
      original.getObjectByName("short-fur"),
      "existing mascot keeps its fur",
    );
    assert.ok(
      original.getObjectByName("tuft"),
      "existing mascot keeps its crown tuft",
    );
    assert.notEqual(
      sculpture.getObjectByName("head").geometry,
      original.getObjectByName("head").geometry,
    );
  } finally {
    disposePanda(sculpture);
    disposePanda(original);
  }
});
