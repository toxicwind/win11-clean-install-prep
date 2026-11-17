// Drive browser-use MCP: navigate to the NVIDIA 621.24 Reddit thread and extract content.
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
      console.log("NOTIF:", JSON.stringify(msg).slice(0, 300));
    }
  }
});
child.stderr.on("data", (d) => process.stderr.write("[stderr] " + d));

function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const mid = ++id;
    pending.set(mid, resolve);
    child.stdin.write(JSON.stringify({ jsonrpc: "2.0", id: mid, method, params }) + "\n");
    setTimeout(() => { if (pending.has(mid)) { pending.delete(mid); reject(new Error("timeout " + method)); } }, 90000);
  });
}

await call("initialize", { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "omp", version: "1.0" } });
await call("notifications/initialized", {});

const url = "https://www.reddit.com/r/nvidia/comments/1xuef1f/game_ready_driver_62124_faqdiscussion/";
const r = await call("tools/call", {
  name: "browser_exec",
  arguments: {
    code: `import time
from browser_use import Browser
b = Browser()
b.goto("${url}")
time.sleep(6)
# scroll to load comments
for _ in range(8):
    b.evaluate("window.scrollBy(0, 1500)")
    time.sleep(1.5)
text = b.evaluate("document.body.innerText")
print(text[:12000])
b.close()`
  },
});
console.log("RESULT:", JSON.stringify(r).slice(0, 14000));
child.kill();