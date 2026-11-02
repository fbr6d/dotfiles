---
name: dotfiles-backup
description: Back up this computer's settings to the private GitHub dotfiles repo (~/dotfiles). Use when the user asks to back up / save / sync their settings, dotfiles, or config to GitHub (e.g. "설정 백업해줘", "dotfiles 저장해줘", "세팅 깃헙에 올려줘"), or asks how to migrate this setup to another computer.
---

# Dotfiles backup

The repo lives at `~/dotfiles` (remote: the user's private GitHub `dotfiles` repo).

1. Run `~/dotfiles/backup.py`. It snapshots settings, scans for secrets, commits and pushes.
2. Report what it printed: committed or "No changes", the shortstat, and any "Skipped" lines.
3. If it printed `ABORTED: possible secrets found`, show the listed files, propose adding them
   to the matching `*_DENY` list at the top of `~/dotfiles/backup.py`, and rerun only after the user agrees.
   Never weaken the secret scan to get a push through.
4. If a "Skipped ... folder > 150MB" line names real settings (not an app's binaries or caches),
   ask whether to include it; otherwise suggest adding it to a deny list.
5. If the push fails on auth, tell the user to run `gh auth login` and `gh auth setup-git`.

For migrating to a new machine, point to `~/dotfiles/README.md`: clone the repo, then run `~/dotfiles/restore.sh`.
