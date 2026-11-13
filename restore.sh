#!/usr/bin/env bash
# Restore a backup made by backup.py onto a fresh Arch Linux install.
#
#   git clone https://github.com/<you>/dotfiles ~/dotfiles
#   ~/dotfiles/restore.sh            # everything
#   ~/dotfiles/restore.sh files      # only one step: packages|files|zen|home|dconf|etc|services
#
# Existing files that would be overwritten are moved to ~/.dotfiles-old/<time>/ first.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
OLD="$HOME/.dotfiles-old/$(date +%Y%m%d-%H%M%S)"
STEP="${1:-all}"

say() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
want() { [[ "$STEP" == all || "$STEP" == "$1" ]]; }

# Configs, the greetd auto-login and some links hard-code this home path.
BACKUP_HOME=/home/leejaeik
if [[ "$HOME" != "$BACKUP_HOME" ]]; then
    echo "Warning: the backup was made as $BACKUP_HOME, but this account is $HOME."
    echo "Paths in configs (kitty, ghostty, waypaper, swaync, greetd auto-login) will point to the wrong place."
    echo "Create the user 'leejaeik' and run this as that user, or press y to continue anyway."
    read -r -p "Continue? [y/N] " ans
    [[ "$ans" == [yY] ]] || exit 1
fi

# The backup comes from a T2 MacBook. On other hardware, leave out the Mac-only
# kernel, repo, firmware, fan/brightness services and Apple keyboard tweaks.
T2=0
[[ "$(cat /sys/class/dmi/id/sys_vendor 2>/dev/null)" == "Apple Inc." ]] && T2=1
T2_PKGS='^(linux-t2.*|apple-.*|arch-mact2-.*|t2fanrd|tiny-dfr)$'
T2_UNITS='^(t2fanrd|max-brightness)\.service$'
T2_ETC=(systemd/system/max-brightness.service modprobe.d/hid_apple.conf pacman.d/arch-mact2-mirrorlist)

# Kernel, microcode and GPU drivers for the machine being restored.
hw_pkgs() {
    if (( ! T2 )); then echo linux linux-headers; fi
    grep -q AuthenticAMD /proc/cpuinfo && echo amd-ucode
    grep -q GenuineIntel /proc/cpuinfo && echo intel-ucode
    local gpu; gpu=$(lspci -nn 2>/dev/null | grep -Ei 'vga|3d|display' || true)
    grep -qE 'AMD|ATI' <<<"$gpu" && echo mesa vulkan-radeon
    grep -qi intel <<<"$gpu" && echo mesa vulkan-intel intel-media-driver
    grep -qi nvidia <<<"$gpu" && echo nvidia-open nvidia-utils
    true
}

# Copy every file under $1 into $2, backing up anything it replaces.
place() {
    local src="$1" dst="$2" sudo="${3:-}"
    (cd "$src" && find . \( -type f -o -type l \) -print0) | while IFS= read -r -d '' rel; do
        rel="${rel#./}"
        if [[ -e "$dst/$rel" || -L "$dst/$rel" ]] && ! cmp -s "$src/$rel" "$dst/$rel"; then
            mkdir -p "$OLD/$(dirname "${dst#/}/$rel")"
            $sudo cp -a "$dst/$rel" "$OLD/${dst#/}/$rel"
        fi
        $sudo mkdir -p "$(dirname "$dst/$rel")"
        $sudo cp -a --remove-destination "$src/$rel" "$dst/$rel"
    done
}

if want packages; then
    say "Installing packages"
    # Extra repos (e.g. arch-mact2, slsrepo) must exist before installing from them.
    if [[ -f "$REPO/etc/pacman.conf" ]]; then
        tmp=$(mktemp -d) && mkdir -p "$tmp/etc"
        cp -a "$REPO/etc/pacman.conf" "$tmp/etc/"
        [[ -d "$REPO/etc/pacman.d" ]] && cp -a "$REPO/etc/pacman.d" "$tmp/etc/"
        if (( ! T2 )); then
            # Drop the [arch-mact2] repo section (header through the line before the next section).
            sed -i '/^\[arch-mact2\]/,/^\[/{/^\[arch-mact2\]/d;/^\[/!d}' "$tmp/etc/pacman.conf"
            rm -f "$tmp/etc/pacman.d/arch-mact2-mirrorlist"
        fi
        place "$tmp/etc" /etc sudo
        # A repo whose mirrorlist package isn't installed yet still needs that file: placed above.
        sudo pacman -Sy
    fi
    # Skip names no longer in the repos instead of failing the whole install.
    want_pkgs() {
        if (( T2 )); then cat "$REPO/meta/pacman.txt"; else grep -vE "$T2_PKGS" "$REPO/meta/pacman.txt"; fi
        hw_pkgs | tr ' ' '\n'
    }
    mapfile -t pkgs < <(comm -12 <(want_pkgs | sort -u) <(pacman -Slq | sort -u))
    sudo pacman -Syu --needed "${pkgs[@]}"
    if [[ -s "$REPO/meta/aur.txt" ]]; then
        if ! command -v yay >/dev/null; then
            sudo pacman -S --needed git base-devel
            tmp=$(mktemp -d) && git clone https://aur.archlinux.org/yay-bin.git "$tmp/yay-bin"
            (cd "$tmp/yay-bin" && makepkg -si --noconfirm)
        fi
        grep -vxE 'yay|yay-bin|yay-debug|yay-bin-debug' "$REPO/meta/aur.txt" | yay -S --needed - || true
    fi
    if [[ -s "$REPO/meta/flatpak.txt" ]] && command -v flatpak >/dev/null; then
        xargs -a "$REPO/meta/flatpak.txt" flatpak install -y flathub || true
    fi
fi

if want files; then
    say "Restoring home files"
    place "$REPO/home" "$HOME"
    chmod +x "$HOME"/.local/bin/* 2>/dev/null || true
    fc-cache -f >/dev/null 2>&1 || true
    # Links whose target isn't in the backup (e.g. the Claude Code CLI, ~325MB).
    find "$HOME/.local/bin" -maxdepth 1 -xtype l -print | while read -r l; do
        echo "Broken link: $l -> $(readlink "$l")"
        [[ "$(basename "$l")" == claude ]] && echo "  Reinstall Claude Code: curl -fsSL https://claude.ai/install.sh | bash"
    done
fi

if want zen && [[ -d "$REPO/zen" ]]; then
    say "Restoring Zen browser profile (close Zen first)"
    if pgrep -x zen >/dev/null || pgrep -f zen-bin >/dev/null; then
        echo "Zen is running; skipping. Close it and run: $0 zen"
    else
        place "$REPO/zen" "$HOME/.config/zen"
        # Bookmarks: Zen imports the newest bookmarkbackups file when places.sqlite is missing.
    fi
fi

if want home; then
    say "Restoring personal files (Documents, Pictures, ...) from the home-backup repo"
    if [[ ! -d "$HOME/home-backup/.git" ]]; then
        gh repo clone home-backup "$HOME/home-backup" || git clone "https://github.com/$(gh api user --jq .login)/home-backup.git" "$HOME/home-backup"
    fi
    place "$HOME/home-backup/files" "$HOME"
    # Files from Claude "No folder" sessions, one folder per session.
    [[ -d "$HOME/home-backup/claude-sessions" ]] && place "$HOME/home-backup/claude-sessions" "$HOME/Claude-sessions"
    for pkg in "$HOME"/home-backup/anki/*/latest.colpkg; do
        [[ -f "$pkg" ]] && echo "Anki cards: open Anki, then File > Import > $pkg (audio/images are not in the backup)"
    done
fi

if want dconf && [[ -s "$REPO/meta/dconf.ini" ]]; then
    say "Loading dconf (GTK/GNOME app) settings"
    dconf load / < "$REPO/meta/dconf.ini"
fi

if want etc && [[ -d "$REPO/etc" ]]; then
    say "Restoring /etc files (needs sudo)"
    # Boot files depend on the hardware; show them instead of overwriting.
    tmp=$(mktemp -d) && cp -a "$REPO/etc/." "$tmp/"
    rm -f "$tmp/default/grub" "$tmp/mkinitcpio.conf"
    if (( ! T2 )); then for f in "${T2_ETC[@]}"; do rm -f "$tmp/$f"; done; fi
    place "$tmp" /etc sudo
    sudo systemctl daemon-reload
    [[ -f "$REPO/etc/locale.gen" ]] && sudo locale-gen
    for f in default/grub mkinitcpio.conf; do
        if [[ -f "$REPO/etc/$f" ]] && ! cmp -s "$REPO/etc/$f" "/etc/$f"; then
            echo "Not applied (boot-critical): /etc/$f differs from the backup. Compare with:"
            echo "  diff /etc/$f $REPO/etc/$f"
            echo "  then: sudo cp $REPO/etc/$f /etc/$f && sudo mkinitcpio -P / sudo grub-mkconfig -o /boot/grub/grub.cfg"
            (( T2 )) || echo "  (Not a T2 Mac: copy only the quiet/splash options; drop intel_iommu, pcie_ports, pm_async, mem_sleep_default.)"
        fi
    done
fi

if want services; then
    say "Enabling services"
    while read -r u; do
        (( ! T2 )) && [[ "$u" =~ $T2_UNITS ]] && continue
        [[ -n "$u" && "$u" != *@* ]] && sudo systemctl enable "$u" 2>/dev/null || true
    done < "$REPO/meta/services-system.txt"
    while read -r u; do
        [[ -n "$u" && "$u" != *@* ]] && systemctl --user enable "$u" 2>/dev/null || true
    done < "$REPO/meta/services-user.txt"
fi

say "Done. Replaced files (if any) are in $OLD. Log out and back in to apply everything."
