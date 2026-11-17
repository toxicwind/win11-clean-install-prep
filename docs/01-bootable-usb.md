# 01 — Bootable USB

How the bootable Windows 11 USB was created.

## Tool: Rufus

Rufus was used (headless / CLI) to write the Windows 11 ISO to the USB drive.

```powershell
.\rufus.exe
```

## Rufus options used

These were selected to make the clean install smooth:

- **Remove requirement for an online Microsoft account** — allows a local
  account during setup
- **Remove TPM requirement** — bypasses the TPM 2.0 check
- **Remove BitLocker encryption** — no auto-encryption on install
- **Remove data collection** — disables telemetry prompts

## Result

- USB drive: `G:` (NTFS)
- `install.wim` — 7.6 GB
- `boot.wim` — 0.57 GB
- `boot/`, `efi/`, `sources/`, `support/` present

## Notes

- The USB is the **source** for the installer; the target disk becomes `C:`
  during install.
- Back up anything on the target disk before wiping — a clean install erases it.
- Rufus `/compact` variants exist (`/compact`, `/compact soft`,
  `/compact snapcompact`) to shrink the install — not needed here.