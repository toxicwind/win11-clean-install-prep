// Read browser-use MCP full instructions via --cli-mcp
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
    setTimeout(() => { if (pending.has(mid)) { pending.delete(mid); reject(new Error("timeout " + method)); } }, 60000);
  });
}
const init = await call("initialize", { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "omp", version: "1.0" } });
console.log(init.result?.instructions ?? JSON.stringify(init).slice(0, 3000));
child.kill();