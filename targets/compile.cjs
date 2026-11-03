(async()=>{
const { chromium } = require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const [out, ...imgs] = process.argv.slice(2);
const types = { '.html':'text/html', '.js':'text/javascript', '.jpg':'image/jpeg', '.png':'image/png' };
const srv = http.createServer((q, r) => { const f = path.join(process.cwd(), decodeURIComponent(q.url.split('?')[0])); if (!fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, {'content-type': types[path.extname(f)] || 'application/octet-stream'}); fs.createReadStream(f).pipe(r); }).listen(8765);
const b = await chromium.launch({ args: ['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
const p = await b.newPage(); p.on('console', m => console.log('[page]', m.text()));
await p.goto('http://localhost:8765/compile.html'); await p.waitForFunction('window.ready');
const t0 = Date.now(); const iv = setInterval(async () => console.log('progress', await p.evaluate('window.prog').catch(()=>'?')), 15000);
const b64 = await p.evaluate((s) => window.run(s), imgs.map(i => '/' + i));
clearInterval(iv); fs.writeFileSync(out, Buffer.from(b64, 'base64'));
console.log('done', out, fs.statSync(out).size, 'bytes', (Date.now()-t0)/1000, 's');
await b.close(); srv.close();
})();
