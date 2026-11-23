// 음악 앱 탭 줄 (2026-11-24 마스터: 음악 알약을 누르면 탭으로 Spotify ↔ 유튜브 뮤직 전환)
// 고른 앱 창이 바 아래 팝업(작업공간 99 에서 꺼내 띄운 떠 있는 창)으로 보일 때만 그 바로 위에 뜬다.
//   탭을 누르면 music-app set <앱> → 재생 중인 앱은 일시정지, 팝업 창이 고른 앱으로 바뀜.
//   시험: MIKU_TABS_OPEN=1 이면 창이 없어도 보인다.
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

    // 지금 작업공간에 음악 앱이 떠 있는 창으로 있나 (창이 열리고 옮겨질 때마다 다시 읽음)
    property int winTick: 0
    readonly property bool appShown: {
        winTick;
        const ws = Hyprland.focusedMonitor && Hyprland.focusedMonitor.activeWorkspace
                   ? Hyprland.focusedMonitor.activeWorkspace.id : -1;
        const classes = MusicState.apps.map(a => a.cls);
        return Hyprland.toplevels.values.some(t => t.workspace && t.workspace.id === ws && t.lastIpcObject
                                                   && t.lastIpcObject.floating === true
                                                   && classes.includes(String(t.lastIpcObject["class"] || "").toLowerCase()));
    }
    readonly property bool open: appShown || Quickshell.env("MIKU_TABS_OPEN") === "1"
    onOpenChanged: MusicState.popupOpen = open
    Connections {
        target: Hyprland
        function onRawEvent(ev) {
            if (["openwindow", "closewindow", "movewindow", "movewindowv2", "changefloatingmode",
                 "workspacev2", "focusedmonv2"].includes(ev.name)) refresh.restart();
        }
    }
    Timer { id: refresh; interval: 120; onTriggered: { Hyprland.refreshToplevels(); win.winTick++ } }
    Component.onCompleted: refresh.restart()

    property real slide: open ? 1 : 0
    Behavior on slide { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
    visible: slide > 0.001
    color: "transparent"
    anchors { top: true; left: true }
    margins { top: 7; left: 8 }
    implicitWidth: 900            // 음악 창 너비와 같게 (music-app GEOM)
    implicitHeight: 32
    exclusionMode: ExclusionMode.Normal
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.namespace: "miku-musictabs"

    Pill {
        id: strip
        anchors.fill: parent
        hoverable: false
        opacity: win.slide
        Row {
            id: tabs
            anchors.fill: parent
            anchors.margins: 4
            spacing: 4
            Repeater {
                model: MusicState.apps
                Rectangle {
                    id: tab
                    required property var modelData
                    readonly property bool sel: MusicState.app === modelData.id
                    readonly property var pl: MusicState.playerOf(modelData.id)
                    readonly property bool playing: pl !== null && pl.isPlaying
                    width: (tabs.width - tabs.spacing * (MusicState.apps.length - 1)) / MusicState.apps.length
                    height: tabs.height
                    radius: height / 2
                    color: sel ? Theme.text : (th.hovered ? Theme.surface : "transparent")
                    Behavior on color { ColorAnimation { duration: Theme.fast } }
                    HoverHandler { id: th; cursorShape: tab.sel ? Qt.ArrowCursor : Qt.PointingHandCursor }
                    TapHandler { onTapped: MusicState.choose(tab.modelData.id) }
                    Row {
                        anchors.centerIn: parent
                        spacing: 7
                        // 재생 중 표시 점 (색은 상태에만: 초록)
                        Rectangle {
                            visible: tab.playing
                            anchors.verticalCenter: parent.verticalCenter
                            width: 6; height: 6; radius: 3
                            color: "#a6e3a1"
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: tab.modelData.label
                            color: tab.sel ? Theme.onLight : Theme.dim
                            font.family: Theme.font
                            font.pixelSize: 13
                            font.weight: tab.sel ? Font.ExtraBold : Font.DemiBold
                            Behavior on color { ColorAnimation { duration: Theme.fast } }
                        }
                    }
                }
            }
        }
    }
}
