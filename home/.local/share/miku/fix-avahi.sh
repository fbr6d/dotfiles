#!/usr/bin/env bash
# avahi 이름 충돌 수정 (2026-11-20, 마스터 승인 '문제는 고쳐주고')
# Tailscale 통로(tailscale0)에서는 이름 알리기를 하지 않게 한다.
LOG="$HOME/.local/share/miku/fix-avahi.log"
exec > >(tee "$LOG") 2>&1
CONF=/etc/avahi/avahi-daemon.conf
echo "== $(date) avahi 수정 시작"
echo "아래에서 PC 로그인 비밀번호를 입력하세요 (글자가 안 보이는 게 정상이에요)"
sudo -v || { echo "EXIT sudo-failed"; read -r -t 600 _; exit 1; }
[ -e "$CONF.bak-tailscale" ] || sudo cp -p "$CONF" "$CONF.bak-tailscale"
if grep -q '^deny-interfaces=' "$CONF"; then
  echo "이미 deny-interfaces 줄이 있어요:"; grep -n '^deny-interfaces=' "$CONF"
else
  sudo sed -i 's/^#deny-interfaces=eth1$/#deny-interfaces=eth1\ndeny-interfaces=tailscale0/' "$CONF"
fi
grep -n 'interfaces' "$CONF"
sudo systemctl restart avahi-daemon.service
rc=$?
sleep 4
systemctl is-active avahi-daemon.service
journalctl -u avahi-daemon --since "-10 s" --no-pager | grep -E "Host name|conflict|tailscale0"
echo "EXIT $rc"
echo; echo "끝났어요! 이 창은 닫아도 돼요."
read -r -t 600 _
