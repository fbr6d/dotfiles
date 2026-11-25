#!/usr/bin/env python3
"""KSAT 과목별 W단계 '사실상' 수치를 마크다운 표로 출력한다(읽기 전용).

ksat_plan_progress.py 출력을 받아 아래 보정만 한다.
- W4(검수) <= W3(집필): 쓴 만큼만 검수할 수 있다.
- W5(필수 암기) = 절반(교재 조사)은 그대로 + 절반(위키 보강)은 W3 이하.
✅ = 총괄이 원장에 [단계 완료]로 적은 단계.
"""
import json
import subprocess
import sys

SUBS = ["국어", "수학", "영어", "통합사회", "통합과학"]
CODES = [("W1", "공식 범위 확인"), ("W2", "개념 목록"), ("W3", "집필·문항 연결"),
         ("W4", "전수 검수·수정"), ("W5", "필수 암기"), ("W6", "정식판 인수")]


def main():
    out = subprocess.run([sys.executable, __file__.replace("ksat_real_stages.py", "ksat_plan_progress.py")],
                         capture_output=True, text=True).stdout
    d = json.loads(out[out.index("{"):])
    st, done = d["stages"], set(d.get("done_codes", []))
    real = {}
    for s in SUBS:
        g = {c: st.get(f"{s}-{c}", 0.0) for c, _ in CODES}
        g["W4"] = min(g["W4"], g["W3"])
        g["W5"] = 0.5 * g["W5"] + 0.5 * min(g["W5"], g["W3"])
        real[s] = g
    if "--json" in sys.argv:  # TUI 위젯(miku-ksat.mjs)용
        print(json.dumps({
            "version": d.get("version"), "at": d.get("at"), "subjects": SUBS,
            "rows": [{"code": c, "name": name,
                      "cells": [{"pct": round(real[s][c] * 100), "done": f"{s}-{c}" in done} for s in SUBS]}
                     for c, name in CODES],
        }, ensure_ascii=False))
        return
    print("| 단계 | " + " | ".join(SUBS) + " |")
    print("|---|" + "---|" * len(SUBS))
    for c, name in CODES:
        cells = []
        for s in SUBS:
            v = round(real[s][c] * 100)
            cells.append(("✅ " if f"{s}-{c}" in done else "") + str(v))
        print(f"| {c} {name} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
