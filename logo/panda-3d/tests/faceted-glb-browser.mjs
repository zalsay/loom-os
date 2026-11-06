import { chromium } from "playwright";
import assert from "node:assert/strict";
import { once } from "node:events";
import { readFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { startServer } from "../server.mjs";

const glb = await readFile(
  new URL("../assets/panda-faceted-standing.glb", import.meta.url),
);
const server = startServer(0);
let browser;
try {
  await once(server, "listening");
  const origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch(
    process.env.PLAYWRIGHT_EXECUTABLE_PATH
      ? {
          executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH,
          headless: true,
        }
      : { channel: "chrome", headless: true },
  );
  const page = await browser.newPage({
    viewport: { width: 1100, height: 900 },
    deviceScaleFactor: 1,
  });
  const errors = [],
    external = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (url.origin === origin && url.pathname === "/actual-standing.glb")
      return route.fulfill({
        status: 200,
        contentType: "model/gltf-binary",
        body: glb,
      });
    if (url.origin === origin || ["data:", "blob:"].includes(url.protocol))
      return route.continue();
    external.push(url.origin);
    return route.abort();
  });
  await page.goto(origin);
  await page.locator('#stage[data-state="ready"]').waitFor();
  const result = await page.evaluate(async (origin) => {
    const THREE = await import("three");
    const { GLTFLoader } = await import("three/addons/loaders/GLTFLoader.js");
    const { createFacetedPanda } = await import("./src/panda-faceted.js");
    const { createStudio, frameModel, viewPosition } = await import(
      "./src/studio.js"
    );
    const gltf = await new GLTFLoader().loadAsync(
      `${origin}/actual-standing.glb`,
    );
    const loaded = gltf.scene,
      source = createFacetedPanda();
    source.updateMatrixWorld(true);
    source.position.y -= new THREE.Box3().setFromObject(source).min.y;
    loaded.updateMatrixWorld(true);
    source.updateMatrixWorld(true);
    const checks = [];
    for (const name of [
      "head",
      "torso",
      "belly",
      "eye-patch-left",
      "eye-patch-right",
      "nose",
      "arm-left",
      "arm-right",
      "foot-left",
      "foot-right",
    ]) {
      const a = source.getObjectByName(name),
        b = loaded.getObjectByName(name);
      if (!a || !b) throw new Error(`Missing source or loaded part: ${name}`);
      const p = a.geometry.getAttribute("position"),
        q = b.geometry.getAttribute("position");
      if (p.count !== q.count) throw new Error(`Vertex count changed: ${name}`);
      let maxError = 0;
      for (let i = 0; i < p.count; i++) {
        const u = new THREE.Vector3()
          .fromBufferAttribute(p, i)
          .applyMatrix4(a.matrixWorld);
        const v = new THREE.Vector3()
          .fromBufferAttribute(q, i)
          .applyMatrix4(b.matrixWorld);
        maxError = Math.max(maxError, u.distanceTo(v));
      }
      if (maxError > 1e-5)
        throw new Error(`Transformed geometry changed: ${name}: ${maxError}`);
      checks.push({ name, vertices: p.count, maxError });
    }
    const bounds = new THREE.Box3().setFromObject(loaded),
      size = bounds.getSize(new THREE.Vector3());
    const front = new THREE.Box3()
      .setFromObject(loaded.getObjectByName("head"))
      .getCenter(new THREE.Vector3());
    const torso = new THREE.Box3()
      .setFromObject(loaded.getObjectByName("torso"))
      .getCenter(new THREE.Vector3());
    if (Math.abs(bounds.min.y) > 0.00001)
      throw new Error(`Feet are not grounded at y=0: ${bounds.min.y}`);
    if (front.y <= torso.y || size.y <= size.x || size.z <= 1.5)
      throw new Error("Asset is not standing upright in 3D");
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      preserveDrawingBuffer: true,
    });
    renderer.setSize(1100, 900, false);
    const scene = createStudio(renderer, 1);
    loaded.traverse((object) => {
      if (object.isMesh) object.castShadow = true;
    });
    scene.add(loaded);
    const camera = new THREE.PerspectiveCamera(32, 1100 / 900, 0.1, 100);
    const fit = frameModel(bounds, camera.aspect, camera.fov);
    document.body.replaceChildren(renderer.domElement);
    renderer.domElement.id = "actual-asset";
    window.__renderStandingView = (name) => {
      camera.position.copy(viewPosition(name, fit.distance)).add(fit.target);
      camera.lookAt(fit.target);
      renderer.render(scene, camera);
    };
    return { size: size.toArray(), headY: front.y, torsoY: torso.y, checks };
  }, origin);
  for (const view of ["front", "side", "back"]) {
    await page.evaluate((name) => window.__renderStandingView(name), view);
    if (process.env.PANDA_CHECK_IMAGES) {
      await mkdir(process.env.PANDA_CHECK_IMAGES, { recursive: true });
      await page.locator("#actual-asset").screenshot({
        path: path.join(process.env.PANDA_CHECK_IMAGES, `${view}.png`),
      });
    }
  }
  assert.deepEqual(errors, []);
  assert.deepEqual(external, []);
  console.log(
    JSON.stringify({ actualFileBytes: glb.length, ...result }, null, 2),
  );
} finally {
  await browser?.close();
  await new Promise((resolve) => server.close(resolve));
}
