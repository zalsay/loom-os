// Set files directly on the video file input (nodeId discovered via pierced DOM)
const CDP_URL = process.argv[2];
const FILE = process.argv[3];

const ws = new WebSocket(CDP_URL);
let id = 0;
const pending = new Map();

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
    await send('DOM.enable', {}, sessionId);
    const { root } = await send('DOM.getDocument', { depth: -1, pierce: true }, sessionId);
    // re-find the file input (nodeIds change between sessions)
    let fileNode = null;
    const walk = (node) => {
      if (fileNode) return;
      if (node.nodeName === 'INPUT') {
        const attrs = {};
        for (let i = 0; i < (node.attributes || []).length; i += 2) attrs[node.attributes[i]] = node.attributes[i + 1];
        if (attrs.type === 'file' && (attrs.accept || '').includes('video')) { fileNode = node; return; }
      }
      for (const c of node.children || []) walk(c);
      for (const c of node.shadowRoots || []) walk(c);
      if (node.templateContent) walk(node.templateContent);
      if (node.contentDocument) walk(node.contentDocument);
    };
    walk(root);
    if (!fileNode) { console.log('file input NOT FOUND'); process.exit(1); }
    console.log('file input nodeId', fileNode.nodeId, 'accept', (fileNode.attributes || []).join(' ').slice(0, 80));
    await send('DOM.setFileInputFiles', { files: [FILE], nodeId: fileNode.nodeId }, sessionId);
    console.log('FILES SET OK');
    process.exit(0);
  } catch (e) {
    console.error('ERR', e.message);
    process.exit(1);
  }
};
ws.onerror = (e) => { console.error('WS ERR', e.message || e); process.exit(1); };
