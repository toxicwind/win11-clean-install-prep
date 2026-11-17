# Download remaining critical ASUS drivers (Chipset, SerialIO, GNA, DTT, RST)
import json, subprocess, urllib.parse, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests as cr

DEST = r"G:\Drivers\ASUS"
os.makedirs(DEST, exist_ok=True)
CHUNK = 8 * 1024 * 1024
WORKERS = 8

HDRS = [
    "-H", "Content-Type: application/json",
    "-H", "Referer: https://www.asus.com/",
    "-H", "Origin: https://www.asus.com",
    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36",
]

# Exact paths for the drivers we need (latest of each)
TARGETS = [
    ("Chipset", "/pub/ASUS/mb/03CHIPSET/DRV_Chipset_Intel_RPL_TP_W11_64_V101205328842_20260701R.zip"),
    ("SerialIO", "/pub/ASUS/mb/LGA4677/Pro_WS_W790E-SAGE_SE/DRV_SerialIO_Intel_RPL_TP_W11_64_V30100241730_20240806R.zip"),
    ("GNA", "/pub/ASUS/mb/LGA1700/Pro_WS_W680-ACE/DRV_GNA_Intel_RPL_TP_W11_64_V3501578_20240806R.zip"),
    ("DTT", "/pub/ASUS/mb/03CHIPSET/DRV_DTT_Intel_RPL_TP_W11_64_V101140542038_20240319R.zip"),
    ("RST", "/pub/ASUS/mb/05SATA/DRV_RST_Intel_ARL_TP_W11_64_V20211016_20241204R.zip"),
]

def get_signed_url(path, model="PRIME Z690-A"):
    base = f"https://dlcdnta.asus.com{path}?model={urllib.parse.quote(model)}"
    enc = urllib.parse.quote(base, safe='').replace('%3A', ':')
    url = f"https://cdnta.asus.com/api/v1/TokenHQ?filePath={enc}&systemCode=asus"
    r = subprocess.run(["curl", "-s", "-m", "20", "-X", "POST", url] + HDRS,
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        res = d.get("result", {})
        sig, exp, kp = res.get("signature"), res.get("expires"), res.get("keyPairId")
        if not sig:
            print(f"  NO SIG: {r.stdout[:150]}")
            return None
        return f"{base}&Signature={sig}&Expires={exp}&Key-Pair-Id={kp}"
    except Exception as e:
        print(f"  SIG ERR: {e} {r.stdout[:150]}")
        return None

def fetch_chunk(url, start, end, idx, tmpdir):
    headers = {"Referer": "https://www.asus.com/", "Range": f"bytes={start}-{end}"}
    for attempt in range(3):
        try:
            resp = cr.get(url, impersonate="chrome", headers=headers, timeout=120)
            if resp.status_code == 206:
                tmp = os.path.join(tmpdir, f"chunk_{idx:04d}")
                with open(tmp, "wb") as f:
                    f.write(resp.content)
                return idx, start, len(resp.content)
        except Exception:
            pass
        time.sleep(1)
    return idx, start, None

def download_file(url, outname, total_size):
    outpath = os.path.join(DEST, outname)
    if os.path.exists(outpath) and os.path.getsize(outpath) >= total_size:
        print(f"  SKIP (complete): {outname}")
        return True
    tmpdir = os.path.join(DEST, f".tmp_{outname}")
    os.makedirs(tmpdir, exist_ok=True)
    chunks = []
    pos = 0
    while pos < total_size:
        end = min(pos + CHUNK - 1, total_size - 1)
        chunks.append((pos, end))
        pos = end + 1
    print(f"  {len(chunks)} chunks x {CHUNK//1024//1024}MB for {outname} ({total_size/1024/1024:.0f}MB)")
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_chunk, url, s, e, i, tmpdir): (i, s) for i, (s, e) in enumerate(chunks)}
        for fut in as_completed(futs):
            idx, start, n = fut.result()
            if n is None:
                print(f"  FAILED chunk {idx} of {outname}")
                return False
            done += 1
            if done % 8 == 0 or done == len(chunks):
                print(f"    {done}/{len(chunks)} chunks")
    with open(outpath, "wb") as out:
        for idx in range(len(chunks)):
            tmp = os.path.join(tmpdir, f"chunk_{idx:04d}")
            with open(tmp, "rb") as f:
                out.write(f.read())
            os.remove(tmp)
    os.rmdir(tmpdir)
    final = os.path.getsize(outpath)
    print(f"  -> {outname} complete: {final/1024/1024:.1f}MB")
    return final >= total_size

def main():
    for n, p in TARGETS:
        outname = os.path.basename(p)
        outpath = os.path.join(DEST, outname)
        print(f"[{n}] {outname}")
        url = get_signed_url(p)
        if not url:
            continue
        resp = cr.head(url, impersonate="chrome", headers={"Referer": "https://www.asus.com/"})
        total = int(resp.headers.get("Content-Length", 0))
        if total == 0:
            print("  HEAD failed, skipping")
            continue
        ok = download_file(url, outname, total)
        if not ok:
            print(f"  FAILED: {outname}")
        time.sleep(0.3)

    print("\n=== FINAL CONTENTS ===")
    for f in sorted(os.listdir(DEST)):
        sz = os.path.getsize(os.path.join(DEST, f))
        print(f"  {f} ({sz/1024/1024:.1f} MB)")

if __name__ == "__main__":
    main()