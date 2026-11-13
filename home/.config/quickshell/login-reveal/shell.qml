// Login reveal: after the boot-time lock screen (~/.local/bin/login-lock) is
// unlocked, the blurred, darkened wallpaper it showed melts into the sharp
// desktop. login-lock starts this before the lock screen (it shows exactly the
// same picture, so there is no seam), then plays it after the unlock with:
//   qs -c login-reveal ipc call reveal start
// It never takes keyboard or mouse input (empty mask) and quits when done.
//   LOGIN_REVEAL_IMAGE   the wallpaper (sharp)
//   LOGIN_REVEAL_BLURRED the lock screen's background (blurred + darkened)
import QtQuick
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: root

    property string wallpaper: Quickshell.env("LOGIN_REVEAL_IMAGE") || ""
    property string blurred: Quickshell.env("LOGIN_REVEAL_BLURRED") || ""
    // 0 = looks like the lock screen, 1 = the sharp desktop wallpaper
    property real progress: 0

    Variants {
        model: Quickshell.screens

        PanelWindow {
            required property var modelData
            screen: modelData
            anchors { top: true; bottom: true; left: true; right: true }
            color: "transparent"
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.namespace: "quickshell:login-reveal"
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            mask: Region {}   // clicks and keys go straight through

            // the sharp wallpaper, blurred less and less
            Image {
                id: sharp
                anchors.fill: parent
                source: root.wallpaper ? "file://" + root.wallpaper : ""
                fillMode: Image.PreserveAspectCrop
                asynchronous: false
                visible: false
            }
            MultiEffect {
                anchors.fill: parent
                source: sharp
                blurEnabled: true
                blurMax: 64
                blurMultiplier: 1.5
                blur: 1 - root.progress
                autoPaddingEnabled: false
            }
            // the lock screen's 55% brightness, lifted as it clears
            Rectangle {
                anchors.fill: parent
                color: "black"
                opacity: 0.45 * (1 - root.progress)
            }
            // the exact lock-screen picture on top, faded out at the start so
            // the hand-over from the lock screen has no visible step
            Image {
                anchors.fill: parent
                source: root.blurred ? "file://" + root.blurred : ""
                fillMode: Image.PreserveAspectCrop
                asynchronous: false
                opacity: Math.max(0, 1 - root.progress * 3)
            }
        }
    }

    NumberAnimation {
        id: reveal
        target: root
        property: "progress"
        from: 0
        to: 1
        duration: 1600
        easing.type: Easing.InOutSine
        onFinished: Qt.quit()
    }

    // safety: never stay on screen long after being told to reveal
    Timer { id: guard; interval: 5000; onTriggered: Qt.quit() }

    IpcHandler {
        target: "reveal"
        function start(): void {
            guard.start()
            reveal.start()
        }
    }
}
