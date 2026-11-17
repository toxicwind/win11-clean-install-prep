# 03 — NVIDIA Driver: 610.88 (not 621.24)

The RTX 5090 driver decision, based on Reddit community research
(November 17, 2026).

## Decision: **610.88**

| | 610.88 | 621.24 |
|---|--------|--------|
| Verdict | ✅ **Chosen** | ❌ Rejected |
| Community trust | Last stable, widely recommended | Problematic branch |
| Audio (Ableton) | No known DPC latency issues | **`nvlddmkm` high DPC latency → audio crackling** |
| Stability | Stable | Shader-compile crashes, black screens on 50-series |
| Security | No acknowledged CVEs | — |

## Why not 621.24

The `/r/nvidia` 621.24 FAQ thread confirms the 621.xx branch causes:

1. **`nvlddmkm` high DPC latency** → audio crackling. This is a **dealbreaker
   for Ableton** — audio dropouts/crackle during production.
2. **Shader-compile crashes** on 50-series GPUs.
3. **Black screens** in some configurations.

## Download

Verified URL (HTTP 200, ~980 MB):

```
https://us.download.nvidia.com/Windows/610.88/610.88-desktop-win10-win11-64bit-international-dch-whql.exe
```

```bash
curl -L -o 610.88-desktop-win10-win11-64bit-international-dch-whql.exe \
  "https://us.download.nvidia.com/Windows/610.88/610.88-desktop-win10-win11-64bit-international-dch-whql.exe"
```

## Install note

Install the NVIDIA driver **after** the chipset driver on the fresh system.
Use a **clean install** (custom) to avoid leftover config from any prior driver.