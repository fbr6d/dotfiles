//@ pragma IconTheme breeze-dark
// (트레이·알림 아이콘 테마: GTK 처럼 색을 바꿔 주지 않으므로 어두운 바탕용 밝은 아이콘 테마를 쓴다)
// 미쿠 셸 (Quickshell): waybar·swaync 를 대신하는 데스크톱 셸.
//   Bar            상단 바 (모니터마다 하나)
//   ControlCenter  제어센터 (qs -c miku-shell ipc call cc toggle)
//   Popups         알림 팝업 (Notifs 싱글톤이 알림 서버)
import Quickshell
import QtQuick

ShellRoot {
    ControlCenter { id: cc }
    Popups {}
    TrackCard {}
    Mascot {}
    Variants {
        model: {
            const want = Quickshell.env("MIKU_CC_OUTPUT");
            return want ? Quickshell.screens.filter(s => s.name === want) : Quickshell.screens;
        }
        Bar {
            required property var modelData
            screen: modelData
            controlCenter: cc
        }
    }
}
