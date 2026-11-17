# 설정 인수인계 문서 (에이전트용) — 이 세션에서 한 작업

이 문서는 이 컴퓨터를 다루게 될 **다른 AI 에이전트**를 위한 것입니다.
1~12장은 **한 Claude 세션("컴퓨터 세팅")에서 사용자와 함께 설정한 것**입니다.
13장은 **다른 세션에서 만들었지만 이 시스템과 직접 관련된 것** 중 사용자가 고른 항목입니다(Hermes 에이전트는 제외).
디자인 취향은 `~/Documents/design-guide.md`에 따로 있습니다.

> 값은 작성 시점(2026-11-16)에 확인한 것입니다. 행동하기 전에 지금 상태를 다시 확인하세요.

---

## 1. 사용자와 작업 규칙

| 규칙 | 내용 |
|---|---|
| 언어 | 사용자에게 보이는 모든 글은 **한국어**. 코드·명령·경로·에러 원문은 그대로 |
| 기존 프로그램 우선 | 새로 만들기 전에 이미 있는 프로그램을 찾고, 직접 만들 땐 먼저 물어봄 |
| 한국어 설정 보고 | 앱을 설치할 때마다 한국어 UI 설정이 있는지 확인해 알려줌 |
| sudo | 에이전트는 비밀번호를 모름. root 작업은 스크립트를 만들어 **터미널 탭에 `sudo ...`를 띄우고 사용자가 비밀번호를 입력**하게 함. 결과는 터미널 출력이나 `chmod 644`로 만든 결과 파일로 확인 |
| 백업 | 설정 파일은 바꾸기 전에 `<파일>.bak-<이유>`로 백업하는 관례 |
| 확인 | 캡처·측정·로그로 실제 확인한 뒤 보고. 확인 못 한 것은 못 했다고 말함 |
| 원상복구 | 사용자가 "원상복구"라고 하면 백업으로 정확히 되돌림 |
| 거절된 작업 | 자동 모드가 막은 작업(sudoers 파일 설치, `ya pkg add` 등)은 우회하지 말고 사용자가 직접 실행. `/etc/sudoers.d/10-timeout` 제거는 사용자가 거절함 |

---

## 2. 환경 요약 (이 세션 중에 바뀜)

- 세션 전반부는 **MacBook Air 2018 (T2)**, 후반부(2026-11-15~)는 **데스크톱**으로 이전된 뒤입니다. 같은 설정 파일을 그대로 가져왔기 때문에 맥북 전용 설정이 일부 남아 있습니다.
- 데스크톱: Ryzen 9 7900X, ASRock B850I Lightning WiFi, Radeon RX 6600, Samsung DDR5 16GB×2, 980 PRO 2TB(Arch), 970 EVO 500GB(Windows, 건드리지 말 것), Samsung LC27G5xT 2560×1440 모니터(`HDMI-A-1`).
- Hyprland 0.57, **Lua 설정**(`~/.config/hypr/hyprland.lua`). `hyprctl` 디스패치도 Lua 문법: `hyprctl dispatch 'hl.dsp.focus({window="address:0x..."})'`.

---

## 3. 로그인 화면 = 잠금화면 (자동 로그인 + hyprlock)

로그인 화면과 잠금화면을 똑같이 보이게 하려고, 부팅 시 자동 로그인한 뒤 곧바로 잠금화면을 띄우는 방식으로 바꿨습니다.

```
greetd
 ├ initial_session (부팅당 1회): ~/.local/bin/start-hyprland-autologin
 │     → $XDG_RUNTIME_DIR/hypr-autologin 표시 파일 생성 → Hyprland
 └ default_session (로그아웃 후): ReGreet (배경 /var/lib/greeter-bg/background.jpg)

Hyprland 시작
 ├ ~/.local/bin/session-start
 │    ├ 표시 파일이 있으면 login-lock 실행
 │    │    ├ quickshell login-reveal 오버레이를 먼저 띄움
 │    │    ├ hyprlock (미리 흐리게 만든 배경 사용)
 │    │    └ 잠금 해제 → 오버레이가 1.6초 동안 흐림을 걷어냄
 │    └ exec session-apps  (시작 프로그램은 첫 잠금 해제 뒤에)
 └ ~/.local/bin/wallpaper-restore (로그인 화면과 같은 바탕화면, 슬라이드쇼는 한 주기 뒤)
```

| 파일 | 내용 |
|---|---|
| `/etc/greetd/config.toml` | `[initial_session]` 추가 (백업 `.bak-autologin`) |
| `/etc/greetd/regreet.toml`, `regreet.css` | 배경 경로, 부드러운 전환 (백업 `.bak-lockbg`, `.bak-smooth`) |
| `/var/lib/greeter-bg/` | `background.jpg`(흐리고 55% 어둡게), `source`(원본 경로). 소유 `leejaeik:greeter` |
| `~/.local/bin/greeter-bg` | 위 배경 생성. waypaper `post_command`와 session-apps에서 실행 |
| `~/.local/bin/login-lock` | 부팅 시 잠금화면 실행 + 풀릴 때 연출 |
| `~/.config/quickshell/login-reveal/shell.qml` | 흐림이 걷히는 오버레이 (1600ms, InOutSine) |
| `~/.local/bin/session-start`, `session-apps`, `start-hyprland-autologin` | 위 흐름 |
| `~/.local/bin/wallpaper-restore` | `waypaper --restore` 대신 사용 |
| `~/.config/hypr/hyprlock.conf` | 블러 4회/크기 12, 밝기 0.55, 테두리 없는 입력칸, 점이 가운데서 나옴, 부드러운 애니메이션 |
| `hyprland.lua` | waybar 레이어 규칙 `slide top`(상단 바가 위에서 내려옴) |

**하지 말 것**: hyprlock 해제 fade-out(잠긴 동안 데스크톱이 안 그려져 회색 화면이 보임), `--immediate-render`(블러 안 됨), 로그인 때 `waypaper --restore`/`waypaperd` 바로 실행(즉시 랜덤 배경으로 바뀜).

### 3.1 계정 잠김 안내
- `/etc/security/faillock.conf`: `deny = 10`, `unlock_time = 60` (원래 3회/600초, 백업 `.bak`).
- `~/.local/bin/lock-faillock-status`: 잠금화면 라벨이 1초마다 실행. 저널에서 잠김 기록을 읽어 "비밀번호를 10번 틀려 잠시 잠겼습니다 · N초 뒤에 다시 입력하세요"를 표시.
- 배경: 모니터 절전 해제 직후 비밀번호가 3번 틀려 10분간 잠겼고, 잠긴 동안 맞는 비밀번호도 거부돼 로그인이 안 되는 것처럼 보였던 일이 있었음.

---

## 4. 제어센터 (swaync)

| 파일 | 역할 |
|---|---|
| `~/.config/swaync/config.json` | 위젯 순서: `menubar#net`(상태 줄) → `buttons-grid`(기기 연결·방해 금지) → `volume` → (`backlight`) → `buttons-grid#power`(3등분) → (`label#battery`) → `title` → `notifications` |
| `~/.config/swaync/style.css` | 상태 줄 Wi-Fi 1/4 · 유선 1/4 · 블루투스 1/2, 모든 줄 좌우 끝 맞춤(백업 `.bak-align`) |
| `~/.local/bin/swaync-status` | Python 데몬(3초): Wi-Fi·유선·블루투스 상태와 라벨을 config에 써 넣고 `swaync-client -R`. **패널이 열려 있으면 적용 안 함**. 배터리·밝기 조절 장치가 없으면 해당 칸을 숨김 |
| `~/.local/bin/cc-toggle` | 상태 칸의 `update-command`(state wifi/wired/bt). 상태 칸은 누르면 패널만 다시 열림(표시 전용) |
| `~/.local/bin/device-settings` | "기기 연결" → GNOME 설정 Wi-Fi 화면(한국어). `XDG_CURRENT_DESKTOP=GNOME`, `/usr/lib/gsd-rfkill` 필요 |
| `~/.local/bin/cc-focus-keeper` | 제어센터가 닫힐 때 포커스가 다른 창으로 넘어가 scrolling 배치가 밀리면 원래 창으로 되돌림 |
| `~/.local/bin/session-apps` | swaync를 `systemctl --user start swaync`로 시작(직접 실행하면 D-Bus 활성화와 겹쳐 서비스가 실패함) |

- Overskride(블루투스 GUI)는 삭제하고 GNOME 설정(`gnome-control-center`)으로 대체. 창 규칙 `org.gnome.Settings` 가운데 1000×720.
- `ko_KR.UTF-8` 로케일을 생성함(GNOME 설정을 한국어로 띄우기 위해. 시스템 언어는 그대로).

---

## 5. 상단 바 (waybar)에서 바꾼 것

- 시계: 18px로 키움(`style.css`의 `.modules-right #clock` 규칙). 형식 `%H:%M`(24시간).
  - 시계 아래 CPU/GPU/RAM 색 막대를 만들었다가 사용자 요청으로 **원상복구**함. 관련 스크립트는 삭제됨.
- 곡 컨트롤(이전·재생·다음): 글꼴 아이콘 대신 **SVG**(`~/.config/waybar/icons/media-*.svg`, hover용 `*-hover.svg`)를 CSS 배경으로. `~/.local/bin/waybar-media`는 공백 + `playing`/`paused` 클래스만 출력. 버튼 사이 이음새 제거. 백업 `style.css.bak-svgmedia`.

---

## 6. 앱 설치·설정

| 앱 | 한 일 |
|---|---|
| csvlens | TSV 보기, 기본 앱 연결 |
| imv | 가벼운 이미지 뷰어 |
| mpv | uosc + thumbfast, 한국어 메뉴(`scripts/uosc/intl/ko.json`), Claude/Catppuccin 테마(`script-opts/uosc.conf`), `scale=1`, `scale_fullscreen=1` |
| LibreOffice | Claude 색 구성, sifr_dark 아이콘, 한국어 UI, 기본 도구모음 (`~/.config/libreoffice/4/user/registrymodifications.xcu`) |
| f3d | STL/STEP 미리보기 |
| udiskie | USB 자동 마운트 (`~/.config/udiskie/config.yml`) |
| Codex CLI | `openai-codex` (공식 저장소) |
| GNOME 설정 | 기기 연결용 |
| 1Password ↔ Zen | `/etc/1password/custom_allowed_browsers`에 `zen-bin` |
| 인쇄 | CUPS + avahi + nss-mdns 설치, resolved mDNS 끔(`/etc/systemd/resolved.conf.d/10-no-mdns.conf`), `nsswitch.conf`에 `mdns_minimal`(백업 `.bak-printer`). 프린터 `HP_Officejet_Pro_8610`을 **IP `192.168.219.161`로 고정 등록**, 기본 프린터 |
| 벤치마크 도구 | stress-ng, fio, smartmontools, glmark2, vkmark, memtester |
| 삭제 | Wireshark, Minecraft, Overskride |

### 6.1 kitty
- 창 옮기기 `ctrl+alt+h/j/k/l` (`move_window`).
- yazi 창에서는 `ctrl+shift+t`를 kitty가 가로채지 않고 yazi로 넘김(`map --when-focus-on 'title:"(?i)^yazi"'`).

### 6.2 yazi (`~/.config/yazi/`)
- **Enter = 열기 메뉴**(`open --interactive`), Shift+Enter = 기본 앱.
- 열기 메뉴 확장(`yazi.toml` `[opener]`): nvim, Kate, KWrite, 기본 앱, HTML 보기(`html-view`), f3d, imv, mpv, ffplay, Papers, draw.io, Nautilus, **LocalSend로 보내기**, 포맷 변환(`convert-to`), csvlens, **16진수 보기**(기본이 아닌 파일의 첫 항목), 다른 앱 고르기(`open-with`), 압축 풀기. Zen·Chromium은 메뉴에서 뺌.
- USB: `/run/media/*/*/` 폴더에 들어가기·마운트 해제·안전하게 꺼내기 메뉴, `g u`로 USB 목록, `M`으로 mount 플러그인(사용자가 직접 설치).
- 닫은 탭 복구: `q`/`Q`/`Ctrl+C`가 `closed-tabs` 플러그인을 거쳐 기록, `Ctrl+Shift+T`(`<C-T>`)로 복구.
- 알려진 문제(사용자가 **그대로 두라고 함**): `prepend_rules` 맨 끝 `url = "*"` 규칙이 휴지통 파일 규칙을 가로챔.
- PDF 미리보기가 반쯤 회색으로 보이면 `/tmp/yazi-1000`의 해당 캐시 이미지가 깨진 것(두 yazi 창이 동시에 만들 때 생김). 파일을 지우면 다시 만들어짐.

### 6.3 입력기
- kitty·yazi 창에 포커스가 가면 fcitx5를 영어로(`hyprland.lua`의 `terminalClasses`).
- Ctrl+Alt+H가 fcitx5 힌트 전환과 겹쳐서 keyboard-us의 "Hint Trigger"를 비움(D-Bus `SetConfig`로 변경).

### 6.4 nvim
- 키 입력 기록 창을 오른쪽 아래로 옮김.

---

## 7. 직접 만든 도구

| 도구 | 설명 |
|---|---|
| `~/.local/bin/anki-sign` | 판매용 Anki 덱(.apkg)에 구매자별 숨은 서명을 넣고(`anki-sign DECK ID`), 검출·목록 삭제. 새 형식(anki21b, zstd)도 지원. 키 `~/.config/anki-sign/secret`, 장부 `~/.local/share/anki-sign/ledger.csv` |
| `~/.local/bin/html-view`, `open-with`, `convert-to` | yazi 열기 메뉴용 |
| `~/.local/bin/reboot-keep` | 재부팅 후 창 복원(자기 자신이 다시 실행되던 버그 수정함) |

---

## 8. 배율

- 모든 프로그램 **1배율**: 다른 모니터 규칙 `scale = 1`(자동 대신 고정), mpv uosc 1배, Zen·Chromium의 사이트별 확대 기록 모두 삭제.
- 맥북용 `eDP-1` 1.25 규칙은 데스크톱에서 쓰이지 않아 그대로 둠.

---

## 9. 하드웨어 점검 기록 (데스크톱)

| 항목 | 결과 |
|---|---|
| CPU | stress-ng 2분 30초, 오류 0, 평균 5.1GHz, 최고 87°C |
| GPU | vkmark 30,600점, 오류 0, 최고 핫스팟 71°C |
| SSD | 980 PRO 읽기 6.4GB/s·쓰기 5.1GB/s, 부하 시 73°C(다소 뜨거움). 970 EVO SMART 통과(오류 로그 항목 13,487개는 미확인) |
| RAM | 16GB→32GB 증설 확인. **5400 MT/s 수동 오버클럭**(1.1V), stress-ng 10분 오류 0, 처리량 +9.5% |
| memtest86+ | `/dev/sda`(SanDisk USB, 라벨 `MEMTEST`)에 UEFI 부팅용으로 만듦. **실제 장시간 검사는 아직 안 함** |

---

## 10. 맥북 → 데스크톱 이전 충돌 처리

| 충돌 | 상태 |
|---|---|
| swaync를 직접 실행 + D-Bus 활성화가 겹쳐 서비스 실패 | 고침(systemd 유닛으로 시작) |
| 제어센터 밝기 칸이 맥북 장치(`acpi_video0`)를 가리킴 | 고침(장치 없으면 숨김) |
| 배터리 칸 "배터리 없음" | 고침(배터리 없으면 숨김) |
| `lib32-*` 패키지가 있는데 `[multilib]` 저장소가 꺼져 있음 | 고침. `/etc/pacman.conf`에서 `[multilib]` 켬(백업 `pacman.conf.bak-multilib`). lib32 패키지가 모두 multilib에서 관리됨을 확인 |
| 외부 저장소 `slsrepo`가 `SigLevel = Never`(Zen, LocalSend, paru를 여기서 받음) | 고침. `/etc/pacman.conf`에서 뺌(백업 `pacman.conf.bak-slsrepo`), AUR `zen-browser-bin`, `localsend-bin`, `paru-bin`으로 다시 설치. 실행 경로(`/usr/bin/zen-browser`, `/opt/localsend/localsend`)는 그대로 |
| 15분 뒤 모니터 끄기(맥북 시절 설정) → 이 HDMI 모니터는 꺼질 때 연결이 끊겼다 붙음 | 관찰만 함. 로그인 문제와 겹친 적 있음 |

---

## 11. 실제로 겪은 함정

| 상황 | 주의할 점 |
|---|---|
| `pkill -f <이름>` | 그 이름이 명령줄에 들어간 **에이전트 자신의 셸까지 죽음**. PID를 정확히 골라 `kill` |
| swaync | 패널이 열린 채 `-R` 하면 볼륨 슬라이더가 0으로 보임 / `update-command`의 `sh -c` 중첩 따옴표 동작 안 함 / 켜짐 클래스는 `.active` / 기본 CSS `.end` 오른쪽 여백 8px 때문에 줄 끝이 안 맞음 / buttons-grid는 칸 폭이 모두 같아서 비율 배치는 menubar로 |
| waybar | text가 빈 문자열이면 모듈이 숨겨짐 / 글꼴 아이콘은 세로 정렬이 어긋남 → SVG / `text-shadow`는 라벨 전체에 적용 |
| CUPS | 자동 임시 프린터가 `Bad device URI "://"`로 실패 / `lpadmin`이 `.local` 이름을 못 풀어서 IP로 등록 |
| GNOME 설정 | Hyprland에서는 `XDG_CURRENT_DESKTOP=GNOME`, 블루투스 화면엔 `gsd-rfkill` |
| Zen | 실행 중엔 프로필 DB를 고치지 말 것 |
| 1Password | `settings.json`이 서명돼 있어 직접 수정 불가(앱에서 바꿔야 함) |
| LibreOffice | UI 언어는 `Linguistic/General/UILocale`, 색 구성은 `oor:op="replace"`. 프로세스를 죽이면 복구 창이 뜸 → 창을 닫아서 종료 |
| yazi | 폴더 URL 규칙은 끝에 `/` 필요 |
| fcitx5 | 빈 섹션 설정 파일은 무시됨 → D-Bus `SetConfig` |
| Anki | `collection.anki21b`는 zstd, `unicase` collation 필요 |
| 화면 시험 | `hyprctl output create headless NAME`으로 가상 모니터를 만들어 시험·캡처하고 `output remove`로 지우면 사용자 화면을 건드리지 않음 |

---

## 12. 남은 일

- memtest86+ 장시간 검사(사용자가 USB로 부팅해서 실행).
- 프린터 실제 인쇄 시험, 공유기에서 프린터 IP 고정 권장.
- 980 PRO 방열판 확인 권장.

---

## 13. 다른 세션에서 만든 것 (시스템과 직접 관련)

이 장의 항목은 이 세션에서 만들지 않았습니다. 파일 맨 위 주석에 자세한 설명이 있으니, 고치기 전에 먼저 읽으세요.

### 13.1 설치 구성

| 항목 | 값 |
|---|---|
| 호스트 이름 | `arch-linux` |
| 파티션 | `nvme0n1p1` 1GB vfat → `/efi`, `nvme0n1p2` 1.8TB ext4 → `/` |
| 스왑 | zram (`zram-generator`, 약 15GB) |
| 커널 | `linux`와 `linux-lts` 둘 다 설치(작성 시점엔 LTS로 부팅), `amd-ucode` |
| 그래픽 | mesa, vulkan-radeon(RADV), 32비트는 multilib |
| 부트로더 | GRUB, 테마 `/boot/grub/themes/monochrome-dark`, 대기 30초. 메뉴는 **Arch Linux 한 줄 + Windows + memtest86+**만 보이도록 사용자 생성 스크립트 사용: `/etc/grub.d/11_arch-only`, `31_windows-only`, `40_custom`, `41_custom`, `60_memtest86+-efi`. 기본 `10_linux`, `30_os-prober` 등은 pacman 훅 `/etc/pacman.d/hooks/90-grub-menu-only.hook`이 업데이트 때마다 실행 권한을 다시 뺌 |
| 로케일·시간 | `LANG=C.UTF-8`, `ko_KR.UTF-8`·`en_US.UTF-8` 생성, Asia/Seoul |
| 네트워크 | NetworkManager + systemd-resolved (mDNS는 avahi 담당) |
| 로그인 | greetd (3장 참고) |
| 켜진 시스템 서비스 | greetd, NetworkManager, systemd-resolved, bluetooth, avahi-daemon, cups, fstrim.timer |
| 켜진 사용자 서비스 | pipewire, wireplumber, openrgb-server, rgb-notify-flash, dotfiles-backup-prompt.timer (+ hermes-gateway) |
| AUR 도우미 | yay (paru도 설치됨) |

### 13.2 dotfiles 백업·복원

| 항목 | 내용 |
|---|---|
| 저장소 | `~/dotfiles` (비공개 GitHub) |
| 백업 | `~/dotfiles/backup.py` — 설정을 모아 커밋·push. 제외 방식(새 앱 설정도 자동 포함). `--no-push`, `--dry-run` |
| 제외 | SSH/GPG 키, 브라우저 쿠키·비밀번호·기록, 셸 기록, 토큰, 캐시, 20MB 넘는 파일, 150MB 넘는 폴더. 토큰처럼 보이는 문자열이 있으면 커밋을 멈춤 |
| 구성 | `home/`(점파일·`~/.config`·`~/.local/bin`·`~/.claude` 설정), `zen/`(Zen 프로필 일부), `etc/`(수정한 시스템 설정), `meta/`(패키지 목록·dconf·서비스 목록) |
| 복원 | `~/dotfiles/restore.sh [packages\|files\|zen\|home\|dconf\|etc\|services]`. 덮어쓴 파일은 `~/.dotfiles-old/<시각>/` |
| 홈 전체 | `~/dotfiles/usb_backup.sh` → `HOME-MIGRATE` 라벨 USB(ext4)에 홈 전체 복사 |
| 알림 | `dotfiles-backup-prompt.timer`(1시간 간격)가 백업을 권함 |
| 스킬 | Claude Code 스킬 `dotfiles-backup` ("설정 백업해줘") |

### 13.3 화면·알림

| 항목 | 파일 | 설명 |
|---|---|---|
| 미쿠 인사 | `~/.local/bin/miku-boot` → `~/.local/bin/miku-start`, 그림 `~/.local/share/miku/miku.ans`, Hermes 스킬 `miku-boot-greeting`(miku 프로필) | 부팅 후 첫 로그인 때 한 번(표시 파일 `$XDG_RUNTIME_DIR/miku-greeted`). `kitty --class miku-greeter` 창에 미쿠 그림을 띄우고, Hermes miku 프로필이 `chat -Q -s miku-boot-greeting -q "…"`로 시각·세종 날씨(Open-Meteo)에 맞춘 인사를 함. Enter = 그 대화를 `chat --resume`으로 이어 감(이때 화면이 지워지는 것은 의도된 동작), 다른 키 = fish 셸. 옛 `miku-greeting`은 삭제(백업 `~/.local/share/backups/miku-greeting-20261116/`). `session-apps`에서 실행 |
| 알림 RGB | `~/.local/bin/rgb-notify-flash`, 사용자 서비스 `rgb-notify-flash`, `openrgb-server` | 데스크톱 알림이 뜰 때마다 메인보드 RGB를 잠깐 다른 색으로 깜빡이고 원래 모드로 되돌림. OpenRGB 서버(`openrgb --server --noautoconnect`)를 통해 제어 |
| 단축키 안내창 | `~/.local/bin/hypr-cheatsheet` | SUPER+/ 로 켜고 끔. 반투명, 모든 작업공간에 고정, 마우스로 끌어 옮김. 창 클래스 `local.hypr.cheatsheet`(창 규칙으로 scrolling 배치에서 제외) |
| 리눅스 명령어 사전 | `~/.local/share/linux-cheatsheet/` (`viewer.py`, `linux-all.html`, `linux-top50.html`, `toggle.sh`) | SUPER+I 로 켜고 끔. `popup-window`로 화면 80%×90% 가운데 팝업. 창 클래스 `local.LinuxCheatsheet` |

### 13.4 상단 바·창

| 항목 | 파일 | 설명 |
|---|---|---|
| 작업공간 섬 | `~/.local/bin/waybar-island` | 상단 바 가운데. 작업공간마다 회색 점, 활성은 흰 알약. 표시 전용이고, 클릭하면 바탕화면 선택(waypaper) |
| 음악 시각화 | `~/.local/bin/waybar-cava` | 왼쪽 알약. cava 출력을 블록 문자로, 소리 나는 막대는 Catppuccin 색이 천천히 흐름 |
| 가사 | `~/.local/bin/waybar-lyrics` | "제목 · 아티스트" + Spotify 현재 가사 줄(LRCLIB, 곡별 캐시). 폭이 바뀔 때 부드럽게 늘고 줆 |
| Spotify 팝업 | `~/.local/bin/spotify-popup` | 왼쪽 알약·가사 클릭 → Spotify를 바 아래 팝업으로 열고 닫음. 숨기면 작업공간 99로 옮겨 계속 재생 |
| 창 전환 | hyprshell (`~/.config/hyprshell/config.toml`) | ALT+Tab / ALT+SHIFT+Tab |
| 팝업 도구 | `~/.local/bin/popup-window`, `popup-toggle` | 앱 창을 팝업처럼 보이기/숨기기. 숨긴 창은 **작업공간 99**에 둠(Hyprland 0.57에서 special 작업공간은 id가 없어 hyprshell이 목록을 못 만드는 문제 회피). `popup-toggle <class> <cmd>`는 바 클릭용 |
| 재부팅 확인 | `~/.local/bin/power-confirm reboot\|poweroff` | 제어센터 전원 버튼, CTRL+ALT+SHIFT+R |
| 알림 클릭 → 창 포커스 | `~/.local/bin/notify-focus` | swaync 알림을 누르면 보낸 앱 창으로 이동(작업공간 99에 숨은 팝업도 꺼냄) |
| 최고 주사율 | `~/.local/bin/monitor-maxrr --watch` | 모든 모니터를 원래 해상도의 최고 주사율로. 모니터를 다시 꽂아도 적용. Hyprland 시작 때 실행 |
| kitty 재시작 | `~/.local/bin/kitty-restart` | kitty에서 Ctrl+Shift+F6: 지금 상태 그대로 재시작 |
| 폴더에서 보기 | `~/.local/bin/yazi-filemanager1` + `~/.local/share/dbus-1/services/org.freedesktop.FileManager1.service` | 앱의 "폴더에서 보기" 요청을 yazi(kitty 안)로 처리. 시스템의 같은 이름 서비스(Nautilus)보다 우선 |

### 13.5 키보드 VIA 규칙

| 파일 | 내용 |
|---|---|
| `/etc/udev/rules.d/70-qk65v2-via.rules` | QK65 V2 키보드(`fffe:0040`) hidraw 장치를 로그인한 사용자가 쓸 수 있게(VIA로 키 배치 설정) |
| `/etc/udev/rules.d/92-viia.rules` | 모든 hidraw 장치 `0666` + uaccess (VIA 웹 설정용, 넓은 권한) |

### 13.6 Hyprland 단축키 전체 (`mainMod` = SUPER)

| 키 | 동작 |
|---|---|
| SUPER+Return | kitty |
| SUPER+E | yazi(kitty 안) |
| SUPER+Space | rofi 앱 실행기 |
| SUPER+Q | 창 닫기 |
| SUPER+SHIFT+E | 로그아웃(hyprshutdown) |
| SUPER+F / SUPER+M | 전체화면 / 최대화 |
| SUPER+V | 떠 있는 창 전환 |
| SUPER+SHIFT+V | clipse 클립보드 기록 |
| SUPER+P | pseudo 타일 |
| SUPER+T | kitty 분할 세션(`~/.config/kitty/split.session`) |
| SUPER+C | 현재 열을 가운데로 |
| SUPER+G / SUPER+Tab | 창 그룹 켜기·끄기 / 그룹 안 다음 창 |
| ALT+Tab / ALT+SHIFT+Tab | 창 전환(hyprshell) |
| SUPER+I | 리눅스 명령어 사전 |
| SUPER+/ | 단축키 안내창 |
| SUPER+, / SUPER+. | 옆 열로 창 합치기·빼기 |
| SUPER+S / SUPER+SHIFT+S | 특수 작업공간 magic 보기 / 그곳으로 보내기 |
| SUPER+휠 | 작업공간 이동 |
| SUPER+왼쪽·오른쪽 드래그 | 창 옮기기 / 크기 조절 |
| SUPER+CTRL+Q | 화면 잠금 |
| CTRL+ALT+SHIFT+R | 재부팅 확인 |
| 볼륨·음소거·마이크·밝기 키 | swayosd (잠금화면에서도 동작) |
| 미디어 키 | playerctl (이전·재생·다음) |

### 13.7 앱 실행 래퍼

| 항목 | 내용 |
|---|---|
| ChatGPT 데스크톱 | `~/.config/chatgpt-flags.conf`: `--ozone-platform=wayland`, `--enable-wayland-ime`, `--wayland-text-input-version=3` (Wayland 창 + fcitx5 한글 입력) |
| Discord | `~/.local/bin/discord` → `~/.local/share/Discord/discord` 실행 |
