# ASUS Driver Downloader

Reverse-engineered downloader for ASUS motherboard drivers. ASUS hides every
download behind a **per-file signed URL** (CloudFront Signature + Expires +
Key-Pair-Id) that is only generated when you click the download button on their
site. This repo reproduces that flow with plain HTTP — no browser needed.

## The problem

The ASUS support API (`GetPDDrivers`) returns only the file *paths*, e.g.:

```
/pub/ASUS/mb/03CHIPSET/DRV_Chipset_Intel_RPL_TP_W11_64_V101205328842_20260701R.zip
```

The actual downloadable URL is signed per-file and expires:

```
https://dlcdnta.asus.com/pub/ASUS/mb/...zip?model=PRIME%20Z690-A
  &Signature=<sig>&Expires=<ts>&Key-Pair-Id=K2ITB7O97XKKCX
```

The signature is **path-bound** — reusing one for a different file returns
`403 Forbidden`. Each file needs its own freshly-signed URL.

## How it works (reverse-engineered)

1. **Get the driver list** from the public ASUS API:
   ```
   https://www.asus.com/support/webapi/ProductV2/GetPDDrivers
     ?website=global&model=prime-z690-a&pdhashedid=z8oofpynawhdp7z3
     &pdid=19159&cpu=&osid=52&siteID=www&sitelang=
   ```
   Returns `Result.Obj[].Files[].DownloadUrl.Global` — the file paths.

2. **Get a signed URL** from the token API (found in the page's JS bundle
   `levelFourProductSupportPage-*.js`):
   ```
   POST https://cdnta.asus.com/api/v1/TokenHQ
     ?filePath=<urlencoded full dlcdnta URL>&systemCode=asus
   ```
   Returns `{signature, expires, keyPairId}`.

   **Critical headers** (this is the "Cloudflare bypass" — without them you get
   `400 Bad Request`):
   ```
   Referer: https://www.asus.com/
   Origin: https://www.asus.com
   User-Agent: <a real Chrome UA>
   Content-Type: application/json
   ```

3. **Download** with the signed URL. Two gotchas:
   - The `model` query param must be `%20`-encoded (`PRIME%20Z690-A`), matching
     what the browser actually sends — the signature is computed over that form.
   - Use `curl_cffi` with `impersonate="chrome"` so the TLS fingerprint matches
     a real browser (plain `requests`/`urllib` gets rejected or mangles the URL).

## Files

| File | Purpose |
|------|---------|
| `download_asus.py` | Full pipeline: list → sign → parallel chunked download |
| `download_remaining.py` | Download a hardcoded list of specific driver paths |
| `requirements.txt` | `curl_cffi` |

## Usage

```bash
pip install -r requirements.txt
python download_asus.py            # downloads latest of each category
python download_remaining.py       # downloads specific paths (Chipset/SerialIO/GNA/DTT/RST)
```

Downloads land in `G:\Drivers\ASUS` by default — edit `DEST` at the top.

## Parallel chunked download

Large drivers (the ME firmware is ~500 MB) download via HTTP `Range` requests —
8 parallel 8 MB chunks, each written to its own temp file immediately (no
memory buffering), then merged in order. This is the "file mover" logic: chunks
land in `.tmp_<name>/chunk_0000` … and get concatenated into the final file.

## Why not just click the buttons?

The download buttons are Vue components (DIVs with `role="button"`, no href).
`.click()` doesn't fire the handler, and the page virtualizes the list so
off-screen buttons aren't even rendered. Clicking 65 buttons one at a time is
insane — the token API is the clean path.