---
name: antigravity
description: Google Antigravity IDE (VS Code fork) CLI for opening files, folders, diffs, and merges. Use when user wants to open code in Antigravity/agy, compare files, or perform three-way merges.
---

# Antigravity IDE CLI

Google's VS Code fork. CLI at `/Applications/Antigravity.app/Contents/Resources/app/bin/antigravity`

Alias: `agy`

## Basic Usage

```bash
# Open file
antigravity file.py

# Open folder
antigravity /path/to/project

# Open multiple
antigravity file1.py file2.py folder/

# Read from stdin
cat file.py | antigravity -

# Open at specific line
antigravity -g file.py:42

# Open at line and column
antigravity -g file.py:42:10
```

## Window Management

```bash
# New window
antigravity -n file.py

# Reuse existing window
antigravity -r file.py

# Add folder to current window
antigravity -a ./newfolder

# Remove folder from window
antigravity --remove ./folder

# Wait for file to close before returning
antigravity -w file.py
```

## Diff & Merge

```bash
# Compare two files
antigravity -d file1.py file2.py

# Three-way merge
antigravity -m modified1.py modified2.py base.py result.py
```

## Profiles

```bash
# Open with specific profile
antigravity --profile "Python Dev" project/

# Custom user data directory (isolated instance)
antigravity --user-data-dir ~/.antigravity-work project/
```

## URL Protocol

Opens `antigravity://` URLs for extension installs and deep links.

## Notes

- Signed into Google account (per Mike's setup)
- Extensions from Open VSX registry
- Electron-based, same keybindings as VS Code
