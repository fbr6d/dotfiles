#!/bin/sh
# Real-ESRGAN 설치 (미쿠가 만든 패키지를 pacman으로 설치)
LOG=/home/leejaeik/.local/share/miku/install-realesrgan.log
PKG="/home/leejaeik/.hermes/profiles/miku/cache/scratch/aur-resr/realesrgan-ncnn-vulkan-bin-0.2.5.0-1-x86_64.pkg.tar.zst"
echo "Real-ESRGAN 설치를 시작해요. PC 로그인 비밀번호를 입력해 주세요 (글자는 안 보이는 게 정상이에요)."
echo "시작 $(date)" > "$LOG"
sudo pacman -U --noconfirm "$PKG" >> "$LOG" 2>&1
rc=$?
echo "종료코드 $rc" >> "$LOG"
if [ $rc -eq 0 ]; then echo "설치 완료! 이 창은 5초 뒤에 닫혀요."; else echo "설치 실패 (종료코드 $rc). 로그: $LOG"; fi
sleep 5
