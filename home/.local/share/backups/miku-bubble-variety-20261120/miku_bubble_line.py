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
# 사실 확인은 Sonnet (2026-11-20 시험: Haiku 확인은 맞는 사실을 떨어뜨리고 논란 주장을 통과시켜서 못 믿음)
VERIFY_MODEL = "claude-sonnet-5-5"
# 매번 다른 이야기를 하도록 주제만 무작위로 고른다(대사는 AI가 그때그때 만든다)

# 2026-11-19 마스터 요청: 리눅스 관련 이야기만 (이전 주제 목록은 ~/.local/share/backups/miku-bubble-20261119/)
# 2026-11-20 마스터 요청: 리눅스 대신 '조금 모를 만한 재밌는 사실'(예: 코알라 지문은 사람 지문과 아주 비슷하다)
#   (이전 리눅스 주제 목록은 ~/.local/share/backups/miku-bubble-trivia-20261120/)
TOPICS = ["동물의 신기한 몸과 습성", "곤충·바다 생물의 의외의 사실", "식물·버섯의 신기한 점",
          "사람 몸의 의외의 사실", "우주·행성·별의 신기한 사실", "지구·날씨·지리의 의외의 사실",
          "음식·요리 재료의 숨은 사실", "물건·발명품이 생긴 뜻밖의 이야기", "단어·말의 뜻밖의 어원(한국어·영어)",
          "역사 속 의외의 사실", "화학·물리로 보는 일상 속 신기한 현상", "숫자·수학의 재밌는 성질",
          "세계 여러 나라의 독특한 문화·기록", "음악·악기·소리의 신기한 사실"]


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
        "- 내용은 '조금 모를 만한 재밌는 사실' 한 가지(이번 주제 안에서). 누구나 아는 뻔한 상식(물은 100도에서 끓는다 등)은 피하고, "
        "듣고 '오, 진짜요?' 할 만한 것을 고른다.\n"
        "- 발랄한 여고생 말투로 신기한 사실 한 토막. 1~2문장, 띄어쓰기 포함 60~90자(말풍선이 4줄 고정이라 90자를 넘으면 잘린다).\n"
        "- 정확하고 널리 확인된 사실만 말한다. 확실하지 않은 수치·인명·연도는 쓰지 않는다. 명령어를 예로 들면 실제로 있는 것만.\n"
        "- 쉽게 줄이다가 틀린 말이 되면 안 된다. 널리 퍼진 가짜 상식은 사실처럼 말하지 않는다: 뇌의 10%만 쓴다, 금붕어 기억력은 3초, "
        "만리장성이 우주에서 맨눈으로 보인다, 박쥐는 앞을 못 본다, 삼킨 껌이 7년 남는다, 혀에 맛 구역 지도가 있다, "
        "번개는 같은 곳에 두 번 안 친다, 타조는 머리를 모래에 묻는다, 절대영도에서 분자가 완전히 멈춘다 등. "
        "애매하면 그 주제는 피하고 확실히 아는 다른 내용을 고른다.\n"
        "- '~래요/~대요' 말투를 써도 되지만 내용은 백과사전·교과서 수준으로 확인된 것만. 출처 불분명한 인터넷 밈은 쓰지 않는다.\n"
        "- 학자들 사이에 논란이 있거나 추정치에 기대는 이야기(오래된 바이올린 소리가 더 좋다, ~년 뒤 사라진다 등)는 고르지 않는다. 네가 90% 이상 확신하는 사실만.\n"
        "- 처음 듣는 사람도 알아듣게, 어려운 용어는 짧게 풀어 준다.\n"
        "- 아침·점심·저녁·밤·새벽, 요일, 날짜 같은 시간 이야기는 하지 않는다(시간 인사 금지).\n"
        "- 아스키 이모티콘(예: (≧▽≦) >_< (｀・ω・´)ゞ ٩(◕‿◕)۶)은 넣어도 되고 안 넣어도 된다. ^^ 금지.\n"
        "- 따옴표·설명·머리말 없이 대사만 출력.\n"
        "좋은 예: 코알라 지문은 사람 지문이랑 정말 비슷해서 현미경으로 봐도 구별하기 어렵대요! (≧▽≦) / "
        "꿀은 거의 상하지 않아서, 고대 이집트 무덤에서 나온 아주 오래된 꿀도 썩지 않은 상태였대요~"
    )
    user = (ctx + f"이번 주제: {topic}."
            + (f" 바로 전에 한 말은 \"{prev}\"이니 겹치지 않게 해 줘." if prev else "")
            + " 이 주제로 조금 모를 만한 재밌는 사실 하나 말해 줘!")

    # 2026-11-20: 재밌는 사실은 틀리기 쉬워서, 만든 대사를 한 번 더 사실 확인하고 틀리면 다시 만든다(최대 3번)
    for _ in range(3):
        line = ask(system, user, 1.0)
        if line and check(line):
            print(line[:300])
            return
    sys.exit(1)


def ask(system, user, temperature, max_tokens=400, model=None):
    from agent.auxiliary_client import call_llm

    resp = call_llm(
        "miku_bubble",
        provider="anthropic",
        model=model or MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=40,
    )
    try:
        text = resp.choices[0].message.content
    except Exception:
        text = getattr(resp, "content", "") or ""
    if isinstance(text, list):
        text = "".join(getattr(p, "text", "") or (p.get("text", "") if isinstance(p, dict) else "") for p in text)
    return " ".join(str(text).strip().strip('"“”').split())


def check(line):
    """사실 확인: 틀리거나 과장·논란이 있으면 False"""
    verdict = ask(
        "너는 사실 확인 담당이야. 주어진 한국어 문장의 핵심 사실 주장만 판단해. "
        "핵심 주장이 명백히 틀렸거나, 널리 퍼진 가짜 상식이거나, 학계에서 크게 논란인 주장이면 NO. "
        "어린이용 백과사전처럼 쉬운 말로 줄인 표현, 흔히 소개되는 정설, '~래요' 같은 전언 말투는 YES로 본다(세부 용어가 덜 정밀한 것은 문제 삼지 마). "
        "첫 단어로 YES 또는 NO만 답하고, NO면 짧은 이유를 덧붙여.",
        line, 0.0, max_tokens=60, model=VERIFY_MODEL)
    return verdict.upper().startswith("YES")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"miku_bubble_failed: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
