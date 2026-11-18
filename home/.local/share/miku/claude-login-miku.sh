#!/bin/bash
LOG=~/.local/share/miku/claude-login-miku.log
echo "== 시작 $(date)" > "$LOG"
echo "미쿠: 미쿠 전용 Claude 로그인을 만드는 창이에요."
echo "브라우저가 열리면 '지금 미쿠가 쓰는 원래 계정(se...@gmail.com)'으로 로그인해 주세요."
echo "(방금 검수 봇에 붙인 새 계정이 아니에요!)"
echo
hermes -p miku auth add anthropic --type oauth --label miku-claude 2>&1 | tee -a "$LOG"
echo "== 종료코드 ${PIPESTATUS[0]} $(date)" >> "$LOG"
echo; echo "끝났어요! Enter를 누르면 창이 닫혀요."; read
