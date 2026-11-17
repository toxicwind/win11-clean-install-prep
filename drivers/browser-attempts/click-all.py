# Click all 65 ASUS download buttons, capture signed URLs, write to txt
import time, json, os

OUT = r"C:\Users\Snacky\AppData\Local\Temp\blackbird\asus-urls.txt"

# Hook window.open + fetch to capture CDN URLs
js("""
(() => {
  window.__cdn = [];
  const ow = window.open;
  window.open = function(u){ try{ if(String(u) && String(u).includes('dlcdn')) window.__cdn.push(String(u)); }catch(e){} return ow.apply(this,arguments); };
  const of = window.fetch;
  window.fetch = function(...a){ try{ const u=String(a[0]); if(u.includes('dlcdn')) window.__cdn.push(u); }catch(e){} return of.apply(this,a); };
  return 'hooked';
})()
""")

# Click each download button one at a time
clicked = 0
for i in range(65):
    res = js("""
    (() => {
      const els = Array.from(document.querySelectorAll('*')).filter(e => e.children.length===0 && e.textContent.trim()==='DOWNLOAD');
      const e = els[0];
      if(!e) return 'none';
      let p = e;
      for(let j=0;j<4 && p;j++){ p = p.parentElement; }
      p.click();
      return 'clicked';
    })()
    """)
    if res == 'clicked':
        clicked += 1
    time.sleep(1.2)

cdn = js("window.__cdn || []")
print("clicked:", clicked, "| CDN URLs:", len(cdn))
with open(OUT, "w") as f:
    for u in cdn:
        f.write(u + "\n")
print("written to", OUT)