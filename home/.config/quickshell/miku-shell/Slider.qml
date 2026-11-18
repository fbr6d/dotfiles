// 둥근 슬라이더: 홈 raised, 채움 text, 흰 손잡이 (그림자 없음)
import QtQuick

Item {
    id: root
    property real value: 0          // 0..1
    readonly property bool pressed: ma.pressed
    signal moved(real v)             // 끄는 중
    signal released(real v)          // 손을 뗐을 때
    implicitHeight: 20

    Rectangle {
        id: trough
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width; height: 8; radius: 4
        color: Theme.raised
        Rectangle {
            width: Math.max(8, root.value * parent.width); height: parent.height; radius: 4
            color: Theme.text
        }
    }
    Rectangle {
        width: 16; height: 16; radius: 8
        color: Theme.text
        anchors.verticalCenter: parent.verticalCenter
        x: Math.max(0, Math.min(root.width - width, root.value * root.width - width / 2))
    }
    MouseArea {
        id: ma
        anchors.fill: parent
        anchors.margins: -6
        cursorShape: Qt.PointingHandCursor
        function at(mx) { return Math.max(0, Math.min(1, (mx - 6) / root.width)) }
        onPressed: mouse => { root.value = at(mouse.x); root.moved(root.value) }
        onPositionChanged: mouse => { if (pressed) { root.value = at(mouse.x); root.moved(root.value) } }
        onReleased: root.released(root.value)
    }
}
