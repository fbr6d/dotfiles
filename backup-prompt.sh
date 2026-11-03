#!/usr/bin/env bash
# Ask with a desktop notification whether to back up now; run both backups on "yes".
# Started every 30 minutes by ~/.config/systemd/user/dotfiles-backup-prompt.timer.
# Stays quiet when nothing changed since the last backup.
set -uo pipefail

DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
STAMP="${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles-backup.stamp"
mkdir -p "$(dirname "$STAMP")"

# Anything newer than the last backup? Skip folders that change on their own all the time.
changed() {
    [[ -e "$STAMP" ]] || return 0
    find "$HOME" -mindepth 1 \
        \( -path "$HOME/.cache" -o -path "$HOME/.config/Claude" -o -path "$HOME/.config/zen" \
           -o -path "$HOME/.config/pulse" -o -path "$HOME/.claude" -o -path "$HOME/.local/state" \
           -o -path "$HOME/.local/share/Trash" -o -path "$HOME/.local/share/gvfs-metadata" \
           -o -path "$HOME/dotfiles" -o -path "$HOME/home-backup" -o -path "$HOME/yay" \
           -o -name .git -o -name node_modules -o -name '*history*' \) -prune \
        -o -newer "$STAMP" -type f -print -quit 2>/dev/null | grep -q .
}

changed || exit 0

answer=$(notify-send --app-name="Backup" --icon=document-save --expire-time=300000 --wait \
    --action=yes="백업" --action=no="나중에" \
    "설정 백업" "마지막 백업 이후 바뀐 파일이 있어요. 지금 GitHub에 백업할까요?")
[[ "$answer" == yes ]] || exit 0

notify-send --app-name="Backup" --icon=document-save "백업 중…" "설정과 홈 파일을 올리고 있어요."
out1=$("$DIR/backup.py" 2>&1); rc1=$?
out2=$("$DIR/home_backup.py" 2>&1); rc2=$?

if (( rc1 == 0 && rc2 == 0 )); then
    touch "$STAMP"
    notify-send --app-name="Backup" --icon=emblem-ok-symbolic "백업 완료" \
        "설정: $(tail -n2 <<<"$out1" | head -n1)
홈: $(tail -n2 <<<"$out2" | head -n1)"
else
    # Most likely the secret scan stopped it; ask Claude ("설정 백업해줘") to sort it out.
    notify-send --app-name="Backup" --urgency=critical --icon=dialog-error "백업 실패" \
        "$( ((rc1)) && tail -n4 <<<"$out1")
$( ((rc2)) && tail -n4 <<<"$out2")"
fi
