import { createServer } from 'node:http';
import { readFile, realpath } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const ROOT = fileURLToPath(new URL('./', import.meta.url));
const REFERENCES = {
  '/reference/panda.png': path.resolve(ROOT, '../LoomOS-panda-ink-clean.png'),
  '/reference/logo.svg': path.resolve(ROOT, '../Zhi-Jie-logo.svg'),
};
const TYPES = { '.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.css':'text/css; charset=utf-8', '.png':'image/png', '.svg':'image/svg+xml', '.glb':'model/gltf-binary' };
export function resolveRequest(url) {
  let pathname;
  try { pathname = decodeURIComponent(url.split('?')[0]); } catch { return null; }
  if (!pathname.startsWith('/') || pathname.includes('\\') || pathname.includes('\0') || pathname.split('/').some(s => s.startsWith('.'))) return null;
  if (REFERENCES[pathname]) return { path: REFERENCES[pathname], reference: true };
  const allowed = pathname==='/' || pathname==='/index.html' || pathname==='/style.css'
    || /^\/src\/[a-z-]+\.js$/.test(pathname)
    || /^\/node_modules\/three\/(build|examples\/jsm)\/[\w/.-]+\.js$/.test(pathname)
    || /^\/evidence\/[a-z-]+\.glb$/.test(pathname);
  if (!allowed) return null;
  return { path:path.join(ROOT,pathname==='/'?'index.html':pathname), reference:false };
}
export function startServer(port=4178) {
  const server = createServer(async(req,res)=>{
    const target = resolveRequest(req.url || '/');
    if (!['GET','HEAD'].includes(req.method)) { res.writeHead(405,{Allow:'GET, HEAD'});return res.end('Method not allowed'); }
    if (!target) { res.writeHead(404);return res.end('Not found'); }
    try {
      // Lexical validation above is supplemented by realpath to reject symlink escapes.
      const actual=await realpath(target.path);
      if ((!target.reference && !actual.startsWith(ROOT)) || (target.reference && actual!==target.path)) {res.writeHead(404);return res.end('Not found');}
      const body=await readFile(actual);
      res.writeHead(200,{'Content-Type':TYPES[path.extname(actual)]||'application/octet-stream','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self' blob:; object-src 'none'; frame-ancestors 'none'",'Content-Length':body.length});
      res.end(req.method==='HEAD'?undefined:body);
    }catch{res.writeHead(404);res.end('Not found');}
  });
  server.listen(port,'127.0.0.1',()=>console.log(`Panda studio: http://127.0.0.1:${server.address().port}`));
  return server;
}
if(process.argv[1] && import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href) {
 const port=Number(process.env.PORT||4178);
 if(!Number.isInteger(port)||port<0||port>65535) throw new Error('Invalid PORT');
 const server=startServer(port);
 server.on('error',err=>{console.error(err.code==='EADDRINUSE'?`Port ${port} is already in use; choose another with PORT=... npm start.`:err.message);process.exitCode=1;});
}
