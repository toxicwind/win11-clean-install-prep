# Capture ASUS PRIME Z690-A driver download URLs by clicking each button
# and reading the CDN URL from the newly opened tab.
import time, json, subprocess

EXE = r"C:\Users\Snacky\browseruse-venv\.venv\Scripts\browser-use.exe"
URL = "https://www.asus.com/motherboards-components/motherboards/prime/prime-z690-a/helpdesk_download?model2Name=PRIME-Z690-A"

def bu(code):
    r = subprocess.run([EXE], input=code, capture_output=True, text=True, timeout=180)
    return r.stdout + r.stderr

# Open ASUS page fresh
print(bu(f'''
new_tab("{URL}")
import time
time.sleep(9)
print("LOADED:", page_info()["title"])
'''))

# Click each download button inside one JS call, capturing window.open URLs
code = '''
import time
# Hook window.open, then click all download buttons sequentially
res = js("""
(() => {
  window.__cdn = [];
  const ow = window.open;
  window.open = function(u){ try{ if(String(u).includes('dlcdn')) window.__cdn.push(String(u)); }catch(e){} return ow.apply(this,arguments); };
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
time.sleep(8)
cdn = js("window.__cdn || []")
print("CDN:", json.dumps(cdn, indent=2))
'''
print(bu(code))