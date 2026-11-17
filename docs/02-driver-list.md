# 02 — Driver List

Every driver needed for the ASUS PRIME Z690-A + RTX 5090 clean install, and
why. All staged on the USB under `G:/Drivers/`.

## ASUS motherboard drivers (`G:/Drivers/ASUS/`)

| Driver | Version | File | Size | Why |
|--------|---------|------|------|-----|
| LAN | Intel I225/I226 NDIS 1.1.4.43 | `DRV_LAN_Intel_I226_UWD_TP_W10_64_V11443_20240710R.zip` | 2.5 MB | Ethernet — needed for first boot / updates |
| Chipset | Intel 10.1.20532.8842 | `DRV_Chipset_Intel_RPL_TP_W11_64_V101205328842_20260701R.zip` | 96.7 MB | Core platform drivers |
| ME (Management Engine) | 2603.9.4.0 | `DRV_MEI_Intel_Cons_RPL_TP_W11_64_V2603940_20260701R.zip` | 473 MB | Firmware + MEI driver |
| Audio | Realtek 6.0.9244.1 | `DRV_Audio_RTK_UWD_DTSXU_TP_W11_64_V6092441_20211027R.zip` | 177 MB | **S1220A onboard audio — Ableton-critical** |
| Serial IO | 30.100.2417.30 | `DRV_SerialIO_Intel_RPL_TP_W11_64_V30100241730_20240806R.zip` | 4.8 MB | Intel Serial IO |
| GNA | 3.5.0.1578 | `DRV_GNA_Intel_RPL_TP_W11_64_V3501578_20240806R.zip` | 2.2 MB | Gaussian Neural Accelerator |
| DTT | 9.0.11405.42569 | `DRV_DTT_Intel_RPL_TP_W11_64_V101140542038_20240319R.zip` | 15.2 MB | Dynamic Tuning Technology |
| RST (SATA) | 20.2.1.1016 | `DRV_RST_Intel_ARL_TP_W11_64_V20211016_20241204R.zip` | 26 MB | Rapid Storage Technology |

**Skipped:** Intel iGPU VGA driver — the RTX 5090 is the primary GPU, the
onboard iGPU driver is unnecessary.

## NVIDIA (`G:/Drivers/NVIDIA/`)

| Driver | Version | File | Size |
|--------|---------|------|------|
| RTX 5090 | **610.88** | `610.88-desktop-win10-win11-64bit-international-dch-whql.exe` | 979 MB |

See `03-nvidia-driver.md` for why 610.88 and not 621.24.

## Audio routing (`G:/Drivers/`)

| Driver | File | Size |
|--------|------|------|
| VB-Audio Virtual Cable | `VBCABLE_Driver_Pack46.zip` | 1.3 MB |

VB-Audio Virtual Cable is installed and in use on the current machine (multiple
instances, one OK) — it's the routing glue for Ableton. It does **not** survive
a clean install, so it's staged here.

## How the ASUS drivers were obtained

The ASUS support API returns file paths, but every download is behind a
per-file signed URL. The token API + `curl_cffi` flow is fully documented in
`drivers/REVERSE_ENGINEERING.md` and automated in `drivers/download_asus.py`.