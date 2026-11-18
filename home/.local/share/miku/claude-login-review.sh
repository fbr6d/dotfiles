#!/bin/bash
LOG=~/.local/share/miku/claude-login-review.log
echo "== 시작 $(date)" > "$LOG"
echo "미쿠: ksat-review(검수 봇)에 새 Claude Pro 계정을 로그인하는 창이에요."
echo "브라우저가 열리면 '새 계정'으로 로그인해 주세요. (지금 미쿠가 쓰는 계정이 아니에요!)"
echo
hermes -p ksat-review auth add anthropic --type oauth --label claude-pro-review 2>&1 | tee -a "$LOG"
echo "== 종료코드 ${PIPESTATUS[0]} $(date)" >> "$LOG"
echo; echo "끝났어요! Enter를 누르면 창이 닫혀요."; read
