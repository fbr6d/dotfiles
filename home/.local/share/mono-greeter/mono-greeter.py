#!/usr/bin/env python3
# Minimal greetd greeter: solid background, centered user name and a rounded
# password field. On success it starts Hyprland directly (no session picker).
# Runs under cage as the greetd "greeter" user. Without GREETD_SOCK it runs in
# preview mode (any password is rejected except "demo").
import json
import os
import socket
import struct
import sys
import threading

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk

USERNAME = "leejaeik"
SESSION_CMD = ["start-hyprland"]
SESSION_ENV = ["XDG_SESSION_TYPE=wayland", "XDG_CURRENT_DESKTOP=Hyprland"]

# Colors: monochrome dark (Claude dark-mode grays)
CSS = """
window, window.background { background: #262624; }
.name {
    color: #faf9f5;
    font-family: "Pretendard", "Noto Sans CJK KR", sans-serif;
    font-size: 34px;
    font-weight: 600;
}
entry.password {
    background: #30302e;
    color: #faf9f5;
    caret-color: #faf9f5;
    border: 1px solid #4a4a47;
    border-radius: 999px;
    min-height: 54px;
    padding: 0 24px;
    font-family: "Pretendard", "Noto Sans CJK KR", sans-serif;
    font-size: 20px;
    box-shadow: none;
    outline: none;
}
entry.password:focus-within { border-color: #e6e6e6; }
entry.password > text > placeholder { color: #9c9a92; }
entry.password image { color: #9c9a92; }
.status {
    color: #9c9a92;
    font-family: "Pretendard", "Noto Sans CJK KR", sans-serif;
    font-size: 16px;
    min-height: 22px;
}
"""


class Greetd:
    """greetd IPC: 32-bit native-endian length prefix + JSON payload."""

    def __init__(self, path):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(path)

    def call(self, **msg):
        data = json.dumps(msg).encode()
        self.sock.sendall(struct.pack("=I", len(data)) + data)
        (length,) = struct.unpack("=I", self._recv(4))
        return json.loads(self._recv(length))

    def _recv(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("greetd closed the connection")
            buf += chunk
        return buf


def login(password):
    """Return None on success (session queued), or an error message."""
    sock_path = os.environ.get("GREETD_SOCK")
    if not sock_path:
        return None if password == "demo" else "비밀번호가 올바르지 않습니다"

    g = Greetd(sock_path)
    try:
        resp = g.call(type="create_session", username=USERNAME)
        while resp["type"] == "auth_message":
            if resp["auth_message_type"] in ("secret", "visible"):
                answer = password
            else:  # info / error messages from PAM need no input
                answer = None
            resp = g.call(type="post_auth_message_response", response=answer)

        if resp["type"] == "success":
            resp = g.call(type="start_session", cmd=SESSION_CMD, env=SESSION_ENV)
            if resp["type"] == "success":
                return None

        g.call(type="cancel_session")
    finally:
        g.sock.close()
    if resp.get("error_type") == "auth_error":
        return "비밀번호가 올바르지 않습니다"
    return resp.get("description") or "로그인할 수 없습니다"


class Greeter(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="local.mono.greeter")
        self.connect("activate", self.build)

    def build(self, app):
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        win = Gtk.ApplicationWindow(application=app, title="Login")
        Gtk.StyleContext.add_provider_for_display(
            win.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=22,
                      halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
        name = Gtk.Label(label=USERNAME)
        name.add_css_class("name")

        self.entry = Gtk.PasswordEntry(show_peek_icon=False)
        self.entry.set_size_request(380, -1)
        self.entry.connect("activate", self.submit)

        self.status = Gtk.Label(label="")
        self.status.add_css_class("status")

        box.append(name)
        box.append(self.entry)
        box.append(self.status)
        win.set_child(box)

        if os.environ.get("GREETD_SOCK"):
            win.fullscreen()
        else:
            win.set_default_size(900, 600)
        win.present()
        self.entry.grab_focus()

    def submit(self, entry):
        password = entry.get_text()
        if not password:
            return
        entry.set_sensitive(False)
        self.status.set_text("")
        threading.Thread(target=self._login, args=(password,), daemon=True).start()

    def _login(self, password):
        try:
            error = login(password)
        except Exception as e:  # keep the greeter alive on IPC errors
            error = str(e)
        GLib.idle_add(self._done, error)

    def _done(self, error):
        if error is None:
            self.quit()  # greetd starts the session once the greeter exits
            return False
        self.status.set_text(error)
        self.entry.set_text("")
        self.entry.set_sensitive(True)
        self.entry.grab_focus()
        return False


if __name__ == "__main__":
    sys.exit(Greeter().run([]))
