---
name: korean-everywhere
description: 사용자는 모든 답변·대화상자·진행 상황을 한국어로 받기를 원함 (전역 규칙)
metadata:
  type: feedback
---

답변, 질문 카드, 작업 목록, wrap-up 요약 등 사용자에게 보이는 모든 텍스트를 한국어로 쓴다. 코드 식별자·명령어·경로는 원문 유지.

**Why:** 2026-11-03 사용자가 "클로드 답변이나 대화상자, 진행상황 같은건 전부 한국어로 써줘 전역적으로 지금부터" 라고 요청. ~/.claude/CLAUDE.md 에도 같은 규칙을 기록함.

**How to apply:** 세션 시작부터 update_plan 항목, wrap_up recap/ask, AskUserQuestion 선택지까지 모두 한국어로 작성.
