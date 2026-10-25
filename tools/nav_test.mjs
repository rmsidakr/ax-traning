// 서버에 띄운 교안을 헤드리스 Chrome으로 열고, 왼쪽 목차 링크를 실제 마우스로 눌러 스크롤이 이동하는지 확인
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = process.argv[2] || 'http://127.0.0.1:8765/';
const W = +(process.argv[3] || 1920), H = +(process.argv[4] || 1080);
const prof = mkdtempSync(join(tmpdir(), 'navtest-'));
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--remote-debugging-port=9333',
  `--user-data-dir=${prof}`, `--window-size=${W},${H}`, 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));

let tabs;
for (let i = 0; i < 40; i++) {
  try { tabs = await (await fetch('http://127.0.0.1:9333/json')).json(); break; } catch { await sleep(250); }
}
const page = tabs.find(t => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let id = 0; const pending = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true })).result.result.value;

await send('Page.enable');
await send('Page.navigate', { url: URL });
await sleep(2500);
console.log('title:', await ev('document.title'), '| links:', await ev("document.querySelectorAll('nav a').length"));
const n = await ev("document.querySelectorAll('nav a').length");
for (let i = 0; i < n; i++) {
  const info = await ev(`(function(){var a=document.querySelectorAll('nav a')[${i}];a.scrollIntoView({block:'center'});var r=a.getBoundingClientRect();var x=r.left+r.width/2,y=r.top+r.height/2;var top=document.elementFromPoint(x,y);return {href:a.getAttribute('href'),text:a.textContent.trim(),x:x,y:y,hit:top===a||a.contains(top),top:top?top.tagName+'.'+top.className:null};})()`);
  const before = await ev('scrollY');
  for (const type of ['mousePressed', 'mouseReleased'])
    await send('Input.dispatchMouseEvent', { type, x: info.x, y: info.y, button: 'left', clickCount: 1 });
  await sleep(1500);
  const after = await ev(`(function(){var t=document.querySelector('${info.href}');return {y:scrollY,hash:location.hash,tTop:t?Math.round(t.getBoundingClientRect().top):null};})()`);
  const ok = after.hash === info.href && after.tTop !== null && Math.abs(after.tTop) < 140;
  console.log(`${ok ? 'OK  ' : 'FAIL'} ${info.text} (${info.href}) hit=${info.hit} top=${info.top} scroll ${before}->${after.y} targetTop=${after.tTop} hash=${after.hash}`);
}
ws.close(); chrome.kill();
