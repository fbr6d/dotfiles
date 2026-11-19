#!/bin/bash
LOG=~/.local/share/miku/remove-waypaper.log
echo "START $(date)" > "$LOG"
echo "waypaper를 지워요. 비밀번호를 물으면 PC 로그인 비밀번호를 입력하세요 (글자가 안 보이는 게 정상이에요)."
SUDO_ASKPASS="$__hermes_sudo_dir/a" sudo "${__hermes_sudo_o[@]}" pacman -R --noconfirm waypaper 2>&1 | tee -a "$LOG"
echo "EXIT ${PIPESTATUS[0]}" >> "$LOG"
echo "END $(date)" >> "$LOG"
echo; echo "끝났어요! 이 창은 10초 뒤에 닫혀요."; sleep 10
