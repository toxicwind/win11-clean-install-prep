// Drive the browser-use MCP server over stdio JSON-RPC.
import { spawn } from 'node:child_process';

const exe = "C:\\Users\\Snacky\\browseruse-venv\\.venv\\Scripts\\browser-use.exe";
const child = spawn(exe, ["--mcp"], { stdio: ["pipe", "pipe", "pipe"] });

let buf = "";
let id = 0;
const pending = new Map();

child.stdout.on("data", (d) => {
  buf += d.toString();
  let idx;
  while ((idx = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, idx).trim();
    buf = buf.slice(idx + 1);
    if (!line) continue;
    let msg;
    try { msg = JSON.parse(line); } catch { console.log("RAW:", line); continue; }
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    } else {
      console.log("NOTIF:", JSON.stringify(msg).slice(0, 500));
    }
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

const init = await call("initialize", {
  protocolVersion: "2025-11-25",
  capabilities: {},
  clientInfo: { name: "omp", version: "1.0" },
});
console.log("INIT:", JSON.stringify(init).slice(0, 300));
await call("notifications/initialized", {});
const tools = await call("tools/list", {});
console.log("TOOLS:", JSON.stringify(tools.result?.tools?.map(t => t.name) ?? tools, null, 2));
child.kill();