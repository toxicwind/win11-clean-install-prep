# One-shot: use browser-use Browser's own CDP to click all ASUS download buttons
# and download to G:/Drivers/ASUS
import asyncio, sys, os, time, shutil
from pathlib import Path

sys.path.insert(0, r"C:\Users\Snacky\browseruse-venv\.venv\Lib\site-packages")
from browser_use.browser.browser import Browser

URL = "https://www.asus.com/motherboards-components/motherboards/prime/prime-z690-a/helpdesk_download?model2Name=PRIME-Z690-A"
DEST = Path(r"G:\Drivers\ASUS")
DEST.mkdir(parents=True, exist_ok=True)

async def main():
    b = Browser(kind="chromium", headless=True)
    await b.start()
    cdp = b._cdp()
    
    # Set download behavior to DEST
    try:
        cdp("Browser.setDownloadBehavior", behavior="allowAndName", downloadPath=str(DEST), eventsEnabled=True)
        print("download behavior set")
    except Exception as e:
        print("setDownloadBehavior:", e)
    
    # Create a tab and navigate
    tid = cdp("Target.createTarget", url="about:blank", background=True)["targetId"]
    sid = cdp("Target.attachToTarget", targetId=tid, flatten=True)["sessionId"]
    
    def ev(method, **params):
        return cdp(method, sid, **params)
    
    ev("Page.enable")
    ev("Runtime.enable")
    ev("Page.navigate", url=URL)
    await asyncio.sleep(10)
    
    # Click all download buttons
    res = ev("Runtime.evaluate", expression="""
    (() => {
      const els = Array.from(document.querySelectorAll('*')).filter(e => e.children.length===0 && e.textContent.trim()==='DOWNLOAD');
      let n = 0;
      for(const e of els){
        let p = e;
        for(let i=0;i<4 && p;i++){ p = p.parentElement; }
        if(p && p.click){ try{ p.click(); n++; }catch(err){} }
      }
      return n;
    })()
    """, returnByValue=True)
    print("clicked:", res.get("result", {}).get("result", {}).get("value"))
    
    await asyncio.sleep(30)
    
    # List downloaded files
    files = [f for f in os.listdir(DEST) if os.path.isfile(DEST / f)]
    print("FILES:", len(files))
    for f in files: print(" ", f)
    await b.close()

asyncio.run(main())