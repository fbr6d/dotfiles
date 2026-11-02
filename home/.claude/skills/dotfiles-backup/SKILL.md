---
name: dotfiles-backup
description: Back up this computer's settings to the private GitHub dotfiles repo (~/dotfiles), and personal home-folder files (Documents, Pictures, Downloads, ...) to the separate private home-backup repo. Use when the user asks to back up / save / sync their settings, dotfiles, config, or home directory/files to GitHub (e.g. "설정 백업해줘", "dotfiles 저장해줘", "홈디렉터리 백업해줘", "사진 백업해줘"), or asks how to migrate this setup to another computer.
---

# Dotfiles backup

Two private GitHub repos, both scripts live in `~/dotfiles`:

| User asks for | Run | Local repo |
|---|---|---|
| settings / 설정 / dotfiles | `~/dotfiles/backup.py` | `~/dotfiles` |
| home directory / personal files / 홈디렉터리 / 사진·문서 | `~/dotfiles/home_backup.py` | `~/home-backup` |

Run both when the user asks for both, or for "everything" / "전부".

1. Run the script(s). Each snapshots, scans for secrets, commits and pushes.
2. Report what each printed: committed or "No changes", the shortstat, and any "Skipped" lines.
3. If it printed `ABORTED: possible secrets found`, show the listed files, propose adding them
   to the matching deny list at the top of the script, and rerun only after the user agrees.
   Never weaken the secret scan to get a push through.
4. If a "Skipped ... folder > 150MB" line (backup.py) names real settings (not an app's binaries or caches),
   ask whether to include it; otherwise suggest adding it to a deny list. If home_backup.py skips
   files over 95MB, tell the user they need another place (GitHub's limit is 100MB per file).
5. If the push fails on auth, tell the user to run `gh auth login` and `gh auth setup-git`.

For migrating to a new machine, point to `~/dotfiles/README.md`: clone the dotfiles repo, then run
`~/dotfiles/restore.sh` (its `home` step pulls the home-backup repo too).
