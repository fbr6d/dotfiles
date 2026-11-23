// 화면 오른쪽 아래 마스코트 (그림: ~/Pictures/miku-mascot/*.png, 마스터가 준 파일 그대로. 출처 같은 폴더 CREDITS.txt)
//   음악(Spotify)이 재생 중이면 sway.png 4프레임을 천천히 돌려 살랑살랑
//   알림이 오면 jump.png 4프레임을 한 번 재생 + 위로 폴짝 (방해 금지 중에는 안 함)
//   왼쪽 클릭 = 폴짝 + 말로 묻기(2026-11-23: miku_listen.py가 듣고 → 글자로 → miku_ask.py)
//   오른쪽 클릭 = 폴짝 + 질문 입력창 열기/닫기(엔터 → miku_ask.py가 답을 목소리+말풍선으로, Esc = 닫기)
//   가운데(휠) 클릭 = 숨기기 (제어센터 「미쿠」 버튼으로 다시 보이기)
//   다시 보이기·숨기기: qs -c miku-shell ipc call mascot toggle   (시험: ... ipc call mascot hop)
//   말풍선: qs -c miku-shell ipc call mascot speak "할 말" <보일 ms>   (정각 멘트 miku_hourly.py가 부름, 2026-11-23)
// 창은 마스코트 크기만 하고 클릭도 마스코트에서만 받는다(아래 창을 가리지 않게).
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Services.Mpris
import QtQuick
import QtQuick.Effects

PanelWindow {
    id: win
    readonly property string dir: Quickshell.env("HOME") + "/Pictures/miku-mascot/"   // 공개 dotfiles 저장소에 안 올라가게 ~/.config 밖에 둠
    readonly property real px: 1                      // 원본 64px 그대로 (마스터 지정, 가장 선명)
    readonly property string wantOutput: Quickshell.env("MIKU_CC_OUTPUT") || ""
    screen: {
        const name = wantOutput || (Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "");
        for (const s of Quickshell.screens) if (s.name === name) return s;
        return Quickshell.screens[0];
    }

    readonly property bool playing: {
        for (const p of Mpris.players.values)
            if ((p.dbusName || "").toLowerCase().includes("spotify")) return p.isPlaying;
        return false;
    }
    readonly property bool hidden: !MascotState.shown
    property bool hopping: false

    // 질문 입력창 (2026-11-23 마스터: 클릭해서 짧게 묻고 말로 대답 듣기)
    property bool asking: false
    readonly property string askPy: Quickshell.env("HOME") + "/.hermes/tools/python-3.14.9+20261021-linux-x64/bin/python3"
    readonly property string askScript: Quickshell.env("HOME") + "/.hermes/profiles/miku/scripts/miku_ask.py"
    function openAsk() { sayText = ""; asking = true; askInput.text = ""; askFocus.restart() }
    function closeAsk() { asking = false; askInput.text = "" }
    function sendAsk() {
        const q = askInput.text.trim();
        closeAsk();
        if (q.length > 0) Quickshell.execDetached([askPy, askScript, q]);
    }
    Timer { id: askFocus; interval: 60; onTriggered: askInput.forceActiveFocus() }
    // 말로 묻기 (2026-11-23 마스터): 녹음·인식·대답은 miku_listen.py가 (말풍선 '듣고 있어요…'도 거기서 띄움)
    readonly property string listenPy: Quickshell.env("HOME") + "/.local/share/miku/stt/venv/bin/python"
    readonly property string listenScript: Quickshell.env("HOME") + "/.hermes/profiles/miku/scripts/miku_listen.py"
    function listen() { Quickshell.execDetached([listenPy, listenScript]) }
    // 클릭 → 먼저 멈춤 검사. 종료 코드 0 = 하던 걸 멈춤(그걸로 끝), 1 = 한가함 → 원래 동작
    property string afterStop: ""
    Process {
        id: stopProc
        command: ["/usr/bin/python3", Quickshell.env("HOME") + "/.hermes/profiles/miku/scripts/miku_stop.py"]
        onExited: (code, status) => {
            if (code !== 0) {
                if (win.afterStop === "listen") win.listen();
                else if (win.afterStop === "ask") win.openAsk();
            }
            win.afterStop = "";
        }
    }
    function stopOr(what) {
        if (stopProc.running) return;      // 연타 무시
        afterStop = what;
        stopProc.running = true;
    }

    // 말풍선 (2026-11-23 마스터: 정각 멘트를 PC로 재생할 때 마스코트에 말풍선)
    property string sayText: ""
    readonly property bool saying: sayText !== ""
    // 창 크기는 고정(말풍선 자리까지 미리 잡음). 크기가 바뀌면 Hyprland가 창을 옮기는 애니로 마스코트가 튀었음
    readonly property int roomW: 480
    readonly property int roomH: 230
    property bool tempShown: false                    // 숨겨 둔 상태에서 말하느라 잠깐 보인 것
    function speak(t, ms) {
        if (!MascotState.shown) { MascotState.shown = true; tempShown = true; }
        sayText = t;
        sayTimer.interval = Math.max(1500, ms);
        sayTimer.restart();
        if (tempShown) hopLater.restart(); else hop();   // 방금 나타났으면 창이 그려진 뒤에 폴짝
    }
    Timer { id: hopLater; interval: 400; onTriggered: win.hop() }
    Timer {
        id: sayTimer
        onTriggered: {
            win.sayText = "";
            if (win.tempShown) { win.tempShown = false; MascotState.shown = false; }   // 원래 숨김이었으면 다시 숨김
        }
    }

    function hop() {
        if (hidden || hopping) return;
        hopping = true;
        jumpSprite.currentFrame = 0;
        jumpSprite.restart();
        hopAnim.restart();
    }

    visible: !hidden
    color: "transparent"
    anchors { bottom: true; right: true }
    margins { bottom: 12; right: 16 }
    implicitWidth: roomW
    implicitHeight: roomH                             // 위로 뛰는 공간 + 말풍선 자리 (클릭은 mask로 마스코트만)
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.namespace: "miku-mascot"
    mask: Region { item: body; Region { item: askBox } }
    WlrLayershell.keyboardFocus: asking ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    // 알림이 새로 뜨면 폴짝
    property int lastPopups: 0
    Connections {
        target: Notifs
        function onPopupsChanged() {
            const n = Notifs.popups.length;
            if (n > win.lastPopups && !Notifs.dnd) win.hop();
            win.lastPopups = n;
        }
    }

    Rectangle {
        id: bubble
        visible: win.saying && !win.asking
        x: win.width - width
        y: win.height - 64 * win.px - 10 - height
        width: sayLabel.width + 36
        height: sayLabel.height + 24
        radius: 18
        color: Theme.bg
        Text {
            id: sayLabel
            anchors.centerIn: parent
            width: Math.min(implicitWidth, 440)
            text: win.sayText
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: 18
            wrapMode: Text.WordWrap
            lineHeight: 1.15
        }
        Rectangle {                                    // 꼬리 (마스코트 쪽)
            width: 13; height: 13; rotation: 45
            color: Theme.bg
            x: parent.width - 32 - width / 2
            y: parent.height - height / 2 - 1
            z: -1
        }
    }

    Rectangle {
        id: askBox
        visible: win.asking
        width: win.asking ? 400 : 0
        height: win.asking ? 52 : 0
        x: win.width - width
        y: win.height - 64 * win.px - 10 - height
        radius: 18
        color: Theme.bg
        border.width: 2
        border.color: "#39C5BB"
        TextInput {
            id: askInput
            anchors.fill: parent
            anchors.leftMargin: 18; anchors.rightMargin: 18
            verticalAlignment: TextInput.AlignVCenter
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: 18
            clip: true
            selectByMouse: true
            onAccepted: win.sendAsk()
            Keys.onEscapePressed: win.closeAsk()
            Text {                                     // 안내 글
                anchors.verticalCenter: parent.verticalCenter
                visible: askInput.text.length === 0 && !askInput.preeditText
                text: "미쿠에게 물어보기…"
                color: Theme.text
                opacity: 0.45
                font: askInput.font
            }
        }
        Rectangle {                                    // 꼬리
            width: 13; height: 13; rotation: 45
            color: Theme.bg
            border.width: 0
            x: parent.width - 32 - width / 2
            y: parent.height - height / 2 - 1
            z: -1
        }
    }

    Item {
        id: body
        width: 64 * win.px
        height: 64 * win.px
        x: win.width - width
        y: win.height - height + lift
        property real lift: 0

        // 2026-11-22 마스터: 채도 조금 낮추기 (그림 파일은 그대로, 그릴 때만 효과)
        //   -1 = 흑백, 0 = 원본. 더 줄이려면 값을 더 작게. 백업 Mascot.qml.bak-saturation
        layer.enabled: true
        layer.smooth: false
        layer.effect: MultiEffect { saturation: -0.55 }

        // 음악 들을 때 살랑살랑 (재생이 아니면 첫 프레임에 멈춤)
        AnimatedSprite {
            id: swaySprite
            anchors.fill: parent
            visible: !win.hopping
            source: win.dir + "sway.png"
            frameWidth: 64; frameHeight: 64; frameCount: 4
            frameDuration: 260
            interpolate: false
            smooth: false
            running: win.playing && !win.hopping
            onRunningChanged: if (!running) currentFrame = 0
        }
        // 알림 점프 (한 번만)
        AnimatedSprite {
            id: jumpSprite
            anchors.fill: parent
            visible: win.hopping
            source: win.dir + "jump.png"
            frameWidth: 64; frameHeight: 64; frameCount: 4
            frameDuration: 120
            loops: 1
            interpolate: false
            smooth: false
            running: false
        }
        SequentialAnimation {
            id: hopAnim
            NumberAnimation { target: body; property: "lift"; to: -10; duration: 180; easing.type: Easing.OutQuad }
            NumberAnimation { target: body; property: "lift"; to: 0; duration: 220; easing.type: Easing.OutBounce }
            PauseAnimation { duration: 80 }
            ScriptAction { script: win.hopping = false }
        }

        HoverHandler { cursorShape: Qt.PointingHandCursor }
        // 2026-11-23 마스터 1번: 왼쪽 = 말로 묻기(miku_listen.py), 오른쪽 = 글자 입력창, 가운데(휠) = 숨기기 (이전판 .bak-voice)
        // 2026-11-23 마스터 '실행 중에 클릭하면 강제 멈춤': 왼쪽·오른쪽 클릭은 먼저 miku_stop.py → 듣기·생각·말하기 중이면 멈추고 끝 (이전판 .bak-before-stop)
        TapHandler { acceptedButtons: Qt.LeftButton; onTapped: { win.hop(); if (win.asking) win.closeAsk(); win.stopOr("listen"); } }
        TapHandler { acceptedButtons: Qt.RightButton; onTapped: { win.hop(); if (win.asking) win.closeAsk(); else win.stopOr("ask"); } }
        TapHandler { acceptedButtons: Qt.MiddleButton; onTapped: MascotState.shown = false }
    }

    IpcHandler {
        target: "mascot"
        function toggle(): void { MascotState.shown = !MascotState.shown }
        function hop(): void { win.hop() }
        function speak(text: string, ms: int): void { win.speak(text, ms) }
        function ask(): void { win.openAsk() }
        function listen(): void { win.listen() }
        function tap(what: string): void { win.stopOr(what === "voice" ? "listen" : what) }   // 클릭과 같은 길 시험용(qs가 인자 'listen'을 하위 명령으로 착각해서 'voice'로)
        function closeAsk(): void { win.closeAsk() }
    }
}
