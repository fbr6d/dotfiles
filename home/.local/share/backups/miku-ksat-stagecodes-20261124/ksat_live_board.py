#!/usr/bin/env python3
"""KSAT 실시간 현황 메시지 (2026-11-20 마스터 요청: 디스코드에서 위젯처럼 보기) — AI 사용 없음.

1분마다(systemd 사용자 타이머 miku-ksat-live.timer) 위젯과 같은 ksat_plan_progress.py 결과를
미쿠 봇이 #칸반-보고 채널의 메시지 '하나'에 고쳐 쓴다. 처음 한 번만 새 메시지를 올리고(알림 없음),
그 뒤로는 같은 메시지를 수정한다(수정은 알림이 울리지 않음). 메시지가 지워지면 새로 올린다.
Claude 사용량은 1분마다 `hermes usage`로 조회(숫자만 읽는 조회라 한도를 쓰지 않음).
상태: ~/.cache/miku/ksat-live-board.json (message_id, 사용량 캐시)
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CHANNEL = "1572564598693830677"  # 미쿠의 방 #칸반-보고
HOME = Path.home()
SCRIPTS = HOME / ".hermes/profiles/miku/scripts"
HERMES = str(HOME / ".hermes/hermes-agent/.hermes/bin/hermes")
STATE = HOME / ".cache/miku/ksat-live-board.json"
USAGE_EVERY = 50  # 초 — 2026-11-20 마스터 요청으로 매 실행(1분)마다 조회 (타이머 오차 감안 50초)


def token():
    env = HOME / ".hermes/profiles/miku/.env"
    return next(l.split("=", 1)[1].strip() for l in env.read_text().splitlines() if l.startswith("DISCORD_BOT_TOKEN="))


def discord(method, path, body=None):
    req = urllib.request.Request(
        "https://discord.com/api/v10" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bot " + token(), "Content-Type": "application/json",
                 "User-Agent": "DiscordBot (miku, 1)"},
        method=method)
    return json.load(urllib.request.urlopen(req, timeout=20))


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False))


def progress():
    out = subprocess.run([sys.executable, str(SCRIPTS / "ksat_plan_progress.py")],
                         capture_output=True, text=True, timeout=60).stdout
    return json.loads(out)


def claude_usage(st):
    now = time.time()
    cache = st.get("usage") or {}
    if now - cache.get("at", 0) < USAGE_EVERY:
        return cache
    try:
        out = subprocess.run([HERMES, "-p", "miku", "usage", "--provider", "anthropic", "--json"],
                             capture_output=True, text=True, timeout=60).stdout
        w = {x["label"]: x["used_percent"] for x in json.loads(out).get("windows", [])}
        cache = {"at": now, "session": w.get("Current session"), "week": w.get("Current week")}
    except Exception:
        cache = {"at": now, "session": None, "week": None}
    st["usage"] = cache
    return cache


def bar(pct, width=20):
    fill = round(pct / 100 * width)
    return "█" * fill + "░" * (width - fill)


def render(p, u):
    t = time.strftime("%H:%M")
    if p.get("error"):
        return f"📊 **KSAT 실시간 현황**\n⚠ 진행도를 읽지 못했어요 ({p['error']})\n🕒 {t} 기준 · 1분마다 갱신"
    lines = [f"📊 **KSAT 계획서 {p['version']} · 실시간 현황**",
             f"`{bar(p['percent'])}` **{p['percent']}%**",
             f"전체 무게 {p.get('weight_done')}/{p.get('weight_total')} · 걸리는 시간 기준"]
    # 2026-11-21 마스터: '첫 미완료 단계' 대신 동시에 진행 중인 단계를 무게 큰 순으로
    act = p.get("active") or []
    c = p.get("current")
    if act:
        lines.append("▶ 진행 중: " + " · ".join(f"**{a['name']} {a['pct']}%**" for a in act))
    elif c:
        lines.append(f"▶ 다음: **{c['name']}**")
    else:
        lines.append("✓ 계획서 단계를 모두 마쳤어요!")

    lines.append("")
    waiting = []
    for s in p.get("subjects", []):
        if s["wiki"] == "대기" and s["pdf"] == 0 and not s.get("pdf_note") and not s.get("ext_pct"):
            waiting.append(s["name"])
            continue
        mark = "●" if s["final"] and s["pdf"] >= 2 else "◐"
        wk = f"{s['wiki']} {s['wiki_pct']}%" if not s["final"] and s.get("wiki_pct") is not None else s["wiki"]
        # 2026-11-22 마스터: 숫자(0/2) 대신 글자 — 미제작(또는 제작중·보류·대기) / 제작됨(마스터 판단 대기) / 확정
        pdf = (s.get("pdf_note") or "미제작") if not s["pdf"] else ("확정" if s["pdf"] >= 2 else "제작됨 · 수정중" if s.get("pdf_note") == "수정중" else "제작됨 · 마스터 확인 대기")
        lines.append(f"{mark} {s['name']} · 위키 {wk} · PDF {pdf} · 자료 확장 {s.get('ext_pct', 0)}%")
    if waiting:
        lines.append("○ 대기 " + "·".join(waiting))

    lines.append("")
    run = p.get("running") or []
    if run:
        lines.append(f"**실행 중인 카드 {len(run)}장**")
        for r in run:
            warn = " 🔴 신호 끊김" if r["beat_ago_min"] >= 5 else ""
            model = f"·{r['model']}" if r.get("model") else ""
            lines.append(f"▸ {r['who']}{model} · {r['elapsed_min']}분/{r['max_min']}분{warn}")
            lines.append(f"  {r['title'][:60]}")
    else:
        lines.append("▸ 실행 중인 카드 없음")

    att = p.get("attention") or []
    lines.append("")
    if att:
        lines.append(f"⚠ **결정 필요 {len(att)}건** · " + ", ".join(sorted({a['task'] for a in att})))
    s, w = u.get("session"), u.get("week")
    if s is not None:
        lines.append(f"🤖 Claude 5시간 {s:g}% · 주간 {w:g}%" if w is not None else f"🤖 Claude 5시간 {s:g}%")
    # 2026-11-20 마스터 요청: Codex 주간 사용량(KSAT 봇 공용, 98%면 새 카드 멈춤) — ksat_plan_progress.py의 2분 캐시 값
    cx = p.get("codex")
    if cx:
        mark = "🚨" if cx["pct"] >= 95 else "⚠️" if cx["pct"] >= 80 else "💳"
        when = ""
        try:
            import datetime as _dt
            r = _dt.datetime.fromisoformat(cx["resets_at"].replace("Z", "+00:00")).astimezone(_dt.timezone(_dt.timedelta(hours=9)))
            when = f" · {'월화수목금토일'[r.weekday()]} {r:%H:%M} 초기화"
        except Exception:
            pass
        lines.append(f"{mark} Codex 주간 {cx['pct']}%{when}")
    else:
        lines.append("💳 Codex 주간 사용량 조회 실패")
    lines.append(f"🕒 {t} 기준 · 1분마다 갱신")
    return "\n".join(lines)[:1990]


def main():
    st = load_state()
    try:
        p = progress()
    except Exception as e:
        p = {"error": type(e).__name__}
    text = render(p, claude_usage(st))
    mid = st.get("message_id")
    if mid:
        try:
            discord("PATCH", f"/channels/{CHANNEL}/messages/{mid}", {"content": text})
            save_state(st)
            print("edited", mid)
            return
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    m = discord("POST", f"/channels/{CHANNEL}/messages", {"content": text, "flags": 4096})  # 4096 = 알림 없이
    st["message_id"] = m["id"]
    save_state(st)
    print("posted", m["id"])


if __name__ == "__main__":
    main()
