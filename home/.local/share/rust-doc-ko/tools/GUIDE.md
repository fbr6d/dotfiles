# Rust std 문서 번역 지침

입력: work/<tier>/chunk_NN.jsonl — 한 줄에 {"id", "src", "en"} 하나.
출력: ko/<tier>/chunk_NN.json — {"<id>": "<한국어 번역>", ...} 하나의 JSON 객체 (모든 id 포함).

## 번역 규칙
- 자연스러운 한국어 문어체(~한다/~합니다 중 "~합니다"체 통일)로 번역한다.
- `백틱` 안의 코드(`Vec<T>`, `push`, `None` 등)는 절대 바꾸지 않고 그대로 둔다.
- 영어 용어를 알아야 이해되는 핵심 용어는 처음 나올 때 한국어 뒤 괄호에 영어를 남긴다.
  예: 소유권(ownership), 빌림(borrow), 트레잇(trait), 수명(lifetime), 패닉(panic)
- 짧은 제목("Examples", "Panics", "Safety", "Errors" 등)도 번역: 예시, 패닉, 안전성(Safety), 오류
- 원문에 없는 설명을 덧붙이지 않는다. 원문 의미를 빼지 않는다.
- 마크다운 강조(**, *, 목록 기호 등)는 유지한다.

## 용어집 (통일)
trait=트레잇 / ownership=소유권 / borrow=빌림 / reference=참조 / slice=슬라이스 /
iterator=반복자(iterator) / closure=클로저 / panic=패닉 / lifetime=수명 /
allocate=할당 / capacity=용량 / element=요소 / owned=소유된 / byte=바이트 /
UTF-8 / char boundary=문자 경계 / predicate=조건 함수(predicate) /
unsafe=unsafe(안전하지 않은) / undefined behavior=정의되지 않은 동작(UB) /
consume=소비 / yield(반복자)=내놓다 / adapter=어댑터 / heap=힙 / stack=스택 /
hash=해시 / key=키 / value=값 / entry=엔트리(entry) / mutable=가변 / immutable=불변
