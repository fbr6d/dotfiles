#!/usr/bin/env bash
# Sunshine 설치 (2026-11-20, 마스터 승인 '1번' = Sunshine + Moonlight)
# 공식 LizardByte 패키지를 감싼 AUR sunshine-bin. 의존성(miniupnpc, libmfx 등)은 pacman이 공식 저장소에서 받음.
LOG="$HOME/.local/share/miku/install-sunshine.log"
PKG="$HOME/.local/share/miku/sunshine-bin-2026.914.233613-1-x86_64.pkg.tar.zst"
exec > >(tee "$LOG") 2>&1
echo "== $(date) Sunshine 설치 시작"
echo "아래에서 PC 로그인 비밀번호를 입력하세요 (글자가 안 보이는 게 정상이에요)"
sudo pacman -U --noconfirm "$PKG"
rc=$?
echo "== pacman 종료 코드: $rc"
echo "== setcap 확인:"; getcap "$(readlink -f /usr/bin/sunshine)"
echo "== uinput 권한:"; ls -l /dev/uinput /dev/uhid 2>&1; getfacl /dev/uinput 2>/dev/null | grep user
echo "EXIT $rc"
echo; echo "끝났어요! 이 창은 닫아도 돼요."
read -r -t 600 _
