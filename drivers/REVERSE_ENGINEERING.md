# Reverse-Engineering Notes: ASUS Signed Download URLs

The full journey of figuring out how ASUS serves driver downloads, and why the
obvious approaches fail. Written so the next person (or future-me) doesn't
repeat the 2-hour slog.

## The trap

ASUS's support page shows a "DOWNLOAD" button per driver. Clicking it downloads
the file. But:

1. The button is a **Vue component** — a `<div role="button">` with **no href**.
   The actual download URL is generated *on click* by a JS handler.
2. The URL is **signed per-file** (CloudFront `Signature` + `Expires` +
   `Key-Pair-Id`). The signature is **path-bound** — reusing one for a different
   file returns `403 Forbidden`.
3. The page **virtualizes** the driver list — off-screen buttons aren't even
   rendered in the DOM (their `getBoundingClientRect()` returns `0,0`).

## Failed approaches (don't repeat these)

### 1. Clicking the buttons with `.click()`
```js
// The Vue @click handler does NOT fire on programmatic .click()
p.click();  // nothing happens
```
Vue attaches listeners via its own event delegation; a synthetic `.click()`
doesn't trigger them reliably.

### 2. Real mouse clicks via CDP `Input.dispatchMouseEvent`
```python
click_at_xy(x, y)  # CDP mousePressed + mouseReleased
```
This *does* fire the handler — **but only if you click the actual button
element**, not the parent row. The parent `<div>` spans the whole 1212px row;
the real button is a small 180×35 element at the right edge. Clicking the row
center hits the description text, not the button.

### 3. Scrolling + clicking all 65 buttons
The list is virtualized. `scrollIntoView` on an unrendered element returns
`0,0`. You'd have to scroll the window incrementally, re-query, and click each
as it renders — 65 buttons, one at a time, each generating a fresh signed URL.
Insane and fragile.

## The clean path: reverse-engineer the JS

The page's JS bundle (`levelFourProductSupportPage-*.js`) contains the download
logic. Search it for `dlcdnta`:

```js
// non-CN branch
let x = `https://dlcdnta.asus.com${path}?model=${model}`;
let enc = encodeURIComponent(x);
We.getSupportCDNHQToken({ params: { filePath: enc, systemCode: systemCode } })
  .then(d => {
    x = `${x}&Signature=${d.result.signature}&Expires=${d.result.expires}&Key-Pair-Id=${d.result.keyPairId}`;
    window.open(x, "_blank");
  });
```

So the flow is:
1. Build `https://dlcdnta.asus.com<path>?model=<model>`
2. `encodeURIComponent` it (then the code replaces `%3A` back to `:`)
3. POST to the token API → get `{signature, expires, keyPairId}`
4. Append them to the URL → download

### Finding the token API endpoint

`getSupportCDNHQToken` is defined in the entry bundle (`entry-*.js`):

```js
async getSupportCDNHQToken(e) {
  const t = qi();  // getCdnTokenUrl()
  const { filePath: r, ...n } = e.params;
  const s = new URLSearchParams(n).toString();
  const o = `https://${t}/api/v1/TokenHQ?filePath=${encodeURIComponent(r).replace(/%3A/gi, ":")}&${s}`;
  return y(o, { method: "POST", headers: { "Content-Type": "application/json" }, skipSiteParams: true });
}
```

`qi()` = `getCdnTokenUrl()` maps the API host to the CDN token host:
- `odinapi.asus.com` → `cdnta.asus.com`
- `odinapi.asus.com.cn` → `cdnta.asus.com.cn`

So the endpoint is:
```
POST https://cdnta.asus.com/api/v1/TokenHQ?filePath=<enc>&systemCode=asus
```

### The Cloudflare bypass (the critical headers)

A bare `curl` POST to TokenHQ returns:
```json
{"result":{"expires":"","signature":"","keyPairId":""},"status":400,
 "message":"Bad Request, Request parameters are not formatted correctly."}
```

The fix is **headers** — the API checks the request looks like a real browser:
```
Referer: https://www.asus.com/
Origin: https://www.asus.com
User-Agent: <a real Chrome UA>
Content-Type: application/json
```

With those, it returns a valid signature.

### The download gotcha: `%20` vs raw space

The signed URL contains `?model=PRIME Z690-A` (raw space). The signature is
computed over the URL with the space **encoded as `%20`** — matching what the
browser actually sends. So:

- ✅ `https://dlcdnta.asus.com/...zip?model=PRIME%20Z690-A&Signature=...` → **200**
- ❌ raw space in the URL → curl rejects it / `403`
- ❌ `requests`/`urllib` → reject the raw space as a control character

Also, plain `requests` gets rejected by the CDN's TLS fingerprint check. Use
**`curl_cffi`** with `impersonate="chrome"` — it mimics a real Chrome TLS
handshake.

## The parallel chunked downloader ("file mover")

Large drivers (ME firmware = ~500 MB) download via HTTP `Range` requests:

- Split the file into 8 MB chunks
- Fetch 8 chunks in parallel (8 threads), each writing to its own temp file
  **immediately** (`.tmp_<name>/chunk_0000` …) — never buffer in memory
- Merge in order into the final file, deleting temp chunks

Why immediate disk writes matter: the first version buffered all chunks in
memory and only wrote at the end — the file showed `0 bytes` for minutes and
looked frozen, while 8 python processes each held 500 MB in RAM.

## The driver list API

```
GET https://www.asus.com/support/webapi/ProductV2/GetPDDrivers
  ?website=global&model=prime-z690-a&pdhashedid=z8oofpynawhdp7z3
  &pdid=19159&cpu=&osid=52&siteID=www&sitelang=
```
- `osid=52` = Windows 11 64-bit
- Returns `Result.Obj[].Files[].DownloadUrl.Global` — the file paths
- **Gotcha:** the first file in the "Chipset" category is actually the **ME
  driver**, not the chipset driver. The real chipset/SerialIO/GNA/DTT drivers
  are deeper in the list. Match by title keyword, not position.

## Key files

| File | What it taught us |
|------|-------------------|
| `levelFourProductSupportPage-*.js` | The download click handler, `getSupportCDNHQToken` call |
| `entry-*.js` | The `getSupportCDNHQToken` definition + `getCdnTokenUrl` host mapping |
| `browser-attempts/` | All the failed browser-clicking approaches (for reference) |