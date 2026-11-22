// 둥근 슬라이더: 홈 raised, 채움 text, 흰 손잡이 (그림자 없음)
import QtQuick

Item {
    id: root
    property real value: 0          // 0..1, 바깥(실제 볼륨·밝기)이 정하는 값
    readonly property bool pressed: ma.pressed
    // (2026-11-22) 끄는 동안 value에 직접 쓰면 바깥 바인딩이 끊겨 실제 볼륨을 안 따라갔음.
    // 끄는 동안·뗀 직후 잠깐만 dragValue를 보여 주고, 바깥 값이 바뀌거나 3초 지나면 value로 돌아감.
    property real dragValue: 0
    property bool holding: false
    readonly property real shown: holding ? dragValue : value
    onValueChanged: if (!ma.pressed) holding = false
    Timer { id: holdTimer; interval: 3000; onTriggered: root.holding = false }
    signal moved(real v)             // 끄는 중
    signal released(real v)          // 손을 뗐을 때
    implicitHeight: 20

    Rectangle {
        id: trough
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width; height: 8; radius: 4
        color: Theme.raised
        Rectangle {
            width: Math.max(8, root.shown * parent.width); height: parent.height; radius: 4
            color: Theme.text
        }
    }
    Rectangle {
        width: 16; height: 16; radius: 8
        color: Theme.text
        anchors.verticalCenter: parent.verticalCenter
        x: Math.max(0, Math.min(root.width - width, root.shown * root.width - width / 2))
    }
    MouseArea {
        id: ma
        anchors.fill: parent
        anchors.margins: -6
        cursorShape: Qt.PointingHandCursor
        function at(mx) { return Math.max(0, Math.min(1, (mx - 6) / root.width)) }
        onPressed: mouse => { holdTimer.stop(); root.holding = true; root.dragValue = at(mouse.x); root.moved(root.dragValue) }
        onPositionChanged: mouse => { if (pressed) { root.dragValue = at(mouse.x); root.moved(root.dragValue) } }
        onReleased: { root.released(root.dragValue); holdTimer.restart() }
    }
}
