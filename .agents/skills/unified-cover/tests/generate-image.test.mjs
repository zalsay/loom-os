import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createCanvas, loadImage } from '@napi-rs/canvas';
import { generateImage } from '../scripts/generate-image.mjs';

const apiKey = 'sk-test-image-secret-do-not-record';
const liveEnv = {
  IMAGE_API_BASE_URL: 'https://images.example.test/v1',
  IMAGE_API_KEY: apiKey,
  IMAGE_MODEL: 'test-image-model',
};
const pngSignature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

async function png(color, width = 24, height = 32) {
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, width, height);
  return canvas.encode('png');
}

async function fixture(t, changes = {}) {
  const root = fs.realpathSync(os.tmpdir());
  const dir = fs.mkdtempSync(path.join(root, 'unified-cover-generate-test-'));
  t.after(() => {
    assert.ok(path.isAbsolute(dir));
    assert.equal(fs.realpathSync(dir), path.resolve(dir));
    assert.equal(path.dirname(dir), root);
    assert.ok(path.basename(dir).startsWith('unified-cover-generate-test-'));
    fs.rmSync(dir, { recursive: true });
  });
  const reference = path.join(dir, 'reference.png');
  const paletteImage = path.join(dir, 'palette.png');
  fs.writeFileSync(reference, await png('#b84466'));
  fs.writeFileSync(paletteImage, await png('#21a87b'));
  const job = { prompt: 'A clear photograph of a small paper house.', output: './generated.png', ...changes };
  const config = path.join(dir, 'job.json');
  fs.writeFileSync(config, JSON.stringify(job));
  return { dir, reference, paletteImage, config, job, generated: await png('#4078ac') };
}

function change(f, patch) {
  Object.assign(f.job, patch);
  fs.writeFileSync(f.config, JSON.stringify(f.job));
}

function locations(f) {
  const output = path.resolve(f.dir, f.job.output);
  return { output, manifest: output.replace(/\.png$/i, '.generation.json') };
}

function noOutputs(f) {
  const { output, manifest } = locations(f);
  assert.equal(fs.existsSync(output), false, 'no image should have been written');
  assert.equal(fs.existsSync(manifest), false, 'no generation record should have been written');
}

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

function successResponse(f) {
  return jsonResponse({ data: [{ b64_json: f.generated.toString('base64') }] });
}

function noFetch(t) {
  let calls = 0;
  t.after(() => assert.equal(calls, 0, 'fetchImpl must not be called'));
  return async () => {
    calls++;
    assert.fail('fetchImpl must not be called');
  };
}

function endpoint(value) {
  return new URL(String(value));
}

function assertSafe(value, forbidden = []) {
  const text = typeof value === 'string' ? value : JSON.stringify(value);
  for (const secret of [apiKey, ...forbidden]) {
    assert.equal(text.includes(secret), false, 'preview or record must not contain sensitive data');
  }
  assert.doesNotMatch(text, /data:image\/[^;]+;base64,/i);
}

async function assertGenerated(f, result, forbidden = []) {
  const expected = locations(f);
  assert.equal(path.resolve(result.output), expected.output);
  assert.equal(path.resolve(result.manifest), expected.manifest);
  const bytes = fs.readFileSync(result.output);
  assert.deepEqual(bytes.subarray(0, 8), pngSignature);
  const image = await loadImage(bytes);
  assert.equal(image.width, 24);
  assert.equal(image.height, 32);
  const record = fs.readFileSync(result.manifest, 'utf8');
  assert.doesNotThrow(() => JSON.parse(record));
  assertSafe(record, [f.generated.toString('base64'), ...forbidden]);
}

test('dry-run uses prompt defaults without credentials, fetch, or output', async t => {
  const f = await fixture(t);
  const result = await generateImage(f.config, { dryRun: true, env: {}, fetchImpl: noFetch(t) });
  assert.equal(result.dryRun, true);
  assert.equal(result.mode, 'prompt');
  assert.equal(endpoint(result.endpoint).href, 'https://api.openai.com/v1/images/generations');
  assert.ok(result.request && typeof result.request === 'object');
  assertSafe(result);
  noOutputs(f);
});

test('dry-run reference preview does not expose source bytes or credentials', async t => {
  const f = await fixture(t, { mode: 'reference', reference: './reference.png' });
  const before = fs.readFileSync(f.reference);
  const result = await generateImage(f.config, { dryRun: true, env: liveEnv, fetchImpl: noFetch(t) });
  assert.equal(result.dryRun, true);
  assert.equal(result.mode, 'reference');
  assert.equal(endpoint(result.endpoint).pathname, '/v1/images/edits');
  assert.equal(result.model, liveEnv.IMAGE_MODEL);
  assertSafe(result, [before.toString('base64')]);
  assert.deepEqual(fs.readFileSync(f.reference), before);
  noOutputs(f);
});

test('dry-run accepts all documented sizes and optional qualities', async t => {
  const f = await fixture(t);
  for (const size of ['1024x1024', '1536x1024', '1024x1536', 'auto']) {
    for (const quality of ['auto', 'low', 'medium', 'high']) {
      change(f, { size, quality });
      const result = await generateImage(f.config, { dryRun: true, env: {}, fetchImpl: noFetch(t) });
      assert.equal(result.dryRun, true);
      noOutputs(f);
    }
  }
});

test('live prompt sends authenticated JSON with one image and writes PNG plus safe record', async t => {
  const f = await fixture(t);
  let calls = 0;
  const result = await generateImage(f.config, {
    env: liveEnv,
    fetchImpl: async (url, init) => {
      calls++;
      assert.equal(endpoint(url).href, 'https://images.example.test/v1/images/generations');
      assert.equal(init.method, 'POST');
      const headers = new Headers(init.headers);
      assert.equal(headers.get('authorization'), `Bearer ${apiKey}`);
      assert.match(headers.get('content-type'), /application\/json/i);
      const body = JSON.parse(init.body);
      assert.equal(body.model, liveEnv.IMAGE_MODEL);
      assert.equal(body.n, 1);
      assert.equal(body.size, '1024x1536');
      assert.ok(body.prompt.includes(f.job.prompt));
      assert.equal('image' in body, false);
      assert.equal('images' in body, false);
      return successResponse(f);
    },
  });
  assert.equal(calls, 1);
  await assertGenerated(f, result);
});

test('reference request uploads exactly the reference image, never its palette image', async t => {
  const f = await fixture(t, {
    mode: 'reference', reference: './reference.png', paletteImage: './palette.png',
    palette: ['#112233', '#AABBCC'], size: '1536x1024', quality: 'high',
  });
  const referenceBefore = fs.readFileSync(f.reference);
  const paletteBefore = fs.readFileSync(f.paletteImage);
  let calls = 0;
  const result = await generateImage(f.config, {
    env: liveEnv,
    fetchImpl: async (url, init) => {
      calls++;
      assert.equal(endpoint(url).pathname, '/v1/images/edits');
      assert.equal(init.method, 'POST');
      const headers = new Headers(init.headers);
      assert.equal(headers.get('authorization'), `Bearer ${apiKey}`);
      assert.equal(headers.has('content-type'), false, 'fetch must create the multipart boundary');
      assert.ok(init.body instanceof FormData);
      const form = init.body;
      assert.equal(form.get('model'), liveEnv.IMAGE_MODEL);
      assert.equal(form.get('n'), '1');
      assert.equal(form.get('size'), '1536x1024');
      assert.equal(form.get('quality'), 'high');
      assert.ok(form.get('prompt').includes(f.job.prompt));
      assert.equal(form.getAll('image').length, 1);
      const files = [...form.entries()].filter(([, value]) => typeof value !== 'string');
      assert.equal(files.length, 1, 'palette input must not become a second upload');
      assert.equal(files[0][0], 'image');
      assert.deepEqual(Buffer.from(await files[0][1].arrayBuffer()), referenceBefore);
      assertSafe([...form.entries()].filter(([, value]) => typeof value === 'string'), [paletteBefore.toString('base64')]);
      return successResponse(f);
    },
  });
  assert.equal(calls, 1);
  await assertGenerated(f, result, [referenceBefore.toString('base64'), paletteBefore.toString('base64')]);
  assert.deepEqual(fs.readFileSync(f.reference), referenceBefore);
  assert.deepEqual(fs.readFileSync(f.paletteImage), paletteBefore);
});

test('palette-only prompt mode extracts locally and remains a JSON generations request', async t => {
  const f = await fixture(t, { paletteImage: './palette.png' });
  const before = fs.readFileSync(f.paletteImage);
  const preview = await generateImage(f.config, { dryRun: true, env: {}, fetchImpl: noFetch(t) });
  fs.writeFileSync(f.paletteImage, await png('#e4b329'));
  const changedPreview = await generateImage(f.config, { dryRun: true, env: {}, fetchImpl: noFetch(t) });
  assert.notDeepEqual(changedPreview.request, preview.request, 'palette pixels should affect the safe request preview');
  fs.writeFileSync(f.paletteImage, before);
  change(f, { palette: ['#ABCDEF'] });
  let calls = 0;
  const result = await generateImage(f.config, {
    env: liveEnv,
    fetchImpl: async (url, init) => {
      calls++;
      assert.equal(endpoint(url).pathname, '/v1/images/generations');
      assert.equal(typeof init.body, 'string');
      const body = JSON.parse(init.body);
      assert.ok(body.prompt.includes(f.job.prompt));
      assert.match(JSON.stringify(body), /#abcdef/i);
      assert.equal('image' in body, false);
      assert.equal('images' in body, false);
      assert.equal('paletteImage' in body, false);
      assertSafe(body, [before.toString('base64'), f.paletteImage, './palette.png']);
      return successResponse(f);
    },
  });
  assert.equal(calls, 1);
  await assertGenerated(f, result, [before.toString('base64')]);
  assert.deepEqual(fs.readFileSync(f.paletteImage), before);
});

test('API key falls back to OPENAI_API_KEY and IMAGE_API_KEY takes precedence', async t => {
  const f = await fixture(t);
  const fallback = 'sk-test-fallback-secret';
  for (const [env, expected] of [
    [{ IMAGE_MODEL: 'fallback-model', OPENAI_API_KEY: fallback }, fallback],
    [{ ...liveEnv, OPENAI_API_KEY: fallback }, apiKey],
  ]) {
    change(f, { output: `./key-${expected === apiKey ? 'primary' : 'fallback'}.png` });
    let calls = 0;
    const result = await generateImage(f.config, {
      env,
      fetchImpl: async (url, init) => {
        calls++;
        assert.equal(new Headers(init.headers).get('authorization'), `Bearer ${expected}`);
        assert.equal(endpoint(url).hostname, env.IMAGE_API_BASE_URL ? 'images.example.test' : 'api.openai.com');
        return successResponse(f);
      },
    });
    assert.equal(calls, 1);
    await assertGenerated(f, result, [fallback]);
  }
});

test('live requests require an API key and explicit model before fetch', async t => {
  const f = await fixture(t);
  for (const [env, pattern] of [
    [{ IMAGE_MODEL: 'test-model' }, /key|credential|auth/i],
    [{ IMAGE_API_KEY: apiKey }, /model/i],
  ]) {
    await assert.rejects(generateImage(f.config, { env, fetchImpl: noFetch(t) }), pattern);
    noOutputs(f);
  }
});

test('rejects unknown fields and invalid configuration before any network request', async t => {
  const f = await fixture(t);
  const original = { ...f.job };
  const cases = [
    [{ unexpectedField: true }, /unknown|field|config|unsupported/i],
    [{ prompt: undefined }, /prompt|required|config/i],
    [{ prompt: '' }, /prompt|required|config/i],
    [{ prompt: '   ' }, /prompt|required|config/i],
    [{ prompt: 42 }, /prompt|config|invalid/i],
    [{ output: undefined }, /output|required|config/i],
    [{ output: '' }, /output|required|config/i],
    [{ output: './generated.jpg' }, /output|png|config/i],
    [{ output: 42 }, /output|config|invalid/i],
    [{ mode: 'edit' }, /mode|config|invalid/i],
    [{ mode: 'toString' }, /mode|config|invalid/i],
    [{ size: '1024x768' }, /size|config|invalid/i],
    [{ size: 'toString' }, /size|config|invalid/i],
    [{ quality: 'ultra' }, /quality|config|invalid/i],
    [{ palette: '#112233' }, /palette|config|invalid/i],
    [{ palette: ['#123'] }, /palette|color|config|invalid/i],
    [{ palette: ['#12345z'] }, /palette|color|config|invalid/i],
    [{ palette: [123] }, /palette|color|config|invalid/i],
    [{ mode: 'reference' }, /reference|required|config/i],
    [{ mode: 'reference', reference: './missing.png' }, /reference|file|ENOENT|exist/i],
    [{ mode: 'reference', reference: 'https://example.test/input.png' }, /reference|local|file|path|ENOENT|URL/i],
    [{ mode: 'reference', reference: '.' }, /reference|file|directory|EISDIR|image/i],
    [{ paletteImage: './missing.png' }, /palette|file|ENOENT|exist/i],
    [{ paletteImage: 'https://example.test/palette.png' }, /palette|local|file|path|ENOENT|URL/i],
    [{ paletteImage: '.' }, /palette|file|directory|EISDIR|image/i],
  ];
  for (const [patch, pattern] of cases) {
    f.job = { ...original, ...patch };
    fs.writeFileSync(f.config, JSON.stringify(f.job));
    await assert.rejects(generateImage(f.config, { env: liveEnv, fetchImpl: noFetch(t) }), pattern);
    assert.equal(fs.existsSync(path.join(f.dir, 'generated.png')), false);
    assert.equal(fs.existsSync(path.join(f.dir, 'generated.generation.json')), false);
  }
});

test('rejects malformed JSON and non-object configurations before fetch', async t => {
  const f = await fixture(t);
  for (const contents of ['{broken', 'null', '[]', '"prompt"']) {
    fs.writeFileSync(f.config, contents);
    await assert.rejects(generateImage(f.config, { env: liveEnv, fetchImpl: noFetch(t) }));
    noOutputs(f);
  }
});

test('occupied output or generation record fails before fetch and preserves existing files', async t => {
  const f = await fixture(t);
  const existing = Buffer.from('existing artifact');
  for (const kind of ['output', 'manifest']) {
    change(f, { output: `./occupied-${kind}.png` });
    const paths = locations(f);
    const occupied = paths[kind];
    fs.writeFileSync(occupied, existing);
    await assert.rejects(generateImage(f.config, { env: liveEnv, fetchImpl: noFetch(t) }), /output|exist|overwrite|occupied/i);
    assert.deepEqual(fs.readFileSync(occupied), existing);
    const other = kind === 'output' ? paths.manifest : paths.output;
    assert.equal(fs.existsSync(other), false);
  }
});

test('output cannot overwrite a reference directly or through a symlink', async t => {
  const f = await fixture(t, { mode: 'reference', reference: './reference.png', output: './reference.png' });
  const before = fs.readFileSync(f.reference);
  await assert.rejects(generateImage(f.config, { env: liveEnv, fetchImpl: noFetch(t) }), /output|exist|overwrite|input|reference/i);
  const alias = path.join(f.dir, 'alias.png');
  fs.symlinkSync(f.reference, alias);
  change(f, { output: './alias.png' });
  await assert.rejects(generateImage(f.config, { env: liveEnv, fetchImpl: noFetch(t) }), /output|exist|overwrite|input|reference/i);
  assert.deepEqual(fs.readFileSync(f.reference), before);
  assert.equal(fs.existsSync(path.join(f.dir, 'reference.generation.json')), false);
  assert.equal(fs.existsSync(path.join(f.dir, 'alias.generation.json')), false);
});

test('authentication errors do not echo API secrets or server response text', async t => {
  const f = await fixture(t);
  const signed = 'https://storage.example.test/file.png?sig=private-response-token';
  let calls = 0;
  await assert.rejects(generateImage(f.config, {
    env: liveEnv,
    fetchImpl: async () => {
      calls++;
      return jsonResponse({ error: { message: `Rejected Bearer ${apiKey}; ${signed}` } }, 401);
    },
  }), error => {
    assertSafe(String(error), [signed, 'private-response-token']);
    return true;
  });
  assert.equal(calls, 1);
  noOutputs(f);
});

test('fetch failures redact echoed credentials', async t => {
  const f = await fixture(t);
  await assert.rejects(generateImage(f.config, {
    env: liveEnv,
    fetchImpl: async () => { throw new Error(`Network rejected Bearer ${apiKey}`); },
  }), error => {
    assertSafe(String(error));
    return true;
  });
  noOutputs(f);
});

test('malformed API JSON fails without creating output', async t => {
  const f = await fixture(t);
  await assert.rejects(generateImage(f.config, {
    env: liveEnv,
    fetchImpl: async () => new Response('{broken', { headers: { 'Content-Type': 'application/json' } }),
  }));
  noOutputs(f);
});

test('missing or malformed image data fails without creating output', async t => {
  const f = await fixture(t);
  for (const body of [
    null, {}, { data: null }, { data: [] }, { data: [{}] },
    { data: [{ b64_json: 42 }] }, { data: [{ b64_json: '' }] },
    { data: [{ b64_json: 'not valid base64!!!' }] },
    { data: [{ b64_json: Buffer.from('not an image').toString('base64') }] },
    { data: [{ b64_json: pngSignature.toString('base64') }] },
  ]) {
    let calls = 0;
    await assert.rejects(generateImage(f.config, {
      env: liveEnv,
      fetchImpl: async () => { calls++; return jsonResponse(body); },
    }));
    assert.equal(calls, 1);
    noOutputs(f);
  }
});

test('URL downloads default to the exact API hostname, without bearer credentials', async t => {
  const f = await fixture(t);
  const signedUrl = 'https://images.example.test/result.png?sig=private-download-token';
  let calls = 0;
  const result = await generateImage(f.config, {
    env: liveEnv,
    fetchImpl: async (url, init = {}) => {
      calls++;
      if (calls === 1) return jsonResponse({ data: [{ url: signedUrl }] });
      assert.equal(calls, 2);
      assert.equal(String(url), signedUrl);
      assert.ok(init.method === undefined || init.method === 'GET');
      const headers = new Headers(init.headers);
      assert.equal(headers.has('authorization'), false);
      assert.equal(headers.has('cookie'), false);
      assert.ok(['error', 'manual'].includes(init.redirect), 'download redirects must not be followed');
      return new Response(f.generated, { headers: { 'Content-Type': 'image/png' } });
    },
  });
  assert.equal(calls, 2);
  await assertGenerated(f, result, [signedUrl, 'private-download-token']);
});

test('explicit comma-separated download host allowlist supports a separate exact host', async t => {
  const f = await fixture(t);
  const url = 'https://cdn.example.test/result.png?signature=separate-host-secret';
  let calls = 0;
  const result = await generateImage(f.config, {
    env: { ...liveEnv, IMAGE_DOWNLOAD_HOSTS: 'other.example.test, cdn.example.test' },
    fetchImpl: async (input, init = {}) => {
      calls++;
      if (calls === 1) return jsonResponse({ data: [{ url }] });
      assert.equal(calls, 2);
      assert.equal(String(input), url);
      assert.equal(new Headers(init.headers).has('authorization'), false);
      assert.ok(['error', 'manual'].includes(init.redirect));
      return new Response(f.generated, { headers: { 'Content-Type': 'image/png' } });
    },
  });
  assert.equal(calls, 2);
  await assertGenerated(f, result, [url, 'separate-host-secret']);
});

test('rejects insecure URLs, fake allowlisted hostnames, and subdomains before download', async t => {
  const f = await fixture(t);
  for (const url of [
    'http://images.example.test/result.png',
    'https://images.example.test.evil.test/result.png',
    'https://evil.test/images.example.test/result.png',
    'https://images.example.test@evil.test/result.png',
    'https://child.images.example.test/result.png',
    'data:image/png;base64,aGVsbG8=',
    'not-a-url',
  ]) {
    let calls = 0;
    await assert.rejects(generateImage(f.config, {
      env: liveEnv,
      fetchImpl: async () => {
        calls++;
        assert.equal(calls, 1, 'an untrusted URL must not be fetched');
        return jsonResponse({ data: [{ url }] });
      },
    }));
    assert.equal(calls, 1);
    noOutputs(f);
  }
});

test('explicit download allowlist also rejects hostname suffix matches', async t => {
  const f = await fixture(t);
  let calls = 0;
  await assert.rejects(generateImage(f.config, {
    env: { ...liveEnv, IMAGE_DOWNLOAD_HOSTS: 'cdn.example.test,other.example.test' },
    fetchImpl: async () => {
      calls++;
      assert.equal(calls, 1);
      return jsonResponse({ data: [{ url: 'https://cdn.example.test.evil.test/result.png' }] });
    },
  }));
  assert.equal(calls, 1);
  noOutputs(f);
});

test('download redirects are rejected without fetching their destination', async t => {
  const f = await fixture(t);
  let calls = 0;
  await assert.rejects(generateImage(f.config, {
    env: liveEnv,
    fetchImpl: async (url, init = {}) => {
      calls++;
      if (calls === 1) return jsonResponse({ data: [{ url: 'https://images.example.test/result.png' }] });
      assert.equal(calls, 2);
      assert.ok(['error', 'manual'].includes(init.redirect));
      return new Response(null, { status: 302, headers: { Location: 'https://evil.test/stolen.png' } });
    },
  }));
  assert.equal(calls, 2);
  noOutputs(f);
});

test('failed downloads and non-image download payloads leave no output', async t => {
  const f = await fixture(t);
  for (const [status, contentType, bytes] of [
    [403, 'text/plain', Buffer.from('forbidden')],
    [200, 'text/html', Buffer.from('<html>not an image</html>')],
    [200, 'image/png', Buffer.from('not really a PNG')],
    [200, 'image/png', pngSignature],
  ]) {
    let calls = 0;
    await assert.rejects(generateImage(f.config, {
      env: liveEnv,
      fetchImpl: async () => {
        calls++;
        assert.ok(calls <= 2);
        if (calls === 1) return jsonResponse({ data: [{ url: 'https://images.example.test/result.png' }] });
        return new Response(bytes, { status, headers: { 'Content-Type': contentType } });
      },
    }));
    assert.equal(calls, 2);
    noOutputs(f);
  }
});

test('download transport errors do not expose signed URLs or credentials', async t => {
  const f = await fixture(t);
  const signedUrl = 'https://images.example.test/result.png?sig=transport-secret';
  let calls = 0;
  await assert.rejects(generateImage(f.config, {
    env: liveEnv,
    fetchImpl: async () => {
      calls++;
      if (calls === 1) return jsonResponse({ data: [{ url: signedUrl }] });
      throw new Error(`Could not fetch ${signedUrl}; Bearer ${apiKey}`);
    },
  }), error => {
    assertSafe(String(error), [signedUrl, 'transport-secret']);
    return true;
  });
  assert.equal(calls, 2);
  noOutputs(f);
});
