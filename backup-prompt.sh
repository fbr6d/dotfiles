#!/usr/bin/env bash
# Run the settings backup (GitHub) and report the result in a desktop notification.
# Started every hour by ~/.config/systemd/user/dotfiles-backup-prompt.timer.
# Does nothing (and shows nothing) when no settings changed since the last backup.
# Personal files go to the HOME-MIGRATE USB instead (usb_backup.sh, run by hand).
set -uo pipefail

DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
STAMP="${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles-backup.stamp"
mkdir -p "$(dirname "$STAMP")"

# Any settings newer than the last backup? Only hidden files/folders in ~ hold settings;
# skip the ones that change on their own all the time.
changed() {
    [[ -e "$STAMP" ]] || return 0
    find "$HOME" -mindepth 1 \
        \( \( -path "$HOME/*" ! -path "$HOME/.*" \) \
           -o -path "$HOME/.cache" -o -path "$HOME/.config/Claude" -o -path "$HOME/.config/zen" \
           -o -path "$HOME/.config/pulse" -o -path "$HOME/.claude" -o -path "$HOME/.local/state" \
           -o -path "$HOME/.local/share/Trash" -o -path "$HOME/.local/share/gvfs-metadata" \
           -o -name .git -o -name node_modules -o -name '*history*' \) -prune \
        -o -newer "$STAMP" -type f -print -quit 2>/dev/null | grep -q .
}

changed || exit 0

out=$("$DIR/backup.py" 2>&1); rc=$?

if (( rc == 0 )); then
    touch "$STAMP"
    notify-send --transient --app-name="Backup" --icon=emblem-ok-symbolic "설정 백업 완료" \
        "$(tail -n2 <<<"$out" | head -n1)"
else
    # Most likely the secret scan stopped it; ask Claude ("설정 백업해줘") to sort it out.
    notify-send --transient --app-name="Backup" --urgency=critical --icon=dialog-error "설정 백업 실패" \
        "$(tail -n4 <<<"$out")"
fi
