#!/bin/bash
LOG=~/.local/share/miku/miku-login-leejaeik.log
echo "START $(date)" > $LOG
echo "브라우저에서 leejaeik0406@gmail.com 계정으로 로그인한 뒤, 나온 코드를 여기에 붙여 넣으세요."
hermes -p miku auth add anthropic --type oauth --label miku-claude-leejaeik --priority 0
echo "EXIT $? $(date)" >> $LOG
echo; echo "끝났어요! 이 창은 Enter를 누르면 닫혀요."; read
