#!/bin/bash
# VOCALOID7 + 초음 미쿠 V6 체험판 시험 실행기 (미쿠, 2026-11-23). 사용: vocaloid-setup.sh <단계>
#   prefix   : 전용 공간 ~/Games/vocaloid 만들기 (wine-staging, Windows 11, mono 없이)
#   deps     : winetricks corefonts cjkfonts dotnet48 (오래 걸림)
#   dotnet8  : .NET Desktop Runtime 8 최신판(x64·x86) 공식 배포처에서 받아 설치 (sha512 대조)
#   editor   : VOCALOID7 Editor 설치 창 (약관 동의는 마스터)
#   miku     : 초음 미쿠 V6 체험판 설치 창
#   run      : VOCALOID7 실행 (첫 실행부터 31일 체험 시작!)
export WINEPREFIX=$HOME/Games/vocaloid
export WINEARCH=win64
export DISPLAY=${DISPLAY:-:0}
SETUP=$HOME/Games/vocaloid-setup
LOG=$SETUP/$1.log
mkdir -p "$SETUP"
echo "START $1 $(date '+%F %T')" > "$LOG"
find_exe() { find "$WINEPREFIX/drive_c" -iname "$1" -type f 2>/dev/null | head -1; }
unz() { python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$1" "$2"; }
case "$1" in
  prefix)
    WINEDLLOVERRIDES="mscoree,mshtml=" wineboot -i >> "$LOG" 2>&1
    winetricks -q win11 >> "$LOG" 2>&1 ;;
  deps)    winetricks -q corefonts cjkfonts dotnet48 >> "$LOG" 2>&1 ;;
  dotnet8)
    D=$SETUP/dotnet8; mkdir -p "$D"
    python3 - "$D" >> "$LOG" 2>&1 <<'PY'
import json, urllib.request, hashlib, sys, os
d = sys.argv[1]
rel = json.load(urllib.request.urlopen("https://builds.dotnet.microsoft.com/dotnet/release-metadata/8.0/releases.json"))["releases"][0]
print("release", rel["release-version"])
for f in rel["windowsdesktop"]["files"]:
    if f["name"] in ("windowsdesktop-runtime-win-x64.exe", "windowsdesktop-runtime-win-x86.exe"):
        p = os.path.join(d, f["name"])
        urllib.request.urlretrieve(f["url"], p)
        h = hashlib.sha512(open(p, "rb").read()).hexdigest()
        print(f["name"], "sha512", "OK" if h == f["hash"] else "MISMATCH")
        if h != f["hash"]: sys.exit(3)
PY
    rc=$?; [ $rc = 0 ] || { echo "EXIT $rc download" >> "$LOG"; exit $rc; }
    for a in x64 x86; do wine "$D/windowsdesktop-runtime-win-$a.exe" /install /quiet /norestart >> "$LOG" 2>&1; echo "dotnet8 $a rc=$?" >> "$LOG"; done ;;
  editor)
    E=$SETUP/editor; mkdir -p "$E"; unz "$(ls -t "$HOME"/Downloads/VOCALOID7_Editor_*_Installer_win64.zip | head -1)" "$E" >> "$LOG" 2>&1
    cd "$E" && wine ./VOCALOID7_Editor_Installer_x64.exe >> "$LOG" 2>&1 ;;
  miku)
    M=$SETUP/miku; mkdir -p "$M"; unz "$HOME/Downloads/C9520_win.zip" "$M" >> "$LOG" 2>&1
    cd "$M" && wine ./HATSUNE_MIKU_V6_for_VOCALOID_Installer.exe >> "$LOG" 2>&1 ;;
  run)     wine "$(find_exe 'VOCALOID7.exe')" >> "$LOG" 2>&1 ;;
  *) echo "unknown step $1" >> "$LOG"; exit 2 ;;
esac
echo "EXIT $? $(date '+%F %T')" >> "$LOG"
