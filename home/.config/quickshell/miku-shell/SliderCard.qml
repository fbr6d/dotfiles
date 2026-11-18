// 아이콘 + 슬라이더를 담은 카드 (볼륨, 조명 밝기)
import QtQuick

Rectangle {
    id: root
    property string icon: ""
    property alias value: slider.value
    property alias pressed: slider.pressed
    property bool iconClickable: false
    signal moved(real v)
    signal released(real v)
    signal iconClicked()

    implicitHeight: 44
    radius: 12
    color: Theme.surface

    Icon {
        id: ic
        text: root.icon
        color: icMa.containsMouse ? Theme.text : Theme.dim
        anchors.left: parent.left
        anchors.leftMargin: 14
        anchors.verticalCenter: parent.verticalCenter
        MouseArea {
            id: icMa
            anchors.fill: parent
            anchors.margins: -6
            enabled: root.iconClickable
            hoverEnabled: true
            cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: root.iconClicked()
        }
    }
    Slider {
        id: slider
        anchors.left: ic.right
        anchors.leftMargin: 14
        anchors.right: parent.right
        anchors.rightMargin: 16
        anchors.verticalCenter: parent.verticalCenter
        onMoved: v => root.moved(v)
        onReleased: v => root.released(v)
    }
}
