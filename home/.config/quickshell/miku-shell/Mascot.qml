// 화면 오른쪽 아래 마스코트 (그림: ~/Pictures/miku-mascot/*.png, 마스터가 준 파일 그대로. 출처 같은 폴더 CREDITS.txt)
//   음악(Spotify)이 재생 중이면 sway.png 4프레임을 천천히 돌려 살랑살랑
//   알림이 오면 jump.png 4프레임을 한 번 재생 + 위로 폴짝 (방해 금지 중에는 안 함)
//   왼쪽 클릭 = 폴짝, 오른쪽 클릭 = 숨기기 (제어센터 「마스코트」 버튼으로 다시 보이기)
//   다시 보이기·숨기기: qs -c miku-shell ipc call mascot toggle   (시험: ... ipc call mascot hop)
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
    implicitWidth: 64 * px
    implicitHeight: 64 * px + 12                      // 위로 뛰는 공간
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.namespace: "miku-mascot"
    mask: Region { item: body }

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

    Item {
        id: body
        width: 64 * win.px
        height: 64 * win.px
        x: 0
        y: 12 + lift
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
        TapHandler { acceptedButtons: Qt.LeftButton; onTapped: win.hop() }
        TapHandler { acceptedButtons: Qt.RightButton; onTapped: MascotState.shown = false }
    }

    IpcHandler {
        target: "mascot"
        function toggle(): void { MascotState.shown = !MascotState.shown }
        function hop(): void { win.hop() }
    }
}
