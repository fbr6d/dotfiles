// 미디어 버튼: SVG 아이콘(icons/media-*.svg), hover 면 *-hover.svg
import QtQuick

Item {
    id: root
    property string name: "play"
    property bool big: false
    signal clicked()
    width: big ? 26 : 22
    height: 32
    Image {
        anchors.centerIn: parent
        readonly property int s: root.big ? 24 : 20
        width: s; height: s
        sourceSize.width: s * 2; sourceSize.height: s * 2
        source: Qt.resolvedUrl("icons/media-" + root.name + (ma.containsMouse ? "-hover" : "") + ".svg")
    }
    MouseArea { id: ma; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.clicked() }
}
