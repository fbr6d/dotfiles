#!/bin/sh
# kitty 창 안에서 실행: sudo로 fix-1password.sh를 돌리고 단계별 기록을 남긴다.
T=/home/leejaeik/.local/share/miku/fix-1password-window.log
echo "$(date '+%T') 창 시작" > "$T"
echo "1Password 수정 스크립트를 실행해요. 아래에 sudo 비밀번호를 입력해 주세요."
echo
sudo /home/leejaeik/.local/share/miku/fix-1password.sh
rc=$?
echo "$(date '+%T') sudo 종료 코드 $rc" >> "$T"
echo
echo "===== 실행 기록 ====="
cat /home/leejaeik/.local/share/miku/fix-1password.log 2>/dev/null || echo "(기록 없음: 스크립트가 시작되지 않았어요)"
echo
echo "결과 코드: $rc  (0이면 성공)"
echo "창을 닫으려면 q 를 누르고 Enter"
while read x; do [ "$x" = q ] && break; done
echo "$(date '+%T') 사용자가 q로 닫음" >> "$T"
