# Wiki Notebook - Project Overview

## Purpose

Wiki Notebook is a self-hosted, offline-first journal and wiki designed for:

1. **Personal Knowledge Management** - Capture thoughts, ideas, and information
2. **Note Consolidation** - Combine related notes into single documents
3. **AI-Enhanced Writing** - Optimize notes with AI-powered improvements
4. **Local Data Sovereignty** - Keep all data on your own device

## Goals

- **Offline-First** - Works without internet connection
- **Self-Hosted** - No cloud services, no telemetry
- **AI-Enabled** - Leverages local Ollama for intelligent features
- **Simple** - Easy to install and maintain
- **Secure** - XSS protection, input validation, parameterized queries

## Key Features

| Feature | Description |
|---------|-------------|
| **CRUD Operations** | Create, read, update, delete notes |
| **Auto-Categorization** | Ollama suggests category + tags on save |
| **Full-Text Search** | FTS5 with BM25 ranking and snippet highlighting |
| **Multi-Select & Combine** | Merge notes with concatenate or AI synthesis |
| **Optimize & Undo** | AI-powered writing enhancement with revision tracking |
| **Category Filtering** | Organize notes by category |
| **Markdown Preview** | Live preview of Markdown content |
| **Keyboard Shortcuts** | Fast navigation and actions |

## Use Cases

- **Developers** - Technical notes, snippets, documentation
- **Writers** - Drafts, ideas, research notes
- **Researchers** - Paper notes, experiment logs
- **Students** - Lecture notes, study materials
- **Project Managers** - Meeting notes, action items

## Data Sovereignty

- All notes stored in local SQLite database
- No cloud services, no telemetry, no tracking
- Export is simply copying the `.db` file
- Full control over data and privacy
