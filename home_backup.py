#!/usr/bin/env python3
"""Back up personal files in $HOME (Documents, Pictures, ...) to a separate
private GitHub repo, apart from the settings in ~/dotfiles.

Usage: ~/dotfiles/home_backup.py [--no-push]

Every non-hidden top-level folder/file in $HOME is included, so new folders
are picked up automatically. Settings (dotfiles) are not; backup.py owns those.
"""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backup import GLOB_DENY, SECRET_RE  # noqa: E402

import fnmatch

HOME = Path.home()
REPO = HOME / "home-backup"
REMOTE = "home-backup"     # repo name under the logged-in GitHub account
OUT = REPO / "files"
# Files Claude made in "No folder" sessions; the app deletes them with the session.
SCRATCH = HOME / ".config/Claude/scratch-workspaces"
SESSIONS_META = HOME / ".config/Claude/claude-code-sessions"
SESSIONS_OUT = REPO / "claude-sessions"  # kept even after the session is deleted
MAX_FILE = 95 * 1024**2    # GitHub rejects files over 100MB

# Top-level entries of $HOME never copied: build caches and the backup repos themselves.
TOP_DENY = {"yay", "paru", "dotfiles", "home-backup", "go", "snap", "Steam"}
# Folder names skipped at any depth: dependency/build output and nested git data.
DIR_DENY = {".git", "node_modules", ".venv", "venv", "__pycache__", "target",
            "build", "dist", ".next", ".cache", ".gradle", ".tox"}
# GLOB_DENY from backup.py also skips history/cookie/key/token-named files.
# In personal projects, lock/bak/log files are real data (Cargo.lock, Ghidra ~index.bak, tool logs).
SKIP_GLOBS = [g for g in GLOB_DENY if g not in ("cache", "Cache", "build", "*.lock", "*.bak", "*.log")]
# Videos (lectures, recordings) would push the repo past GitHub's size limits.
VIDEO_GLOBS = ["*.mp4", "*.MP4", "*.mkv", "*.mov", "*.MOV", "*.avi", "*.webm", "*.m4v", "*.wmv", "*.flv"]
SKIP_GLOBS += VIDEO_GLOBS

skipped = []


def run(*cmd, check=True):
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def git(*args, check=True):
    return run("git", "-C", str(REPO), *args, check=check)


def ensure_repo():
    if (REPO / ".git").is_dir():
        return
    user = run("gh", "api", "user", "--jq", ".login + \" \" + (.id|tostring)").stdout.split()
    login, uid = user[0], user[1]
    if run("gh", "repo", "view", f"{login}/{REMOTE}", check=False).returncode != 0:
        run("gh", "repo", "create", f"{login}/{REMOTE}", "--private",
            "--description", "Personal files from ~ (separate from dotfiles)")
        REPO.mkdir(exist_ok=True)
        run("git", "init", "-q", "-b", "main", str(REPO))
        git("remote", "add", "origin", f"https://github.com/{login}/{REMOTE}.git")
    else:
        run("gh", "repo", "clone", f"{login}/{REMOTE}", str(REPO))
    git("config", "user.name", login)
    git("config", "user.email", f"{uid}+{login}@users.noreply.github.com")


def copy(src: Path, dst: Path):
    if src.is_symlink():
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink() or dst.exists():
            dst.unlink()
        os.symlink(os.readlink(src), dst)
    elif src.is_dir():
        if src.name in DIR_DENY:
            return
        for child in sorted(src.iterdir()):
            copy(child, dst / child.name)
    elif src.is_file():
        if any(fnmatch.fnmatch(src.name, g) for g in VIDEO_GLOBS):
            pass  # skipped on purpose, not worth a line per file
        elif any(fnmatch.fnmatch(src.name, g) for g in SKIP_GLOBS):
            skipped.append(f"{src} (name looks like a secret/cache file)")
        elif src.stat().st_size > MAX_FILE:
            skipped.append(f"{src} (file > 95MB, GitHub limit)")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dst)
            except PermissionError:
                skipped.append(f"{src} (no read permission)")


def session_titles() -> dict[str, str]:
    """Map scratch folder path -> session title, from the desktop app's session files."""
    titles = {}
    for f in SESSIONS_META.glob("*/*/*.json"):
        try:
            meta = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if meta.get("cwd") and meta.get("title"):
            titles[meta["cwd"]] = meta["title"]
    return titles


def backup_sessions():
    """Copy each session's files into claude-sessions/<date> <title> [<id>]/.

    Additive: a deleted session keeps its last copy. A renamed session's folder
    is renamed in place (matched by the [<id>] suffix).
    """
    titles = session_titles()
    for ws in sorted(SCRATCH.glob("*/*/scratch-*")):
        if not any(p.is_file() for p in ws.rglob("*")):
            continue
        _, y, m, d, sid = ws.name.split("-", 4)
        title = re.sub(r'[/\\:*?"<>|]+', "·", titles.get(str(ws), "")).strip() or "제목 없음"
        name = f"{y}-{m}-{d} {title} [{sid}]"
        dst = SESSIONS_OUT / name
        for old in SESSIONS_OUT.glob(f"* [[]{sid}[]]"):
            if old != dst:
                old.rename(dst)
        for child in sorted(ws.iterdir()):
            if child.name == ".claude":
                continue  # per-session Claude settings, not work
            copy(child, dst / child.name)


def backup_anki():
    """Keep the newest Anki backup (.colpkg: cards + review history, no media) per profile.

    A fixed file name so each run replaces the last one instead of piling up.
    Import it in Anki with File > Import.
    """
    for prof in sorted((HOME / ".local/share/Anki2").glob("*/backups")):
        pkgs = sorted(prof.glob("*.colpkg"))
        if pkgs:
            dst = REPO / "anki" / prof.parent.name / "latest.colpkg"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pkgs[-1], dst)


def main():
    ensure_repo()
    shutil.rmtree(OUT, ignore_errors=True)
    for child in sorted(HOME.iterdir()):
        if child.name.startswith(".") or child.name in TOP_DENY:
            continue
        copy(child, OUT / child.name)
    backup_sessions()
    backup_anki()
    if not (REPO / "README.md").exists():
        (REPO / "README.md").write_text(
            "# home-backup\n\n`~` 의 개인 파일(문서, 사진, 다운로드 등). 설정은 dotfiles 저장소에 따로 있음.\n\n"
            "복원: `~/dotfiles/restore.sh home`\n")

    if skipped:
        print("Skipped:")
        for s in skipped:
            print("  -", s)

    hits = []
    for root, _, files in (*os.walk(OUT), *os.walk(SESSIONS_OUT)):
        for f in files:
            p = Path(root) / f
            if p.is_symlink():
                continue
            data = p.read_bytes()
            if b"\0" not in data[:4096] and (m := SECRET_RE.search(data)):
                hits.append(f"{p.relative_to(REPO)}: {m.group(0)[:12].decode(errors='replace')}…")
    if hits:
        print("\nABORTED: possible secrets found, nothing committed:")
        for h in hits:
            print("  !", h)
        sys.exit(2)

    git("add", "-A")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        print("No changes since the last home backup.")
    else:
        stat = git("diff", "--cached", "--shortstat").stdout.strip()
        msg = f"home backup: {socket.gethostname()} {datetime.now():%Y-%m-%d %H:%M}"
        git("commit", "-m", msg)
        print(f"Committed: {msg} ({stat})")

    if "--no-push" not in sys.argv:
        r = git("push", "-u", "origin", "HEAD", check=False)
        if r.returncode != 0:
            print("Push failed:\n" + r.stderr)
            sys.exit(1)
        print("Pushed to GitHub.")


if __name__ == "__main__":
    main()
