// 알림 한 장 (팝업과 제어센터 목록에서 같이 씀)
import Quickshell
import Quickshell.Services.Notifications
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    required property var notif
    property bool popup: false
    property int now: 0                        // 시각 글자를 새로 그리게 하는 값
    readonly property bool hovered: hover.hovered

    implicitHeight: body.implicitHeight + 24
    radius: 16
    color: popup ? Theme.bgDeep : (hover.hovered ? Theme.raised : Theme.surface)
    Behavior on color { ColorAnimation { duration: Theme.fast } }

    // 엠보스(안쪽 위 빛·아래 그늘)
    Rectangle { anchors { left: parent.left; right: parent.right; top: parent.top; leftMargin: 10; rightMargin: 10 }
                height: 1; color: Qt.rgba(250/255, 249/255, 245/255, 0.10); visible: root.popup }
    Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 10; rightMargin: 10 }
                height: 1; color: Qt.rgba(0, 0, 0, 0.55); visible: root.popup }

    HoverHandler { id: hover }
    TapHandler { onTapped: Notifs.activate(root.notif) }

    HoverHandler {
        onHoveredChanged: if (root.popup) {
            if (hovered) Notifs.hovered[root.notif.id] = true; else delete Notifs.hovered[root.notif.id];
        }
    }

    RowLayout {
        id: body
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
        spacing: 12

        Image {
            id: img
            Layout.preferredWidth: 40; Layout.preferredHeight: 40
            Layout.alignment: Qt.AlignTop
            source: Notifs.icon(root.notif)
            visible: status === Image.Ready
            sourceSize.width: 80; sourceSize.height: 80
            fillMode: Image.PreserveAspectCrop
            smooth: true
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text {
                    Layout.fillWidth: true
                    text: root.notif.summary || root.notif.appName
                    color: root.notif.urgency === NotificationUrgency.Critical ? Theme.red : Theme.text
                    font.family: Theme.font; font.pixelSize: 14; font.weight: Font.Bold
                    elide: Text.ElideRight
                }
                Text {
                    text: { root.now; return Notifs.ago(root.notif.id) }
                    color: Theme.dim
                    font.family: Theme.font; font.pixelSize: 12
                }
                Rectangle {
                    width: 22; height: 22; radius: 11
                    color: closeMa.containsMouse ? Theme.text : Theme.raised
                    Icon { anchors.centerIn: parent; text: "close"; size: 14; color: closeMa.containsMouse ? Theme.onLight : Theme.text }
                    MouseArea {
                        id: closeMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.notif.dismiss()
                    }
                }
            }
            Text {
                Layout.fillWidth: true
                visible: text !== ""
                text: root.notif.body
                textFormat: Text.StyledText
                color: Theme.muted
                font.family: Theme.font; font.pixelSize: 13
                wrapMode: Text.Wrap
                maximumLineCount: root.popup ? 4 : 3
                elide: Text.ElideRight
                linkColor: "#89b4fa"
                onLinkActivated: link => Qt.openUrlExternally(link)
            }
            Flow {
                Layout.fillWidth: true
                Layout.topMargin: 6
                spacing: 6
                visible: actRep.count > 0
                Repeater {
                    id: actRep
                    model: root.notif.actions.filter(a => a.identifier !== "default")
                    Tile {
                        required property var modelData
                        implicitHeight: 32
                        width: Math.max(80, implicitWidth)
                        implicitWidth: lbl.implicitWidth + 24
                        radius: 10
                        base: root.popup ? Theme.surface : Theme.raised
                        label: modelData.text
                        fontSize: 12
                        Text { id: lbl; visible: false; text: parent.modelData.text; font.family: Theme.font; font.pixelSize: 12 }
                        onClicked: { modelData.invoke(); root.notif.dismiss() }
                    }
                }
            }
        }
    }
}
