# Wiki Notebook Documentation

A self-hosted, offline-first journal and wiki with automatic categorization, full-text search, multi-note composition, and local Ollama-powered optimization.

## Quick Links

- [Overview](./overview.md) - Project purpose and goals
- [Architecture](./architecture.md) - High-level design and data flow
- [Tech Stack](./tech-stack.md) - Technologies and versions
- [Installation](./installation.md) - Setup & usage instructions
- [API Reference](./api/reference.md) - API endpoint documentation
- [Developer Guide](./development.md) - Contributing and development

## Project Status

**Current Version:** 0.2.0 (pre-release)

| Feature | Status |
|---------|--------|
| CRUD API | ✅ Complete |
| Search & Indexing | ✅ Complete |
| Auto-Categorization | ✅ Complete |
| Multi-Select & Combine | ✅ Complete |
| Optimize & Insights | ✅ Complete |
| Polish & Packaging | ✅ Complete |

**Test Coverage:** 82 tests passing

## Getting Started

1. **Prerequisites:** Python 3.11+, SQLite with FTS5, Ollama (for AI features)
2. **Install:** See [Installation Guide](./installation.md)
3. **Run:** `python -m wiki_notebook`
4. **Access:** `http://localhost:5000/`

## Documentation Structure

```
docs/
├── README.md              (this file)
├── overview.md            - Project overview and goals
├── architecture.md        - System architecture
├── tech-stack.md          - Technologies used
├── installation.md        - Installation guide
├── development.md         - Developer guide
├── api/
│   ├── reference.md       - API endpoint reference
│   └── schema.md          - Data models and schemas
└── guides/
    ├── keyboard-shortcuts.md
    └── troubleshooting.md
```

## Support

- GitHub: https://github.com/coreconduit/wiki-notebook
- Issues: https://github.com/coreconduit/wiki-notebook/issues
- License: MIT
