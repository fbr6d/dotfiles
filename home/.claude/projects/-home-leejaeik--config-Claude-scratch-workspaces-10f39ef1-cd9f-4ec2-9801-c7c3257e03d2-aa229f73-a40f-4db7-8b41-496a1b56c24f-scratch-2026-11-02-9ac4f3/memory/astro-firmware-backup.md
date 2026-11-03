---
name: astro-firmware-backup
description: "Where the verified original ASTRO vape (CMS32C030) MCU + external flash dumps are backed up, and what is still missing"
metadata:
  node_type: memory
  type: project
  originSessionId: c73685a4-80b1-4d76-9a4b-a3f1903e3c1c
  modified: 2026-11-03T06:26:56.262Z
---

Original dumps of the ASTRO "buck boost" board (MCU Cmsemicon CMS32C030, 1MB external SPI flash) are backed up at `~/firmware-backups/astro-cms32c030-20261103/` (read-only `original/`, SHA256SUMS, README with restore notes) plus `~/firmware-backups/astro-cms32c030-20261103.tar.gz` (made 2026-11-03).

**Why:** the user wants to be able to fully restore the device if a firmware/image modification goes wrong.

**How to apply:** never overwrite `original/`; verify with `sha256sum -c SHA256SUMS` before any restore. Still missing as of 2026-11-03: MCU data flash / option bytes (address unknown without datasheet), and an off-machine copy. MCU flash writing has no OpenOCD driver — restore needs Cmsemicon tool or Keil DFP + pyOCD; external flash write needs a SOIC-8 clip + serprog/flashrom.
