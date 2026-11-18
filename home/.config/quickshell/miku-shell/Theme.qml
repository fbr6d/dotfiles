pragma Singleton
// 디자인 가이드(~/Documents/design-guide.md) 값 모음
import Quickshell
import QtQuick

Singleton {
    readonly property color bgDeep: "#141413"
    readonly property color bg: "#262624"
    readonly property color surface: "#30302e"
    readonly property color raised: "#4a4a47"
    readonly property color text: "#faf9f5"
    readonly property color muted: "#c2c0b6"
    readonly property color dim: "#9c9a92"
    readonly property color onLight: "#262624"
    readonly property color red: "#f38ba8"
    readonly property string font: "Pretendard"
    readonly property string iconFont: "Material Symbols Rounded"
    readonly property int fast: 120
    readonly property int base: 250
}
