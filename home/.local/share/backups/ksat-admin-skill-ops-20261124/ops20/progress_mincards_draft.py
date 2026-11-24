#!/usr/bin/env python3
"""진행도 스크립트: 등록 카드가 10장 미만인 단계의 완료 비율을 덜 믿게 하는 초안(기록 20의 12절, 마스터 승인 2026-11-24 16:1x).
원본을 읽어 scratch에 새 판을 쓰기만 한다. 원본은 건드리지 않는다."""
import hashlib
import os
import sys

SRC = os.path.expanduser('~/.hermes/profiles/miku/scripts/ksat_plan_progress.py')
OUT = os.path.expanduser('~/.hermes/profiles/miku/cache/scratch/eng20/ksat_plan_progress_mincards.py')
s = open(SRC, encoding='utf-8').read()
if not hashlib.sha256(s.encode()).hexdigest().startswith('c3bc20d52a4c986d'):
    sys.exit('원본이 예상한 파일이 아니다')


def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f'{old[:50]!r}가 {s.count(old)}번 있다')
    s = s.replace(old, new)


# 1. 머리말
rep("    ② 아니면 본문에 '단계: <과목>-<코드>' 줄이 있는 카드(보관 제외)의 완료 비율. 0.9를 넘기지 않는다.",
    "    ② 아니면 본문에 '단계: <과목>-<코드>' 줄이 있는 카드(보관 제외)의 완료 비율. 0.9를 넘기지 않는다.\n"
    "       등록된 카드가 10장(MIN_CARDS) 미만이면 끝난 카드 수를 10으로 나눈다(2026-11-24 마스터 승인).\n"
    "       총괄은 카드를 몇 장씩만 등록해서, 단계 초반에는 1/1·2/2처럼 다 끝난 것으로 보여 부풀려졌다.")

# 2. 상수
rep('CAP = 0.9  # [단계 완료] 줄이 없는 단계가 받을 수 있는 가장 큰 점수',
    'CAP = 0.9  # [단계 완료] 줄이 없는 단계가 받을 수 있는 가장 큰 점수\n'
    'MIN_CARDS = 10  # 등록 카드가 이보다 적으면 완료 비율을 (카드 수 / MIN_CARDS)만큼만 믿는다')

# 3. 점수 계산
rep('        frac = sum(t["status"] == "done" for t in cards) / len(cards) if cards else 0.0\n',
    '        # 끝난 카드 수 ÷ max(등록 카드 수, MIN_CARDS): 카드가 적은 단계는 그만큼 덜 믿는다\n'
    '        frac = sum(t["status"] == "done" for t in cards) / max(len(cards), MIN_CARDS) if cards else 0.0\n')

open(OUT, 'w', encoding='utf-8').write(s)
print('쓴 파일:', OUT, '| 줄 수', s.count('\n'), '| sha', hashlib.sha256(s.encode()).hexdigest()[:16])
