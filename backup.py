#!/usr/bin/env python3
"""Snapshot this machine's settings into the dotfiles repo, then commit and push.

Usage: ~/dotfiles/backup.py [--no-push] [--dry-run]

Strategy: copy *everything* under the watched locations except a denylist,
so new apps' settings get picked up automatically. Secrets, caches, history
and huge files are skipped. Each run rebuilds the mirror directories from
scratch so deleted settings disappear from the repo too.
"""
import configparser
import fnmatch
import os
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
REPO = Path(__file__).resolve().parent
MIRRORS = ["home", "zen", "etc", "meta"]  # rebuilt on every run

MAX_FILE = 20 * 1024**2   # skip single files bigger than this
MAX_ENTRY = 150 * 1024**2  # skip a whole top-level folder bigger than this

# Top-level entries of $HOME that are never copied.
HOME_DENY = {
    ".cache", ".local", ".config", ".claude", ".ssh", ".gnupg", ".pki",
    ".mozilla", ".var", ".npm", ".cargo", ".rustup", ".gradle", ".m2", ".nv",
    ".steam", ".wine", ".Trash", ".dbus", ".nuget", ".dotnet", ".vscode",
    ".vscode-oss", ".android", ".java", ".docker", ".kube", ".aws", ".azure",
    ".bash_history", ".zsh_history", ".python_history", ".node_repl_history",
    ".lesshst", ".viminfo", ".wget-hsts", ".Xauthority", ".ICEauthority",
    ".claude.json", ".claude.json.backup", ".sudo_as_admin_successful",
    ".netrc", ".git-credentials", ".pypirc", ".npmrc",
}
# Children of ~/.config that are never copied.
CONFIG_DENY = {
    "Claude", "pulse", "dconf", "go", "yay", "zen", "gh", "github-copilot",
    "google-chrome", "chromium", "BraveSoftware", "vivaldi", "discord",
    "Slack", "Signal", "Element", "spotify", "obsidian", "Code", "VSCodium",
    "Cursor", "1Password", "Bitwarden", "keepassxc", "rclone", "session",
    "libvirt", "unity3d", "JetBrains", "Electron", "kdeconnect",
}
# Children of ~/.local/share that are never copied.
SHARE_DENY = {
    "gvfs-metadata", "nautilus", "pki", "Trash", "keyrings", "recently-used.xbel",
    "Steam", "flatpak", "containers", "docker", "baloo", "klipper", "kwalletd",
    "zoxide", "fish", "zsh", "bash", "lutris", "bottles", "applications/mimeinfo.cache",
    "Claude", "zen", "virtualenvs", "pnpm", "go", "nvim/lazy", "nvim/mason",
    "sddm", "xorg", "TelegramDesktop", "spotify-launcher",
    "mime", "icons/hicolor/icon-theme.cache",
    "org.localsend.localsend_app/shared_preferences.json",  # holds its TLS private key
}
# Code/IDE settings worth keeping even though the app folder is denied.
CONFIG_EXTRA = [
    "Code/User/settings.json", "Code/User/keybindings.json", "Code/User/snippets",
    "VSCodium/User/settings.json", "VSCodium/User/keybindings.json",
    "Cursor/User/settings.json", "Cursor/User/keybindings.json",
]
# File/dir name patterns skipped everywhere.
GLOB_DENY = [
    "*.bak-*", "*.bak", "*.removed", "*.orig", "*~", "*.swp", "*.log", "*.lock",
    "lock", ".parentlock", "__pycache__", "*.pyc", "Cache", "cache", "Caches",
    "CachedData", "GPUCache", "Code Cache", "*history*", "*.sqlite*",
    "*.db", "*.db-*", "cookie", "cookies*", "Cookies*", "*.kdbx",
    "id_rsa*", "id_ed25519*", "*.pem", "*.key", "hosts.yml", "credentials*",
    "*token*", "*secret*", ".env", "auth.json", "*.socket",
]
# What to keep from ~/.claude (Claude Code); everything else there is session data.
CLAUDE_KEEP = [
    "settings.json", "CLAUDE.md", "keybindings.json", "statusline*",
    "skills", "agents", "commands", "hooks", "output-styles",
    "plugins/installed_plugins.json", "plugins/known_marketplaces.json",
    "projects/*/memory",
]
# What to keep from each Zen profile. No cookies, logins, history or sessions.
ZEN_KEEP = [
    "prefs.js", "user.js", "chrome", "extensions", "extensions.json",
    "extension-settings.json", "extension-preferences.json", "containers.json",
    "handlers.json", "search.json.mozlz4", "xulstore.json", "zen-themes.json",
    "zen-keyboard-shortcuts.json", "times.json", "compatibility.ini",
]
# Edited /etc files tied to this machine's disks/users; restoring them elsewhere breaks things.
ETC_MACHINE_ONLY = {
    "/etc/fstab", "/etc/crypttab", "/etc/passwd", "/etc/group", "/etc/shadow", "/etc/gshadow",
    "/etc/subuid", "/etc/subgid", "/etc/shells", "/etc/resolv.conf", "/etc/hostname",
    "/etc/hosts", "/etc/machine-id", "/etc/sudoers",
}
# Patterns that look like real credentials; the backup aborts if any match.
SECRET_RE = re.compile(
    rb"(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|gho_[A-Za-z0-9]{30,}"
    rb"|sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{40,}|AKIA[0-9A-Z]{16}"
    rb"|xox[abpr]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}"
    rb"|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)

DRY = "--dry-run" in sys.argv
skipped = []


def run(*cmd, check=True, **kw):
    return subprocess.run(cmd, check=check, text=True, capture_output=True, **kw)


def denied(path: Path, base: Path, deny: set) -> bool:
    rel = path.relative_to(base).as_posix()
    if any(rel == d or rel.startswith(d + "/") for d in deny):
        return True
    return any(fnmatch.fnmatch(path.name, g) for g in GLOB_DENY)


def tree_size(p: Path) -> int:
    if p.is_symlink() or p.is_file():
        return p.lstat().st_size
    total = 0
    for root, _, files in os.walk(p):
        for f in files:
            try:
                total += (Path(root) / f).lstat().st_size
            except OSError:
                pass
    return total


def copy(src: Path, dst: Path, base: Path | None = None, deny: set = frozenset()):
    """Copy src (file or dir) to dst, honoring deny lists and size limits."""
    if base is not None and denied(src, base, deny):
        return
    if src.is_symlink():
        if not DRY:
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(os.readlink(src), dst)
        return
    if src.is_dir():
        for child in sorted(src.iterdir()):
            copy(child, dst / child.name, base, deny)
        return
    if not src.is_file():
        return
    if src.stat().st_size > MAX_FILE:
        skipped.append(f"{src} (file > {MAX_FILE // 1024**2}MB)")
        return
    if not DRY:
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
        except PermissionError:
            skipped.append(f"{src} (no read permission)")


def copy_children(src_dir: Path, dst_dir: Path, deny: set):
    """Copy each child of src_dir unless denied or the whole child is too big."""
    if not src_dir.is_dir():
        return
    for child in sorted(src_dir.iterdir()):
        if denied(child, src_dir, deny):
            continue
        if tree_size(child) > MAX_ENTRY:
            skipped.append(f"{child} (folder > {MAX_ENTRY // 1024**2}MB, add to a deny list or raise MAX_ENTRY)")
            continue
        copy(child, dst_dir / child.name, src_dir, deny)


def backup_home():
    out = REPO / "home"
    for child in sorted(HOME.iterdir()):
        if not child.name.startswith(".") or child.name in HOME_DENY:
            continue
        if any(fnmatch.fnmatch(child.name, g) for g in GLOB_DENY):
            continue
        if tree_size(child) > MAX_ENTRY:
            skipped.append(f"{child} (> {MAX_ENTRY // 1024**2}MB)")
            continue
        copy(child, out / child.name, HOME, set())

    copy_children(HOME / ".config", out / ".config", CONFIG_DENY)
    for rel in CONFIG_EXTRA:
        p = HOME / ".config" / rel
        if p.exists():
            copy(p, out / ".config" / rel)

    copy_children(HOME / ".local/bin", out / ".local/bin", set())
    share = HOME / ".local/share"
    if share.is_dir():
        for child in sorted(share.iterdir()):
            if denied(child, share, SHARE_DENY):
                continue
            if tree_size(child) > MAX_ENTRY:
                skipped.append(f"{child} (folder > {MAX_ENTRY // 1024**2}MB)")
                continue
            copy(child, out / ".local/share" / child.name, share, SHARE_DENY)

    claude = HOME / ".claude"
    for pattern in CLAUDE_KEEP:
        for p in sorted(claude.glob(pattern)):
            copy(p, out / ".claude" / p.relative_to(claude), claude, set())


def backup_zen():
    zen = HOME / ".config/zen"
    ini = zen / "profiles.ini"
    if not ini.exists():
        return
    out = REPO / "zen"
    copy(ini, out / "profiles.ini")
    copy(zen / "installs.ini", out / "installs.ini")
    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read(ini)
    for sec in cp.sections():
        if not sec.startswith("Profile") or "Path" not in cp[sec]:
            continue
        rel = cp[sec]["Path"]
        prof = zen / rel if cp[sec].get("IsRelative", "1") == "1" else Path(rel)
        if not prof.is_dir():
            continue
        dst = out / prof.name
        dst.mkdir(parents=True, exist_ok=True)
        for name in ZEN_KEEP:
            if (prof / name).exists():
                copy(prof / name, dst / name)
        # Newest bookmark backup holds bookmarks only (no history).
        bms = sorted((prof / "bookmarkbackups").glob("*.jsonlz4"))
        if bms:
            copy(bms[-1], dst / "bookmarkbackups" / bms[-1].name)


def backup_etc():
    out = REPO / "etc"
    # Hand-made units (not owned by any package) and greetd setup.
    candidates = list(Path("/etc/systemd/system").glob("*.service"))
    candidates += list(Path("/etc/systemd/system").glob("*.timer"))
    for p in candidates:
        if p.is_symlink():
            continue
        if run("pacman", "-Qo", str(p), check=False).returncode != 0:
            copy(p, out / p.relative_to("/etc"))
    for d in ["greetd", "keyd", "modprobe.d", "mkinitcpio.conf.d", "sysctl.d", "udev/rules.d", "X11/xorg.conf.d"]:
        p = Path("/etc") / d
        if p.is_dir():
            copy(p, out / d, Path("/etc"), set())
    # Package-owned config files the user edited ("/etc/x [modified]" in pacman -Qii).
    res = run("pacman", "-Qii", check=False)
    for m in re.finditer(r"(/etc/\S+) \[modified\]", res.stdout):
        p = Path(m.group(1))
        if p.as_posix() not in ETC_MACHINE_ONLY and p.is_file():
            copy(p, out / p.relative_to("/etc"))


def backup_meta():
    out = REPO / "meta"
    out.mkdir(parents=True, exist_ok=True)

    def save(name, *cmd):
        r = run(*cmd, check=False)
        if r.returncode == 0:
            (out / name).write_text(r.stdout)

    save("pacman.txt", "pacman", "-Qqen")
    save("aur.txt", "pacman", "-Qqem")
    save("dconf.ini", "dconf", "dump", "/")
    save("services-system.txt", "systemctl", "list-unit-files", "--state=enabled", "--no-legend", "--plain")
    save("services-user.txt", "systemctl", "--user", "list-unit-files", "--state=enabled", "--no-legend", "--plain")
    if shutil.which("flatpak"):
        save("flatpak.txt", "flatpak", "list", "--app", "--columns=application")
    if shutil.which("code"):
        save("vscode-extensions.txt", "code", "--list-extensions")
    for f in ["services-system.txt", "services-user.txt"]:
        p = out / f
        if p.exists():
            p.write_text("".join(l.split()[0] + "\n" for l in p.read_text().splitlines() if l.strip()))


def scan_secrets() -> list[str]:
    hits = []
    for d in MIRRORS:
        for root, _, files in os.walk(REPO / d):
            for f in files:
                p = Path(root) / f
                if p.is_symlink():
                    continue
                try:
                    data = p.read_bytes()
                except OSError:
                    continue
                if b"\0" in data[:4096]:
                    continue  # binary
                m = SECRET_RE.search(data)
                if m:
                    hits.append(f"{p.relative_to(REPO)}: {m.group(0)[:12].decode(errors='replace')}…")
    return hits


def main():
    if not DRY:
        for d in MIRRORS:
            shutil.rmtree(REPO / d, ignore_errors=True)
    backup_home()
    backup_zen()
    backup_etc()
    if not DRY:
        backup_meta()

    if skipped:
        print("Skipped:")
        for s in skipped:
            print("  -", s)
    if DRY:
        print("Dry run: nothing written.")
        return

    hits = scan_secrets()
    if hits:
        print("\nABORTED: possible secrets found, nothing committed:")
        for h in hits:
            print("  !", h)
        print("Add the file to a deny list in backup.py, then run again.")
        sys.exit(2)

    run("git", "-C", str(REPO), "add", "-A")
    if run("git", "-C", str(REPO), "diff", "--cached", "--quiet", check=False).returncode == 0:
        print("No changes since the last backup.")
    else:
        stat = run("git", "-C", str(REPO), "diff", "--cached", "--shortstat").stdout.strip()
        msg = f"backup: {socket.gethostname()} {datetime.now():%Y-%m-%d %H:%M}"
        run("git", "-C", str(REPO), "commit", "-m", msg)
        print(f"Committed: {msg} ({stat})")

    if "--no-push" not in sys.argv:
        r = run("git", "-C", str(REPO), "push", "-u", "origin", "HEAD", check=False)
        if r.returncode != 0:
            print("Push failed:\n" + r.stderr)
            sys.exit(1)
        print("Pushed to GitHub.")


if __name__ == "__main__":
    main()
