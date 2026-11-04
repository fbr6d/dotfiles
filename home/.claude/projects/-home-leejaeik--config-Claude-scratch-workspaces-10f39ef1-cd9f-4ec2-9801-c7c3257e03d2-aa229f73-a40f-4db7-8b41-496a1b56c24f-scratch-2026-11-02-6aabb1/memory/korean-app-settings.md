---
name: korean-app-settings
description: "When installing any app, tell the user whether it has a Korean language setting and how to turn it on"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 5f5d5ddb-cbb4-4bc6-bf12-3becd0240098
  modified: 2026-11-04T12:04:52.288Z
---

Whenever I install an app (from 2026-11-04 on), check whether it offers a Korean UI and tell the user: the setting name/location, or that none exists.

**Why:** The user asked for this after lazygit was installed in English and they had to ask for Korean separately (2026-11-04).

**How to apply:** In the closing message of any install task, include a line about Korean support. Don't silently switch it on unless the user asked; mention it (offer to apply). Related: [[prefer-existing-programs]].
