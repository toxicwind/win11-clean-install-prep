// Use browser-use MCP browser_exec to capture ASUS download URLs
import { spawn } from 'node:child_process';
const exe = "C:\\Users\\Snacky\\browseruse-venv\\.venv\\Scripts\\browser-use.exe";
const child = spawn(exe, ["--cli-mcp"], { stdio: ["pipe", "pipe", "pipe"] });
let buf = "", id = 0;
const pending = new Map();
child.stdout.on("data", (d) => {
  buf += d.toString();
  let idx;
  while ((idx = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, idx).trim();
    buf = buf.slice(idx + 1);
    if (!line) continue;
    let msg; try { msg = JSON.parse(line); } catch { continue; }
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  }
});
child.stderr.on("data", (d) => process.stderr.write("[stderr] " + d));
function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const mid = ++id;
    pending.set(mid, resolve);
    child.stdin.write(JSON.stringify({ jsonrpc: "2.0", id: mid, method, params }) + "\n");
    setTimeout(() => { if (pending.has(mid)) { pending.delete(mid); reject(new Error("timeout " + method)); } }, 120000);
  });
}
await call("initialize", { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "omp", version: "1.0" } });
await call("notifications/initialized", {});

const code = `
import time
# Navigate to ASUS download page
new_tab("https://www.asus.com/motherboards-components/motherboards/prime/prime-z690-a/helpdesk_download?model2Name=PRIME-Z690-A")
time.sleep(9)
# Hook window.open + fetch to capture CDN URLs, then click all download buttons
js("""
(() => {
  window.__cdn = [];
  const ow = window.open;
  window.open = function(u){ try{ if(String(u).includes('dlcdn')) window.__cdn.push(String(u)); }catch(e){} return ow.apply(this,arguments); };
  const of = window.fetch;
  window.fetch = function(...a){ try{ const u=String(a[0]); if(u.includes('dlcdn')) window.__cdn.push(u); }catch(e){} return of.apply(this,a); };
  return 'hooked';
})()
""")
# Click each download button
res = js("""
(() => {
  const els = Array.from(document.querySelectorAll('*')).filter(e => e.children.length===0 && e.textContent.trim()==='DOWNLOAD');
  let clicked = 0;
  for(const e of els){
    let p = e;
    for(let i=0;i<4 && p;i++){ p = p.parentElement; }
    if(p && p.click){ try{ p.click(); clicked++; }catch(err){} }
  }
  return {clicked, total: els.length};
})()
""")
print("CLICK:", res)
time.sleep(10)
cdn = js("window.__cdn || []")
print("CDN_COUNT:", len(cdn))
for u in cdn: print("CDN:", u)
`;

const r = await call("tools/call", { name: "browser_exec", arguments: { code } });
console.log("RESULT:", JSON.stringify(r).slice(0, 8000));
child.kill();