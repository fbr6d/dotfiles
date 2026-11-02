#!/usr/bin/env python3
"""리눅스 명령어 치트시트를 브라우저 없이 독립 창으로 띄운다.

Super+H 로 실행한다.
- 창이 없으면 새로 띄운다.
- 창이 앞에 있으면(포커스) 최소화한다. 완전히 닫기는 Ctrl+W.
- 창이 다른 창 뒤에 있거나 최소화돼 있으면 앞으로 가져온다. GNOME(Wayland)은 이를 "준비됨" 알림으로
  바꿔 버리므로, cheatsheet-raise@leejaeik 확장이 그 요청을 받아 창을 바로 활성화한다.
Ctrl+W 닫기 · Ctrl+P 인쇄(PDF 저장)
Esc · 방향키 · Ctrl+휠 · Ctrl+=/-/0 확대는 페이지가 직접 처리한다.
"""
import os
import sys

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gdk, Gio, GLib, Gtk, WebKit2  # noqa: E402

APP_ID = "local.LinuxCheatsheet"
PAGE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "linux-all.html")

# GTK3 on Wayland uses the program name as the window class; make it the app ID
# so compositor rules (Hyprland: special workspace "linuxcheat") can match it
GLib.set_prgname(APP_ID)


class Cheatsheet(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.win = None
        self.view = None

    def do_activate(self):
        if self.win is not None:
            if self.win.is_active():
                self.win.iconify()
            else:
                self.win.present()
            return

        win = Gtk.ApplicationWindow(application=self, title="리눅스 명령어 사전")
        win.set_icon_name("utilities-terminal")
        width, height = 1240, 900
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        if monitor is not None:
            area = monitor.get_workarea()
            width = min(width, int(area.width * 0.92))
            height = int(area.height * 0.92)
        win.set_default_size(width, height)
        win.set_position(Gtk.WindowPosition.CENTER)

        view = WebKit2.WebView()
        view.load_uri("file://" + PAGE)
        view.connect("decide-policy", self.on_policy)
        win.add(view)
        win.connect("key-press-event", self.on_key)
        win.connect("destroy", self.on_destroy)
        win.show_all()
        self.win, self.view = win, view

    def on_destroy(self, *_):
        self.win = self.view = None

    def on_policy(self, view, decision, kind):
        # 페이지 밖으로 나가는 링크는 기본 브라우저로 연다
        if kind == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri()
            if not uri.startswith("file://"):
                Gio.AppInfo.launch_default_for_uri(uri, None)
                decision.ignore()
                return True
        return False

    def on_key(self, win, ev):
        ctrl = ev.state & Gdk.ModifierType.CONTROL_MASK
        key = ev.keyval
        if ctrl and key in (Gdk.KEY_w, Gdk.KEY_q):
            win.close()
        elif ctrl and key == Gdk.KEY_p:
            WebKit2.PrintOperation.new(self.view).run_dialog(win)
        else:
            return False
        return True


if __name__ == "__main__":
    sys.exit(Cheatsheet().run(sys.argv))
