---
name: prefer-existing-programs
description: "For any request, first check for an existing off-the-shelf program; ask before building a custom one"
metadata:
  node_type: memory
  type: feedback
  originSessionId: bfbe5840-2645-4f54-951d-b52f4142dcb9
  modified: 2026-11-02T22:38:11.826Z
---

For every request, first check whether an existing (off-the-shelf) program does the job and use it if so. If I'd have to build something myself, ask the user first before writing it.

**Why:** Custom-made tools (greeter, cheatsheet, popups, etc.) were slow or broke (e.g. the custom greetd greeter login loop on 2026-11-03); user prefers established programs.

**How to apply:** Search AUR/official repos/upstream projects before writing code; present the found program, and use AskUserQuestion before building anything custom.
