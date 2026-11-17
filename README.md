# Windows 11 Clean-Install Prep

Everything needed to do a clean Windows 11 install on an **ASUS PRIME Z690-A**
with an **RTX 5090**, prioritizing **Ableton (audio)**. This repo captures the
full process: bootable USB, driver staging, the reverse-engineered ASUS
download flow, and the NVIDIA driver decision.

## Hardware

| Component | Detail |
|-----------|--------|
| Motherboard | ASUS PRIME Z690-A |
| CPU | Intel i9-12900K |
| GPU | NVIDIA RTX 5090 |
| Audio | Realtek S1220A (onboard) |
| Headset | CORSAIR HS80 RGB Wireless |
| Audio routing | VB-Audio Virtual Cable (Ableton) |

## Repo layout

```
win11-clean-install-prep/
├── README.md                  ← this file
├── docs/
│   ├── 01-bootable-usb.md     ← Rufus, Windows 11 ISO, options
│   ├── 02-driver-list.md      ← every driver needed + why
│   ├── 03-nvidia-driver.md    ← 610.88 vs 621.24 decision (Reddit research)
│   ├── 04-ableton-audio.md    ← audio stack + what survives a wipe
│   └── 05-post-install.md     ← install order, what to reconfigure
└── drivers/
    ├── README.md              ← ASUS downloader overview
    ├── REVERSE_ENGINEERING.md ← how the signed-URL flow was cracked
    ├── download_asus.py       ← full pipeline (list → sign → download)
    ├── download_remaining.py  ← specific driver paths
    ├── requirements.txt
    └── browser-attempts/      ← failed browser-clicking approaches (reference)
```

## Quick start

```bash
# Stage drivers on the USB
pip install -r drivers/requirements.txt
python drivers/download_asus.py --model "PRIME Z690-A" --pdid 19159 --hashedid z8oofpynawhdp7z3

# NVIDIA driver (verified URL, ~980 MB)
curl -L -o 610.88-desktop-win10-win11-64bit-international-dch-whql.exe \
  "https://us.download.nvidia.com/Windows/610.88/610.88-desktop-win10-win11-64bit-international-dch-whql.exe"

# VB-Audio Virtual Cable (Ableton routing)
curl -L -o VBCABLE_Driver_Pack46.zip \
  "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack46.zip"
```

## The hard-won lessons

1. **ASUS signed URLs** — every download is signed per-file and path-bound.
   The token API (`cdnta.asus.com/api/v1/TokenHQ`) generates them, but only
   with browser headers (`Referer`, `Origin`, real UA) and `curl_cffi`'s Chrome
   impersonation. Full story in `drivers/REVERSE_ENGINEERING.md`.
2. **NVIDIA 610.88, not 621.24** — the 621.xx branch has `nvlddmkm` high DPC
   latency → audio crackling (Ableton killer) + shader-compile crashes on
   50-series. 610.88 is the last stable community-recommended driver. See
   `docs/03-nvidia-driver.md`.
3. **Ableton audio routing doesn't survive a wipe** — drivers can be staged,
   but the ASIO config / default-device / sample-rate settings live in Ableton
   and the Windows audio registry. You'll reconfigure those by hand. See
   `docs/04-ableton-audio.md`.

## License

MIT

## Related repos

- [**diskaudit**](https://github.com/toxicwind/diskaudit) — the disk migration
  + `install/post-install.ps1` headless post-install script for this reinstall.
- [**omp-windows**](https://github.com/toxicwind/omp-windows) — the omp configs
  restored after install.
- [**omp-model-benchmarks**](https://github.com/toxicwind/omp-model-benchmarks)
  — the model catalog/benchmark data gathered during this prep.