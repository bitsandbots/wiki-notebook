# Keyboard Shortcuts

## Global

| Key | Action |
|-----|--------|
| `/` | Focus search input (from anywhere) |
| `Esc` | Clear search / return to grid / close detail |

## Grid View

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Move focus between note cards |
| `Enter` or `Space` | Open focused card in detail view |

## Detail View (Edit Mode)

| Key | Action |
|-----|--------|
| `Ctrl+Enter` | Save note |
| `Esc` | Return to grid (prompts if unsaved changes) |

## Notes

- **Autosave** — existing notes save automatically 2 seconds after you stop typing. The status bar below the editor shows `Saving…` / `Saved`.
- **First save** — new notes still require a manual `Ctrl+Enter` or clicking Save (to set the title before autosave can run).
- `Ctrl`/`Cmd` is handled automatically — use `Cmd` on macOS.

## Multi-Select

1. Click a checkbox on any card to select it.
2. Select multiple cards; the action bar appears at the bottom.
3. Click **Combine** to merge selected notes.
4. Click **Clear** or press `Esc` to deselect.

## Customization

Shortcuts live in `handleKeydown()` in `static/app.js`. Card keyboard activation is in the `keydown` delegation block immediately after the `click` delegation.
