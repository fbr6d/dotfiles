#!/usr/bin/env bash
# 방화벽(ufw) + Tailscale 설치 (2026-11-20, 마스터 승인 '이대로 설치해 주세요')
LOG="$HOME/.local/share/miku/install-firewall.log"
exec > >(tee "$LOG") 2>&1
LAN4=192.168.219.0/24
LAN6=fe80::/10
echo "== $(date) 방화벽 + Tailscale 설치 시작"
echo "아래에서 PC 로그인 비밀번호를 입력하세요 (글자가 안 보이는 게 정상이에요)"
sudo -v || { echo "EXIT sudo-failed"; read -r -t 600 _; exit 1; }

echo "== 1) 패키지 설치"
sudo pacman -S --needed --noconfirm ufw tailscale || { echo "EXIT pacman-failed"; read -r -t 600 _; exit 1; }

echo "== 2) 방화벽 기본값: 들어오는 연결 막기, 나가는 연결 허용"
sudo ufw --force reset >/dev/null
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw default deny routed

echo "== 3) 집 공유기 안에서만 허용"
for SRC in $LAN4 $LAN6; do
  # 홈브리지(애플 홈): HAP, 웹 화면, mDNS 기기 찾기
  sudo ufw allow from $SRC to any port 51826 proto tcp comment 'Homebridge HAP'
  sudo ufw allow from $SRC to any port 8581 proto tcp comment 'Homebridge UI'
  sudo ufw allow from $SRC to any port 5353 proto udp comment 'mDNS'
  # LocalSend
  sudo ufw allow from $SRC to any port 53317 comment 'LocalSend'
  # Spotify Connect
  sudo ufw allow from $SRC to any port 57621 comment 'Spotify Connect'
  sudo ufw allow from $SRC to any port 1900 proto udp comment 'Spotify SSDP'
  # Sunshine
  sudo ufw allow from $SRC to any port 47984,47989,47990,48010 proto tcp comment 'Sunshine TCP'
  sudo ufw allow from $SRC to any port 47998:48010 proto udp comment 'Sunshine UDP'
done
# WiZ 전구 답장 (homebridge-wiz-lan, IPv4만)
sudo ufw allow from $LAN4 to any port 38900 proto udp comment 'WiZ bulb replies'

echo "== 4) Tailscale 통로 안에서는 Sunshine만, 직접 연결용 41641"
sudo ufw allow in on tailscale0 to any port 47984,47989,47990,48010 proto tcp comment 'Sunshine via Tailscale'
sudo ufw allow in on tailscale0 to any port 47998:48010 proto udp comment 'Sunshine via Tailscale'
sudo ufw allow 41641/udp comment 'Tailscale direct'

echo "== 5) 방화벽 켜기 + 부팅 때 자동 시작"
sudo ufw --force enable
sudo systemctl enable --now ufw.service
sudo ufw status verbose

echo "== 6) Tailscale 켜기"
sudo systemctl enable --now tailscaled.service
sleep 2
echo
echo "★ 아래에 나오는 https://login.tailscale.com/... 주소를 Ctrl+Shift+클릭(또는 복사)해서 브라우저에서 로그인하세요."
echo "★ 구글/애플/마이크로소프트 계정 중 편한 걸로 가입하면 돼요. 휴대폰·노트북도 같은 계정으로 로그인해야 해요."
sudo tailscale up --operator="$USER"
rc=$?
echo "== tailscale up 종료 코드: $rc"
tailscale ip -4 2>&1
tailscale status 2>&1 | head -5
echo "EXIT $rc"
echo; echo "끝났어요! 이 창은 닫아도 돼요."
read -r -t 600 _
