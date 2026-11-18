// 화면 오른쪽 위 알림 팝업 (최대 4장, 새 알림이 위)
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import QtQuick

PanelWindow {
    id: win
    readonly property string wantOutput: Quickshell.env("MIKU_CC_OUTPUT") || ""
    screen: {
        const name = wantOutput || (Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "");
        for (const s of Quickshell.screens) if (s.name === name) return s;
        return Quickshell.screens[0];
    }
    visible: Notifs.popups.length > 0 && !Notifs.ccOpen
    color: "transparent"
    anchors { top: true; right: true }
    margins { top: 8; right: 8 }
    implicitWidth: 380
    implicitHeight: Math.max(1, stack.implicitHeight)
    exclusionMode: ExclusionMode.Normal
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "miku-notifications"

    Timer { id: tick; property int n: 0; interval: 30000; repeat: true; running: win.visible; onTriggered: n++ }

    Column {
        id: stack
        width: parent.width
        spacing: 8
        Repeater {
            model: Notifs.popups
            NotificationCard {
                required property var modelData
                notif: modelData
                popup: true
                now: tick.n
                width: stack.width
                opacity: 0
                Component.onCompleted: opacity = 1
                Behavior on opacity { NumberAnimation { duration: Theme.base } }
            }
        }
    }
}
