#!/bin/sh
# SUPER+I: open the Linux command dictionary, or show/hide it if already open.
exec "$HOME/.local/bin/popup-window" local.LinuxCheatsheet "center:80%x90%" -- "$HOME/.local/share/linux-cheatsheet/viewer.py"
