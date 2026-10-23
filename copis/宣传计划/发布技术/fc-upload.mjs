// Raw CDP file-chooser intercept upload (Node 22 global WebSocket)
const CDP_URL = process.argv[2];           // ws://127.0.0.1:PORT/devtools/browser/...
const FILE = process.argv[3];
const CLICK_X = parseFloat(process.argv[4] || '361');
const CLICK_Y = parseFloat(process.argv[5] || '379');

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
    return;
  }
  if (msg.method === 'Page.fileChooser' && msg.sessionId === pageSession) {
    console.log('fileChooser intercepted, backendNodeId =', msg.params.backendNodeId);
    (async () => {
      await send('DOM.setFileInputFiles', { files: [FILE], backendNodeId: msg.params.backendNodeId }, pageSession);
      console.log('FILES SET OK');
      setTimeout(() => process.exit(0), 1500);
    })();
  }
};

ws.onopen = async () => {
  try {
    const { targetInfos } = await send('Target.getTargets');
    const page = targetInfos.find(t => t.type === 'page' && t.url.includes('channels.weixin.qq.com'));
    if (!page) throw new Error('page target not found: ' + targetInfos.map(t => t.url).join(' | '));
    console.log('target:', page.url);
    const { sessionId } = await send('Target.attachToTarget', { targetId: page.targetId, flatten: true });
    pageSession = sessionId;
    await send('Page.enable', {}, pageSession);
    await send('Page.setInterceptFileChooserDialog', { enabled: true }, pageSession);
    console.log('file chooser interception ON');
    // click the upload zone
    for (const [type, x, y] of [
      ['mousePressed', CLICK_X, CLICK_Y],
      ['mouseReleased', CLICK_X, CLICK_Y],
    ]) {
      await send('Input.dispatchMouseEvent', {
        type, x, y, button: 'left', clickCount: 1, buttons: type === 'mousePressed' ? 1 : 0,
      }, pageSession);
    }
    console.log('clicked upload zone at', CLICK_X, CLICK_Y);
    setTimeout(() => { console.log('TIMEOUT: no fileChooser event'); process.exit(2); }, 8000);
  } catch (e) {
    console.error('ERR', e.message);
    process.exit(1);
  }
};
ws.onerror = (e) => { console.error('WS ERR', e.message || e); process.exit(1); };
