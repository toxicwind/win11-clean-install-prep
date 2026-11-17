# ASUS motherboard driver downloader — reverse-engineered signed-URL flow.
# Usage:
#   python download_asus.py --model "PRIME Z690-A" --pdid 19159 --hashedid z8oofpynawhdp7z3
# Downloads the latest driver of each category to DEST.
import json, subprocess, urllib.parse, os, time, sys, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests as cr

DEST = r"G:\Drivers\ASUS"
CHUNK = 8 * 1024 * 1024  # 8 MB
WORKERS = 8

HDRS = [
    "-H", "Content-Type: application/json",
    "-H", "Referer: https://www.asus.com/",
    "-H", "Origin: https://www.asus.com",
    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36",
]

def get_driver_list(model, pdid, hashedid, osid=52):
    """Fetch the driver list from the public ASUS API. osid=52 = Windows 11 64-bit."""
    url = ("https://www.asus.com/support/webapi/ProductV2/GetPDDrivers"
           f"?website=global&model={urllib.parse.quote(model)}"
           f"&pdhashedid={hashedid}&pdid={pdid}&cpu=&osid={osid}&siteID=www&sitelang=")
    r = subprocess.run(["curl", "-s", "-m", "30", url], capture_output=True, text=True)
    return json.loads(r.stdout)

def get_signed_url(path, model):
    """path like /pub/ASUS/mb/...zip ; returns full signed download URL."""
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
    # merge in order
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
    ap = argparse.ArgumentParser(description="Download ASUS motherboard drivers")
    ap.add_argument("--model", default="PRIME Z690-A")
    ap.add_argument("--pdid", default="19159")
    ap.add_argument("--hashedid", default="z8oofpynawhdp7z3")
    ap.add_argument("--osid", default="52", help="52 = Windows 11 64-bit")
    ap.add_argument("--dest", default=DEST)
    ap.add_argument("--skip-categories", default="VGA Drivers",
                    help="comma-separated category names to skip (e.g. iGPU VGA)")
    args = ap.parse_args()
    global DEST
    DEST = args.dest
    os.makedirs(DEST, exist_ok=True)

    skip = {s.strip() for s in args.skip_categories.split(",") if s.strip()}
    d = get_driver_list(args.model, args.pdid, args.hashedid, args.osid)
    picks = []
    for cat in d["Result"]["Obj"]:
        name = cat["Name"]
        if name in skip:
            print(f"SKIP category: {name}")
            continue
        files = cat["Files"]
        if not files:
            continue
        f = files[0]
        path = f.get("DownloadUrl", {}).get("Global")
        title = f.get("Title") or f.get("Name") or ""
        if path:
            picks.append((name, title, path))
    print(f"Selected {len(picks)} drivers")

    for n, t, p in picks:
        outname = os.path.basename(p)
        outpath = os.path.join(DEST, outname)
        print(f"[{n}] {outname}")
        url = get_signed_url(p, args.model)
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