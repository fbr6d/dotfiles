#!/bin/bash
LOG=~/.local/share/miku/install-node.log
echo "== 시작 $(date)" > "$LOG"
echo "미쿠: Homebridge용 Node.js 설치예요. 비밀번호를 입력해 주세요~"
sudo pacman -S --needed --noconfirm nodejs-lts-krypton npm 2>&1 | tee -a "$LOG"
echo "== 종료코드 ${PIPESTATUS[0]} $(date)" >> "$LOG"
echo; echo "끝났어요! Enter를 누르면 창이 닫혀요."; read
