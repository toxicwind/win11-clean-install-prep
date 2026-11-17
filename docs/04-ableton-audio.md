# 04 — Ableton Audio Setup

The audio stack and what survives a clean install.

## The audio stack

| Device | Role |
|--------|------|
| **Realtek S1220A** (onboard) | The board's audio — Ableton's audio driver target |
| **VB-Audio Virtual Cable** | Routing glue — pipes audio between apps / into Ableton |
| CORSAIR HS80 RGB Wireless | Headset (wireless) |
| USB Audio Device | Some USB interface |
| NVIDIA High Definition Audio | HDMI/DP audio from the GPU |
| Virtual Desktop Audio | VR/desktop virtual device |

## The critical problem

**Drivers can be staged, but the *routing* cannot.**

On a clean install, the following are **lost** and must be reconfigured by hand:

1. **Ableton's audio settings** — which ASIO driver, sample rate, buffer size,
   and input/output device mapping. This lives in Ableton's preferences and
   does **not** survive a wipe.
2. **Windows default playback/recording device** — which device is the system
   default.
3. **VB-Audio Virtual Cable routing** — how the virtual cable is wired into
   Ableton (ASIO config).

## What IS staged on the USB

- **Realtek S1220A driver** (`DRV_Audio_RTK_UWD_DTSXU_TP_W11_64_V6092441_20211027R.zip`)
  — the onboard audio driver, Ableton-critical.
- **VB-Audio Virtual Cable** (`VBCABLE_Driver_Pack46.zip`) — reinstalls the
  routing glue.

## Post-install checklist (manual)

1. Install the Realtek audio driver.
2. Install VB-Audio Virtual Cable.
3. In Windows Sound settings, set the correct default playback device.
4. Open Ableton → Preferences → Audio:
   - Select the ASIO driver (Realtek ASIO or the interface's ASIO)
   - Set sample rate (e.g. 48 kHz) and buffer size (lower = less latency,
     higher = more stable)
   - Map inputs/outputs, including the VB-Cable channels if used
5. Test for crackling — if present, raise the buffer size.

## Why the NVIDIA driver matters here

The 621.24 NVIDIA driver causes `nvlddmkm` high DPC latency → **audio
crackling**. That's why 610.88 was chosen (see `03-nvidia-driver.md`) — it
keeps the audio clean for Ableton.