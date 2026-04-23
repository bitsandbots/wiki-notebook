# Wiki Notebook — Project Overview

## Purpose

Wiki Notebook is a self-hosted, offline-first journal and wiki designed for personal knowledge management without cloud dependencies.

## Goals

- **Offline-First** — works with no internet connection
- **Self-Hosted** — no cloud services, no telemetry
- **AI-Enabled** — local Ollama for categorization, optimization, and title generation
- **Simple** — zero-build frontend, single SQLite file, one-liner install
- **Secure** — XSS protection, input validation, parameterized queries

## Key Features

| Feature | Description |
|---------|-------------|
| **Grid-First UI** | Notes grid is home view; clicking opens full-page detail |
| **CRUD Operations** | Create, read, update, delete notes with Markdown support |
| **Autosave** | Debounced 2-second autosave for existing notes |
| **Auto-Categorization** | Ollama suggests category + tags on save |
| **Full-Text Search** | FTS5 with BM25 ranking and snippet highlighting |
| **File Import** | Upload `.txt`/`.md` files; preview and select chunks before creating notes |
| **AI Chunk Titles** | Suggest titles for import chunks via Ollama |
| **Multi-Select & Combine** | Merge notes with concatenate or AI synthesis |
| **Optimize & Undo** | AI-powered rewrite with revision tracking and undo |
| **Keyboard Navigation** | Tab through cards, Enter/Space to open, `/` to search |
| **Drag-to-Reorder** | Reorder import preview chunks before confirming |
| **Word & Char Count** | Live count shown in editor status bar |

## Use Cases

- Developers — technical notes, snippets, documentation
- Writers — drafts, ideas, research notes
- Researchers — paper notes, experiment logs
- Students — lecture notes, study materials
- Anyone who wants their notes on their own device

## Data Sovereignty

- All notes stored in a local SQLite database (`data/notebook.db`)
- No cloud services, no telemetry, no tracking
- Backup = copy the `.db` file
- Full control over data and privacy
