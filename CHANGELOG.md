# Changelog - Wiki Notebook

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-05-06

### Added
- **HTML file import** — `.html`/`.htm` files parsed as single chunks; FTS5 indexes stripped plain text via `COALESCE(search_text, body)`; DOMPurify preserves table/section/article elements in preview
- **Import preview toolbar** — "Select All" / "Deselect All" toggle with live "N of M selected" counter; confirm button shows count ("Import 5 Selected")
- **Chunk search filter** — client-side filter by title/body; hidden cards excluded from select-all and import counts
- **Keyboard shortcuts** — `?` opens help modal; `Ctrl+A`/`Ctrl+Shift+A` select/deselect visible chunks; `Ctrl+F` focuses chunk search; `N`/`Ctrl+N` new note (grid); `E` toggle edit (detail); `Escape` clears filter then exits import preview

### Changed
- AbortController moved to `state.importAbort` (was DOM property); properly cleaned up in `navigateTo()` when leaving import-preview
- Import loop restructured for per-note error recovery: successful imports uncheck their cards; failed count shown in alert with retry guidance

### Fixed
- `{ signal }` passed AbortController object instead of `.signal` — event listeners were never aborting (listener leak on re-render)
- `card` null-guard missing in select-all loop and `updateImportSelectionCount`
- `isNaN(idx)` guard added in `filterImportChunks` and `handleImportSelected`
- AI suggest button had bare `catch {}` with no logging
- `return` missing after Escape clears chunk search (fell through to `confirmLeaveEdit` check)

## [0.3.1] - 2026-05-05
### Added
### Changed
### Fixed

## [0.3.0] - 2026-04-23

### Added
- **Grid-first UI** — notes grid is now the home view; clicking a note opens a full-page detail view
- **View state machine** — `state.view` (`"grid"` | `"detail"` | `"import-preview"`) drives `renderView()`; `navigateTo()` is the only transition function
- **File import** — upload `.txt`/`.md` files, preview and select chunks before creating notes; drag-to-reorder chunks
- **AI chunk title suggestions** — `POST /api/notes/suggest-title` + ✦ button per import chunk
- **Autosave** — debounced 2-second autosave for existing notes with inline status indicator
- **Keyboard navigation** — note cards have `tabindex="0"`; Enter/Space activates the focused card
- **Word & char count** — live count shown in editor status bar below textarea
- **Scroll management** — detail view scrolls to top on open; grid restores scroll position on back
- `chunking.py` — hybrid `.txt`/`.md` chunker (headings → paragraphs → word-boundary fallback, MIN_CHUNK_SIZE=10)
- `/api/notes/import` — multipart upload endpoint (5 MB limit, `secure_filename` guard)
- `/api/notes/suggest-title` — stateless Ollama title suggestion endpoint

### Changed
- Title input auto-focused when switching to edit mode
- Unsaved-changes guard (`confirmLeaveEdit()`) on all view transitions
- Import preview route ordered before parametric routes in Flask blueprint

### Fixed
- Note opening at top of page, out of view of scroll position

## [0.1.0] - 2026-04-16

### Added
- Initial project scaffolding
- Flask API with CRUD operations
- SQLite with FTS5 search
- Auto-categorization with Ollama
- Vanilla JavaScript frontend
- Full test suite

### Features
- Create, read, update, delete notes
- Full-text search with BM25 ranking
- Snippet highlighting
- Category filtering
- Tag management
- Markdown preview
- Keyboard shortcuts
- Dark silver theme UI

### Technical
- pytest test suite
- FTS5 triggers for search index sync
- Background enrichment worker
- Input validation
- XSS protection with DOMPurify

## [0.0.1] - 2026-04-16

### Added
- Project skeleton
- Base Flask application
- Database schema with FTS5
- Initial API endpoints

## [0.2.0] - 2026-04-16
### Added
- Multi-select functionality with checkboxes
- Combine notes endpoint (concatenate and AI modes)
- Optimize note endpoint with revision tracking
- Undo optimize endpoint

### Changed
### Fixed
### Removed
