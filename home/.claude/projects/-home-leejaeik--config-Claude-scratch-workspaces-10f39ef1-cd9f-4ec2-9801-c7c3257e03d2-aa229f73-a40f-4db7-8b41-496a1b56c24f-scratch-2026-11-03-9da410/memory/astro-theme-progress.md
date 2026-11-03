---
name: astro-theme-progress
description: "Where the ASTRO external-flash Miku theme work stood when its original session was deleted (2026-11-03)"
metadata:
  type: project
---

The original working session was deleted on 2026-11-03 ~18:10 KST; its transcript is gone. Theme builds live in `~/firmware-backups/astro-cms32c030-20261103/modified/` (v3 … v15); latest is `extflash_1MB_theme_v15_vaping_teal.bin`, built by `tools/build_theme.sh` (recolor → Miku logo → battery pixel art → "01" icon). v15 was written to the real board on 2026-11-03 19:08 KST (211 sectors, full readback of 0x0-0xD2FFF matched v15). Confirmed on the device the same day: after a button press the screen comes on with the theme (idle = deep-sleep WFI at 0x5BB4, screen off until woken). Restore = `write_extflash.sh write ../original/extflash/extflash_full_1MB.bin`.

SWD write path added 2026-11-03: `tools/write_extflash.sh selftest|write|verify` (logic in `tools/extflash_write.tcl`). Dry-run against a simulated flash passed (v15 write, idempotent rerun, restore, injected resets); then used on the real board. On-board fixes: the M0 FPB cannot breakpoint in RAM (stub returns via bx lr to the 0x1B4 trap), and the IWDG at 0x40063000 must get 0xAAAA on every call. The IWDG also keeps counting while the core is halted, so a plain halted `dump_image` of the 64KB MCU flash fails or reads zeros after ~4 s; refresh 0xAAAA every 4KB (worked: 4 identical reads). Gotcha: OpenOCD Jim strings are UTF-8, so binary data must be sliced with `string byterange`/`bytelength`.

**How to apply:** continue from v15 and `build_theme.sh`; obey [[astro-never-touch-mcu-firmware]]; originals per [[astro-firmware-backup]].
