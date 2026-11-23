// 제어센터 (swaync 제어센터 대체)
//   일정: iCloud 캘린더 오늘·내일 (읽기 전용, scripts/cal-feed, 열 때 1분 넘었으면 + 10분마다)
//   상태 줄(Wi-Fi 1/4 · 유선 1/4 · 블루투스 1/2, 표시 전용)
//   기기 연결 · 방해 금지 · 미쿠(마스코트 보이기/숨기기)
//   볼륨 · (화면 밝기: 노트북처럼 밝기 장치가 있을 때만)
//   ── 조명 ── 머리글(전구 고르기 칩: 플로어등·제도등), 켜기/끄기 · 따뜻하게 · 집중 · 색 선택(1/4씩), 색 팔레트, 밝기
//   잠금 · 재부팅 · 끄기 · (배터리: 배터리가 있을 때만)
//   알림 목록 (모두 지우기)
// 열고 닫기: qs -c miku-shell ipc call cc toggle
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Services.Pipewire
import Quickshell.Services.UPower
import QtQuick
import QtQuick.Layouts

PanelWindow {
    id: panel

    readonly property string home: Quickshell.env("HOME")
    readonly property string wiz: home + "/.local/bin/wiz-light"
    property bool open: false

    // 시험용: MIKU_CC_OUTPUT 이 있으면 그 출력에, 없으면 지금 포커스된 모니터에
    readonly property string wantOutput: Quickshell.env("MIKU_CC_OUTPUT") || ""
    screen: {
        const name = wantOutput || (Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "");
        for (const s of Quickshell.screens) if (s.name === name) return s;
        return Quickshell.screens[0];
    }

    onOpenChanged: { Notifs.ccOpen = open; if (open) blProc.running = true; else outOpen = false }
    property bool outOpen: false   // 소리 출력 드롭다운 펼침
    function show() { open = true; refreshAll() }
    function hide() { open = false }
    function toggle() { open ? hide() : show() }
    function run(cmd) { Quickshell.execDetached(cmd) }

    visible: open || fadeOut.running
    color: "transparent"
    anchors { top: true; right: true }
    margins { top: 8; right: 8 }
    implicitWidth: 380
    // 창 높이는 화면 높이로 고정하고 입력은 box 영역만 받는다.
    // (내용 높이를 따라가면 팔레트가 펼쳐지는 동안 매 프레임 창 크기가 바뀌어 애니메이션이 끊긴다)
    implicitHeight: (screen ? screen.height : 1080) - 16
    mask: Region { item: box }
    exclusionMode: ExclusionMode.Normal
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.namespace: "miku-cc"
    WlrLayershell.keyboardFocus: open ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None

    // 바깥을 누르면 닫힘
    HyprlandFocusGrab {
        windows: [panel]
        active: panel.open
        onCleared: if (Quickshell.env("MIKU_CC_OPEN") !== "1") panel.hide()   // 시험 띄우기 중에는 안 닫음
    }

    // ---------------- 상태 읽기 ----------------
    property var net: ({ wifi: { on: false, icon: "wifi", label: "…" },
                         wired: { on: false, icon: "lan", label: "…" },
                         bt: { on: false, icon: "bluetooth", label: "…" } })
    // 전구 두 개(floor 플로어등 · desk 제도등). lamp = 지금 조작할 대상
    property var lights: ({})
    property string lamp: "floor"
    readonly property var lampNames: ({ floor: "플로어등", desk: "제도등" })
    function lampTargets() { return [lamp] }
    readonly property var light: {
        const ps = lampTargets().map(k => lights[k]).filter(x => x && x.state !== undefined);
        if (!ps.length) return ({});
        const lit = ps.filter(x => x.state);
        return Object.assign({}, lit[0] || ps[0], { state: lit.length > 0 });
    }
    onLightChanged: {
        if (!bright.pressed && light.dimming !== undefined) bright.value = (light.dimming - 10) / 90;
        if (light.state === false) colorOpen = false;
    }
    // 머리글 칩의 작은 점: 켜진 전구의 빛 색 (꺼져 있으면 숨김)
    function lampDot(p) {
        if (!p || !p.state) return "transparent";
        if (p.r !== undefined && !p.temp) return Qt.rgba(p.r / 255, p.g / 255, p.b / 255, 1);
        return p.temp <= 3500 ? "#f9e2af" : Theme.text;
    }
    readonly property bool lightKnown: light.state !== undefined
    readonly property bool lightOn: light.state === true
    property bool colorOpen: false

    function refreshAll() { netProc.running = true; refreshLight(); refreshCal(); tick.n++ }
    function refreshLight() { if (!lightProc.running) lightProc.running = true }
    function lightAction(args) { run([wiz, "--lamp", lamp].concat(args)); lightSoon.restart() }

    Process {
        id: netProc
        command: [panel.home + "/.config/quickshell/miku-shell/scripts/cc-status"]
        stdout: StdioCollector { onStreamFinished: { try { panel.net = JSON.parse(text) } catch (e) {} } }
    }
    Process {
        id: lightProc
        command: [panel.wiz, "status-all-json"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const all = JSON.parse(text), out = {};
                    for (const k in all) out[k] = all[k].error ? ({}) : all[k];
                    panel.lights = out;
                } catch (e) { panel.lights = ({}) }
            }
        }
    }
    // ---------------- 일정 (iCloud 캘린더 오늘·내일, 읽기 전용) ----------------
    property var cal: ({})
    property double calAt: 0
    function refreshCal() {
        if (!calProc.running && Date.now() - calAt > 60000) calProc.running = true
    }
    Process {
        id: calProc
        command: [panel.home + "/.config/quickshell/miku-shell/scripts/cal-feed"]
        stdout: StdioCollector {
            onStreamFinished: {
                try { panel.cal = JSON.parse(text); panel.calAt = Date.now() } catch (e) {}
            }
        }
    }
    Timer { interval: 600000; repeat: true; running: true; triggeredOnStart: true; onTriggered: { panel.calAt = 0; panel.refreshCal() } }

    // 닫혀 있을 때도 가끔 읽어 둬서 열자마자 바로 보이게
    Timer { interval: panel.open ? 3000 : 10000; repeat: true; running: true; triggeredOnStart: true; onTriggered: netProc.running = true }
    Timer { id: tick; property int n: 0; interval: 30000; repeat: true; running: panel.open; onTriggered: n++ }
    Timer { interval: panel.open ? 2000 : 10000; repeat: true; running: true; triggeredOnStart: true; onTriggered: panel.refreshLight() }
    Timer { id: lightSoon; interval: 350; onTriggered: panel.refreshLight() }

    function lightStatus() {
        if (!lightKnown) return "연결 안 됨";
        if (!lightOn) return "꺼짐";
        const parts = ["켜짐", "밝기 " + light.dimming + "%"];
        if (light.temp) parts.push(light.temp <= 3000 ? "따뜻한 빛" : light.temp >= 4500 ? "흰 빛" : "중간 빛");
        else if (light.r !== undefined) parts.push("색");
        return parts.join(" · ");
    }
    readonly property string lightHex: light.r !== undefined && !light.temp
        ? Qt.rgba(light.r / 255, light.g / 255, light.b / 255, 1) : "transparent"

    // 화면 밝기 (brightnessctl -m: 장치,종류,현재,퍼센트,최대). 장치가 없으면 칸을 숨김
    property bool hasBacklight: false
    property real backlight: 0
    Process {
        id: blProc
        command: ["sh", "-c", "ls /sys/class/backlight 2>/dev/null | grep -q . && brightnessctl -m -c backlight info"]
        stdout: StdioCollector {
            onStreamFinished: {
                const f = text.trim().split(",");
                panel.hasBacklight = f.length >= 4;
                if (panel.hasBacklight && !blCard.pressed) panel.backlight = parseInt(f[3]) / 100;
            }
        }
    }

    // 배터리 (UPower). 데스크톱처럼 배터리가 없으면 칸을 숨김
    readonly property var battery: UPower.displayDevice
    readonly property bool hasBattery: battery && battery.ready && battery.isLaptopBattery
    function batteryText() {
        const p = Math.round(battery.percentage * 100);
        const st = battery.state === UPowerDeviceState.Charging ? "충전 중"
                 : battery.state === UPowerDeviceState.FullyCharged ? "충전 완료"
                 : battery.state === UPowerDeviceState.PendingCharge ? "충전 안 함" : "사용 중";
        return "배터리 " + p + "% · " + st;
    }

    // 볼륨 (PipeWire 기본 출력)
    readonly property var sink: Pipewire.defaultAudioSink
    PwObjectTracker { objects: [panel.sink] }

    // 출력 장치 고르기 (2026-11-22 마스터 요청). 진짜 출력 장치만: 앱 소리 줄기·Sunshine 가상 출력 제외
    readonly property var sinks: Pipewire.nodes.values.filter(n =>
        n.isSink && !n.isStream && n.audio && !(n.name || "").startsWith("sink-sunshine"))
    function sinkLabel(n) {
        const d = (n.description || n.nickname || n.name || "?").replace(/_/g, " ");
        let suf = "";
        if (/Digital Stereo \(IEC958\)/.test(d)) suf = " 광출력";
        else if (/HDMI|DisplayPort/i.test(d) && /Digital/.test(d)) suf = " HDMI";
        if (/USB-C to 3\.5mm/i.test(d)) return "USB-C 이어폰";
        if (/Ryzen HD Audio/i.test(d)) return "LG 사운드바" + suf;   // 2026-11-23 마스터: 본체 라인 출력에 LG 사운드바(LAS260B)가 연결됨 (예전 "본체", 백업 .bak-soundbar-label)
        if (/Navi|Radeon|HDMI\/DP/i.test(d)) return "모니터" + suf;
        return d.replace(/ (Analog|Digital) Stereo.*$/, "");
    }

    // ---------------- 화면 ----------------
    Rectangle {
        id: box
        width: parent.width
        implicitHeight: col.implicitHeight + 24
        radius: 16
        color: Theme.bg
        border.color: Theme.surface
        border.width: 1
        focus: panel.open
        Keys.onEscapePressed: panel.hide()

        opacity: panel.open ? 1 : 0
        transform: Translate { y: panel.open ? 0 : -8; Behavior on y { NumberAnimation { duration: Theme.base; easing.type: Easing.OutCubic } } }
        Behavior on opacity { NumberAnimation { id: fadeOut; duration: Theme.base; easing.type: Easing.OutCubic } }

        ColumnLayout {
            id: col
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
            spacing: 6

            // ── 일정 (오늘 · 내일) ──
            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 4; Layout.rightMargin: 4; Layout.topMargin: 2
                spacing: 8
                Text {
                    visible: !!panel.cal.error
                    text: panel.cal.error || ""
                    color: Theme.dim; font.family: Theme.font; font.pixelSize: 12
                }
                Text {
                    visible: !panel.cal.error && !panel.cal.days
                    text: "일정 불러오는 중…"
                    color: Theme.dim; font.family: Theme.font; font.pixelSize: 12
                }
                Repeater {
                    model: panel.cal.days || []
                    ColumnLayout {
                        id: day
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 3
                        RowLayout {
                            spacing: 6
                            Text { text: day.modelData.label; color: Theme.text; font.family: Theme.font; font.pixelSize: 13; font.weight: Font.Bold }
                            Text { text: day.modelData.date; color: Theme.dim; font.family: Theme.font; font.pixelSize: 12 }
                        }
                        Text {
                            visible: day.modelData.events.length === 0
                            text: day.modelData.label === "오늘" ? "오늘은 일정이 없어요" : "내일은 일정이 없어요"
                            color: Theme.dim; font.family: Theme.font; font.pixelSize: 12
                        }
                        Repeater {
                            model: day.modelData.events
                            RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: 10
                                Text {
                                    Layout.preferredWidth: 78
                                    text: modelData.when
                                    color: modelData.past ? Theme.dim : Theme.muted; opacity: modelData.past ? 0.7 : 1; font.family: Theme.font; font.pixelSize: 12; font.weight: Font.DemiBold
                                    font.features: { "tnum": 1 }
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.title
                                    color: modelData.past ? Theme.dim : Theme.text;   // 이미 끝난 일정은 흐리게 font.family: Theme.font; font.pixelSize: 13
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }
                }
            }
            Rectangle { Layout.fillWidth: true; Layout.topMargin: 2; Layout.bottomMargin: 2; implicitHeight: 1; color: Theme.raised }

            // 상태 줄: 누를 수 없는 표시 칸
            RowLayout {
                spacing: 6
                // 아래 조명 줄과 같은 1/4 칸 (두 칸째까지 세로로 맞음)
                readonly property real q: (col.width - 18) / 4
                Tile { Layout.preferredWidth: parent.q; clickable: false; active: panel.net.wifi.on; icon: panel.net.wifi.icon; label: panel.net.wifi.label }
                Tile { Layout.preferredWidth: parent.q; clickable: false; active: panel.net.wired.on; icon: panel.net.wired.icon; label: panel.net.wired.label }
                Tile { Layout.fillWidth: true; clickable: false; active: panel.net.bt.on; icon: panel.net.bt.icon; label: panel.net.bt.label }
            }

            RowLayout {
                spacing: 6
                Tile {
                    Layout.fillWidth: true; Layout.preferredWidth: 1
                    icon: "devices"; label: "기기 연결"; fontSize: 13
                    onClicked: { panel.hide(); panel.run([panel.home + "/.local/bin/device-settings"]) }
                }
                Tile {
                    Layout.fillWidth: true; Layout.preferredWidth: 1
                    icon: "do_not_disturb_on"; label: "방해 금지"; fontSize: 13
                    active: Notifs.dnd
                    onClicked: Notifs.dnd = !Notifs.dnd
                }
                Tile {
                    Layout.fillWidth: true; Layout.preferredWidth: 1
                    badge: "01"; label: "미쿠"; fontSize: 13
                    glyph: "M13,0 H31 A13,13 0 0 1 44,13 V47 A13,13 0 0 1 31,60 H13 A13,13 0 0 1 0,47 V13 A13,13 0 0 1 13,0 Z M18,13 H26 A5,5 0 0 1 31,18 V42 A5,5 0 0 1 26,47 H18 A5,5 0 0 1 13,42 V18 A5,5 0 0 1 18,13 Z M20,0 H24 V13 H20 Z M20,47 H24 V60 H20 Z M58,0 H71 V60 H58 V16 L47,24 V11 Z"; glyphW: 71; glyphH: 60   // 미쿠 문신 01 (icons/miku-01.svg)
                    glyphSize: 17; glyphColor: MascotState.shown ? "#E04A5F" : "transparent"; badgeBorder: false   // 테두리 없이, 크게, 켜지면 문신색 / 꺼지면 흰색(fg)
                    active: MascotState.shown
                    onClicked: MascotState.shown = !MascotState.shown
                }
            }

            SliderCard {
                Layout.fillWidth: true
                icon: !panel.sink || panel.sink.audio.muted ? "volume_off" : "volume_up"
                iconClickable: true
                value: panel.sink ? Math.min(1, panel.sink.audio.volume) : 0
                onMoved: v => { if (panel.sink) panel.sink.audio.volume = v }
                onIconClicked: if (panel.sink) panel.sink.audio.muted = !panel.sink.audio.muted
            }

            // ── 소리 출력 장치 드롭다운 (2026-11-22 마스터: 칩 대신 드롭다운) ──
            //   버튼 = 지금 출력 장치, 누르면 아래로 목록이 펼쳐지고 고르면 접힘
            Rectangle {
                id: outBtn
                Layout.fillWidth: true
                implicitHeight: 32; radius: 16
                color: outBtnMa.containsMouse || panel.outOpen ? Theme.raised : Theme.surface
                Behavior on color { ColorAnimation { duration: Theme.fast } }
                Icon {
                    id: outBtnIc
                    anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                    size: 16
                    text: panel.sink && /이어폰|Headphone|Headset/i.test(panel.sinkLabel(panel.sink)) ? "headphones" : "speaker"
                    color: Theme.dim
                }
                Text {
                    anchors { left: outBtnIc.right; leftMargin: 10; right: outArrow.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                    text: panel.sink ? panel.sinkLabel(panel.sink) : "출력 장치 없음"
                    elide: Text.ElideRight
                    color: Theme.text
                    font.family: Theme.font; font.pixelSize: 12
                }
                Icon {
                    id: outArrow
                    anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                    size: 18
                    text: "expand_more"
                    color: Theme.dim
                    rotation: panel.outOpen ? 180 : 0
                    Behavior on rotation { NumberAnimation { duration: Theme.base; easing.type: Easing.OutCubic } }
                }
                MouseArea { id: outBtnMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: panel.outOpen = !panel.outOpen }
            }
            Rectangle {
                id: outList
                Layout.fillWidth: true
                implicitHeight: panel.outOpen ? outCol.implicitHeight + 8 : 0
                visible: implicitHeight > 0
                clip: true
                radius: 12
                color: Theme.surface
                Behavior on implicitHeight { NumberAnimation { duration: Theme.base; easing.type: Easing.OutCubic } }
                Column {
                    id: outCol
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 4 }
                    spacing: 2
                    Repeater {
                        model: panel.sinks
                        Rectangle {
                            id: outItem
                            required property var modelData
                            readonly property bool sel: panel.sink === modelData
                            width: outCol.width
                            height: 30; radius: 10
                            color: outItemMa.containsMouse ? Theme.raised : "transparent"
                            Behavior on color { ColorAnimation { duration: Theme.fast } }
                            Icon {
                                id: outItemIc
                                anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                                size: 16
                                text: /이어폰|Headphone|Headset/i.test(outItemLabel.text) ? "headphones" : "speaker"
                                color: outItem.sel ? Theme.text : Theme.dim
                            }
                            Text {
                                id: outItemLabel
                                anchors { left: outItemIc.right; leftMargin: 10; right: outCheck.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                                text: panel.sinkLabel(outItem.modelData)
                                elide: Text.ElideRight
                                color: outItem.sel ? Theme.text : Theme.muted
                                font.family: Theme.font; font.pixelSize: 12; font.weight: outItem.sel ? Font.Bold : Font.Normal
                            }
                            Icon {
                                id: outCheck
                                anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                                size: 16
                                text: "check"
                                color: Theme.text
                                opacity: outItem.sel ? 1 : 0
                            }
                            MouseArea { id: outItemMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: { Pipewire.preferredDefaultAudioSink = outItem.modelData; panel.outOpen = false } }
                        }
                    }
                }
            }

            SliderCard {
                id: blCard
                visible: panel.hasBacklight
                Layout.fillWidth: true
                icon: "brightness_medium"
                value: panel.backlight
                onMoved: v => panel.run(["brightnessctl", "-q", "-c", "backlight", "set", Math.max(1, Math.round(v * 100)) + "%"])
            }

            // ── 조명 ──
            Rectangle { Layout.fillWidth: true; Layout.topMargin: 6; implicitHeight: 1; color: Theme.raised }
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 4; Layout.rightMargin: 4
                Text { text: "조명"; color: Theme.text; font.family: Theme.font; font.pixelSize: 13; font.weight: Font.Bold }
                Item { Layout.fillWidth: true }
                // 조작할 전구 고르기: 플로어등 · 제도등 (고른 칩 = 흰 알약, 점 = 그 전구가 켜진 빛 색)
                Row {
                    spacing: 4
                    Repeater {
                        model: ["floor", "desk"]
                        Rectangle {
                            id: chip
                            required property string modelData
                            readonly property bool sel: panel.lamp === modelData
                            readonly property var st: panel.lights[modelData]
                            readonly property bool reach: st !== undefined && st.state !== undefined
                            readonly property color dot: panel.lampDot(st)
                            implicitWidth: chipRow.implicitWidth + 20; implicitHeight: 24; radius: 12
                            color: sel ? Theme.text : chipMa.containsMouse ? Theme.raised : Theme.surface
                            Behavior on color { ColorAnimation { duration: Theme.fast } }
                            Row {
                                id: chipRow
                                anchors.centerIn: parent
                                spacing: 5
                                Rectangle {
                                    visible: chip.dot !== Qt.color("transparent")
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 7; height: 7; radius: 3.5; color: chip.dot
                                }
                                Text {
                                    text: panel.lampNames[chip.modelData]
                                    color: chip.sel ? Theme.onLight : chip.reach ? Theme.text : Theme.dim
                                    font.family: Theme.font; font.pixelSize: 12; font.weight: chip.sel ? Font.Bold : Font.Normal
                                }
                            }
                            MouseArea { id: chipMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                        onClicked: panel.lamp = chip.modelData }
                        }
                    }
                }
            }
            RowLayout {
                spacing: 6
                readonly property real q: (col.width - 18) / 4
                Tile {
                    Layout.preferredWidth: parent.q
                    icon: "lightbulb"; label: panel.lightOn ? "켜짐" : "꺼짐"
                    active: panel.lightOn
                    enabled: panel.lightKnown
                    onClicked: {
                        const want = !panel.lightOn, l = Object.assign({}, panel.lights);
                        for (const k of panel.lampTargets()) if (l[k] && l[k].state !== undefined) l[k] = Object.assign({}, l[k], { state: want });
                        panel.lights = l;   // 누르자마자 바뀐 것처럼 보이게 (곧 실제 상태로 다시 읽음)
                        panel.lightAction([want ? "on" : "off"]);
                    }
                }
                Tile {
                    Layout.preferredWidth: parent.q
                    icon: "wb_incandescent"; label: "따뜻하게"
                    enabled: panel.lightOn
                    onClicked: panel.lightAction(["warm"])
                }
                Tile {
                    Layout.preferredWidth: parent.q
                    icon: "light_mode"; label: "집중"
                    enabled: panel.lightOn
                    onClicked: panel.lightAction(["focus"])
                }
                Tile {
                    Layout.fillWidth: true
                    icon: "palette"; label: "색 선택"
                    enabled: panel.lightOn
                    active: panel.colorOpen
                    onClicked: panel.colorOpen = !panel.colorOpen
                }
            }

            // 색 팔레트 (색 선택을 누르면 펼쳐짐): 자주 쓰는 색 8개 + 끌어서 고르는 색상 막대
            Rectangle {
                id: palette
                Layout.fillWidth: true
                // reveal 0→1 하나로 높이·간격·내용 페이드를 함께 움직인다
                property real reveal: panel.colorOpen ? 1 : 0
                Behavior on reveal { NumberAnimation { duration: 300; easing.type: Easing.OutQuart } }
                implicitHeight: 84 * reveal
                Layout.topMargin: -6 * (1 - reveal)   // 접힐 때 줄 간격 6px 도 같이 줄어 '툭' 튀지 않게
                clip: true
                radius: 12
                color: Theme.surface
                opacity: Math.min(1, reveal * 2)
                visible: reveal > 0.001
                Row {
                    id: swatches
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 10 - 8 * (1 - palette.reveal)
                    opacity: palette.reveal
                    spacing: 12
                    Repeater {
                        model: ["39C5BB", "E12885", "F38BA8", "FAB387", "F9E2AF", "A6E3A1", "89B4FA", "CBA6F7"]
                        Rectangle {
                            required property string modelData
                            width: 26; height: 26; radius: 13
                            color: "#" + modelData
                            scale: sw.containsMouse ? 1.15 : 1
                            Behavior on scale { NumberAnimation { duration: Theme.fast } }
                            MouseArea {
                                id: sw
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: panel.lightAction(["rgb", parent.modelData])
                            }
                        }
                    }
                }
                // 색상 막대: 손을 뗄 때 그 색으로 바꿈
                Item {
                    id: hueBar
                    anchors { left: parent.left; right: parent.right; leftMargin: 16; rightMargin: 16 }
                    y: 50 - 8 * (1 - palette.reveal)
                    opacity: palette.reveal
                    height: 22
                    property real hue: 0.5
                    function hex(h) {
                        const c = Qt.hsva(h, 1, 1, 1);
                        const t = v => Math.round(v * 255).toString(16).padStart(2, "0");
                        return (t(c.r) + t(c.g) + t(c.b)).toUpperCase();
                    }
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width; height: 10; radius: 5
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0.0; color: "#ff0000" }
                            GradientStop { position: 1 / 6; color: "#ffff00" }
                            GradientStop { position: 2 / 6; color: "#00ff00" }
                            GradientStop { position: 3 / 6; color: "#00ffff" }
                            GradientStop { position: 4 / 6; color: "#0000ff" }
                            GradientStop { position: 5 / 6; color: "#ff00ff" }
                            GradientStop { position: 1.0; color: "#ff0000" }
                        }
                    }
                    Rectangle {
                        width: 18; height: 18; radius: 9
                        anchors.verticalCenter: parent.verticalCenter
                        x: hueBar.hue * (hueBar.width - width)
                        color: Qt.hsva(hueBar.hue, 1, 1, 1)
                        border.color: Theme.text
                        border.width: 3
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        function at(mx) { return Math.max(0, Math.min(1, mx / width)) }
                        onPressed: mouse => hueBar.hue = at(mouse.x)
                        onPositionChanged: mouse => { if (pressed) hueBar.hue = at(mouse.x) }
                        onReleased: panel.lightAction(["rgb", hueBar.hex(hueBar.hue)])
                    }
                }
            }

            SliderCard {
                id: bright
                Layout.fillWidth: true
                icon: "brightness_6"
                onReleased: v => panel.lightAction(["set-brightness", String(Math.round(10 + v * 90))])
            }

            RowLayout {
                Layout.topMargin: 6
                spacing: 6
                Tile { Layout.fillWidth: true; Layout.preferredWidth: 1; radius: 22; icon: "lock"; iconSize: 20
                       onClicked: { panel.hide(); panel.run(["loginctl", "lock-session"]) } }
                Tile { Layout.fillWidth: true; Layout.preferredWidth: 1; radius: 22; icon: "restart_alt"; iconSize: 20
                       onClicked: { panel.hide(); panel.run([panel.home + "/.local/bin/power-confirm", "reboot"]) } }
                Tile { Layout.fillWidth: true; Layout.preferredWidth: 1; radius: 22; icon: "power_settings_new"; iconSize: 20
                       onClicked: { panel.hide(); panel.run([panel.home + "/.local/bin/power-confirm", "poweroff"]) } }
            }

            Rectangle {
                visible: panel.hasBattery
                Layout.fillWidth: true
                implicitHeight: 44
                radius: 12
                color: Theme.surface
                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: 16
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 10
                    Icon {
                        anchors.verticalCenter: parent.verticalCenter
                        text: panel.hasBattery && panel.battery.state === UPowerDeviceState.Charging ? "battery_charging_full" : "battery_full"
                        color: panel.hasBattery && panel.battery.percentage < 0.1 ? Theme.red
                             : panel.hasBattery && panel.battery.percentage < 0.25 ? "#fab387" : Theme.text
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: panel.hasBattery ? panel.batteryText() : ""
                        color: Theme.text; font.family: Theme.font; font.pixelSize: 13
                    }
                }
            }

            // 알림
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 10
                Layout.leftMargin: 4
                Text { text: "알림"; color: Theme.text; font.family: Theme.font; font.pixelSize: 14; font.weight: Font.Bold }
                Item { Layout.fillWidth: true }
                Rectangle {
                    visible: Notifs.count > 0
                    implicitWidth: clr.implicitWidth + 20; implicitHeight: 24; radius: 8
                    color: clrMa.containsMouse ? Theme.raised : Theme.surface
                    Text { id: clr; anchors.centerIn: parent; text: "모두 지우기"; color: Theme.text; font.family: Theme.font; font.pixelSize: 12 }
                    MouseArea { id: clrMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: Notifs.clearAll() }
                }
            }
            Text {
                visible: Notifs.count === 0
                Layout.fillWidth: true
                Layout.topMargin: 6; Layout.bottomMargin: 6
                horizontalAlignment: Text.AlignHCenter
                text: "알림 없음"
                color: Theme.dim; font.family: Theme.font; font.pixelSize: 13
            }
            ListView {
                id: notifList
                visible: Notifs.count > 0
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(contentHeight, Math.max(160, (panel.screen ? panel.screen.height : 1080) - 700))
                clip: true
                spacing: 6
                boundsBehavior: Flickable.StopAtBounds
                model: Notifs.list.slice().reverse()
                verticalLayoutDirection: ListView.TopToBottom
                delegate: NotificationCard {
                    required property var modelData
                    notif: modelData
                    now: tick.n
                    width: notifList.width
                }
            }
        }
    }

    IpcHandler {
        target: "cc"
        function toggle(): void { panel.toggle() }
        function open(): void { panel.show() }
        function close(): void { panel.hide() }
    }

    Component.onCompleted: {
        if (Quickshell.env("MIKU_CC_OPEN") === "1") show();
        if (Quickshell.env("MIKU_OUT_OPEN") === "1") outOpen = true;   // 시험: 출력 드롭다운 펼친 채로
        if (Quickshell.env("MIKU_CC_COLOR") === "1") colorOpen = true;   // 시험용
    }
}
