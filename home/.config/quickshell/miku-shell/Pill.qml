// 떠 있는 알약: 높이 32, 바탕 bg-deep, 안쪽 1px 엠보스(위 빛·아래 그늘). hover 면 surface
import QtQuick

Item {
    id: root
    property bool hoverable: true
    property alias hovered: hh.hovered
    property real leftRadius: 16
    property real rightRadius: 16
    default property alias content: inner.data
    signal clicked()
    signal rightClicked()

    implicitHeight: 32
    height: 32
    readonly property color fill: hoverable && hh.hovered ? Theme.surface : Theme.bgDeep

    HoverHandler { id: hh; cursorShape: root.hoverable ? Qt.PointingHandCursor : Qt.ArrowCursor }
    TapHandler { acceptedButtons: Qt.LeftButton; onTapped: root.clicked() }
    TapHandler { acceptedButtons: Qt.RightButton; onTapped: root.rightClicked() }

    // 바깥 = 위쪽 빛, 그 안 1px 아래 = 아래쪽 그늘, 그 안 = 바탕
    Rectangle {
        anchors.fill: parent
        topLeftRadius: root.leftRadius; bottomLeftRadius: root.leftRadius
        topRightRadius: root.rightRadius; bottomRightRadius: root.rightRadius
        color: Qt.tint(root.fill, Qt.rgba(250 / 255, 249 / 255, 245 / 255, 0.10))
        Rectangle {
            anchors.fill: parent; anchors.topMargin: 1
            topLeftRadius: root.leftRadius; bottomLeftRadius: root.leftRadius
            topRightRadius: root.rightRadius; bottomRightRadius: root.rightRadius
            color: Qt.tint(root.fill, Qt.rgba(0, 0, 0, 0.55))
            Rectangle {
                anchors.fill: parent; anchors.bottomMargin: 1
                topLeftRadius: root.leftRadius; bottomLeftRadius: root.leftRadius
                topRightRadius: root.rightRadius; bottomRightRadius: root.rightRadius
                color: root.fill
                Behavior on color { ColorAnimation { duration: Theme.fast } }
            }
        }
    }
    Item { id: inner; anchors.fill: parent }
}
