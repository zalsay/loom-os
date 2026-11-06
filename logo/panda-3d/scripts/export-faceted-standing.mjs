import { chromium } from "playwright";
import { once } from "node:events";
import { constants } from "node:fs";
import { createHash } from "node:crypto";
import { access, copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { startServer } from "../server.mjs";

// Do not stamp an old web commit onto a later local edit. Updating the source
// requires a deliberate provenance review and an update to these hashes.
const sourceHashes = {
  "src/panda-faceted.js":
    "6a9061308e4c9e4c47dbe7659296a1a054b655797439e733b5dec18a188cb081",
  "src/model.js":
    "7891d4d71812da28ad695e9ab56a427fa17e0e605f8601871179a0a688104924",
  "src/emblem.js":
    "e2bb49a8e0ea28758ed80dc9a284ae2bad2ee5d75531cd455c71d9591a65cfef",
  "src/emblem-data.js":
    "7bad084966cfd422b928b9c5cd6b8bac505c1221a50678eab4e8954eefa0b71f",
  "src/fur.js":
    "0958a33b8d3418b7cc7ae65c69e13becd18e3a1a1b7db7da30f3344c6706b42d",
};
export async function verifySourceIntegrity(root) {
  for (const [name, expected] of Object.entries(sourceHashes)) {
    const actual = createHash("sha256")
      .update(await readFile(path.join(root, name)))
      .digest("hex");
    if (actual !== expected)
      throw new Error(
        `Source changed: ${name}; review attribution before export`,
      );
  }
}

async function main() {
  const root = fileURLToPath(new URL("../", import.meta.url));
  const output = path.resolve(
    process.argv[2] || path.join(root, "assets/panda-faceted-standing.glb"),
  );
  const preview = path.resolve(
    process.argv[3] ||
      path.join(root, "assets/panda-faceted-standing-preview.png"),
  );
  if (output === preview)
    throw new Error("Model and preview paths must differ");
  for (const target of [output, preview]) {
    try {
      await access(target);
      throw new Error(`Output already exists: ${target}`);
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
  }
  await verifySourceIntegrity(root);
  await mkdir(path.dirname(output), { recursive: true });
  await mkdir(path.dirname(preview), { recursive: true });
  const server = startServer(0);
  let browser;
  try {
    await once(server, "listening");
    const origin = `http://127.0.0.1:${server.address().port}`;
    const launch = process.env.PLAYWRIGHT_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH }
      : { channel: "chrome" };
    browser = await chromium.launch({ ...launch, headless: true });
    const page = await browser.newPage({
      viewport: { width: 1100, height: 900 },
      deviceScaleFactor: 1,
      acceptDownloads: true,
    });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.route("**/*", (route) => {
      const url = new URL(route.request().url());
      return url.origin === origin || ["data:", "blob:"].includes(url.protocol)
        ? route.continue()
        : route.abort();
    });
    await page.goto(origin);
    await page.locator('#stage[data-state="ready"]').waitFor();
    const details = await page.evaluate(async () => {
      const THREE = await import("three");
      const { GLTFExporter } = await import(
        "three/addons/exporters/GLTFExporter.js"
      );
      const { GLTFLoader } = await import("three/addons/loaders/GLTFLoader.js");
      const { createFacetedPanda } = await import("./src/panda-faceted.js");
      const { createStudio, frameModel, viewPosition } = await import(
        "./src/studio.js"
      );
      const source = createFacetedPanda();
      // Preserve the web geometry while making the lowest point sit at y=0.
      source.updateMatrixWorld(true);
      source.position.y -= new THREE.Box3().setFromObject(source).min.y;
      source.updateMatrixWorld(true);
      source.userData.assetVariant = "faceted-standing";
      source.userData.sourceProject = "loom-web";
      source.userData.sourceCommit = "b7b9418d419fa45186f5e88ec53eaf274b5a8e92";
      const bytes = await new GLTFExporter().parseAsync(source, {
        binary: true,
        onlyVisible: true,
      });
      if (!(bytes instanceof ArrayBuffer))
        throw new Error("Exporter did not return a binary GLB");
      const parsed = await new GLTFLoader().parseAsync(bytes, "");
      const model = parsed.scene;
      model.updateMatrixWorld(true);
      const bounds = new THREE.Box3().setFromObject(model);
      const size = bounds.getSize(new THREE.Vector3());
      const part = (name) => {
        const object = model.getObjectByName(name);
        if (!object) throw new Error(`GLB lacks ${name}`);
        return new THREE.Box3()
          .setFromObject(object)
          .getCenter(new THREE.Vector3());
      };
      const head = part("head"),
        torso = part("torso");
      for (const side of ["left", "right"]) {
        const arm = part(`arm-${side}`),
          paw = part(`paw-${side}`),
          foot = part(`foot-${side}`);
        if (!(paw.y < arm.y && foot.y < torso.y))
          throw new Error(`${side} limbs do not form a standing pose`);
        if (model.getObjectByName(`forearm-${side}`))
          throw new Error("Unexpected rooftop climbing limb");
      }
      if (Math.abs(bounds.min.y) > 0.00001)
        throw new Error("Standing GLB does not rest on y=0");
      if (!(head.y > torso.y && size.y > size.x && size.z > 1.5))
        throw new Error(
          "GLB bounds do not form an upright three-dimensional character",
        );
      const root = model.children.find(
        (child) => child.userData.assetVariant === "faceted-standing",
      );
      if (
        !root ||
        root.userData.assetVariant !== "faceted-standing" ||
        !model.getObjectByName("loom-emblem")
      )
        throw new Error("Missing variant provenance or existing belly emblem");
      const renderer = new THREE.WebGLRenderer({
        antialias: true,
        preserveDrawingBuffer: true,
      });
      renderer.setSize(1100, 900, false);
      const scene = createStudio(renderer, 1);
      model.traverse((object) => {
        if (object.isMesh) object.castShadow = true;
      });
      scene.add(model);
      const camera = new THREE.PerspectiveCamera(32, 1100 / 900, 0.1, 100);
      const fit = frameModel(bounds, camera.aspect, camera.fov);
      camera.position
        .copy(viewPosition("quarter", fit.distance))
        .add(fit.target);
      camera.lookAt(fit.target);
      document.body.replaceChildren(renderer.domElement);
      renderer.domElement.id = "export-preview";
      renderer.render(scene, camera);
      window.__facetedExportBlob = new Blob([bytes], {
        type: "model/gltf-binary",
      });
      return {
        bytes: bytes.byteLength,
        size: size.toArray(),
        headY: head.y,
        torsoY: torso.y,
      };
    });
    const screenshot = await page.locator("#export-preview").screenshot();
    const downloadPromise = page.waitForEvent("download");
    await page.evaluate(() => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(window.__facetedExportBlob);
      a.download = "panda-faceted-standing.glb";
      document.body.append(a);
      a.click();
      a.remove();
    });
    const download = await downloadPromise;
    if (errors.length) throw new Error(`Browser errors: ${errors.join("; ")}`);
    await copyFile(await download.path(), output, constants.COPYFILE_EXCL);
    await writeFile(preview, screenshot, { flag: "wx" });
    console.log(JSON.stringify({ output, preview, ...details }, null, 2));
  } finally {
    await browser?.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
)
  await main();
