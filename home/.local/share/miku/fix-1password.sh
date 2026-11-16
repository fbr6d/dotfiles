#!/bin/sh
# 1Password 로그아웃 문제 수정 (2026-11-17, miku)
set -e
LOG=/home/leejaeik/.local/share/miku/fix-1password.log
exec > "$LOG" 2>&1

echo "== 1. gnome-keyring 설치"
pacman -S --needed --noconfirm gnome-keyring

echo "== 2. Zen 허용 브라우저 파일"
install -d -o root -g root -m 755 /etc/1password
printf 'zen-bin\n' > /etc/1password/custom_allowed_browsers
chown root:root /etc/1password/custom_allowed_browsers
chmod 755 /etc/1password/custom_allowed_browsers
ls -la /etc/1password

echo "== 3. hyprlock PAM에 키링 잠금 해제 추가"
if ! grep -q pam_gnome_keyring /etc/pam.d/hyprlock; then
    cp -a /etc/pam.d/hyprlock /etc/pam.d/hyprlock.bak-keyring
    printf 'auth        optional    pam_gnome_keyring.so\n' >> /etc/pam.d/hyprlock
fi
cat /etc/pam.d/hyprlock
chmod 644 "$LOG"
echo "== DONE"
