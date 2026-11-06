---
name: screen-capture-hyprland
description: 사용자 화면/창 캡처 방법(Hyprland Lua 설정 + grim)과 캡처 후 Claude 창으로 포커스 복귀 규칙
metadata:
  node_type: memory
  type: feedback
  originSessionId: d3273618-a955-41a8-ac64-d59d0adad15f
  modified: 2026-11-06T02:59:09.482Z
---

사용자가 "오른쪽 창" 등 화면을 보라고 하면 grim으로 캡처해 Read로 본다. 캡처가 끝나면 반드시 Claude 창으로 포커스를 되돌린다.

**Why:** Arch + Hyprland(스크롤 레이아웃, Lua 설정 ~/.config/hypr/hyprland.lua)라 화면 밖 창은 포커스를 옮겨야 보이고, 그러면 Claude 창이 밀려난다. 2026-11-06에 사용자가 복귀를 요청함. Desktop 앱의 computer use 도구는 이 환경에 없다.

**How to apply:**
- 터미널(kitty) 내용은 캡처보다 텍스트로 직접 읽는 게 우선: kitty.conf에 `allow_remote_control socket-only`, `listen_on unix:/tmp/kitty` → 소켓은 `/tmp/kitty-<pid>`. `kitty @ --to unix:/tmp/kitty-<pid> ls`로 창 id 확인 후 `kitty @ --to unix:... get-text --match id:N` (스크롤백은 `--extent all`). 포커스 이동 불필요. 2026-11-06 동작 확인.
- 화면 모양(밑줄 위치 등)을 봐야 할 때만 아래 캡처 방식 사용.
- 창 목록: `hyprctl clients -j` (at/size/class/address). 모니터 eDP-1 2560x1600, scale 1.25 → 논리 폭 2048.
- 포커스: `hyprctl dispatch 'hl.dsp.focus({ window = "address:0x..." })'` (구 문법 `focuswindow address:` 는 실패함).
- 캡처: `grim -g "x,y wxh" <scratchpad>/x.png` 후 Read.
- 끝나면 class `com.anthropic.Claude` 창 address로 같은 focus 디스패치 실행.
- 오류 질문이면 [[error-questions-explain-only]] 규칙도 따른다.
