// Find file inputs via CDP pierced DOM (including shadow roots)
const CDP_URL = process.argv[2];

const ws = new WebSocket(CDP_URL);
let id = 0;
const pending = new Map();
let pageSession = null;

function send(method, params = {}, sessionId) {
  return new Promise((resolve, reject) => {
    const msgId = ++id;
    pending.set(msgId, { resolve, reject });
    ws.send(JSON.stringify({ id: msgId, method, params, sessionId }));
  });
}

ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
  }
};

ws.onopen = async () => {
  try {
    const { targetInfos } = await send('Target.getTargets');
    const page = targetInfos.find(t => t.type === 'page' && t.url.includes('channels.weixin.qq.com'));
    const { sessionId } = await send('Target.attachToTarget', { targetId: page.targetId, flatten: true });
    pageSession = sessionId;
    await send('DOM.enable', {}, pageSession);
    const { root } = await send('DOM.getDocument', { depth: -1, pierce: true }, pageSession);
    // walk for input[type=file]
    const found = [];
    const walk = (node, path) => {
      const name = node.nodeName || '';
      if (name === 'INPUT') {
        const attrs = {};
        for (let i = 0; i < (node.attributes || []).length; i += 2) attrs[node.attributes[i]] = node.attributes[i + 1];
        found.push({ nodeId: node.nodeId, type: attrs.type, accept: attrs.accept, cls: (attrs.class || '').slice(0, 40), path });
      }
      for (const c of node.children || []) walk(c, path + '>' + (c.nodeName || ''));
      for (const c of node.shadowRoots || []) walk(c, path + '||SHADOW>' + (c.nodeName || ''));
      if (node.templateContent) walk(node.templateContent, path + '|TPL');
      if (node.contentDocument) walk(node.contentDocument, path + '|IFRAME');
    };
    walk(root, 'DOC');
    console.log('total inputs found:', found.length);
    for (const f of found.slice(0, 10)) console.log(JSON.stringify(f));
    process.exit(0);
  } catch (e) {
    console.error('ERR', e.message);
    process.exit(1);
  }
};
ws.onerror = (e) => { console.error('WS ERR', e.message || e); process.exit(1); };
