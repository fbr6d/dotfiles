// 검은 화면 덮개 (2026-11-25 마스터: 제어센터 버튼으로 화면을 검게 덮기. 절전 아님, 실행 중인 작업은 멈추지 않음)
//   모니터마다 맨 위(Overlay) 층에 화면 전체 검은 창 → 덮개가 떠 있는 동안 키보드·마우스는 덮개가 받는다
//   (아래 창에 엉뚱한 입력이 들어가지 않게). 입력이 1초 넘게 이어지면 페이드로 벗김. 마우스 커서도 숨김.
//   켜기/끄기: qs -c miku-shell ipc call blackout toggle | cover | uncover   (비상시 uncover)
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick

Scope {
    Variants {
        model: Quickshell.screens
        PanelWindow {
            id: w
            required property var modelData
            screen: modelData
            readonly property bool showing: BlackoutState.on || shade.opacity > 0.001
            visible: showing
            color: "transparent"
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.namespace: "miku-blackout"
            WlrLayershell.keyboardFocus: BlackoutState.on ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

            Rectangle {
                id: shade
                anchors.fill: parent
                color: "black"
                opacity: BlackoutState.on ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: BlackoutState.on ? 700 : 450; easing.type: Easing.InOutQuad } }
            }
            Item {                                   // 키보드
                anchors.fill: parent
                focus: true
                Keys.onPressed: ev => { if (!ev.isAutoRepeat) BlackoutState.keysDown++; BlackoutState.poke(); ev.accepted = true }
                Keys.onReleased: ev => { if (!ev.isAutoRepeat) BlackoutState.keysDown = Math.max(0, BlackoutState.keysDown - 1); ev.accepted = true }
            }
            MouseArea {                              // 마우스: 움직임·클릭·휠 모두 입력, 커서는 숨김
                anchors.fill: parent
                enabled: BlackoutState.on
                hoverEnabled: true
                acceptedButtons: Qt.AllButtons
                cursorShape: Qt.BlankCursor
                onPositionChanged: BlackoutState.poke()
                onPressed: BlackoutState.poke()
                onWheel: BlackoutState.poke()
            }
        }
    }

    IpcHandler {
        target: "blackout"
        function toggle(): void { BlackoutState.toggle() }
        function cover(): void { BlackoutState.cover() }
        function uncover(): void { BlackoutState.uncover() }
        function poke(): void { BlackoutState.poke() }   // 시험용: 입력 한 번 흉내(hyprctl 커서 이동은 움직임 이벤트를 안 보냄)
        function stat(): string { return "on=" + BlackoutState.on + " armed=" + BlackoutState.armed + " pokes=" + BlackoutState.pokes + " keys=" + BlackoutState.keysDown }
    }
}
