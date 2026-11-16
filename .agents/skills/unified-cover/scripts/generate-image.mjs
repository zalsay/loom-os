#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { createCanvas, loadImage } from '@napi-rs/canvas';

const MAX_IMAGE = 32 * 1024 * 1024;
const MAX_RESPONSE = 64 * 1024 * 1024;
const fail = message => { throw new Error(message); };
const sha256 = data => createHash('sha256').update(data).digest('hex');
const contract = 'Create a sharp, clean cover background image only. No text, letters, numbers, captions, logos or watermarks. No blur or frosted-glass effect. Keep the upper 45 percent visually quiet for a later title overlay; place the main subject below it and preserve safe cropping space. Do not draw title panels or translucent overlays; these are added locally.';

function localPath(value, base, label) {
  if (typeof value !== 'string' || !value.trim() || /[\x00-\x1f]/.test(value) || /^\w+:\/\//.test(value)) fail(`Invalid ${label} path`);
  return path.resolve(base, value);
}
function unoccupied(target) {
  try { fs.lstatSync(target); } catch (error) {
    if (error.code === 'ENOENT') return;
    throw error;
  }
  fail('Output exists; choose a new revision');
}
function apiBase(value) {
  let url;
  try { url = new URL(value); } catch { fail('Invalid API base URL'); }
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if ((url.protocol !== 'https:' && !(local && url.protocol === 'http:')) || url.username || url.password || url.search || url.hash) fail('API base URL must use HTTPS without credentials, query or fragment');
  return url.href.replace(/\/$/, '');
}
function imageMime(bytes) {
  if (bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) return 'image/png';
  if (bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) return 'image/jpeg';
  if (bytes.toString('ascii', 0, 4) === 'RIFF' && bytes.toString('ascii', 8, 12) === 'WEBP') return 'image/webp';
  fail('Expected a PNG, JPEG or WebP image');
}
async function readImage(filename) {
  if (!fs.statSync(filename).isFile() || fs.statSync(filename).size > MAX_IMAGE) fail('Image input must be a file smaller than 32 MiB');
  const bytes = fs.readFileSync(filename);
  const mime = imageMime(bytes);
  let image;
  try { image = await loadImage(bytes); } catch { fail('Cannot decode image input'); }
  return { path: filename, bytes, mime, image, sha256: sha256(bytes) };
}
function extractPalette(image) {
  const canvas = createCanvas(48, 48);
  const ctx = canvas.getContext('2d');
  ctx.drawImage(image, 0, 0, 48, 48);
  const pixels = ctx.getImageData(0, 0, 48, 48).data;
  const groups = new Map();
  for (let i = 0; i < pixels.length; i += 4) {
    if (pixels[i + 3] < 128) continue;
    const key = [pixels[i], pixels[i + 1], pixels[i + 2]].map(v => Math.floor(v / 32)).join(',');
    const group = groups.get(key) ?? { count: 0, rgb: [0, 0, 0] };
    group.count++;
    group.rgb.forEach((_, c) => { group.rgb[c] += pixels[i + c]; });
    groups.set(key, group);
  }
  return [...groups.values()].sort((a, b) => b.count - a.count).slice(0, 5).map(g => '#' + g.rgb.map(v => Math.round(v / g.count).toString(16).padStart(2, '0')).join('').toUpperCase());
}
async function readLimited(response, limit) {
  if (Number(response.headers.get('content-length')) > limit) fail('API response exceeds the size limit');
  if (!response.body) fail('API returned an empty response');
  const reader = response.body.getReader();
  const chunks = [];
  let length = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > limit) fail('API response exceeds the size limit');
      chunks.push(Buffer.from(value));
    }
  } finally { await reader.cancel().catch(() => {}); }
  return Buffer.concat(chunks);
}
async function request(fetchImpl, url, options) {
  let response;
  try { response = await fetchImpl(url, { ...options, redirect: 'error' }); }
  catch { fail('Image API network request failed or timed out; no automatic retry was made'); }
  if (!response.ok || response.redirected) fail(`Image API request failed (HTTP ${response.status}); check endpoint, model and credentials`);
  return response;
}
function imageFromBase64(value) {
  if (typeof value !== 'string' || !value || value.length > Math.ceil(MAX_IMAGE / 3) * 4 || value.length % 4 !== 0 || !/^[A-Za-z0-9+/]+={0,2}$/.test(value)) fail('Invalid base64 image response');
  const bytes = Buffer.from(value, 'base64');
  if (bytes.toString('base64') !== value || bytes.length > MAX_IMAGE) fail('Invalid base64 image response');
  return bytes;
}

export async function generateImage(configPath, { dryRun = false, env = process.env, fetchImpl = globalThis.fetch } = {}) {
  const config = fs.realpathSync(path.resolve(configPath));
  const base = path.dirname(config);
  const input = JSON.parse(fs.readFileSync(config, 'utf8'));
  const allowed = ['mode', 'prompt', 'output', 'reference', 'paletteImage', 'palette', 'size', 'quality', 'timeoutMs'];
  if (!input || typeof input !== 'object' || Array.isArray(input)) fail('Config must be an object');
  for (const key of Object.keys(input)) if (!allowed.includes(key)) fail(`Unknown config field: ${key}`);
  const mode = input.mode ?? 'prompt';
  if (!['prompt', 'reference'].includes(mode)) fail('mode must be prompt or reference');
  if (typeof input.prompt !== 'string' || !input.prompt.trim() || input.prompt.length > 16000 || input.prompt.includes('\0')) fail('A nonempty prompt is required (maximum 16000 characters)');
  if (mode === 'reference' && !input.reference) fail('reference mode requires a local reference image');
  if (mode === 'prompt' && input.reference !== undefined) fail('Use paletteImage for local-only color extraction, or choose reference mode to upload reference');
  const output = localPath(input.output, base, 'output');
  if (path.extname(output).toLowerCase() !== '.png') fail('Output must be PNG');
  const manifest = output.replace(/\.png$/i, '.generation.json');
  [output, manifest].forEach(unoccupied);
  let ancestor = path.dirname(output);
  while (!fs.existsSync(ancestor)) ancestor = path.dirname(ancestor);
  if (!fs.statSync(ancestor).isDirectory()) fail('Output parent must be a directory');
  fs.accessSync(ancestor, fs.constants.W_OK);
  const size = input.size ?? '1024x1536';
  if (!['1024x1536', '1536x1024', '1024x1024', 'auto'].includes(size)) fail('Unsupported image size');
  if (input.quality !== undefined && !['auto', 'low', 'medium', 'high'].includes(input.quality)) fail('Unsupported quality');
  const timeoutMs = input.timeoutMs ?? 180000;
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1000 || timeoutMs > 600000) fail('timeoutMs must be 1000..600000');
  const endpoint = apiBase(env.IMAGE_API_BASE_URL || env.OPENAI_BASE_URL || 'https://api.openai.com/v1') + (mode === 'reference' ? '/images/edits' : '/images/generations');
  const model = env.IMAGE_MODEL?.trim();
  if (model && (!/^[\w./:-]+$/.test(model) || model.length > 128)) fail('Invalid IMAGE_MODEL');
  const key = env.IMAGE_API_KEY || env.OPENAI_API_KEY;
  const missing = [!model && 'IMAGE_MODEL', !key && 'IMAGE_API_KEY or OPENAI_API_KEY'].filter(Boolean);
  if (!dryRun && missing.length) fail(`Missing ${missing.join(', ')}`);
  const reference = mode === 'reference' ? await readImage(fs.realpathSync(localPath(input.reference, base, 'reference'))) : null;
  const colorSource = input.paletteImage !== undefined ? await readImage(fs.realpathSync(localPath(input.paletteImage, base, 'paletteImage'))) : reference;
  if (input.palette !== undefined && (!Array.isArray(input.palette) || input.palette.length > 8 || input.palette.some(c => typeof c !== 'string' || !/^#[a-f\d]{6}$/i.test(c)))) fail('palette must contain at most eight #RRGGBB colors');
  const palette = [...new Set([...(input.palette ?? []).map(c => c.toUpperCase()), ...(colorSource ? extractPalette(colorSource.image) : [])])].slice(0, 8);
  const prompt = [input.prompt.trim(), contract,
    mode === 'reference' ? 'Use the uploaded image as a visual and color reference, not as a source of text to reproduce. Generate a new, text-free scene rather than copying poster lettering.' : '',
    palette.length ? `Keep the dominant palette close to these colors: ${palette.join(', ')}. These colors indicate visual direction, not guaranteed exact pixel values.` : '',
  ].filter(Boolean).join('\n\n');
  const fields = { model: model || '<IMAGE_MODEL>', prompt, n: 1, size, ...(input.quality ? { quality: input.quality } : {}) };
  const describe = item => item ? { path: item.path, sha256: item.sha256, mime: item.mime, width: item.image.width, height: item.image.height } : null;
  const safe = { mode, endpoint, model: fields.model, request: { ...fields, ...(reference ? { image: describe(reference) } : {}) }, palette, paletteImage: describe(colorSource), uploadsReference: Boolean(reference), output, manifest };
  if (dryRun) return { dryRun: true, ready: missing.length === 0, missing, ...safe };
  const signal = AbortSignal.timeout(timeoutMs);
  let body;
  const headers = { Authorization: `Bearer ${key}` };
  if (reference) {
    body = new FormData();
    for (const [name, value] of Object.entries(fields)) body.append(name, String(value));
    body.append('image', new Blob([reference.bytes], { type: reference.mime }), 'reference.' + ({ 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp' }[reference.mime]));
  } else {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(fields);
  }
  const response = await request(fetchImpl, endpoint, { method: 'POST', headers, body, signal });
  let payload;
  try { payload = JSON.parse((await readLimited(response, MAX_RESPONSE)).toString('utf8')); }
  catch { fail('Invalid JSON or oversized image API response'); }
  if (!Array.isArray(payload?.data) || payload.data.length !== 1) fail('Image API response must contain one data image');
  const item = payload.data[0];
  let imageBytes;
  if (item?.b64_json !== undefined) imageBytes = imageFromBase64(item.b64_json);
  else if (typeof item?.url === 'string') {
    let url;
    try { url = new URL(item.url); } catch { fail('Invalid image download URL'); }
    const hosts = new Set((env.IMAGE_DOWNLOAD_HOSTS || new URL(endpoint).hostname).split(',').map(h => h.trim().toLowerCase()).filter(Boolean));
    if (url.protocol !== 'https:' || url.username || url.password || !hosts.has(url.hostname.toLowerCase())) fail('Image download URL must use HTTPS and an allowed host in IMAGE_DOWNLOAD_HOSTS');
    // Download hosts never receive API credentials, including signed asset URLs.
    const download = await request(fetchImpl, url.href, { method: 'GET', signal });
    imageBytes = await readLimited(download, MAX_IMAGE);
  } else fail('Image API response requires b64_json or url');
  imageMime(imageBytes);
  let generated;
  try { generated = await loadImage(imageBytes); } catch { fail('Cannot decode generated image'); }
  if (generated.width * generated.height > 40_000_000) fail('Generated image dimensions exceed the limit');
  const canvas = createCanvas(generated.width, generated.height);
  canvas.getContext('2d').drawImage(generated, 0, 0);
  const png = await canvas.encode('png');
  const record = {
    generator: 'unified-cover-image-api-v1', createdAt: new Date().toISOString(), mode, model,
    endpoint: new URL(endpoint).origin + new URL(endpoint).pathname,
    prompt, palette, size, quality: input.quality ?? null, reference: describe(reference),
    paletteSource: describe(colorSource), uploadedReference: Boolean(reference),
    output, outputSha256: sha256(png), width: generated.width, height: generated.height,
    aiGenerated: true, sourcePreserved: true, review: { visualApproved: false, published: false },
  };
  fs.mkdirSync(path.dirname(output), { recursive: true });
  [output, manifest].forEach(unoccupied);
  const owned = [];
  try {
    for (const target of [output, manifest]) {
      const fd = fs.openSync(target, 'wx');
      owned.push({ target, fd, stat: fs.fstatSync(fd) });
    }
    fs.writeFileSync(owned[0].fd, png);
    fs.writeFileSync(owned[1].fd, JSON.stringify(record, null, 2) + '\n');
  } catch (error) {
    for (const file of owned) {
      const current = fs.lstatSync(file.target);
      // Delete only this invocation's exclusive, absolute-path reservations.
      if (path.isAbsolute(file.target) && current.dev === file.stat.dev && current.ino === file.stat.ino) fs.unlinkSync(file.target);
    }
    throw error;
  } finally { for (const file of owned) fs.closeSync(file.fd); }
  return { output, manifest, width: generated.width, height: generated.height, sha256: record.outputSha256 };
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  const args = process.argv.slice(2);
  if (args.length < 1 || args.length > 2 || (args[1] !== undefined && args[1] !== '--dry-run')) {
    console.error('Usage: node generate-image.mjs <generation.json> [--dry-run]');
    process.exitCode = 2;
  } else {
    try { console.log(JSON.stringify(await generateImage(args[0], { dryRun: args[1] === '--dry-run' }), null, 2)); }
    catch (error) { console.error(`Image generation failed: ${error.message}`); process.exitCode = 1; }
  }
}
