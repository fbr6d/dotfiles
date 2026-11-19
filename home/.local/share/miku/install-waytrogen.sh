#!/bin/bash
LOG=~/.local/share/miku/install-waytrogen.log
echo "START $(date)" > "$LOG"
echo "waytrogen-bin 설치를 시작해요. 비밀번호를 물으면 PC 로그인 비밀번호를 입력하세요 (글자가 안 보이는 게 정상이에요)."
paru -S --needed --noconfirm --skipreview waytrogen-bin 2>&1 | tee -a "$LOG"
echo "EXIT ${PIPESTATUS[0]}" >> "$LOG"
echo "END $(date)" >> "$LOG"
echo; echo "끝났어요! 이 창은 10초 뒤에 닫혀요."; sleep 10
