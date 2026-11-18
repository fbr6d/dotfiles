pragma Singleton
// 알림 서버 (swaync 대체): org.freedesktop.Notifications 를 맡는다.
//   popups   지금 화면에 떠 있는 알림
//   list     제어센터 알림 목록 (server.trackedNotifications)
//   dnd      방해 금지: 팝업만 숨기고 목록에는 쌓는다 (긴급 알림은 그래도 띄움)
import Quickshell
import Quickshell.Services.Notifications
import QtQuick

Singleton {
    id: root
    property bool dnd: false
    property bool ccOpen: false            // 제어센터가 열려 있으면 팝업을 숨긴다
    property var deadlines: ({})           // 알림 id → 팝업이 사라질 시각(ms), 0 = 안 사라짐
    property var hovered: ({})             // 마우스가 올라간 팝업 id (시간 멈춤)
    property var popups: []
    property var times: ({})
    // MIKU_NO_NOTIF=1 이면 알림 서버를 켜지 않는다 (swaync 가 도는 동안 시험할 때)
    readonly property var server: serverLoader.item
    readonly property var empty: []
    readonly property var list: server ? server.trackedNotifications.values : empty
    readonly property int count: list.length

    // 기록에 남기지 않는 앱 (swaync notification-visibility 의 transient 와 같음)
    readonly property var transientApps: ["Backup"]

    function timeout(n) {
        if (n.urgency === NotificationUrgency.Critical) return 0;
        if (n.expireTimeout > 0) return n.expireTimeout;
        return n.urgency === NotificationUrgency.Low ? 4000 : 6000;
    }
    property var transientIds: ({})
    function removePopup(n) {
        popups = popups.filter(p => p !== n);
        if (transientIds[n.id]) { delete transientIds[n.id]; n.dismiss() }
    }
    function clearAll() {
        for (const n of list.slice()) n.dismiss();
        popups = [];
    }
    function ago(id) {
        const t = times[id];
        if (!t) return "";
        const s = (Date.now() - t) / 1000;
        if (s < 60) return "방금";
        if (s < 3600) return Math.floor(s / 60) + "분 전";
        const d = new Date(t);
        return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
    }
    // 알림을 누르면: 기본 동작이 있으면 실행, 그리고 보낸 앱 창으로 이동 (notify-focus)
    function activate(n) {
        const def = n.actions.find(a => a.identifier === "default");
        if (def) def.invoke();
        Quickshell.execDetached([Quickshell.env("HOME") + "/.local/bin/notify-focus",
                                 n.desktopEntry || "", n.appName || ""]);
        n.dismiss();
    }
    function icon(n) {
        // Quickshell 은 아이콘 이름도 image://icon/<이름> 으로 넘겨 줘서, 테마에 없는 이름이면 체크무늬가 나온다
        if (n.image && n.image.startsWith("image://icon/")) {
            if (Quickshell.hasThemeIcon(n.image.slice(13))) return n.image;
        } else if (n.image) return n.image;
        if (n.appIcon && (n.appIcon.startsWith("/") || n.appIcon.startsWith("file:"))) return n.appIcon;
        if (n.appIcon && Quickshell.hasThemeIcon(n.appIcon)) return Quickshell.iconPath(n.appIcon);
        const e = n.desktopEntry ? DesktopEntries.byId(n.desktopEntry) : null;
        if (e && e.icon && Quickshell.hasThemeIcon(e.icon)) return Quickshell.iconPath(e.icon);
        // 마지막으로 앱 이름으로 .desktop 을 짐작해서 (예: "Spotify" → spotify-launcher)
        const g = n.appName && DesktopEntries.heuristicLookup ? DesktopEntries.heuristicLookup(n.appName) : null;
        if (g && g.icon && Quickshell.hasThemeIcon(g.icon)) return Quickshell.iconPath(g.icon);
        return "";
    }

    // 0.5초마다 시간이 다 된 팝업을 내린다 (마우스가 올라가 있으면 그만큼 미룬다)
    Timer {
        interval: 500; repeat: true
        running: root.popups.length > 0
        onTriggered: {
            const now = Date.now();
            for (const n of root.popups) {
                const d = root.deadlines[n.id];
                if (root.hovered[n.id] && d) root.deadlines[n.id] = Math.max(d, now + 1500);
                else if (d && now >= d) root.removePopup(n);
            }
        }
    }

    Loader {
        id: serverLoader
        active: Quickshell.env("MIKU_NO_NOTIF") !== "1"
        sourceComponent: NotificationServer {
        keepOnReload: true
        bodySupported: true
        bodyMarkupSupported: true
        bodyHyperlinksSupported: true
        bodyImagesSupported: false
        actionsSupported: true
        imageSupported: true
        persistenceSupported: true
        onNotification: n => {
            const keep = !n.transient && !root.transientApps.includes(n.appName);
            n.tracked = true;
            root.times[n.id] = Date.now();
            const t = root.timeout(n);
            root.deadlines[n.id] = t > 0 ? Date.now() + t : 0;
            if (!root.dnd || n.urgency === NotificationUrgency.Critical)
                root.popups = [n].concat(root.popups.filter(p => p !== n)).slice(0, 4);
            n.closed.connect(() => root.removePopup(n));
            // 기록에 안 남기는 알림은 팝업이 사라질 때 같이 지운다
            if (!keep) root.transientIds[n.id] = true;
        }
        }
    }
}
