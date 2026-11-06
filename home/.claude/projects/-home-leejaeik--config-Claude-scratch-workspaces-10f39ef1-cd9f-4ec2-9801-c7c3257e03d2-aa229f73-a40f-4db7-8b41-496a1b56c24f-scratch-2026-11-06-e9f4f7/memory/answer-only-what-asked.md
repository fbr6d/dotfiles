---
name: answer-only-what-asked
description: "사용자가 물어본 것만 답하고, 묻지 않은 추가 정보(다른 버그, 참고 사항 등)는 덧붙이지 말 것"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d3273618-a955-41a8-ac64-d59d0adad15f
  modified: 2026-11-06T02:39:16.078Z
---

질문한 내용에만 답한다. 묻지 않은 다른 버그, 논리 오류, 개선점, 부가 설명은 덧붙이지 않는다.

**Why:** 2026-11-06에 nvim 경고를 물었는데 다른 논리 버그(`get(pointer)`)와 오래된 터미널 출력까지 설명하자, 사용자가 "내가 물어보지 않은건 알려주지마"라고 요청함. 직접 찾으며 배우는 중.

**How to apply:** 오류/경고 질문이면 그 항목의 원인만 짧게 설명한다. 다른 문제를 발견해도 말하지 않는다. [[error-questions-explain-only]]와 함께 적용.
