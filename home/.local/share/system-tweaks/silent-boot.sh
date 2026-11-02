#!/usr/bin/env bash
# Hide console text during boot: kernel/systemd messages, cursor, and the gap
# between the Plymouth splash and the greetd login screen. Run with sudo.
set -euo pipefail

# Kernel command line: no kernel/udev/systemd status output, no blinking cursor
cp -n /etc/default/grub /etc/default/grub.orig
sed -i 's|^GRUB_CMDLINE_LINUX_DEFAULT=.*|GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=0 rd.udev.log_level=0 udev.log_level=0 systemd.show_status=false rd.systemd.show_status=false vt.global_cursor_default=0"|' /etc/default/grub
grep '^GRUB_CMDLINE_LINUX_DEFAULT' /etc/default/grub

# Keep later kernel messages off the console too
echo 'kernel.printk = 0 0 0 0' > /etc/sysctl.d/20-quiet-printk.conf
sysctl -q -p /etc/sysctl.d/20-quiet-printk.conf

# Keep the splash image on screen until the login screen draws over it
install -d /etc/systemd/system/plymouth-quit.service.d
cat > /etc/systemd/system/plymouth-quit.service.d/retain-splash.conf <<'EOF'
[Service]
ExecStart=
ExecStart=-/usr/bin/plymouth quit --retain-splash
EOF
systemctl daemon-reload

grub-mkconfig -o /boot/grub/grub.cfg
echo
echo "Done. Takes effect on next boot."
