---
name: bluetooth-mt7922-usb-enum
description: "사용자 PC(Arch, ASRock 보드, MT7922) 블루투스 불량 진단 결과 — USB 1-12 열거 실패"
metadata:
  node_type: memory
  type: project
  originSessionId: b0eeba56-c7af-4a15-ba3e-2ba214a01ea8
  modified: 2026-11-15T06:24:39.332Z
---

2026-11-15 진단: 블루투스 컨트롤러 자체가 안 잡힘(/sys/class/bluetooth 없음). MT7922 BT부(온보드 USB 포트 1-12, 버스1 = PCI 0000:0d:00.0)가
`device descriptor read/64, error -110`, `device not accepting address, error -71`로 USB 열거 단계에서 실패. 드라이버/펌웨어(linux-firmware-mediatek 20261019) 문제 아님.
여러 번 재부팅해도 동일. Windows 듀얼부팅 있음(빠른 시작 의심).

**Why:** 사용자가 "아직도 안돼"라고 반복 문의 — 이전 시도 이력 필요.
**How to apply:** 다음 문의 시 완전 전원 차단(PSU 스위치 off 30초+) 및 Windows 빠른 시작 해제 결과부터 확인.
