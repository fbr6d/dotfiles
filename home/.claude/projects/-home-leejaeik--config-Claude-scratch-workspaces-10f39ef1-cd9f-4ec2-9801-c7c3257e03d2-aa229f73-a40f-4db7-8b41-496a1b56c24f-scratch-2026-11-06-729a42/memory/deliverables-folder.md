---
name: deliverables-folder
description: "완성본은 ~/Documents/하조꾸/ (git 저장소, 비공개 GitHub fbr6d/hajokku와 동기화, 판매용 폴더 구조)"
metadata:
  node_type: memory
  type: reference
  originSessionId: bfda3a90-8e51-4ff9-9684-13767f1d09cf
  modified: 2026-11-08T13:39:12.235Z
---

사용자에게 전달하는 완성본은 `/home/leejaeik/Documents/하조꾸/`에 둔다. 2026-11-08에 사용자가 `수능자료` → `하조꾸`로 이름을 바꿨다.
다른 세션("안키 덱 판매 상품설명")에서 판매용으로 정리했고, 폴더 전체가 git 저장소로 **비공개 GitHub `fbr6d/hajokku`**(main 브랜치)와 연결되어 있다.

폴더 구조 (2026-11-08 기준):
- `01_상품원본/영어/` — 수능영어_1만.apkg, 수능영어_맛보기40.apkg
- `01_상품원본/국어_판매보류/` — 수능국어_독서_중세국어.apkg
- `01_상품원본/기타자료/` — 정리노트·주간트레이닝 PDF
- `02_배포파일/` — 판매용 zip(덱 + Anki 사용 가이드 + 먼저_읽어주세요.txt)
- `03_리틀리/`, `04_인스타/`, `05_원본HTML/`, `99_보관/` — 판매 페이지·SNS 이미지 (litt.ly/hajokku)

**How to apply:** 새 버전을 만들면 해당 하위 폴더의 같은 이름 파일을 바꾸고, 판매용 덱이면 `02_배포파일`의 zip도 함께 갱신해야 한다는 점을 사용자에게 알린다. git 커밋·푸시는 사용자가 요청할 때만 한다. 작업 원본(빌드 스크립트·데이터)은 세션 작업 폴더에 있다. 관련: [[note-format-preference]].
