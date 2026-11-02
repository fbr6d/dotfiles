#!/usr/bin/env bash
# Install greetd + cage with the mono greeter and enable it at boot.
# Run with sudo. Takes effect after reboot (does not touch the running session).
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
USER_HOME="$(getent passwd "${SUDO_USER:-leejaeik}" | cut -d: -f6)"

pacman -S --needed --noconfirm greetd cage

install -Dm755 "$SRC/mono-greeter.py" /etc/greetd/mono-greeter.py

# The greeter user cannot read ~/.local/share/fonts; install Pretendard system-wide
install -d /usr/local/share/fonts/Pretendard
install -m644 "$USER_HOME"/.local/share/fonts/Pretendard/*.otf /usr/local/share/fonts/Pretendard/
fc-cache -f /usr/local/share/fonts >/dev/null

if [[ -f /etc/greetd/config.toml && ! -f /etc/greetd/config.toml.orig ]]; then
    cp /etc/greetd/config.toml /etc/greetd/config.toml.orig
fi
cat > /etc/greetd/config.toml <<'EOF'
[terminal]
vt = 1

[default_session]
command = "cage -s -- python3 /etc/greetd/mono-greeter.py"
user = "greeter"
EOF

systemctl enable greetd.service
echo
echo "Done. Reboot to use the new login screen."
echo "If anything goes wrong: Ctrl+Alt+F2 for a text login, then 'sudo systemctl disable greetd'."
