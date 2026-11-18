// Material Symbols Rounded (꽉 찬 모양) 아이콘. text 에 아이콘 이름을 넣는다
import QtQuick

Text {
    property int size: 18
    font.family: Theme.iconFont
    font.pixelSize: size
    font.variableAxes: { "FILL": 1, "wght": 500, "opsz": 20 }
    renderType: Text.NativeRendering
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
    width: size
    height: size
}
