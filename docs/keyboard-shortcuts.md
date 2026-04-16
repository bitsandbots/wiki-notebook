# Keyboard Shortcuts

This document describes all keyboard shortcuts available in Wiki Notebook.

## Global Shortcuts

### Search
| Shortcut | Action |
|----------|--------|
| `/` | Focus the search input field (available from anywhere in the app) |

### Editor
| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Save the current note (creates new or updates existing) |
| `Esc` | Close editor or reset to new note state |

## Multi-Select Shortcuts

Wiki Notebook supports multi-select operations for power users:

1. **Select Notes**: Click the checkbox next to any note card
2. **Select Multiple**: Hold `Shift` and click to select a range, or click multiple checkboxes
3. **Combine Selected Notes**: Click "Combine (concatenate)" or "Combine (AI)" in the action bar
4. **Clear Selection**: Click "Clear" in the action bar

## Editor Actions

| Action | Button | Shortcut |
|--------|--------|----------|
| Save Note | Save (primary) | `Ctrl+Enter` |
| Preview Markdown | Preview (secondary) | N/A |
| Delete Note | Delete (danger) | N/A |
| Undo Optimization | Undo (link) | N/A |

## Navigation Shortcuts

| Action | Description |
|--------|-------------|
| `Esc` in search | Clear search and reset view |
| `Esc` in editor | Reset to new note (clears form) |
| Category click | Filter by category |

## System Behavior

### Search
- Typing `/` anywhere focuses the search input
- Search debounce: 200ms for performance
- FTS5-powered search for full-text queries
- LIKE fallback for short queries (< 3 chars)

### Editor
- Auto-focuses when editing an existing note
- Preserves category when editing from category view
- Markdown preview toggles view mode

### Multi-Select
- Action bar appears at bottom when notes are selected
- Shows count of selected notes
- Combine requires 2+ notes

## Customization

Keyboard shortcuts are implemented in vanilla JavaScript in `static/app.js`. To modify:

1. Open `static/app.js`
2. Find the `handleKeydown()` function
3. Modify as needed (keep `Ctrl`/`Meta` check for cross-platform compatibility)

## Platform Notes

- **Linux/Windows**: Use `Ctrl` key
- **macOS**: Use `Cmd` key (handled automatically by browser)
