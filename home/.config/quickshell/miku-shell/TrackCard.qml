// 곡 전환 카드: 고른 음악 앱(MusicState, Spotify 또는 유튜브 뮤직) 곡이 바뀌면 왼쪽 위(음악 알약 바로 아래)에 카드가 스르륵 내려왔다가
// 4초 뒤 올라가며 사라진다. 마우스를 올려 두면 사라지지 않고 기다린다.
//   시험: qs -c miku-shell ipc call track pop
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Services.Mpris
import Quickshell.Widgets
import QtQuick

PanelWindow {
    id: win
    readonly property string wantOutput: Quickshell.env("MIKU_CC_OUTPUT") || ""
    screen: {
        const name = wantOutput || (Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "");
        for (const s of Quickshell.screens) if (s.name === name) return s;
        return Quickshell.screens[0];
    }

    readonly property var player: MusicState.player
    readonly property string key: player ? (player.trackTitle || "") + "\u0001" + (player.trackArtist || "") : ""
    property string lastKey: ""
    property bool armed: false        // 셸이 막 켜졌을 때는 띄우지 않는다
    property bool shown: false
    property real slide: shown ? 1 : 0
    Behavior on slide { NumberAnimation { duration: 320; easing.type: Easing.OutCubic } }

    function pop() {
        if (!player || (player.trackTitle || "") === "") return;
        if (MusicState.popupOpen) return;      // 음악 창과 탭 줄이 떠 있으면 카드가 탭을 가리지 않게
        shown = true;
        hideTimer.restart();
    }
    onKeyChanged: {
        if (key === "" || key === lastKey) return;
        lastKey = key;
        if (armed) pop();
    }
    Timer { interval: 3000; running: true; onTriggered: win.armed = true }
    Timer {
        id: hideTimer
        interval: 4000
        onTriggered: if (hover.hovered) restart(); else win.shown = false
    }

    visible: slide > 0.001
    color: "transparent"
    anchors { top: true; left: true }
    margins { top: 7; left: 8 }
    implicitWidth: 320
    implicitHeight: 72
    exclusionMode: ExclusionMode.Normal
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "miku-trackcard"

    Rectangle {
        id: card
        width: parent.width
        height: 72
        y: (win.slide - 1) * 14
        opacity: win.slide
        radius: 16
        color: Theme.bgDeep
        // 엠보스(안쪽 위 빛·아래 그늘) — 알림 카드와 같은 방식
        Rectangle { anchors { left: parent.left; right: parent.right; top: parent.top; leftMargin: 10; rightMargin: 10 }
                    height: 1; color: Qt.rgba(250/255, 249/255, 245/255, 0.10) }
        Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 10; rightMargin: 10 }
                    height: 1; color: Qt.rgba(0, 0, 0, 0.55) }

        HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
        TapHandler { onTapped: MusicState.toggle() }

        ClippingRectangle {
            id: art
            x: 8; y: 8
            width: 56; height: 56
            radius: 10
            color: Theme.surface
            Image {
                anchors.fill: parent
                source: win.player ? (win.player.trackArtUrl || "") : ""
                sourceSize.width: 112; sourceSize.height: 112
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                smooth: true
            }
        }

        Column {
            anchors { left: art.right; leftMargin: 12; right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
            spacing: 3
            Text {
                width: parent.width
                text: win.player ? (win.player.trackTitle || "") : ""
                color: Theme.text
                font.family: Theme.font; font.pixelSize: 15; font.weight: Font.ExtraBold
                elide: Text.ElideRight
            }
            Text {
                width: parent.width
                text: win.player ? (win.player.trackArtist || "") : ""
                color: Theme.dim
                font.family: Theme.font; font.pixelSize: 12; font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
        }
    }

    IpcHandler {
        target: "track"
        function pop(): void { win.pop() }
    }
}
