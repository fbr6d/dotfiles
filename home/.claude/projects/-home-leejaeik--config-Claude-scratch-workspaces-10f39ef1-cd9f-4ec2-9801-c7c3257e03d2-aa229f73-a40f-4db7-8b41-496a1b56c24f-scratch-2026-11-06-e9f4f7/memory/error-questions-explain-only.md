---
name: error-questions-explain-only
description: 사용자가 오류 원인을 물으면 코드를 절대 수정하지 말고 원인만 설명할 것
metadata:
  node_type: memory
  type: feedback
  originSessionId: d3273618-a955-41a8-ac64-d59d0adad15f
  modified: 2026-11-06T02:33:05.711Z
---

오류에 대해 질문하면 코드를 고치지 말고 원인만 설명한다. 수정 제안 질문(“고칠까요?”)도 하지 않는다.

**Why:** 사용자가 직접 수정하면서 Rust를 배우는 중이다(bf_interpreter 등 학습용 프로젝트). 2026-11-06에 명시적으로 요청함.

**How to apply:** 빌드/실행으로 오류를 재현하고 읽는 것은 괜찮다. 파일 편집, 자동 수정, 수정 제안 버튼은 쓰지 않는다. 해결 방향을 설명하는 짧은 예시 코드는 답변 안에서만 보여줘도 된다.
