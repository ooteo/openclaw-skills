---
name: keeping-you-awake
description: Prevent Mac from sleeping using KeepingYouAwake app. Use when user wants to keep Mac awake, prevent sleep, stop screen dimming, or disable sleep for downloads/long tasks.
---

# KeepingYouAwake

Prevents Mac from sleeping. Control via URL schemes.

## Commands

```bash
# Activate (prevent sleep indefinitely)
open "keepingyouawake://activate"

# Activate for duration (seconds)
open "keepingyouawake://activate/3600"  # 1 hour

# Deactivate (allow sleep)
open "keepingyouawake://deactivate"

# Toggle state
open "keepingyouawake://toggle"
```

## Duration Examples

```bash
open "keepingyouawake://activate/1800"   # 30 minutes
open "keepingyouawake://activate/3600"   # 1 hour
open "keepingyouawake://activate/7200"   # 2 hours
open "keepingyouawake://activate/14400"  # 4 hours
open "keepingyouawake://activate/28800"  # 8 hours
```

## Notes

- Shows coffee cup icon in menu bar when active
- Alternative to `caffeinate` command but with GUI indicator
- Deactivates automatically after duration expires
