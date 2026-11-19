// 상단 바 (waybar 대체). 바 자체는 투명하고 알약들이 떠 있다.
//   왼쪽: 음악 시각화(cava) ─ hover 하면 Spotify 이전·재생·다음 서랍 ─ 가사
//   가운데: 작업공간 섬 (회색 점, 지금 작업공간은 흰 알약, 누르면 바탕화면 고르기)
//   오른쪽: 시계(누르면 제어센터) ─ hover 하면 왼쪽으로 트레이 서랍 ─ 그 왼쪽에 시스템 상태 알약
//           (평소엔 숨음. CPU 85° 이상·백업 중/실패·iCloud 인증 7일 이내면 나타남, hover 하면 자세히)
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Services.Mpris
import Quickshell.Services.SystemTray
import Quickshell.Widgets
import QtQuick

PanelWindow {
    id: bar
    property var controlCenter
    readonly property string home: Quickshell.env("HOME")
    readonly property string dir: home + "/.config/quickshell/miku-shell"
    function run(cmd) { Quickshell.execDetached(cmd) }

    color: "transparent"
    anchors { top: true; left: true; right: true }
    margins { top: 8; left: 8; right: 8 }
    implicitHeight: 32
    exclusiveZone: 32
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.namespace: "miku-bar"

    property bool trayMenuOpen: false
    readonly property int gap: 7   // 알약 사이 간격 (마스터 지정: 모든 알약 사이 7px)

    // ================= 왼쪽 =================
    readonly property var spotify: {
        for (const p of Mpris.players.values)
            if ((p.dbusName || "").toLowerCase().includes("spotify")) return p;
        return null;
    }
    readonly property bool hasTrack: spotify !== null && (spotify.trackTitle || "") !== ""

    Row {
        id: left
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        spacing: bar.gap

        // 시각화 + 미디어 서랍 (같은 hover 묶음)
        Item {
            id: mediaGroup
            width: cavaPill.width + drawer.width
            height: 32
            HoverHandler { id: mediaHover }

            Pill {
                id: cavaPill
                width: 101   // 알약 너비 고정 (막대 10개 시절 너비 그대로)
                onClicked: bar.run([bar.home + "/.local/bin/spotify-popup"])
                // 둥근 막대 20개(알약 크기는 10개 시절 그대로, 막대만 가늘게). 소리 없는 칸은 회색 점, 소리 나는 칸은 Catppuccin 색이 천천히 흐름
                Row {
                    id: cavaRow
                    anchors.centerIn: parent
                    height: 14
                    spacing: 1
                    Repeater {
                        model: cava.levels
                        Rectangle {
                            required property int modelData
                            required property int index
                            anchors.bottom: parent.bottom
                            width: (79 - 19 * 1) / 20   // 줄 너비 79px(알약 양옆 여백 11px), 막대 3px
                            radius: width / 2
                            height: 4 + Math.min(7, modelData) / 7 * 10
                            color: modelData === 0 ? "#5a5a56" : cava.ring[(index + 2 * modelData + cava.shift) % cava.ring.length]
                            Behavior on height { NumberAnimation { duration: 60 } }
                            Behavior on color { ColorAnimation { duration: 200 } }
                        }
                    }
                }
            }

            // 이전 · 재생 · 다음 (한 알약, hover 때만 미끄러져 나옴, 곡이 없으면 안 나옴)
            Item {
                id: drawer
                anchors.left: cavaPill.right
                height: 32
                readonly property real full: bar.gap + mediaPill.width
                width: (mediaHover.hovered || Quickshell.env("MIKU_BAR_OPEN") === "1") && bar.hasTrack ? full : 0
                clip: true
                Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
                Pill {
                    id: mediaPill
                    x: bar.gap
                    hoverable: false
                    width: mrow.implicitWidth + 20
                    Row {
                        id: mrow
                        anchors.centerIn: parent
                        spacing: 4
                        MediaButton { name: "prev"; onClicked: if (bar.spotify) bar.spotify.previous() }
                        MediaButton {
                            name: bar.spotify && bar.spotify.isPlaying ? "pause" : "play"
                            big: true
                            onClicked: if (bar.spotify) bar.spotify.togglePlaying()
                        }
                        MediaButton { name: "next"; onClicked: if (bar.spotify) bar.spotify.next() }
                    }
                }
            }
        }

        // 가사
        Pill {
            id: lyricPill
            visible: lyrics.show
            readonly property real maxW: Math.max(120, island.x - left.x - mediaGroup.width - bar.gap * 2 - 14)
            width: Math.min(maxW, lyricRow.implicitWidth + 32)
            Behavior on width { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }
            onClicked: bar.run([bar.home + "/.local/bin/spotify-popup"])
            Item {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                clip: true
                Row {
                    id: lyricRow
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 12
                    // 제목 · 아티스트 (가사가 있으면 작고 흐리게, 170px 넘으면 흐름)
                    Item {
                        visible: lyrics.hasLyrics
                        width: Math.min(170, infoText.implicitWidth)
                        height: 20
                        anchors.verticalCenter: parent.verticalCenter
                        clip: true
                        Row {
                            id: marquee
                            spacing: 24
                            anchors.verticalCenter: parent.verticalCenter
                            readonly property bool scroll: infoText.implicitWidth > 170
                            // 흐름이 멈추거나 제목이 바뀌면 처음 위치로 (안 하면 긴 제목→짧은 제목 때 칸 밖에 멈춰 안 보임)
                            property bool resetting: false
                            function rewind() { resetting = true; x = 0; resetting = false }
                            onScrollChanged: rewind()
                            Text { id: infoText; text: lyrics.info; color: Theme.dim; font.family: Theme.font; font.pixelSize: 12; font.weight: Font.DemiBold
                                   onTextChanged: marquee.rewind() }
                            Text { visible: marquee.scroll; text: lyrics.info; color: Theme.dim; font.family: Theme.font; font.pixelSize: 12; font.weight: Font.DemiBold }
                            NumberAnimation on x {
                                running: marquee.scroll && lyricPill.visible && !marquee.resetting
                                loops: Animation.Infinite
                                from: 0
                                to: -(infoText.implicitWidth + 24)
                                duration: (infoText.implicitWidth + 24) * 25
                            }
                        }
                    }
                    // 지금 가사 줄: 바뀔 때 살짝 흐려졌다가 아래에서 올라오며 나타남
                    Text {
                        id: lineText
                        readonly property string target: lyrics.hasLyrics ? lyrics.line : lyrics.info
                        property real lift: 0
                        text: target
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: 15
                        font.weight: Font.ExtraBold
                        font.letterSpacing: 0.6
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.verticalCenterOffset: lift
                        onTargetChanged: swap.restart()
                        SequentialAnimation {
                            id: swap
                            NumberAnimation { target: lineText; property: "opacity"; to: 0; duration: 90 }
                            ScriptAction { script: { lineText.text = lineText.target; lineText.lift = 6 } }
                            ParallelAnimation {
                                NumberAnimation { target: lineText; property: "opacity"; to: 1; duration: 180; easing.type: Easing.OutCubic }
                                NumberAnimation { target: lineText; property: "lift"; to: 0; duration: 180; easing.type: Easing.OutCubic }
                            }
                        }
                    }
                }
            }
        }
    }

    // ================= 가운데: 작업공간 섬 =================
    Pill {
        id: island
        anchors.centerIn: parent
        // 작업공간이 하나일 때 시계 알약과 같은 너비 (waybar 때와 같음)
        width: dots.implicitWidth + clock.width - 24
        Behavior on width { NumberAnimation { duration: Theme.base; easing.type: Easing.OutCubic } }
        onClicked: bar.run([bar.home + "/.local/bin/popup-toggle", "title:Waytrogen - Iced", "waytrogen"])
        readonly property int active: Hyprland.focusedMonitor && Hyprland.focusedMonitor.activeWorkspace
                                      ? Hyprland.focusedMonitor.activeWorkspace.id : -1
        Row {
            id: dots
            anchors.centerIn: parent
            spacing: 8
            Repeater {
                // 99 는 숨긴 팝업(Spotify 등)을 두는 곳이라 빼고, 특수 작업공간(음수)도 뺀다
                model: Hyprland.workspaces.values.filter(w => w.id > 0 && w.id < 99).sort((a, b) => a.id - b.id)
                Rectangle {
                    required property var modelData
                    readonly property bool on: modelData.id === island.active
                    width: on ? 24 : 8
                    height: 8
                    radius: 4
                    color: on ? Theme.text : "#5a5a56"
                    Behavior on width { NumberAnimation { duration: Theme.base; easing.type: Easing.OutCubic } }
                    Behavior on color { ColorAnimation { duration: Theme.base } }
                }
            }
        }
    }

    // ================= 오른쪽: 트레이 서랍 + 시계 =================
    Item {
        id: right
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        width: statusDrawer.width + trayDrawer.width + clock.width
        height: 32
        HoverHandler { id: rightHover }

        // 시스템 상태 알약 (scripts/sys-status, 15초마다)
        Item {
            id: statusDrawer
            anchors.right: trayDrawer.left
            height: 32
            readonly property bool alert: sys.alerts.length > 0
            readonly property bool open: rightHover.hovered || Quickshell.env("MIKU_BAR_OPEN") === "1"
            width: (alert || open) && sys.detail !== "" ? statusPill.width + bar.gap : 0
            clip: true
            Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
            Pill {
                id: statusPill
                hoverable: false
                anchors.right: parent.right
                anchors.rightMargin: bar.gap
                width: statusRow.implicitWidth + 28
                Row {
                    id: statusRow
                    anchors.centerIn: parent
                    spacing: 8
                    Rectangle {
                        visible: statusDrawer.alert
                        anchors.verticalCenter: parent.verticalCenter
                        width: 8; height: 8; radius: 4
                        readonly property string lv: sys.alerts.some(a => a.level === "red") ? "red"
                                                   : sys.alerts.some(a => a.level === "yellow") ? "yellow" : "info"
                        color: lv === "red" ? "#f38ba8" : lv === "yellow" ? "#f9e2af" : "#94e2d5"
                        SequentialAnimation on opacity {
                            running: statusDrawer.alert; loops: Animation.Infinite
                            NumberAnimation { to: 0.35; duration: 900; easing.type: Easing.InOutSine }
                            NumberAnimation { to: 1; duration: 900; easing.type: Easing.InOutSine }
                        }
                    }
                    // 경고만 보일 때: 경고 글자 한 줄
                    Text {
                        visible: !(statusDrawer.open || !statusDrawer.alert)
                        anchors.verticalCenter: parent.verticalCenter
                        text: sys.alerts.map(a => a.text).join(" · ")
                        color: Theme.text
                        font.family: Theme.font; font.pixelSize: 13; font.weight: Font.Bold
                        font.features: { "tnum": 1 }
                    }
                    // 펼쳤을 때: 온도는 단계별 색 (초록 정상 · 노랑 따뜻 · 주황 뜨거움 · 빨강 위험), 나머지는 흰 글자
                    Repeater {
                        model: statusDrawer.open || !statusDrawer.alert ? sys.parts : []
                        Row {
                            required property var modelData
                            required property int index
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 0
                            Text {
                                visible: index > 0
                                text: " · "
                                color: Theme.dim
                                font.family: Theme.font; font.pixelSize: 13; font.weight: Font.Bold
                            }
                            Text {
                                text: modelData.text
                                readonly property string lv: modelData.level || ""
                                color: lv === "crit" ? "#f38ba8" : lv === "hot" ? "#fab387" : lv === "warm" ? "#f9e2af" : lv === "ok" ? "#a6e3a1" : Theme.text
                                Behavior on color { ColorAnimation { duration: Theme.base } }
                                font.family: Theme.font; font.pixelSize: 13; font.weight: Font.Bold
                                font.features: { "tnum": 1 }
                            }
                        }
                    }
                }
            }
        }

        Item {
            id: trayDrawer
            anchors.right: clock.left
            height: 32
            readonly property bool any: SystemTray.items.values.length > 0
            // 트레이 메뉴가 열려 있는 동안에는 마우스가 메뉴로 옮겨 가도 서랍을 닫지 않는다
            width: (rightHover.hovered || bar.trayMenuOpen || Quickshell.env("MIKU_BAR_OPEN") === "1") && any ? trayPill.width + bar.gap : 0
            clip: true
            Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
            Pill {
                id: trayPill
                hoverable: false
                anchors.right: parent.right
                anchors.rightMargin: bar.gap
                width: trayRow.implicitWidth + 24
                Row {
                    id: trayRow
                    anchors.centerIn: parent
                    spacing: 8
                    Repeater {
                        model: SystemTray.items
                        IconImage {
                            id: ti
                            required property var modelData
                            source: modelData.icon
                            implicitSize: 16
                            // 우클릭 메뉴: 아이콘 바로 아래에 붙여 연다 (열림/닫힘을 알아야 서랍을 붙잡아 둘 수 있어서 display() 대신 씀)
                            QsMenuAnchor {
                                id: menuAnchor
                                menu: ti.modelData.menu
                                anchor.item: ti
                                anchor.edges: Edges.Bottom
                                anchor.gravity: Edges.Bottom
                                anchor.margins.top: 10
                                onOpened: bar.trayMenuOpen = true
                                onClosed: bar.trayMenuOpen = false
                            }
                            MouseArea {
                                anchors.fill: parent
                                acceptedButtons: Qt.LeftButton | Qt.RightButton
                                cursorShape: Qt.PointingHandCursor
                                onClicked: mouse => {
                                    const m = ti.modelData;
                                    if (mouse.button === Qt.LeftButton && !m.onlyMenu) { m.activate(); return; }
                                    if (m.hasMenu) menuAnchor.open();
                                }
                            }
                        }
                    }
                }
            }
        }

        Pill {
            id: clock
            anchors.right: parent.right
            width: clockText.implicitWidth + 26
            onClicked: if (bar.controlCenter) bar.controlCenter.toggle()
            Text {
                id: clockText
                anchors.centerIn: parent
                text: Qt.formatTime(clockTimer.now, "HH:mm")
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: 18
                font.weight: Font.Black
                font.letterSpacing: 0.6
                font.features: { "tnum": 1 }
                // Pretendard 는 900 이 가장 굵다. 같은 색 외곽선 한 겹으로 waybar 때처럼 더 두껍게
                style: Text.Outline
                styleColor: Qt.rgba(250 / 255, 249 / 255, 245 / 255, 0.55)
            }
            Timer {
                id: clockTimer
                property date now: new Date()
                interval: 1000
                repeat: true
                running: true
                onTriggered: now = new Date()
            }
        }
    }

    // ================= 데이터 =================
    // cava 막대 (설정 ~/.config/cava/miku-shell.conf: 20칸, 0~7)
    QtObject {
        id: cava
        property var levels: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        property int shift: 0
        readonly property var ring: ["#f5e0dc", "#f2cdcd", "#f5c2e7", "#cba6f7", "#f38ba8", "#eba0ac", "#fab387",
                                     "#f9e2af", "#a6e3a1", "#94e2d5", "#89dceb", "#74c7ec", "#89b4fa", "#b4befe"]
    }
    Timer { interval: 400; repeat: true; running: true; onTriggered: cava.shift++ }
    Process {
        running: true
        command: ["cava", "-p", bar.home + "/.config/cava/miku-shell.conf"]
        stdout: SplitParser {
            onRead: line => {
                const v = line.split(";").filter(x => x !== "").map(x => parseInt(x));
                if (v.length) cava.levels = v;
            }
        }
    }

    // 시스템 상태 (scripts/sys-status: 온도·iCloud 백업·인증 남은 날)
    QtObject {
        id: sys
        property var alerts: []
        property string detail: ""
        property var parts: []
    }
    Process {
        id: sysProc
        command: [bar.dir + "/scripts/sys-status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try { const j = JSON.parse(text); sys.alerts = j.alerts || []; sys.detail = j.detail || ""; sys.parts = j.parts || [] } catch (e) {}
            }
        }
    }
    Timer { interval: 15000; repeat: true; running: true; triggeredOnStart: true; onTriggered: if (!sysProc.running) sysProc.running = true }

    // 가사 (scripts/lyrics-feed. 시험할 때는 MIKU_LYRICS_CMD 로 바꿀 수 있음)
    QtObject {
        id: lyrics
        property bool show: false
        property string info: ""
        property string line: ""
        property bool hasLyrics: false
    }
    Process {
        running: true
        command: Quickshell.env("MIKU_LYRICS_CMD") ? ["sh", "-c", Quickshell.env("MIKU_LYRICS_CMD")]
                                                   : [bar.dir + "/scripts/lyrics-feed"]
        stdout: SplitParser {
            onRead: line => {
                try {
                    const o = JSON.parse(line);
                    lyrics.show = o.show;
                    lyrics.info = o.info;
                    lyrics.line = o.line;
                    lyrics.hasLyrics = o.lyrics;
                } catch (e) {}
            }
        }
    }
}
