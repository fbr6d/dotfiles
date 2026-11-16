---
name: miku-boot-greeting
description: "Use when the boot greeter sends '…'. Greet master once."
---

# 부팅 인사 (miku-engineer-start 전용)

이 스킬은 `~/.local/bin/miku-engineer-start`가 부팅 직후 `chat -s miku-boot-greeting -q "…"`로 미리 불러온다.
이 세션은 나중에 마스터가 Enter를 눌러 그대로 이어서 대화할 수 있다.

## 첫 메시지가 "…" 하나뿐일 때 (자동 인사 요청)

- 이것은 마스터가 쓴 말이 아니라, 컴퓨터가 막 켜졌다는 자동 신호다. "…"의 뜻을 묻거나 언급하지 않는다.
- 지금 날짜·시각(KST)과 세종(위도 36.48, 경도 127.29) 날씨를 Open-Meteo로 확인한다.
  예: `curl -s 'https://api.open-meteo.com/v1/forecast?latitude=36.48&longitude=127.29&current=temperature_2m,weather_code,apparent_temperature&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia%2FSeoul&forecast_days=1'`
- 그 상황(시간대, 요일, 날씨)에 맞는 인사말을 직접 만들어 마스터에게 3~4문장으로 인사한다.
- 마크다운 없이 평범한 문장으로만 쓴다. 이모티콘은 SOUL.md 말투대로.
- 이 첫 답변에서는 날씨·시각 확인 말고 다른 시스템 작업을 하지 않는다.
- 날씨 조회가 실패하면 날씨 이야기는 빼고 인사만 한다.

## 그 다음 메시지부터

- 이 스킬의 제한은 끝난다. 마스터의 이후 메시지는 평소의 시스템 관리자 역할과 확인 원칙대로 처리한다.
