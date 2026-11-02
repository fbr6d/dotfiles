#!/bin/sh
# SUPER+I: open the Linux command dictionary, or show/hide it if already open.
# Hyprland keeps its window on the special workspace "linuxcheat".
if hyprctl clients -j | grep -q '"class": "local.LinuxCheatsheet"'; then
    hyprctl dispatch 'hl.dsp.workspace.toggle_special("linuxcheat")'
else
    exec "$HOME/.local/share/linux-cheatsheet/viewer.py"
fi
