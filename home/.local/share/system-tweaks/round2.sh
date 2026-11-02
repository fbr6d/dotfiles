#!/usr/bin/env bash
# Install the replacement apps (control center, OSD, lock screen, idle) and
# update the login screen (no user name). Run as your user; asks for sudo.
set -euo pipefail

sudo pacman -S --needed swaync swayosd hyprlock hypridle
sudo install -Dm755 "$HOME/.local/share/mono-greeter/mono-greeter.py" /etc/greetd/mono-greeter.py
yay -S --needed waypaper

echo
echo "Done."
