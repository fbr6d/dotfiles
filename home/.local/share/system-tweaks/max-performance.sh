#!/usr/bin/env bash
# Keep the screen at full brightness and the CPU in maximum-performance mode,
# now and on every boot. Run with sudo.
set -euo pipefail

# Full brightness at boot, after systemd-backlight restores the saved level
cat > /etc/systemd/system/max-brightness.service <<'EOF'
[Unit]
Description=Set all backlights to maximum brightness
After=systemd-backlight@backlight:acpi_video0.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'for d in /sys/class/backlight/*; do cat "$d/max_brightness" > "$d/brightness"; done'

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now max-brightness.service

# CPU: performance governor + performance energy preference on every boot
cat > /etc/tmpfiles.d/cpu-performance.conf <<'EOF'
w /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor - - - - performance
w /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference - - - - performance
EOF
systemd-tmpfiles --create /etc/tmpfiles.d/cpu-performance.conf

echo
echo "brightness: $(cat /sys/class/backlight/*/brightness)/$(cat /sys/class/backlight/*/max_brightness)"
echo "governor:   $(sort -u /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | tr '\n' ' ')"
echo "epp:        $(sort -u /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference | tr '\n' ' ')"
