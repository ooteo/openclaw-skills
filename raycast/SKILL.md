---
name: raycast
description: Raycast launcher automation via URL schemes and deeplinks. Use when user wants to trigger Raycast commands, extensions, or search from CLI/scripts.
---

# Raycast

Productivity launcher with extensive URL scheme support.

## URL Scheme

Base: `raycast://`

### Built-in Commands

```bash
# Open Raycast
open "raycast://extensions"

# Clipboard history
open "raycast://extensions/raycast/clipboard-history/clipboard-history"

# Search files
open "raycast://extensions/raycast/file-search/search-files"

# Calculator
open "raycast://extensions/raycast/calculator/calculator"

# Calendar
open "raycast://extensions/raycast/calendar/my-schedule"

# Window management
open "raycast://extensions/raycast/window-management/maximize"
open "raycast://extensions/raycast/window-management/left-half"
open "raycast://extensions/raycast/window-management/right-half"

# Snippets
open "raycast://extensions/raycast/snippets/search-snippets"
```

### Extension Pattern

```
raycast://extensions/{author}/{extension}/{command}
```

### With Arguments

```bash
# Search with query
open "raycast://extensions/raycast/file-search/search-files?arguments=%7B%22query%22%3A%22test%22%7D"
```

### Confetti

```bash
open "raycast://confetti"
```

## Script Commands

Raycast can run custom scripts. Scripts live in `~/.config/raycast/scripts/` or configured script directories.

## Notes

- Extensions installable from Raycast Store
- Check installed extensions in Raycast preferences
- Some extensions require API keys configured in Raycast
- Deeplinks work even when Raycast window is closed
