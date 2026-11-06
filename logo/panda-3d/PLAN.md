# LoomOS panda 3D prototype — design and implementation plan

Approved direction: reconstruct the panda as a rounded 3D character, not an extruded SVG.
Baseline: main at 54531f1b996290d8d1888b63b4e7a7bf6e0badef. Existing dirty work stays untouched.

## Design contract
- Independent web viewer in logo/panda-3d; no Lua/runtime/root dependency changes.
- Original PNG/SVG assets are read-only. The original front image is reference, not a billboard pretending to be 3D.
- Procedural rounded geometry: head, ears, complete torso, limbs, tail and sculpted tuft.
- Eye patches and belly conform to their underlying curved surfaces; emblem now uses the original 104 SVG paint paths as a tight surface-conforming relief, preserving source overlap order.
- Warm ivory/charcoal matte material, soft studio lighting, restrained cream/teal UI.
- Drag orbit, scroll/pinch zoom, front/three-quarter/side/back presets, optional rotation, reference toggle, PNG/GLB export.
- Respect reduced-motion, respond to resize, pause off-screen, handle WebGL and export failures visibly.
- Node static server is bound to loopback, serves only viewer and two named reference assets, disallows traversal/other workspace files.
- Prototype only: not a production rig, image-to-3D reconstruction, exact watercolor recreation or watertight printable sculpt.
- Code review is performed by the main agent only. No commit, push, deploy or publication.

## Implementation / test sequence
1. [x] Write model tests first; confirm RED before model exists. Verify actual 3D extent, named parts, finite geometry, conformed details, no external image dependency, shared resources disposal.
2. [x] Implement model.js and make model tests GREEN. Use Three.js public APIs, deterministic material grain and reusable surface projection.
3. [x] Build studio.js / viewer.js and accessible responsive index.html + style.css. Add tests for view presets, PNG crop framing and static-server path security; confirm RED first.
4. [x] Main-agent review; run node tests and syntax checks. Execute a real Chromium browser smoke: WebGL render, orbit drag, zoom, front/side/back, reference, rotation, PNG and GLB export, reduced-motion, resize/mobile, error console, offline requests and independent GLB reload. Save screenshots and a results.json in evidence/.

## Commands
```sh
cd /Volumes/RC500/dev/loom-os/logo/panda-3d
npm ci
npm test
npm run check
npm run test:browser
npm start
```

Dependencies pinned in package-lock.json. Browser verification can use an isolated Playwright Chromium instance when the app browser cannot navigate to localhost. No existing user browser session is controlled.

## 2026-10-27 focused logo correction

- [x] Reproduce loss of source detail and floating overpass; identify original tube approximation as cause.
- [x] Add RED regression tests for source provenance, four crossing orders and surface contact.
- [x] Replace the old emblem implementation, not layer more disconnected tubes onto it. Compile original SVG paths using existing dependencies.
- [x] Add triangle-interior contact and subdivision-budget tests; retain every source contour.
- [x] Main-agent review and compare all 35 non-emblem meshes against pre-fix geometry/material hashes.
- [x] Verify actual GLB download/reload preserves all 104 paths; save front and oblique close-ups from the exported model.

## 2026-10-27 video-guided volume and pelt refinement

- [x] Inspect actual user video and sampled frames, noting the absence of a full side view.
- [x] Add RED tests for rounded depth/width ratios, muzzle projection, physical short fur and local microdetail.
- [x] Update existing volumes and shared projection functions; retain exact source SVG logo data.
- [x] Use deterministic surface-sampled short fur with original-logo occupancy avoidance, not remote assets or custom render-only shaders.
- [x] Fix normal-texture GLB portability through explicit tangent frames, not by stripping the new detail from the export.
- [x] Test unique texture, geometry, material and instanced-buffer disposal.
- [x] Main-agent review, browser multiview inspection, source-logo integrity and independent GLB reload with instancing/embedded textures.
