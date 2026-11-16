import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createCanvas } from '@napi-rs/canvas';
import { generateImage } from '../scripts/generate-image.mjs';
import { renderCover } from '../scripts/render-cover.mjs';

test('mock generated background flows into the local cover renderer with provenance', async t => {
  const dir = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'unified-cover-integration-'));
  t.after(() => {
    assert.equal(path.dirname(dir), fs.realpathSync(os.tmpdir()));
    assert.ok(path.basename(dir).startsWith('unified-cover-integration-'));
    fs.rmSync(dir, { recursive: true });
  });
  const source = createCanvas(512, 768);
  const ctx = source.getContext('2d');
  ctx.fillStyle = '#C8DDD1';
  ctx.fillRect(0, 0, 512, 768);
  ctx.fillStyle = '#718C32';
  ctx.fillRect(0, 400, 512, 368);
  const png = await source.encode('png');
  const generationJob = path.join(dir, 'generation.json');
  fs.writeFileSync(generationJob, JSON.stringify({ mode: 'prompt', prompt: 'A green meadow with a warm white bus', output: './background.png', palette: ['#C8DDD1', '#718C32'] }));
  let requests = 0;
  const generated = await generateImage(generationJob, {
    env: { IMAGE_API_BASE_URL: 'https://image.test/v1', IMAGE_API_KEY: 'mock-test-key', IMAGE_MODEL: 'mock-image' },
    fetchImpl: async () => {
      requests++;
      return new Response(JSON.stringify({ data: [{ b64_json: png.toString('base64') }] }), { headers: { 'content-type': 'application/json' } });
    },
  });
  const coverJob = path.join(dir, 'cover.json');
  fs.writeFileSync(coverJob, JSON.stringify({ image: './background.png', output: './cover.png', title: '把日子\n搬进山野', accent: '一起住，也一起创造' }));
  const cover = await renderCover(coverJob);
  const generationRecord = JSON.parse(fs.readFileSync(generated.manifest, 'utf8'));
  const coverRecord = JSON.parse(fs.readFileSync(cover.manifest, 'utf8'));
  assert.equal(requests, 1);
  assert.equal(generationRecord.aiGenerated, true);
  assert.equal(coverRecord.source.sha256, generationRecord.outputSha256);
  assert.equal(cover.width, 1080);
  assert.equal(cover.height, 1440);
  assert.equal(coverRecord.style.overlay.opacity, 0);
  assert.equal(coverRecord.content.subtitle, '');
  assert.ok(fs.statSync(cover.output).size > 100);
});
