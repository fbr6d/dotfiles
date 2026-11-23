// 버튼·토글·상태 칸 하나.
//   active    켜짐 = 흰 알약
//   clickable false 면 상태만 보여 주는 칸(hover 없음)
//   enabled   false 면 흐린 글자, 눌리지 않음
//   badge     아이콘 대신 작은 네모 배지 안 글자(예: 미쿠 버튼 "01", 2026-11-23)
//   glyph     배지 안을 글자 대신 SVG 경로 그림으로 (glyphW×glyphH 좌표, 색은 fg 따라감). 원본 그림: icons/miku-01.svg
import QtQuick
import QtQuick.Shapes

Rectangle {
    id: root
    property string icon: ""
    property string label: ""
    property string badge: ""
    property string glyph: ""
    property real glyphW: 1
    property real glyphH: 1
    property int glyphSize: iconSize - 7         // 그림 높이(px)
    property color glyphColor: "transparent"     // 정하면 버튼 상태와 상관없이 이 색 (예: 미쿠 문신색)
    property bool badgeBorder: true              // 배지 네모 테두리
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
        Rectangle {                                  // 배지: 테두리 네모 + 굵은 글자 (어깨 문신 느낌)
            visible: root.badge !== ""
            width: (root.glyph ? glyphShape.width : badgeText.implicitWidth) + (root.badgeBorder ? 8 : 0)
            height: root.badgeBorder ? root.iconSize - 1 : glyphShape.height
            radius: 3
            color: "transparent"
            border.width: root.badgeBorder ? 1.5 : 0
            border.color: root.fg
            anchors.verticalCenter: parent.verticalCenter
            Behavior on border.color { ColorAnimation { duration: Theme.fast } }
            Shape {                                  // SVG 그림 (미쿠 문신 01)
                id: glyphShape
                visible: root.glyph !== ""
                readonly property real k: root.glyphSize / root.glyphH
                width: root.glyphW * k
                height: root.glyphH * k
                anchors.centerIn: parent
                layer.enabled: true
                layer.samples: 8                     // 작은 크기에서도 매끈하게
                ShapePath {
                    fillColor: root.glyphColor.a > 0 ? root.glyphColor : root.fg
                    fillRule: ShapePath.OddEvenFill
                    strokeWidth: -1
                    scale: Qt.size(glyphShape.k, glyphShape.k)
                    PathSvg { path: root.glyph }
                    Behavior on fillColor { ColorAnimation { duration: Theme.fast } }
                }
            }
            Text {
                id: badgeText
                visible: root.glyph === ""
                anchors.centerIn: parent
                text: root.badge
                color: root.fg
                font.family: Theme.font
                font.pixelSize: root.iconSize - 7
                font.weight: Font.Black
                Behavior on color { ColorAnimation { duration: Theme.fast } }
            }
        }
        Icon {
            visible: root.icon !== "" && root.badge === ""
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
            width: Math.min(implicitWidth, root.width - 16 - (root.badge ? root.iconSize + 22 : root.icon ? root.iconSize + 6 : 0))
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
