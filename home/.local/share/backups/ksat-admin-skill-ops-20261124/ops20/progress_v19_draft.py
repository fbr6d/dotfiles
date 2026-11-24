#!/usr/bin/env python3
"""진행도 스크립트 v19 맞춤 초안(기록 20). 원본을 읽어 scratch에 새 판을 쓰기만 한다. 원본은 건드리지 않는다."""
import hashlib
import os
import sys

SRC = os.path.expanduser('~/.hermes/profiles/miku/scripts/ksat_plan_progress.py')
OUT = os.path.expanduser('~/.hermes/profiles/miku/cache/scratch/eng20/ksat_plan_progress_v19.py')
s = open(SRC, encoding='utf-8').read()
if not hashlib.sha256(s.encode()).hexdigest().startswith('51ec2c88f1bebfc8'):
    sys.exit('원본이 예상한 파일이 아니다')


def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f'{old[:50]!r}가 {s.count(old)}번 있다')
    s = s.replace(old, new)


# 1. 머리말: 무게 합과 바뀐 것
rep('  단계: 과목마다 W1~W6(위키)·P1~P3(PDF)·X1(자료 확장), 공통은 A1·D1·X0. 무게는 계획서 3-1·3-2절 표(합 357).',
    '  단계: 과목마다 W1~W6(위키)·P1~P3(PDF)·X1(자료 확장), 공통은 A1·D1·X0. 무게는 계획서 3-1·3-2절 표(v19부터 합 338).')
rep("    ① 원장 t_729e2d91 댓글에 '[단계 완료] <과목>-<코드>, …'로 시작하는 줄이 있으면 1.",
    "    ① 원장 t_729e2d91 댓글에 '[단계 완료] <과목>-<코드>, …'로 시작하는 줄이 있으면 1.\n"
    "       [단계 완료] 바로 뒤에 쉼표로 이어 적은 코드만 센다. 문장 속에 나오는 코드는 세지 않는다(2026-11-24).")
rep('판단 근거는 칸반 카드·원장 댓글·기준값 파일뿐이고, 카드·파일은 건드리지 않는다."""',
    '2026-11-24 (계획서 v19, 마스터 승인): 영어 범위가 지문·문법 개념(구문·어법·독해 43개)으로 줄어 영어 무게를\n'
    '  W3 6·W4 9·W5 4로 고쳤다. 영어-W5는 범위 변경 뒤에 만든 카드만 센다(그 전 카드는 단어·숙어 전사·대조).\n'
    '  이전판 백업: ~/.local/share/backups/miku-ksat-v19-20261124/\n'
    '판단 근거는 칸반 카드·원장 댓글·기준값 파일뿐이고, 카드·파일은 건드리지 않는다."""')

# 2. 영어 무게
rep('# 과목마다 다른 무게: 국어는 W1~W3를 합쳐 5, W4 48, W5 15. 영어 PDF는 논문 기반 지문 검증 때문에 8\n'
    'WEIGHT_FIX = {("국어", "W1"): 1, ("국어", "W2"): 1, ("국어", "W3"): 3, ("국어", "W4"): 48, ("국어", "W5"): 15,\n'
    '              ("영어", "P1"): 8}',
    '# 과목마다 다른 무게: 국어는 W1~W3를 합쳐 5, W4 48, W5 15. 영어 PDF는 논문 기반 지문 검증 때문에 8.\n'
    '# 영어 위키는 개념이 43개로 줄어 W3 6·W4 9·W5 4 (계획서 v19 3-1절)\n'
    'WEIGHT_FIX = {("국어", "W1"): 1, ("국어", "W2"): 1, ("국어", "W3"): 3, ("국어", "W4"): 48, ("국어", "W5"): 15,\n'
    '              ("영어", "W3"): 6, ("영어", "W4"): 9, ("영어", "W5"): 4, ("영어", "P1"): 8}\n'
    '# 범위가 바뀐 단계: 이 시각(epoch) 뒤에 만든 카드만 센다. 그 전 카드는 옛 범위의 일이라 세지 않는다.\n'
    '# 영어-W5: 2026-11-24 14:51:08 영어 범위 변경(단어·숙어 제외) 마스터 결정\n'
    'STAGE_SINCE = {"영어-W5": 1795499468}')

# 3. [단계 완료] 줄: 바로 뒤에 이어 적은 코드만
rep('TAG_RE = re.compile(',
    '_ONE = r"[\\s*`]*(?:국어|수학|영어|통합사회|통합과학|공통)-[WPXAD]\\d(?!\\d)[*`]*"\n'
    'HEAD_CODES_RE = re.compile(_ONE + r"(?:\\s*[,·、]\\s*" + _ONE + r")*")   # [단계 완료] 바로 뒤에 쉼표로 이어 적은 코드들\n'
    'TAG_RE = re.compile(')
rep('    """댓글 본문들에서 \'[단계 완료]\'로 시작하는 줄의 코드를 모은다 (줄 중간에 나오는 말은 세지 않는다)"""',
    '    """댓글 본문들에서 \'[단계 완료]\'로 시작하는 줄의 코드를 모은다 (줄 중간에 나오는 말은 세지 않는다).\n'
    '    [단계 완료] 바로 뒤에 이어 적은 코드만 센다. \'[단계 완료] 영어 … 영어-W5 확정은 아니다\'처럼\n'
    '    문장으로 시작하는 줄의 코드는 세지 않는다 (2026-11-24: 한정 인수 줄이 완료로 세어졌다)"""')
rep('            if m:\n                out.update(f"{a}-{b}" for a, b in CODE_RE.findall(m.group(1)))',
    '            h = HEAD_CODES_RE.match(m.group(1)) if m else None\n'
    '            if h:\n                out.update(f"{a}-{b}" for a, b in CODE_RE.findall(h.group(0)))')

# 4. 범위가 바뀐 단계의 옛 카드는 세지 않는다
rep('        if m:\n            out.setdefault(f"{m.group(1)}-{m.group(2)}", []).append(t)',
    '        if m:\n'
    '            key = f"{m.group(1)}-{m.group(2)}"\n'
    '            if (t.get("created_at") or 0) < STAGE_SINCE.get(key, 0):\n'
    '                continue   # 범위가 바뀌기 전에 만든 카드\n'
    '            out.setdefault(key, []).append(t)')
rep('    """본문에 \'단계: <과목>-<코드>\' 줄이 있는 카드 → {코드: [카드…]} (카드 하나는 첫 줄의 단계 하나로만 센다)"""',
    '    """본문에 \'단계: <과목>-<코드>\' 줄이 있는 카드 → {코드: [카드…]} (카드 하나는 첫 줄의 단계 하나로만 센다).\n'
    '    STAGE_SINCE에 있는 단계는 그 시각 뒤에 만든 카드만 넣는다"""')

open(OUT, 'w', encoding='utf-8').write(s)
print('쓴 파일:', OUT, '| 줄 수', s.count('\n'), '| sha', hashlib.sha256(s.encode()).hexdigest()[:16])
