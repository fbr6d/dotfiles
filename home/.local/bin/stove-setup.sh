#!/bin/bash
# 스토브(STOVE) 설치 단계 실행기 (미쿠, 2026-11-22). 사용: stove-setup.sh <단계>
#   prefix  : 윈도우 흉내 공간 만들기 + Proton 받기 + arial 글꼴
#   fonts   : 한글 글꼴(Noto Sans CJK) 연결 + 맑은 고딕 등 대체 글꼴 등록
#   install : STOVESetup.exe 실행 (화면에 설치 창이 뜸)
#   webview : WebView2 설치
#   run     : 스토브 실행
export WINEPREFIX=$HOME/Games/stove
export GAMEID=umu-stove
export PROTONPATH=GE-Proton
export STORE=none
LOG=$HOME/Games/stove-setup/$1.log
mkdir -p "$WINEPREFIX" "$(dirname "$LOG")"
echo "START $1 $(date '+%F %T')" > "$LOG"
case "$1" in
  prefix)  umu-run winetricks -q arial >> "$LOG" 2>&1 ;;
  fonts)
    F=$WINEPREFIX/drive_c/windows/Fonts
    mkdir -p "$F"
    for f in /usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc /usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc; do
      [ -f "$f" ] && ln -sf "$f" "$F/$(basename "$f")" && echo "linked $f" >> "$LOG"
    done
    cat > "$WINEPREFIX/miku-fonts.reg" <<'REG'
REGEDIT4

[HKEY_LOCAL_MACHINE\Software\Microsoft\Windows NT\CurrentVersion\FontSubstitutes]
"Malgun Gothic"="Noto Sans CJK KR"
"맑은 고딕"="Noto Sans CJK KR"
"Gulim"="Noto Sans CJK KR"
"굴림"="Noto Sans CJK KR"
"Dotum"="Noto Sans CJK KR"
"돋움"="Noto Sans CJK KR"
"Batang"="Noto Sans CJK KR"
"MS Shell Dlg"="Noto Sans CJK KR"
"MS Shell Dlg 2"="Noto Sans CJK KR"
"Segoe UI"="Noto Sans CJK KR"
"Tahoma"="Noto Sans CJK KR"
REG
    umu-run regedit /S "$WINEPREFIX/miku-fonts.reg" >> "$LOG" 2>&1 ;;
  install) umu-run "$HOME/Games/stove-setup/STOVESetup.exe" >> "$LOG" 2>&1 ;;
  webview) umu-run "$WINEPREFIX/drive_c/ProgramData/Smilegate/STOVE/MicrosoftEdgeWebview2Setup.exe" >> "$LOG" 2>&1 ;;
  run)     umu-run "$WINEPREFIX/drive_c/ProgramData/Smilegate/STOVE/STOVE.exe" >> "$LOG" 2>&1 ;;
  *) echo "unknown step $1" >> "$LOG"; exit 2 ;;
esac
echo "EXIT $? $(date '+%F %T')" >> "$LOG"
