pragma Singleton
// 음악 앱 고르기 상태 (2026-11-24 마스터: Spotify ↔ 유튜브 뮤직 선택)
//   app     지금 고른 앱 (~/.local/state/miku/music-app, ~/.local/bin/music-app 이 씀)
//   player  고른 앱의 MPRIS 재생기 (바 서랍·곡 카드·마스코트가 따라감)
import Quickshell
import Quickshell.Io
import Quickshell.Services.Mpris
import QtQuick

Singleton {
    id: root
    readonly property string home: Quickshell.env("HOME")
    readonly property string tool: home + "/.local/bin/music-app"
    readonly property var apps: [
        { id: "spotify", label: "Spotify", cls: "spotify" },
        { id: "youtube-music", label: "YouTube Music", cls: "com.github.th-ch.youtube-music" }
    ]
    property string app: "spotify"
    property bool popupOpen: false        // MusicTabs 가 채움 (탭 줄이 떠 있는 동안 곡 카드는 안 띄움)

    // Pear 는 단축키 플러그인이 켜지면 dbus 이름 YoutubeMusic (2026-11-24 켬), 꺼져 있으면 Chromium 기본(identity YouTube Music)
    function isApp(p, id) {
        const dbus = (p.dbusName || "").toLowerCase();
        if (id === "spotify") return dbus.includes("spotify");
        const ident = (p.identity || "").toLowerCase();
        const desk = (p.desktopEntry || "").toLowerCase();
        return dbus.includes("youtubemusic") || dbus.includes("youtube-music") || ident.includes("youtube music")
               || desk.includes("youtube-music");
    }
    function playerOf(id) {
        for (const p of Mpris.players.values)
            if (isApp(p, id)) return p;
        return null;
    }
    readonly property var player: playerOf(app)
    function labelOf(id) {
        for (const a of apps) if (a.id === id) return a.label;
        return id;
    }

    function run(args) { Quickshell.execDetached([tool].concat(args)) }
    function toggle() { run(["toggle"]) }
    function choose(id) { if (id !== app) { app = id; run(["set", id]) } }

    FileView {
        id: stateFile
        path: root.home + "/.local/state/miku/music-app"
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            const a = text().trim();
            root.app = (a === "youtube-music") ? a : "spotify";
        }
    }
}
