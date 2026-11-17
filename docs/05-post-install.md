# 05 — Post-Install

The recommended install order and manual reconfiguration after the clean
Windows 11 install.

## Install order

1. **Boot from the USB** (`G:`), install Windows 11 to the target disk (becomes
   `C:`).
2. **LAN driver** first — gives you network for updates.
3. **Chipset driver** — core platform drivers.
4. **ME (Management Engine)** — firmware + MEI.
5. **Audio (Realtek S1220A)** — Ableton-critical.
6. **NVIDIA 610.88** — clean install (custom) to avoid leftover config.
7. **Serial IO, GNA, DTT, RST** — remaining platform drivers.
8. **VB-Audio Virtual Cable** — audio routing glue.

## Manual reconfiguration (doesn't survive a wipe)

- **Ableton audio settings** — ASIO driver, sample rate, buffer size, I/O
  mapping (see `04-ableton-audio.md`).
- **Windows default audio device**.
- **VB-Cable routing** into Ableton.

## Driver locations on the USB

```
G:/Drivers/
├── ASUS/        ← all 8 motherboard drivers
├── NVIDIA/      ← 610.88 installer (979 MB)
└── VBCABLE_Driver_Pack46.zip
```

## After everything works

- Run Windows Update to catch any remaining drivers.
- Verify audio has no crackling (test in Ableton at your usual buffer size).
- If crackling appears, raise the buffer size or check DPC latency.