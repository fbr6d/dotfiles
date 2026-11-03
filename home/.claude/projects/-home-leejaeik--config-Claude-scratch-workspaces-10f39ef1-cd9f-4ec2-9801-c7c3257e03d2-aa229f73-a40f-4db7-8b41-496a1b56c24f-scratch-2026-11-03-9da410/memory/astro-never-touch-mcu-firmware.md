---
name: astro-never-touch-mcu-firmware
description: "User forbids any change to the ASTRO board's MCU (CMS32C030) firmware; only external-flash image edits are allowed"
metadata:
  type: feedback
---

Never modify, patch, or reflash the ASTRO board's MCU firmware (CMS32C030 main flash), not even a 48-byte table edit. Customisation is limited to the external SPI flash images, and each image must keep its original RLE word length and address.

**Why:** the user believes the firmware also handles battery/power logic, so any firmware change or bug is an unacceptable safety risk (said 2026-11-03).

**How to apply:** reject plans that need MCU edits (e.g. relocating battery frames by patching the table at MCU 0xBCA4); fit everything into the existing external-flash slots. See [[astro-firmware-backup]].
