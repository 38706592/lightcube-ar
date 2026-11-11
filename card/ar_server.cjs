// Local server for compiling the AR targets in a browser: serves the lightcube-ar repo and saves POST /save → targets.mind.new
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', 'lightcube-ar');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.png': 'image/png', '.json': 'application/json', '.mind': 'application/octet-stream', '.svg': 'image/svg+xml' };
http.createServer((q, r) => {
  if (q.method === 'POST' && q.url.startsWith('/png/')) { const chunks = []; q.on('data', c => chunks.push(c)); q.on('end', () => { const dir = path.join(__dirname, 'png_layers'); fs.mkdirSync(dir, { recursive: true }); const f = path.join(dir, path.basename(decodeURIComponent(q.url.slice(5)))); fs.writeFileSync(f, Buffer.from(Buffer.concat(chunks).toString(), 'base64')); r.end('ok'); }); return; }
  if (q.method === 'POST' && q.url === '/save') { const chunks = []; q.on('data', c => chunks.push(c)); q.on('end', () => { const b = Buffer.concat(chunks); fs.writeFileSync(path.join(ROOT, 'targets.mind.new'), b); r.end('saved ' + b.length); }); return; }
  const url = decodeURIComponent(q.url.split('?')[0]);
  const f = url === '/_compile.html' ? path.join(__dirname, 'compile_page.html') : url === '/_render.html' ? path.join(__dirname, 'render_layers.html') : url.startsWith('/_svg/') ? path.join(__dirname, 'svg_layers', path.basename(url)) : path.join(ROOT, url === '/' ? 'index.html' : url);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream', 'cache-control': 'no-store' }); fs.createReadStream(f).pipe(r);
}).listen(8767, () => console.log('ar server on 8767'));
