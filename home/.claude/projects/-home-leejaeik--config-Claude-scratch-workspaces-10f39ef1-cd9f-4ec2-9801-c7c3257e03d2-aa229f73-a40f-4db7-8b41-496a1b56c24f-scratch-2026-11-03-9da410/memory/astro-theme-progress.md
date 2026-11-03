---
name: astro-theme-progress
description: "Where the ASTRO external-flash Miku theme work stood when its original session was deleted (2026-11-03)"
metadata:
  type: project
---

The original working session was deleted on 2026-11-03 ~18:10 KST; its transcript is gone. Theme builds live in `~/firmware-backups/astro-cms32c030-20261103/modified/` (v3 … v15); latest is `extflash_1MB_theme_v15_vaping_teal.bin`, built by `tools/build_theme.sh` (recolor → Miku logo → battery pixel art → "01" icon). Nothing has been written to the device yet as far as known.

SWD write path added 2026-11-03: `tools/write_extflash.sh selftest|write|verify` (logic in `tools/extflash_write.tcl`). Dry-run against a simulated flash passed (v15 write, idempotent rerun, restore, injected resets); not yet run on the real board. Gotcha: OpenOCD Jim strings are UTF-8, so binary data must be sliced with `string byterange`/`bytelength`.

**How to apply:** continue from v15 and `build_theme.sh`; obey [[astro-never-touch-mcu-firmware]]; originals per [[astro-firmware-backup]].
