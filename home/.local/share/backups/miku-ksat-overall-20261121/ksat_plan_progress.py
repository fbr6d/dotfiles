#!/usr/bin/env python3
"""KSAT 계획서 전체 진행도 (2026-11-19, 마스터 요청: 카드 장수 말고 계획서 전체 진행도) — 읽기 전용.
TUI 위젯 tui-widgets/miku-ksat.mjs가 1분마다 부른다. JSON 한 줄을 출력한다.

기준: plan/20261118_전과목_위키정식판_PDF*.md 중 가장 높은 판(v5 이상 자동 선택)의 4절 '작업 순서' 표를 17단계로 나눠 단계마다 0~1점.
  2026-11-20 마스터 A안: %는 단계 수가 아니라 WEIGHTS(대략 걸리는 시간) 가중 평균. 국어 검수·다른 과목 위키는 하위 단계(카드 제목 낱말)로 부분 점수.
  이전판 백업: ~/.local/share/backups/miku-ksat-widget-weighted-20261120/
  (v5는 4절 작업 순서가 v4와 같고, 8-4절로 공식 기출·EBS 검수 방식만 바뀜. 4절 표가 바뀌는 판이 나오면 단계표를 고칠 것)
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
PLAN_PREFIX = "20261118_전과목_위키정식판_PDF"


def latest_plan():
    """plan/ 에서 가장 높은 판 파일 이름과 판 번호(v1 = 접미사 없음)"""
    best = (1, PLAN_PREFIX + ".md")
    for n in os.listdir(os.path.join(ROOT, "plan")):
        m = re.fullmatch(re.escape(PLAN_PREFIX) + r"_v(\d+)\.md", n)
        if m and int(m.group(1)) > best[0]:
            best = (int(m.group(1)), n)
    return best
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
    # '판본: **1.0.0' 또는 '판본: **국어 Wiki v1.0.0 제한부 인수본' 둘 다 읽는다 (2026-11-20)
    m = re.search(r"판본:\s*\**([^*\n]*)", open(p, encoding="utf-8").read())
    if not m:
        return "?"
    v = re.search(r"v?(\d+\.\d+(?:\.\d+)?)", m.group(1))
    return (v.group(1) + (" 제한부" if "제한부" in m.group(1) else "")) if v else "?"


def pdf_days(sub, ts=None):
    """PDF 진행(0~2): 예전 방식 폴더 <과목>-day01/-day02, 또는 칸반 카드(2026-11-20 '국어-day01~02' 한 폴더로 바뀜)
    — 1~2일차 PDF 제작 카드 done = 1, 그 PDF의 검수·인수 카드 done = 2"""
    d = os.path.join(ROOT, "derived", "study-cycle-02")
    n = sum(1 for x in ("day01", "day02") if os.path.isdir(os.path.join(d, f"{sub}-{x}")))
    for t in ts or []:
        title = t["title"]
        if t["status"] != "done" or sub not in title or "PDF" not in title or "양식" in title or "디자인" in title:
            continue
        n = max(n, 2 if ("검수" in title or "인수" in title) else 1 if "제작" in title else n)
    return n


# 단계 무게 (2026-11-20 마스터 A안). 대략 '걸리는 시간(시간 단위)'에 맞춘 값.
# 근거: 칸반 기록 — 암기법 조사 약 10시간, 국어 ID·집필 약 4시간, 국어 검수~최종 판정 약 48시간+.
# 다른 과목 위키는 국어보다 빠를 것으로 보고(v5 간소화·경험) 35, PDF 2일치 4(영어는 AI 지문 9.2 검증이라 8).
WEIGHTS = {
    "착수 점검": 0.5, "암기법 조사": 7, "암기법 검수·인수": 2.5, "국어 임시판 보관": 0.5,
    "국어 ID 바꾸기·남은 문제": 4, "국어 전수 검수": 48, "국어 정식판 인수": 1, "공통 디자인 확정": 3,
    "수학 위키 정식판": 35, "영어 위키 정식판": 35, "통합사회 위키 정식판": 35, "통합과학 위키 정식판": 35,
    "국어 1~2일차 PDF": 4, "수학 1~2일차 PDF": 4, "영어 1~2일차 PDF": 8,
    "통합사회 1~2일차 PDF": 4, "통합과학 1~2일차 PDF": 4,
}


def _live(ts, sub):
    return [t for t in ts if sub in t["title"] and not t["title"].startswith("[보관")]


def _frac(cards):
    return sum(t["status"] == "done" for t in cards) / len(cards) if cards else 0.0


def kor_review_stage(ts, kor_final):
    """국어 3단계: 첫 전수 검수 70 → 필수 수정 8 → 변경 재확인 7 → 마지막 한정 수정 3 → 마지막 재확인 4 → 최종 대사 8"""
    if kor_final:
        return 1.0, ""
    k = _live(ts, "국어")
    first = [t for t in k if "검수" in t["title"] and "r1" not in t["title"] and "r2" not in t["title"]
             and "대사" not in t["title"] and "보강" not in t["title"]]
    fix1 = [t for t in k if "필수 수정" in t["title"]]
    re1 = [t for t in k if "r1" in t["title"] and "재확인" in t["title"]]
    fix2 = [t for t in k if "한정 수정" in t["title"]]
    re2 = [t for t in k if "r2" in t["title"] and "재확인" in t["title"]]
    final = [t for t in k if "전체 항목 대사" in t["title"]]
    parts = [(70, first if not _frac(fix1) else None, "첫 전수 검수"), (8, fix1, "필수 수정"),
             (7, re1, "변경 재확인"), (3, fix2, "마지막 수정"), (4, re2, "마지막 재확인"), (8, final, "최종 판정")]
    got, note = 0.0, ""
    for w, cards, name in parts:
        f = 1.0 if cards is None else _frac(cards)
        got += w * f
        if f < 1.0 and not note:
            note = name + (f" {sum(t['status'] == 'done' for t in cards)}/{len(cards)}" if cards and len(cards) > 1 else "")
    return got / 100, note


def wiki_stage(ts, sub):
    """다른 과목 위키: 공식 범위 5 → 개념 목록 10 → 집필 30 → 전수 검수·수정 50 → (인수 5는 README 1.x로 판정)"""
    c = _live(ts, sub)
    has = lambda *w: any(t["status"] == "done" and all(x in t["title"] for x in w) for t in c)
    got, note = 0.0, ""
    if has("범위") or has("성취기준"):
        got += 5
    else:
        note = note or "공식 범위"
    if has("개념 목록"):
        got += 10
    else:
        note = note or "개념 목록"
    if any(t["status"] == "done" and "집필" in t["title"] and "개념 목록" not in t["title"] for t in c):
        got += 30
    else:
        note = note or ("집필" if got else "")
    rv = [t for t in c if "검수" in t["title"] or "수정" in t["title"]]
    got += 50 * _frac(rv)
    if got >= 45 and _frac(rv) < 1.0:
        note = note or "전수 검수"
    return got / 100, (note if got else "")


def codex_usage():
    """KSAT 봇들이 함께 쓰는 Codex 주간 사용량(%)·초기화 시각 — 2분 캐시 (2026-11-20 마스터 요청)"""
    cache = os.path.expanduser("~/.cache/miku/ksat-codex-usage.json")
    try:
        with open(cache, encoding="utf-8") as f:
            c = json.load(f)
        if time.time() - c.get("at", 0) < 120:
            return c.get("u")
    except Exception:
        pass
    u = None
    try:
        out = subprocess.run([HERMES, "-p", "ksat-administrator", "usage", "--provider", "openai-codex", "--json"],
                             capture_output=True, text=True, timeout=20).stdout
        w = [x for x in json.loads(out).get("windows", []) if "eek" in x.get("label", "")]
        if w:
            u = {"pct": round(float(w[0]["used_percent"])), "resets_at": w[0].get("resets_at")}
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump({"at": time.time(), "u": u}, f)
    except OSError:
        pass
    return u


def running_cards(ts):
    """실행 중 카드: 제목·담당·모델·시작 후 경과·최대 실행 시간·마지막 신호(heartbeat) — kanban.db 읽기 전용"""
    import sqlite3
    run = [t for t in ts if t["status"] == "running"]
    beats = {}
    try:
        db = sqlite3.connect("file:" + os.path.expanduser("~/.hermes/kanban/boards/ksat-10000/kanban.db") + "?mode=ro", uri=True, timeout=2)
        for t in run:
            r = db.execute("select max(created_at) from task_events where task_id=? and kind in ('heartbeat','claimed','spawned','started')",
                           (t["id"],)).fetchone()
            beats[t["id"]] = r[0] if r else None
        db.close()
    except Exception:
        pass
    now = time.time()
    out = []
    for t in sorted(run, key=lambda x: x.get("started_at") or 0):
        st = t.get("started_at") or now
        hb = beats.get(t["id"]) or st
        out.append({"id": t["id"], "title": re.sub(r"^\[[^\]]*\]\s*", "", t["title"]),
                    "who": (t.get("assignee") or "").replace("ksat-", ""),
                    "model": (t.get("model_override") or "").replace("claude-", "").replace("gpt-6.1-", "").replace("gpt-6-", ""),
                    "elapsed_min": int((now - st) // 60), "max_min": int((t.get("max_runtime_seconds") or 7200) // 60),
                    "beat_ago_min": int((now - hb) // 60)})
    return out


def main():
    plan_ver, plan_name = latest_plan()
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
    # 3단계는 카드 장수가 아니라 '어느 하위 단계까지 왔는지'로 매긴다 (2026-11-20 마스터 A안)
    # 하위 단계 몫(실제 걸린 시간 비율 근거): 첫 전수 검수 70, 필수 수정 8, 변경 재확인 7, 마지막 한정 수정 3, 마지막 재확인 4, 최종 대사 8
    s3, note3 = kor_review_stage(ts, kor_final)
    steps.append(("3", "국어 전수 검수", s3, note3))
    steps.append(("4", "국어 정식판 인수", 1.0 if kor_final else 0.0, ""))
    steps.append(("5", "공통 디자인 확정", 1.0 if done(ts, "디자인") else 0.0, ""))

    subjects = []
    num = {"국어": ("-", "6"), "수학": ("7", "8"), "영어": ("9", "9"), "통합사회": ("10", "10"), "통합과학": ("11", "12")}
    for sub in SUBJECTS:
        ver = wiki_version(sub)
        final = bool(ver and ver.startswith("1."))
        days = pdf_days(sub, ts)
        if sub != "국어":
            sw, nw = (1.0, "") if final else wiki_stage(ts, sub)
            steps.append((num[sub][0], f"{sub} 위키 정식판", sw, nw))
        steps.append((num[sub][1], f"{sub} 1~2일차 PDF", days / 2, ""))
        if final:
            wiki = ver if "제한부" in ver else "정식판 " + ver   # 칸 폭 13칸 안에 맞춤
        elif not ver and any(t["title"].startswith(sub + " ") and "암기법" not in t["title"] and "PDF" not in t["title"]
                                for t in ts if t["status"] in ("done", "running")):
            wiki = "작업 중"   # 위키 폴더가 아직 없어도 그 과목 카드가 돌았으면
        elif sub == "국어" and ver:
            wiki = "검수 중"
        elif ver:
            wiki = "작업 중"
        else:
            wiki = "대기"
        subjects.append({"name": sub, "wiki": wiki, "final": final, "pdf": days})

    total = len(steps)
    wsum = sum(WEIGHTS.get(s[1], 1.0) for s in steps)
    score = sum(s[2] * WEIGHTS.get(s[1], 1.0) for s in steps)
    steps_done = sum(1 for s in steps if s[2] >= 1.0)
    current = next((s for s in steps if s[2] < 1.0), None)
    # 마스터 결정이 필요한 열린 건 (scripts/kanban_attention.py가 5분마다 적는다)
    try:
        with open(os.path.expanduser("~/.cache/miku/kanban-attention.json"), encoding="utf-8") as f:
            attention = [{"task": o["task"], "text": o["text"][:120]} for o in json.load(f).get("open", [])]
    except Exception:
        attention = []
    print(json.dumps({
        "plan": plan_name,
        "version": f"v{plan_ver}",
        "attention": attention,
        "percent": round(score / wsum * 100),
        "score": steps_done,
        "total": total,
        "weighted": True,
        "current": {"no": current[0], "name": current[1], "note": current[3]} if current else None,
        "subjects": subjects,
        "running": running_cards(ts),
        "codex": codex_usage(),
        "at": int(time.time()),
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}"}, ensure_ascii=False))
