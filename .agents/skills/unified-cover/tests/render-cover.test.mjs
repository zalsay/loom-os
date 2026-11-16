import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createCanvas, loadImage } from '@napi-rs/canvas';
import { DEFAULT_STYLE, SIZES, imagePlacement, prepareCover, renderCover, validateStyle } from '../scripts/render-cover.mjs';

const defaultStyle = JSON.parse(fs.readFileSync(DEFAULT_STYLE, 'utf8'));

async function fixture(t, changes = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'unified-cover-test-'));
  t.after(() => {
    assert.equal(path.dirname(dir), fs.realpathSync(os.tmpdir()));
    assert.ok(path.basename(dir).startsWith('unified-cover-test-'));
    fs.rmSync(dir, { recursive: true });
  });
  const source = createCanvas(120, 160);
  const ctx = source.getContext('2d');
  ctx.fillStyle = '#c89070';
  ctx.fillRect(0, 0, 120, 160);
  ctx.fillStyle = '#70b8a8';
  ctx.fillRect(60, 0, 60, 160);
  const image = path.join(dir, 'source.png');
  fs.writeFileSync(image, await source.encode('png'));
  const job = { image: './source.png', output: './cover.png', title: '从一个问题\n到一次尝试', ...changes };
  const config = path.join(dir, 'job.json');
  fs.writeFileSync(config, JSON.stringify(job));
  return { dir, image, config, job };
}
function change(f, patch) {
  Object.assign(f.job, patch);
  fs.writeFileSync(f.config, JSON.stringify(f.job));
}

test('default style and unknown style fields', () => {
  assert.equal(validateStyle(structuredClone(defaultStyle)).version, 'unified-cover-v2');
  const legacy = structuredClone(defaultStyle);
  delete legacy.overlay.fadeStart;
  assert.doesNotThrow(() => validateStyle(legacy));
  const badFade = structuredClone(defaultStyle);
  badFade.overlay.fadeStart = badFade.overlay.fadeEnd;
  assert.throws(() => validateStyle(badFade), /fadeStart/);
  assert.throws(() => validateStyle({ ...defaultStyle, typo: true }), /Unknown style field/);
  const bad = structuredClone(defaultStyle);
  bad.overlay.opacity = 1;
  assert.throws(() => validateStyle(bad), /opacity/);
  bad.overlay.opacity = 0.24;
  bad.type.titleMin = 0.14;
  assert.throws(() => validateStyle(bad), /minimum title size/);
});

test('crop preserves aspect ratio and focus chooses the source edge', () => {
  const left = imagePlacement(200, 100, 100, 100, 'cover', [0, 0]);
  const right = imagePlacement(200, 100, 100, 100, 'cover', [1, 1]);
  assert.deepEqual(left, { x: 0, y: 0, width: 200, height: 100, scale: 1 });
  assert.equal(right.x, -100);
  assert.deepEqual(imagePlacement(200, 100, 100, 100, 'contain', [0, 0]), { x: 0, y: 25, width: 100, height: 50, scale: 0.5 });
});

test('validate only checks all four sizes without creating outputs', async t => {
  const f = await fixture(t);
  for (const [ratio, [w, h]] of Object.entries(SIZES)) {
    change(f, { ratio });
    const result = await renderCover(f.config, { validateOnly: true });
    assert.equal(result.width, w);
    assert.equal(result.height, h);
    assert.equal(fs.existsSync(path.join(f.dir, 'cover.png')), false);
    assert.equal(fs.existsSync(path.join(f.dir, 'cover.manifest.json')), false);
  }
});

test('renders Chinese text, translucent mask, source hash and review state', async t => {
  const f = await fixture(t, { series: '探索记录', accent: '让想法慢慢成形', subtitle: '一次尝试，一次记录' });
  const before = fs.readFileSync(f.image);
  const result = await renderCover(f.config);
  assert.deepEqual(fs.readFileSync(f.image), before);
  const manifest = JSON.parse(fs.readFileSync(result.manifest, 'utf8'));
  assert.equal(manifest.width, 1080);
  assert.equal(manifest.height, 1440);
  assert.equal(manifest.source.sha256.length, 64);
  assert.equal(manifest.font.sha256.length, 64);
  assert.equal(manifest.outputSha256, result.sha256);
  assert.equal(manifest.content.title, f.job.title);
  assert.deepEqual(manifest.review, { visualApproved: false, privacyApproved: false, published: false });
  assert.equal(manifest.text.filter(b => b.kind === 'title').length, 2);
  let end = 0;
  for (const block of manifest.text) {
    assert.ok(block.bounds.y >= end);
    assert.ok(block.bounds.x + block.bounds.width <= manifest.width * 0.925 + 1);
    assert.ok(block.bounds.y + block.bounds.height <= manifest.height * 0.92);
    end = block.bounds.y + block.bounds.height;
  }
  const canvas = createCanvas(1080, 1440);
  const ctx = canvas.getContext('2d');
  ctx.drawImage(await loadImage(result.output), 0, 0);
  const top = ctx.getImageData(10, 10, 1, 1).data;
  const bottom = ctx.getImageData(10, 1430, 1, 1).data;
  assert.ok(top[0] < bottom[0], 'top mask should darken the background more');
  assert.deepEqual([...bottom], [200, 144, 112, 255], 'bottom must retain the original source pixels without a mask');
  assert.equal(top[3], 255);
});

test('top overlay retains sharp edges and lower region equals the original pixels', async t => {
  const f = await fixture(t);
  const result = await renderCover(f.config);
  const actual = createCanvas(1080, 1440);
  const ac = actual.getContext('2d');
  ac.drawImage(await loadImage(result.output), 0, 0);
  const expected = createCanvas(1080, 1440);
  const ec = expected.getContext('2d');
  ec.drawImage(await loadImage(f.image), 0, 0, 1080, 1440);
  assert.deepEqual(ac.getImageData(0, 800, 1080, 640).data, ec.getImageData(0, 800, 1080, 640).data);
  ec.globalAlpha = defaultStyle.overlay.topOpacity;
  ec.fillStyle = defaultStyle.overlay.color;
  ec.fillRect(0, 0, 1080, 80);
  assert.deepEqual(ac.getImageData(0, 16, 1080, 20).data, ec.getImageData(0, 16, 1080, 20).data);
});

test('refuses to overwrite the cover or its manifest', async t => {
  const f = await fixture(t);
  await renderCover(f.config);
  await assert.rejects(renderCover(f.config), /Output exists/);
  change(f, { output: './another.png' });
  fs.writeFileSync(path.join(f.dir, 'another.manifest.json'), 'prior record');
  await assert.rejects(renderCover(f.config), /Output exists/);
  assert.equal(fs.existsSync(path.join(f.dir, 'another.png')), false);
});

test('protects inputs even when output is a symlink', async t => {
  const f = await fixture(t);
  change(f, { output: './source.png' });
  await assert.rejects(renderCover(f.config), /Output exists/);
  fs.symlinkSync(f.image, path.join(f.dir, 'alias.png'));
  change(f, { output: './alias.png' });
  await assert.rejects(renderCover(f.config), /Output exists/);
});

test('refuses invalid configuration and extra lines', async t => {
  const f = await fixture(t);
  for (const patch of [
    { title: '' }, { title: 'one\n\ntwo' }, { title: 'one\ntwo\nthree\nfour' },
    { ratio: '2:3' }, { ratio: 'toString' }, { focus: [NaN, 0.5] },
    { focus: [1.2, 0.5] }, { fit: 'stretch' }, { subtitle: 'one\ntwo' },
    { accent: '非常长的强调行'.repeat(40) }, { title: '非常长的标题'.repeat(40) },
  ]) {
    const original = { image: './source.png', output: './cover.png', title: '测试标题' };
    f.job = { ...original, ...patch };
    fs.writeFileSync(f.config, JSON.stringify(f.job));
    await assert.rejects(prepareCover(f.config));
  }
  f.job = { image: './source.png', output: './cover.png', title: '测试标题', typo: 1 };
  fs.writeFileSync(f.config, JSON.stringify(f.job));
  await assert.rejects(prepareCover(f.config), /Unknown job field/);
});

test('title wraps without losing Chinese characters and preserves Latin words', async t => {
  const f = await fixture(t, { title: '在真实的探索中发现一个新的问题再进行一次尝试' });
  const prepared = await prepareCover(f.config);
  const title = prepared.manifest.text.filter(b => b.kind === 'title');
  assert.ok(title.length <= 3);
  assert.equal(title.map(b => b.text).join(''), f.job.title);
  change(f, { title: 'Build something meaningful with reference images' });
  const latin = (await prepareCover(f.config)).manifest.text.filter(b => b.kind === 'title');
  assert.equal(latin.map(b => b.text).join(' ').replace(/\s+/g, ' '), f.job.title);
});

test('relative custom style font resolves from the style directory', async t => {
  const f = await fixture(t);
  const styleDir = path.join(f.dir, 'styles');
  fs.mkdirSync(styleDir);
  const font = path.resolve(path.dirname(DEFAULT_STYLE), defaultStyle.font);
  const style = { ...structuredClone(defaultStyle), font: path.relative(styleDir, font) };
  fs.writeFileSync(path.join(styleDir, 'style.json'), JSON.stringify(style));
  change(f, { style: './styles/style.json' });
  assert.equal((await prepareCover(f.config)).manifest.font.path, fs.realpathSync(font));
  style.font = './missing.ttf';
  fs.writeFileSync(path.join(styleDir, 'style.json'), JSON.stringify(style));
  await assert.rejects(prepareCover(f.config), /ENOENT/);
});

test('rejects visible missing glyph boxes instead of silently delivering tofu', async t => {
  const f = await fixture(t, { title: '测试🚀' });
  await assert.rejects(prepareCover(f.config), /missing glyph/);
  change(f, { title: '正常中文', subtitle: '测试🧑' });
  await assert.rejects(prepareCover(f.config), /missing glyph/);
});

test('retries smaller title sizes when vertical safe area overflows', async t => {
  const f = await fixture(t, { ratio: '16:9', title: '第一行\n第二行\n第三行', series: '探索记录', accent: '一次尝试', subtitle: '记录成长' });
  const style = structuredClone(defaultStyle);
  style.font = path.resolve(path.dirname(DEFAULT_STYLE), style.font);
  style.layout.top = 0.25;
  style.layout.bottom = 0.25;
  style.type.title = 0.14;
  fs.writeFileSync(path.join(f.dir, 'style.json'), JSON.stringify(style));
  change(f, { style: './style.json' });
  const result = await prepareCover(f.config);
  const title = result.manifest.text.find(block => block.kind === 'title');
  assert.ok(title.size < 151 && title.size >= 67);
  assert.ok(result.manifest.text.every(block => block.bounds.y + block.bounds.height <= 810));
});

test('same source, content and style render identical PNG bytes', async t => {
  const f = await fixture(t);
  const first = await renderCover(f.config);
  change(f, { output: './cover-v002.png' });
  const second = await renderCover(f.config);
  assert.equal(first.sha256, second.sha256);
});
