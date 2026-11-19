#!/usr/bin/env python3
"""KSAT 계획서 전체 진행도 (2026-11-19, 마스터 요청: 카드 장수 말고 계획서 전체 진행도) — 읽기 전용.
TUI 위젯 tui-widgets/miku-ksat.mjs가 1분마다 부른다. JSON 한 줄을 출력한다.

기준: plan/20261118_전과목_위키정식판_PDF_v4.md 4절 '작업 순서' 표를 17단계로 나눠 단계마다 0~1점.
  공통 5단계: 0 착수 점검, 0.5 암기법 조사, 0.6 암기법 검수·인수, 1 국어 임시판 보관, 2 국어 ID·남은 문제,
             3 국어 전수 검수(검수·수정 카드 완료 비율만큼 부분 점수), 4 국어 정식판 인수, 5 공통 디자인 확정
  과목별: 국어 PDF(6), 수학·영어·통합사회·통합과학 각각 위키 정식판(7·9·10·11) + PDF(8·…)
  위키 정식판 = wiki/<과목>/README.md 판본이 1.x (총괄 인수 뒤 v1.0.0)
  PDF = derived/study-cycle-02/<과목>-day01, -day02 폴더 (하나에 0.5점)
판단 근거는 칸반 카드 상태와 산출물 경로뿐이고, 카드·파일은 건드리지 않는다."""
import json
import os
import re
import subprocess
import time

ROOT = "/home/leejaeik/Projects/ksat-10000"
BOARD = "ksat-10000"
PLAN = "plan/20261118_전과목_위키정식판_PDF_v4.md"
TENANT_PREFIX = "study-cycle-02"
SUBJECTS = ["국어", "수학", "영어", "통합사회", "통합과학"]
HERMES = os.path.expanduser("~/.hermes/hermes-agent/.hermes/bin/hermes")


def tasks():
    out = subprocess.run([HERMES, "kanban", "--board", BOARD, "list", "--json"],
                         capture_output=True, text=True, timeout=40).stdout
    return [t for t in json.loads(out or "[]")
            if str(t.get("tenant") or "").startswith(TENANT_PREFIX) and t["status"] != "archived"]


def done(ts, *words):
    return any(t["status"] == "done" and all(w in t["title"] for w in words) for t in ts)


def wiki_version(sub):
    p = os.path.join(ROOT, "wiki", sub, "README.md")
    if not os.path.exists(p):
        return None
    m = re.search(r"판본:\s*\**([0-9][^*\s]*)", open(p, encoding="utf-8").read())
    return m.group(1) if m else "?"


def pdf_days(sub):
    d = os.path.join(ROOT, "derived", "study-cycle-02")
    return sum(1 for n in ("day01", "day02") if os.path.isdir(os.path.join(d, f"{sub}-{n}")))


def main():
    ts = tasks()
    steps = []  # (번호, 이름, 점수 0~1, 덧붙임)

    steps.append(("0", "착수 점검", 1.0 if any("계획 실행 원장" in t["title"] for t in ts) else 0.0, ""))
    research = [t for t in ts if "암기법" in t["title"] and "근거" in t["title"]]
    s05 = 1.0 if done(ts, "암기법", "종합") else (sum(t["status"] == "done" for t in research) / 7 if research else 0.0)
    steps.append(("0.5", "암기법 조사", s05, ""))
    s06 = 1.0 if done(ts, "암기법", "총괄 인수") else (0.5 if done(ts, "암기법", "검수") else 0.0)
    steps.append(("0.6", "암기법 검수·인수", s06, ""))
    archived = os.path.isdir(os.path.join(ROOT, "derived", "llm-wiki", "archive", "국어-v0.1.0"))
    steps.append(("1", "국어 임시판 보관", 1.0 if archived or done(ts, "국어", "보관") else 0.0, ""))
    s2 = 1.0 if done(ts, "국어", "정식판 집필") else (0.5 if done(ts, "국어", "ID 대응표") else 0.0)
    steps.append(("2", "국어 ID 바꾸기·남은 문제", s2, ""))

    kor_ver = wiki_version("국어") or ""
    kor_final = kor_ver.startswith("1.")
    review = [t for t in ts if "국어" in t["title"] and ("검수" in t["title"] or "수정" in t["title"])]
    rd = sum(t["status"] == "done" for t in review)
    s3 = 1.0 if kor_final else (rd / len(review) if review else 0.0)
    steps.append(("3", "국어 전수 검수", s3, f"카드 {rd}/{len(review)}" if review and not kor_final else ""))
    steps.append(("4", "국어 정식판 인수", 1.0 if kor_final else 0.0, ""))
    steps.append(("5", "공통 디자인 확정", 1.0 if done(ts, "디자인") else 0.0, ""))

    subjects = []
    num = {"국어": ("-", "6"), "수학": ("7", "8"), "영어": ("9", "9"), "통합사회": ("10", "10"), "통합과학": ("11", "12")}
    for sub in SUBJECTS:
        ver = wiki_version(sub)
        final = bool(ver and ver.startswith("1."))
        days = pdf_days(sub)
        if sub != "국어":
            steps.append((num[sub][0], f"{sub} 위키 정식판", 1.0 if final else 0.0, ""))
        steps.append((num[sub][1], f"{sub} 1~2일차 PDF", days / 2, ""))
        if final:
            wiki = "정식판 " + ver
        elif sub == "국어" and ver:
            wiki = "검수 중"
        elif ver:
            wiki = "작업 중"
        else:
            wiki = "대기"
        subjects.append({"name": sub, "wiki": wiki, "final": final, "pdf": days})

    total = len(steps)
    score = sum(s[2] for s in steps)
    current = next((s for s in steps if s[2] < 1.0), None)
    # 마스터 결정이 필요한 열린 건 (scripts/kanban_attention.py가 5분마다 적는다)
    try:
        with open(os.path.expanduser("~/.cache/miku/kanban-attention.json"), encoding="utf-8") as f:
            attention = [{"task": o["task"], "text": o["text"][:120]} for o in json.load(f).get("open", [])]
    except Exception:
        attention = []
    print(json.dumps({
        "plan": os.path.basename(PLAN),
        "attention": attention,
        "percent": round(score / total * 100),
        "score": round(score, 2),
        "total": total,
        "current": {"no": current[0], "name": current[1], "note": current[3]} if current else None,
        "subjects": subjects,
        "at": int(time.time()),
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}"}, ensure_ascii=False))
