#!/usr/bin/env bash
# Mirror the whole home directory onto the HOME-MIGRATE USB drive (ext4) for
# moving to a new computer. Unlike the GitHub backups this keeps everything,
# videos and big files included; only caches, trash and things that can be
# re-downloaded are left out. Run again any time: it copies just the changes.
#
#   ~/dotfiles/usb_backup.sh            # update the copy on the USB
#   ~/dotfiles/usb_backup.sh --dry-run  # show what would change
#
# Restore on the new computer (same user name), with the USB mounted:
#   rsync -aHAX --info=progress2 /run/media/$USER/HOME-MIGRATE/home/ ~/
set -euo pipefail

LABEL=HOME-MIGRATE
DEST="$(findmnt -nro TARGET LABEL="$LABEL" 2>/dev/null | head -n1 || true)"
if [[ -z "$DEST" ]]; then
    dev=$(blkid -L "$LABEL" 2>/dev/null || true)
    [[ -n "$dev" ]] || { echo "USB '$LABEL' not found. Plug it in."; exit 1; }
    udisksctl mount -b "$dev" >/dev/null
    DEST="$(findmnt -nro TARGET LABEL="$LABEL" | head -n1)"
fi

# Re-creatable or junk; everything else in ~ is copied.
EXCLUDES=(
    /.cache/
    /.local/share/Trash/
    /home-backup/                 # same files as ~, already on GitHub
    /.local/share/claude/         # Claude Code CLI binaries (reinstall)
    /.local/share/spotify-launcher/
    /.config/Claude/Cache/ "/.config/Claude/Code Cache/" /.config/Claude/GPUCache/
    /.config/Claude/GPUPersistentCache/ /.config/Claude/logs/
    "Cache/" "Code Cache/" "GPUCache/" "DawnCache/" "DawnGraphiteCache/" "DawnWebGPUCache/"
    "GrShaderCache/" "ShaderCache/" "component_crx_cache/" "__pycache__/"
    /.cargo/registry/ /.cargo/git/   # crate downloads, fetched again by cargo
)
args=(-aHAX --delete --delete-excluded --info=progress2,stats1 --human-readable)
for e in "${EXCLUDES[@]}"; do args+=(--exclude="$e"); done
[[ "${1:-}" == --dry-run ]] && args+=(--dry-run)

mkdir -p "$DEST/home"
rsync "${args[@]}" "$HOME/" "$DEST/home/"
date '+%F %T' > "$DEST/last-backup.txt"
sync
df -h "$DEST" | tail -n1 | awk '{print "USB used " $3 " / " $2 " (" $5 ")"}'
