# Grid-First UI with Card Detail View and File Import

**Date:** 2026-04-22
**Status:** Approved
**Approach:** State-machine view switching (single `app.js`)

## Summary

Restructure the Wiki Notebook UI so the notes grid is the primary home view. Clicking a note opens a full-page detail view (replacing the grid) in read-only preview mode. Add a "+ New Note" button with dropdown for file import. Import `.txt` and `.md` files with hybrid chunking and a preview step before note creation.

## Decisions

| Question | Answer |
|----------|--------|
| Navigation model | Grid replaces with detail view; back button returns (Option C) |
| Default detail mode | Read-only preview; explicit Edit button (Option A) |
| New note entry point | "+ New Note" button in header (Option A) |
| Import chunking | Hybrid: headings > paragraphs > size fallback (Option C) |
| Import entry point | Dropdown on "+ New Note" button (Option B) |
| Close/back behavior | Preview = instant; edit with changes = confirm dialog (Option A) |
| Import preview | Show proposed chunks before creating notes (Option A) |

## Architecture

### View State Machine

The `state` object gains a `view` property with three values:

```
  grid  <->  detail
   |
  import-preview
```

- **`"grid"`** — Notes list visible, editor hidden. Default on load.
- **`"detail"`** — Single note view. Sub-states via `state.isPreviewMode` (true = reading, false = editing).
- **`"import-preview"`** — Import chunk review screen. Grid hidden.

#### Transitions

| From | To | Trigger |
|------|-----|---------|
| grid | detail (preview) | Click a note card |
| grid | detail (edit) | Click "+ New Note" |
| grid | import-preview | Select file from import dropdown |
| detail | grid | Click X / back button (with unsaved-changes guard if editing) |
| import-preview | grid | Click "Cancel" or "Import All" (after creating notes) |

#### Implementation

A single `renderView()` function toggles visibility of three top-level sections in `index.html`:
- `#notes-list-container` (grid)
- `#editor-container` (detail)
- `#import-preview-container` (new)

### Approach

State-machine view switching within the existing single `app.js` file. No new dependencies, no module system migration. Extends the existing `state` + `render*()` function pattern.

**Rationale:** The app is small enough (~772 lines) that a single file with clear state-machine logic works well. If `app.js` grows past ~1000 lines in a future iteration, that's the right time to split.

## Grid View (Home)

### Changes from current UI

- `#editor-container` is **hidden by default** — grid owns the full `page-content` area on load.
- Note cards lose the "Edit" button in the card footer. Entire card is clickable (opens detail in preview mode). Checkbox for multi-select stays.
- "Recent" heading, category sidebar, search, multi-select action bar, empty state — all unchanged.

### New elements

- **"+ New Note" button** in the header bar, between search input and a11y controls. Styled as compact `btn-primary`. Clicking transitions to detail view in edit mode with blank note.
- **Dropdown caret** on the New Note button. Clicking the caret reveals a small menu with one option: "Import from file...". The dropdown is a simple absolutely-positioned `<ul>` toggled by JS. Clicking outside closes it.

## Detail View (Note Preview/Editor)

### Layout

Replaces the grid in `page-content`. Same max-width (940px).

1. **Top bar** — "< Notes" link on the left (returns to grid with unsaved-changes guard). X button on the right (same behavior).
2. **Title** — rendered as text in preview mode, `<input>` in edit mode.
3. **Category/tags section** — shown below title when present (existing `#editor-category-section`).
4. **Body** — rendered markdown in preview mode, textarea in edit mode.
5. **Action buttons** per mode:
   - **Preview mode:** Edit (primary), Re-categorize (secondary), Delete (danger)
   - **Edit mode:** Save (primary), Preview (secondary), Delete (danger), Undo (link, if applicable)

### Behavior

- Opening from card click -> preview mode (`state.isPreviewMode = true`)
- Opening from "+ New Note" -> edit mode, blank fields, no delete/undo buttons
- "Edit" button -> edit mode, tracks `state.hasUnsavedChanges` (set on input/change events on title or body)
- "Save" -> saves, resets `hasUnsavedChanges`, stays in detail view, switches to preview mode
- Back/X while `state.hasUnsavedChanges === true` -> `confirm("You have unsaved changes. Discard?")` — cancel stays, OK returns to grid
- Escape key: editing with changes -> confirm dialog; preview -> return to grid directly
- `Ctrl+Enter` to save remains

### Reused functions

`switchToEditMode()`, `switchToPreviewMode()`, `handleSave()`, `handleDelete()`, `handleUndo()`, `handleRecategorize()`, `displayEditorCategory()` — mostly unchanged, wired to new view transitions.

## File Import

### Backend: `POST /api/notes/import`

Accepts `multipart/form-data` with one or more `.txt` or `.md` files. Returns proposed chunks as JSON without creating notes.

```json
{
  "chunks": [
    {
      "title": "Section heading or filename-1",
      "body": "chunk content...",
      "source_file": "my-document.md",
      "index": 0
    }
  ]
}
```

### Chunking algorithm (hybrid)

1. **Markdown files:** split on any ATX heading (`#` through `######`). Each heading becomes the chunk title; content until the next heading becomes the body.
2. **Text files:** split on double-newline (blank line) paragraph boundaries.
3. **Oversized chunks:** if any chunk exceeds ~2000 characters, sub-split on the next paragraph/blank-line boundary.
4. **No structure fallback:** if a file has no headings and no blank lines, split at ~2000 character boundaries on the nearest word break.
5. **Tiny fragment merging:** chunks smaller than ~50 characters get merged into the previous chunk.
6. **Chunk titles:** heading text if available, otherwise `"filename - Part N"`.

### Frontend: Import Preview View

**Trigger:** User clicks dropdown caret on "+ New Note" -> "Import from file..." -> browser file picker (accepts `.txt,.md`, `multiple` selection). Files uploaded to `POST /api/notes/import`, response renders the preview.

**Layout:**

1. **Top bar** — "< Cancel" link on the left (returns to grid, discards everything)
2. **Heading** — "Import Preview" with file name and chunk count
3. **Chunk list** — vertical list of cards, each showing:
   - Checkbox (checked by default) — uncheck to exclude
   - Chunk title (editable inline — text input)
   - Body preview (first ~200 chars, plain text, not editable)
   - Character count badge
4. **Bottom actions:**
   - "Import Selected" (primary) — creates notes via `POST /api/notes` for each checked chunk, then transitions to grid
   - "Cancel" (secondary) — returns to grid

**Multi-file:** File picker allows `multiple`. All files sent in one request. Chunks returned with `source_file` field. Preview groups chunks by source file with a subheading.

## Testing Strategy

### Backend tests (pytest)

- **Chunking logic:** heading-based split, paragraph split, oversized sub-split, tiny-fragment merging, mixed heading/no-heading files, empty files, single-line files
- **Import endpoint:** valid `.md` upload, valid `.txt` upload, multi-file upload, rejected file types (`.pdf`), empty file, large file handling
- **Edge cases:** files with only headings (no body), files with no newlines, Unicode content, Windows-style `\r\n` line endings

### Frontend/UI tests (existing CDP pattern)

- Grid view loads as default (editor hidden)
- Click card -> detail view replaces grid
- Back/X from preview -> returns to grid
- Back/X from edit with unsaved changes -> confirm dialog
- New Note button -> opens edit mode
- Import dropdown opens/closes
- Import preview renders chunks with checkboxes
- Uncheck chunk -> excluded from import

### Unchanged (no new tests needed)

Category sidebar, search, multi-select/combine, dark mode, a11y toggles.

## Files to modify

| File | Changes |
|------|---------|
| `static/index.html` | Add New Note button + dropdown to header, add import-preview section, add detail top bar (back/X), hide editor by default |
| `static/app.js` | Add `state.view`, `renderView()`, view transition functions, import upload/preview logic, unsaved-changes tracking, New Note dropdown |
| `static/styles.css` | Styles for detail top bar, New Note button + dropdown, import preview cards/list |
| `wiki_notebook/routes/notes.py` | Add `POST /api/notes/import` endpoint |
| `wiki_notebook/chunking.py` | New file — hybrid chunking algorithm |
| `tests/test_chunking.py` | New file — chunking unit tests |
| `tests/test_import.py` | New file — import endpoint integration tests |
| `tests/ui/test_ui.py` | Add view-switching, import preview, unsaved-changes UI tests |
