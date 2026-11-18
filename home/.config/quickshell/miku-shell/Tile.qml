// 버튼·토글·상태 칸 하나.
//   active    켜짐 = 흰 알약
//   clickable false 면 상태만 보여 주는 칸(hover 없음)
//   enabled   false 면 흐린 글자, 눌리지 않음
import QtQuick

Rectangle {
    id: root
    property string icon: ""
    property string label: ""
    property bool active: false
    property bool clickable: true
    property int iconSize: 18
    property int fontSize: 12
    property color base: Theme.surface           // 꺼진 바탕 (hover 는 한 단계 밝게)
    signal clicked()

    implicitHeight: 44
    radius: 12
    color: active ? Theme.text
         : (ma.containsMouse && clickable) ? (base === Theme.surface ? Theme.raised : "#5a5a56")
         : base
    Behavior on color { ColorAnimation { duration: Theme.fast } }

    readonly property color fg: !enabled ? Theme.dim : active ? Theme.onLight : Theme.text

    Row {
        id: content
        anchors.centerIn: parent
        spacing: root.label ? 6 : 0
        Icon {
            visible: root.icon !== ""
            text: root.icon
            size: root.iconSize
            color: root.fg
            anchors.verticalCenter: parent.verticalCenter
            Behavior on color { ColorAnimation { duration: Theme.fast } }
        }
        Text {
            visible: root.label !== ""
            text: root.label
            color: root.fg
            font.family: Theme.font
            font.pixelSize: root.fontSize
            font.weight: Font.Medium
            elide: Text.ElideRight
            width: Math.min(implicitWidth, root.width - 16 - (root.icon ? root.iconSize + 6 : 0))
            anchors.verticalCenter: parent.verticalCenter
            Behavior on color { ColorAnimation { duration: Theme.fast } }
        }
    }

    MouseArea {
        id: ma
        anchors.fill: parent
        enabled: root.clickable && root.enabled
        hoverEnabled: true
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: root.clicked()
    }
}
