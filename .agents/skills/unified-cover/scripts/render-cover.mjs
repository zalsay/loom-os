#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createCanvas, loadImage, GlobalFonts } from '@napi-rs/canvas';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const DEFAULT_STYLE = path.join(ROOT, 'assets/default-style.json');
export const SIZES = { '3:4': [1080, 1440], '9:16': [1080, 1920], '1:1': [1080, 1080], '16:9': [1920, 1080] };
const hash = buffer => createHash('sha256').update(buffer).digest('hex');
const fail = message => { throw new Error(message); };
const graphemes = new Intl.Segmenter('zh', { granularity: 'grapheme' });
const words = new Intl.Segmenter('zh', { granularity: 'word' });

function object(value, allowed, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail(`${label} must be an object`);
  for (const key of Object.keys(value)) if (!allowed.includes(key)) fail(`Unknown ${label} field: ${key}`);
  for (const key of allowed) if (!(key in value)) fail(`Missing ${label} field: ${key}`);
}
function number(value, min, max, label) {
  if (!Number.isFinite(value) || value < min || value > max) fail(`Invalid ${label}: expected ${min}..${max}`);
}
function color(value) {
  if (typeof value !== 'string' || !/^#[0-9a-f]{6}$/i.test(value)) fail(`Invalid color: ${value}`);
}
function localFile(value, base, label) {
  if (typeof value !== 'string' || !value.trim() || /[\x00-\x1f]/.test(value) || /^\w+:\/\//.test(value)) fail(`Invalid ${label} path`);
  return path.resolve(base, value);
}
function text(value, label, multiline = false) {
  if (typeof value !== 'string' || value.length > 500 || /[\x00-\x09\x0b-\x1f\x7f]/.test(value) || (!multiline && value.includes('\n'))) fail(`Invalid ${label} text`);
  const normalized = value.normalize('NFC').trim();
  if (normalized.split('\n').some(line => !line.trim()) && normalized) fail(`Empty line in ${label}`);
  return normalized;
}
export function validateStyle(style) {
  object(style, ['version', 'font', 'background', 'overlay', 'colors', 'layout', 'type'], 'style');
  if (typeof style.version !== 'string' || !style.version.trim()) fail('Invalid style version');
  color(style.background);
  object({ ...style.overlay, fadeStart: style.overlay?.fadeStart ?? 0 }, ['color', 'opacity', 'topOpacity', 'fadeStart', 'fadeEnd'], 'overlay');
  color(style.overlay.color);
  number(style.overlay.opacity, 0, 0.85, 'overlay opacity');
  number(style.overlay.topOpacity, 0, 0.85, 'top opacity');
  number(style.overlay.fadeEnd, 0.1, 1, 'fadeEnd');
  number(style.overlay.fadeStart ?? 0, 0, style.overlay.fadeEnd - 0.001, 'fadeStart');
  object(style.colors, ['title', 'accent', 'secondary'], 'colors');
  Object.values(style.colors).forEach(color);
  object(style.layout, ['marginX', 'top', 'bottom', 'lineHeight', 'gap'], 'layout');
  for (const key of ['marginX', 'top', 'bottom']) number(style.layout[key], 0.03, 0.25, key);
  number(style.layout.lineHeight, 1.05, 1.8, 'lineHeight');
  number(style.layout.gap, 0.005, 0.06, 'gap');
  object(style.type, ['title', 'titleMin', 'maxLines', 'accent', 'small'], 'type');
  number(style.type.title, 0.04, 0.14, 'title size');
  number(style.type.titleMin, 0.035, style.type.title, 'minimum title size');
  number(style.type.maxLines, 1, 3, 'maxLines');
  if (!Number.isInteger(style.type.maxLines)) fail('maxLines must be an integer');
  number(style.type.accent, 0.035, 0.12, 'accent size');
  number(style.type.small, 0.02, 0.05, 'small size');
  return style;
}

export function imagePlacement(iw, ih, width, height, fit, focus) {
  const scale = fit === 'cover' ? Math.max(width / iw, height / ih) : Math.min(width / iw, height / ih);
  const w = iw * scale;
  const h = ih * scale;
  return { x: (width - w) * (fit === 'cover' ? focus[0] : 0.5) || 0, y: (height - h) * (fit === 'cover' ? focus[1] : 0.5) || 0, width: w, height: h, scale };
}

function wrap(ctx, value, maxWidth) {
  const lines = [];
  for (const paragraph of value.split('\n')) {
    let line = '';
    for (const { segment } of words.segment(paragraph)) {
      const pieces = ctx.measureText(segment).width <= maxWidth ? [segment] : Array.from(graphemes.segment(segment), item => item.segment);
      for (const piece of pieces) {
        if (line && ctx.measureText(line + piece).width > maxWidth) {
          lines.push(line.trimEnd());
          line = piece.trimStart();
        } else line += piece;
      }
    }
    if (line.trim()) lines.push(line.trimEnd());
  }
  return lines;
}

function checkMissingGlyphs(family, value) {
  const probe = createCanvas(128, 128);
  const ctx = probe.getContext('2d');
  ctx.font = `64px "${family}"`;
  function pixels(character) {
    ctx.clearRect(0, 0, 128, 128);
    ctx.fillText(character, 16, 96);
    return Buffer.from(ctx.getImageData(0, 0, 128, 128).data);
  }
  const missing = pixels(String.fromCodePoint(0x10ffff));
  for (const character of new Set(value)) {
    if (/[\s\p{Mark}\p{Cf}]/u.test(character)) continue;
    if (pixels(character).equals(missing)) fail(`Font has a missing glyph for ${character}; choose a suitable font or change the text`);
  }
}

function layoutText(ctx, job, style, family, width, height) {
  const unit = Math.min(width, height);
  const x = Math.ceil(width * style.layout.marginX);
  const maxWidth = width - 2 * x;
  const gap = Math.round(unit * style.layout.gap);
  function font(size) { ctx.font = `${size}px "${family}"`; }
  const small = Math.round(unit * style.type.small);
  for (let titleSize = Math.round(unit * style.type.title); titleSize >= Math.ceil(unit * style.type.titleMin); titleSize--) {
    font(titleSize);
    const lines = wrap(ctx, job.title, maxWidth - 4);
    if (lines.length > style.type.maxLines) continue;
    let y = Math.ceil(height * style.layout.top);
    let fits = true;
    const blocks = [];
    function addLine(value, size, fill, kind) {
      font(size);
      const m = ctx.measureText(value);
      const ascent = Math.max(0, m.actualBoundingBoxAscent);
      const descent = Math.max(0, m.actualBoundingBoxDescent);
      const left = Math.max(0, m.actualBoundingBoxLeft);
      const visualWidth = left + Math.max(m.width, m.actualBoundingBoxRight);
      if (visualWidth > maxWidth + 0.01) { fits = false; return; }
      const lineHeight = Math.ceil(Math.max(size * style.layout.lineHeight, ascent + descent));
      const baseline = y + ascent + Math.max(0, (lineHeight - ascent - descent) / 2);
      blocks.push({ kind, text: value, size, color: fill, x: x + left, baseline, bounds: { x, y, width: visualWidth, height: lineHeight } });
      y += lineHeight;
    }
    if (job.series) { addLine(job.series, small, style.colors.secondary, 'series'); y += gap; }
    lines.forEach(line => addLine(line, titleSize, style.colors.title, 'title'));
    if (job.accent) { y += gap; addLine(job.accent, Math.round(unit * style.type.accent), style.colors.accent, 'accent'); }
    if (job.subtitle) { y += gap; addLine(job.subtitle, small, style.colors.secondary, 'subtitle'); }
    if (fits && y <= height * (1 - style.layout.bottom)) return blocks;
  }
  fail('Text does not fit within the fixed font range, line limit and safe area; shorten it');
}

export async function prepareCover(configPath) {
  const jobPath = fs.realpathSync(path.resolve(configPath));
  const base = path.dirname(jobPath);
  const input = JSON.parse(fs.readFileSync(jobPath, 'utf8'));
  if (!input || typeof input !== 'object' || Array.isArray(input)) fail('Job must be an object');
  const allowed = ['image', 'output', 'title', 'style', 'ratio', 'series', 'accent', 'subtitle', 'fit', 'focus'];
  for (const key of Object.keys(input)) if (!allowed.includes(key)) fail(`Unknown job field: ${key}`);
  const job = { ...input, title: text(input.title, 'title', true), ratio: input.ratio ?? '3:4', fit: input.fit ?? 'cover', focus: input.focus ?? [0.5, 0.5] };
  if (!job.title) fail('Title must not be empty');
  for (const key of ['series', 'accent', 'subtitle']) job[key] = text(input[key] ?? '', key);
  if (!Object.hasOwn(SIZES, job.ratio)) fail('Unsupported ratio');
  if (!['cover', 'contain'].includes(job.fit)) fail('fit must be cover or contain');
  if (!Array.isArray(job.focus) || job.focus.length !== 2) fail('focus must contain two numbers');
  job.focus.forEach(n => number(n, 0, 1, 'focus'));
  const imagePath = fs.realpathSync(localFile(job.image, base, 'image'));
  const stylePath = fs.realpathSync(job.style === undefined ? DEFAULT_STYLE : localFile(job.style, base, 'style'));
  const style = validateStyle(JSON.parse(fs.readFileSync(stylePath, 'utf8')));
  const fontPath = fs.realpathSync(localFile(style.font, path.dirname(stylePath), 'font'));
  const output = localFile(job.output, base, 'output');
  if (path.extname(output).toLowerCase() !== '.png') fail('Output must be PNG');
  const manifestPath = output.replace(/\.png$/i, '.manifest.json');
  for (const target of [output, manifestPath]) {
    if (fs.existsSync(target)) fail(`Output exists; choose a new revision: ${target}`);
  }
  const imageBytes = fs.readFileSync(imagePath);
  const fontBytes = fs.readFileSync(fontPath);
  const family = `UnifiedCover_${hash(fontBytes).slice(0, 16)}`;
  if (!GlobalFonts.has(family) && !GlobalFonts.registerFromPath(fontPath, family)) fail('Could not register font');
  checkMissingGlyphs(family, [job.title, job.series, job.accent, job.subtitle].join(''));
  const image = await loadImage(imageBytes);
  if (image.width <= 0 || image.height <= 0) fail('Empty image');
  const [width, height] = SIZES[job.ratio];
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext('2d');
  const blocks = layoutText(ctx, job, style, family, width, height);
  const placement = imagePlacement(image.width, image.height, width, height, job.fit, job.focus);
  const manifest = {
    renderer: 'unified-cover-v1', createdAt: new Date().toISOString(),
    source: { path: imagePath, sha256: hash(imageBytes), width: image.width, height: image.height },
    font: { path: fontPath, sha256: hash(fontBytes) }, stylePath, style: { ...style, font: fontPath },
    configPath: jobPath, configSha256: hash(fs.readFileSync(jobPath)),
    output, ratio: job.ratio, width, height, fit: job.fit, focus: job.focus,
    content: { title: job.title, series: job.series, accent: job.accent, subtitle: job.subtitle },
    placement, text: blocks, review: { visualApproved: false, privacyApproved: false, published: false },
  };
  return { canvas, ctx, image, job, style, family, output, manifestPath, manifest };
}

export async function renderCover(configPath, { validateOnly = false } = {}) {
  const prepared = await prepareCover(configPath);
  const { canvas, ctx, image, style, family, output, manifestPath, manifest } = prepared;
  if (validateOnly) return { valid: true, ...manifest };
  const { width, height, placement } = manifest;
  ctx.fillStyle = style.background;
  ctx.fillRect(0, 0, width, height);
  ctx.drawImage(image, placement.x, placement.y, placement.width, placement.height);
  ctx.globalAlpha = style.overlay.opacity;
  ctx.fillStyle = style.overlay.color;
  ctx.fillRect(0, 0, width, height);
  ctx.globalAlpha = 1;
  // A separate alpha layer retains source detail without an opaque title panel.
  const mask = createCanvas(width, height);
  const mc = mask.getContext('2d');
  mc.fillStyle = style.overlay.color;
  mc.fillRect(0, 0, width, height);
  mc.globalCompositeOperation = 'destination-in';
  const gradient = mc.createLinearGradient(0, height * (style.overlay.fadeStart ?? 0), 0, height * style.overlay.fadeEnd);
  gradient.addColorStop(0, `rgba(0,0,0,${style.overlay.topOpacity})`);
  gradient.addColorStop(1, 'rgba(0,0,0,0)');
  mc.fillStyle = gradient;
  mc.fillRect(0, 0, width, height);
  ctx.drawImage(mask, 0, 0);
  for (const block of manifest.text) {
    ctx.font = `${block.size}px "${family}"`;
    ctx.fillStyle = block.color;
    ctx.fillText(block.text, block.x, block.baseline);
  }
  const png = await canvas.encode('png');
  manifest.outputSha256 = hash(png);
  fs.mkdirSync(path.dirname(output), { recursive: true });
  // Exclusive writes keep earlier revisions and all input files intact.
  const recordFd = fs.openSync(manifestPath, 'wx');
  try {
    fs.writeFileSync(output, png, { flag: 'wx' });
    fs.writeFileSync(recordFd, JSON.stringify(manifest, null, 2) + '\n');
  } finally { fs.closeSync(recordFd); }
  return { output, manifest: manifestPath, width, height, sha256: manifest.outputSha256 };
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  const args = process.argv.slice(2);
  if (args.length < 1 || args.length > 2 || (args[1] !== undefined && args[1] !== '--validate')) {
    console.error('Usage: node render-cover.mjs <job.json> [--validate]');
    process.exitCode = 2;
  } else {
    try { console.log(JSON.stringify(await renderCover(args[0], { validateOnly: args[1] === '--validate' }), null, 2)); }
    catch (error) { console.error(`Cover failed: ${error.message}`); process.exitCode = 1; }
  }
}
