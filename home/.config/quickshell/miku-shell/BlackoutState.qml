pragma Singleton
// 검은 화면 덮개 상태 (Blackout.qml 과 제어센터 「검은 화면」 버튼이 같이 씀, 2026-11-25 마스터 요청)
//   절전·잠금·화면 끄기가 아니다: 검은 창을 맨 위에 덮기만 하고, 실행 중인 프로그램·소리·작업은 그대로 돈다.
//   키보드·마우스 입력이 1초 넘게 이어지면 벗긴다(살짝 건드린 건 무시). 덮고 벗길 때 페이드.
//   2026-11-25 마스터 '백라이트도 어둡게': 다 덮이면 ~/.local/bin/monitor-dim dim(DDC/CI 밝기 0, 원래 값 기록),
//   벗길 때 monitor-dim restore. 셸이 켜질 때도 restore(덮인 채 꺼졌다 켜져도 원래 밝기로).
import Quickshell
import QtQuick

Singleton {
    id: st
    property bool on: false          // 덮개를 씌우려는 상태(페이드 목표)
    property bool armed: false       // 막 덮은 직후(클릭하며 움직인 마우스 등)는 세지 않음
    property real burstStart: 0      // 이어지는 입력 묶음이 시작된 시각
    property real lastInput: 0
    property int keysDown: 0         // 누르고 있는 키 수(꾹 누르기도 '이어지는 입력')
    readonly property int holdMs: 1000   // 이만큼 이어지면 벗김
    readonly property int gapMs: 350     // 입력 사이가 이보다 벌어지면 새 묶음

    readonly property string dimCmd: Quickshell.env("HOME") + "/.local/bin/monitor-dim"
    property bool dimmed: false
    function cover() { armed = false; keysDown = 0; burstStart = 0; lastInput = 0; on = true; armTimer.restart(); dimTimer.restart() }
    function uncover() {
        on = false; armed = false; keysDown = 0; dimTimer.stop()
        if (dimmed) { dimmed = false; Quickshell.execDetached([dimCmd, "restore"]) }   // 기록이 없으면 restore는 아무것도 안 함
    }
    function toggle() { if (on) uncover(); else cover() }
    property int pokes: 0            // 시험용: 받은 입력 수
    function poke() {                // 키·마우스 입력이 들어올 때마다
        pokes++
        if (!on || !armed) return
        const now = Date.now()
        if (now - lastInput > gapMs) burstStart = now
        lastInput = now
        check(now)
    }
    function check(now) {
        if (lastInput > 0 && now - lastInput <= gapMs && now - burstStart >= holdMs) uncover()
    }

    Timer { id: armTimer; interval: 900; onTriggered: st.armed = true }
    // 검은 페이드(0.7초)가 끝난 뒤 백라이트를 내림(밝기 바뀌는 게 안 보이게)
    Timer { id: dimTimer; interval: 750; onTriggered: if (st.on) { st.dimmed = true; Quickshell.execDetached([st.dimCmd, "dim"]) } }
    Component.onCompleted: Quickshell.execDetached([dimCmd, "restore"])
    Timer {                          // 키를 꾹 누르고 있는 동안은 새 이벤트가 없어도 이어지는 입력으로 봄
        interval: 100; repeat: true; running: st.on && st.armed
        onTriggered: { const now = Date.now(); if (st.keysDown > 0) { if (now - st.lastInput > st.gapMs) st.burstStart = now; st.lastInput = now } st.check(now) }
    }
}
