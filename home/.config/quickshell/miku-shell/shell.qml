// 미쿠 셸 (Quickshell): waybar·swaync 를 대신할 데스크톱 셸.
//   ControlCenter  제어센터 (qs -c miku-shell ipc call cc toggle)
//   Popups         알림 팝업 (Notifs 싱글톤이 알림 서버)
import Quickshell
import QtQuick

ShellRoot {
    ControlCenter {}
    Popups {}
}
