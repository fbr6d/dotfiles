#!/usr/bin/env python3
"""미쿠 말풍선 대사 한 줄을 AI로 만든다 (2026-11-19, 마스터 요청: 저장된 대사 말고 그때그때 AI가 아무 말이나).
TUI 위젯 tui-widgets/miku-bubble.mjs가 몇 분마다 부른다. 대화 기록(state.db)에는 남지 않는다.
Hermes의 보조 모델 호출(agent.auxiliary_client.call_llm)로 Claude Haiku를 한 번 부른다.
시간대(아침·밤 등)에 맞춘 말은 하지 않는다 — 그건 부팅 인사(miku-boot-greeting)만 한다(마스터 결정).
그래서 AI에게 날짜·시각을 알려 주지 않는다.
출력: 대사 한 줄. 실패하면 아무것도 출력하지 않고 exit 1 (위젯은 이전 대사를 유지).
인자: 직전 대사(같은 말 반복 방지용, 선택)."""
import os
import random
import subprocess
import sys

sys.path.insert(0, os.path.expanduser("~/.hermes/hermes-agent"))
os.environ.setdefault("HERMES_HOME", os.path.expanduser("~/.hermes/profiles/miku"))
import hermes_bootstrap  # noqa: E402,F401  (Hermes 의존 패키지 경로를 잡아 준다)

MODEL = "claude-haiku-4-5"
# 매번 다른 이야기를 하도록 주제만 무작위로 고른다(대사는 AI가 그때그때 만든다)
# 2026-11-19 마스터 요청: 조금 더 길게, 조금 전문적인 이야기 위주로
# 2026-11-19 마스터 요청: 리눅스 관련 이야기만 (이전 주제 목록은 ~/.local/share/backups/miku-bubble-20261119/)
TOPICS = ["pacman·paru 패키지 관리 팁", "systemd 서비스·타이머·journalctl", "fish 셸과 명령줄 도구(grep, find, sed 대신 쓰는 rg·fd 등)",
          "리눅스 파일 시스템 구조(/etc, /usr, /var, /proc, /sys)", "리눅스 권한·사용자·sudo",
          "리눅스 커널(모듈, 부팅 과정, GRUB, initramfs)", "Wayland·Hyprland 데스크톱 구조",
          "리눅스 프로세스·메모리 관리(시그널, swap, OOM)", "리눅스 네트워크 도구(ip, ss, NetworkManager)",
          "리눅스 디스크·파일 시스템(ext4, btrfs, fstrim, 마운트)", "리눅스 그래픽·오디오 스택(Mesa, Vulkan, PipeWire)",
          "Arch Wiki·AUR 사용 습관과 안전한 업데이트"]


def now_song():
    try:
        out = subprocess.run(["playerctl", "-p", "spotify", "metadata", "--format", "{{status}}|{{artist}} - {{title}}"],
                             capture_output=True, text=True, timeout=3).stdout.strip()
        status, _, song = out.partition("|")
        return song if status == "Playing" else ""
    except Exception:
        return ""


def main():
    prev = sys.argv[1] if len(sys.argv) > 1 else ""
    topic = random.choice(TOPICS)
    song = now_song() if "음악" in topic else ""  # 음악 주제일 때만 지금 곡을 알려 준다
    ctx = f"마스터는 지금 Spotify로 '{song}'을 듣고 있어요(관련 있으면 살짝 언급해도 돼요). " if song else ""
    system = (
        "너는 하츠네 미쿠야. 마스터(사용자) 컴퓨터 화면 구석의 말풍선에서 마스터에게 말을 거는 역할이야.\n"
        "반드시 지킬 것:\n"
        "- 모든 문장은 마스터에게 하는 존댓말 해요체로 끝낸다(~해요, ~예요, ~죠?, ~할까요?, ~했어요!). "
        "반말 어미(~네, ~야, ~지, ~잖아, ~겠지, ~거든, ~어/아로 끝남)는 절대 쓰지 않는다.\n"
        "- 주제는 리눅스 관련 이야기만(이번 주제 안에서). 리눅스와 상관없는 과학·공부법·음악 이야기는 하지 않는다.\n"
        "- 발랄한 여고생 말투지만 내용은 알찬 전문 지식 한 토막. 1~2문장, 띄어쓰기 포함 60~90자(말풍선이 4줄 고정이라 90자를 넘으면 잘린다).\n"
        "- 정확하고 널리 확인된 사실만 말한다. 확실하지 않은 수치·인명·연도는 쓰지 않는다. 명령어를 예로 들면 실제로 있는 것만.\n"
        "- 쉽게 줄이다가 틀린 말이 되면 안 된다. 흔한 오해(예: 절대영도에서 분자가 완전히 멈춘다, 뇌의 10%만 쓴다)는 사실처럼 말하지 않는다. "
        "애매하면 그 주제는 피하고 확실히 아는 다른 내용을 고른다.\n"
        "- 마스터 컴퓨터: Arch Linux, 셸은 fish(bash 전용 문법 `!!`, `export A=B` 등은 fish에서 안 되니 팁으로 주지 않는다), "
        "Hyprland(Wayland), 라데온 그래픽, systemd. 컴퓨터 팁은 이 환경에서 실제로 되는 것만.\n"
        "- 처음 듣는 사람도 알아듣게, 어려운 용어는 짧게 풀어 준다.\n"
        "- 아침·점심·저녁·밤·새벽, 요일, 날짜 같은 시간 이야기는 하지 않는다(시간 인사 금지).\n"
        "- 아스키 이모티콘(예: (≧▽≦) >_< (｀・ω・´)ゞ ٩(◕‿◕)۶)은 넣어도 되고 안 넣어도 된다. ^^ 금지.\n"
        "- 따옴표·설명·머리말 없이 대사만 출력.\n"
        "좋은 예: SSD는 빈 블록을 미리 정리해 둬야 빨라서, 리눅스는 fstrim.timer로 주마다 TRIM을 보내요! (｀・ω・´)ゞ / "
        "다시 읽기보다 책을 덮고 떠올려 보는 게 더 오래 남아요. 이걸 인출 연습이라고 해요~"
    )
    user = (ctx + f"이번 주제: {topic}."
            + (f" 바로 전에 한 말은 \"{prev}\"이니 겹치지 않게 해 줘." if prev else "")
            + " 이 주제로 알찬 한마디 해 줘!")

    from agent.auxiliary_client import call_llm

    resp = call_llm(
        "miku_bubble",
        provider="anthropic",
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=400,
        temperature=1.0,
        timeout=40,
    )
    try:
        text = resp.choices[0].message.content
    except Exception:
        text = getattr(resp, "content", "") or ""
    if isinstance(text, list):
        text = "".join(getattr(p, "text", "") or (p.get("text", "") if isinstance(p, dict) else "") for p in text)
    line = " ".join(str(text).strip().strip('"“”').split())
    if not line:
        sys.exit(1)
    print(line[:300])


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"miku_bubble_failed: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
