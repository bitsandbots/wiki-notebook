-- Wiki Notebook Schema
-- Authoritative schema definition with FTS5 triggers for search index sync

-- Main notes table
CREATE TABLE IF NOT EXISTS notes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    body          TEXT NOT NULL,
    category      TEXT,
    tags          TEXT,                    -- JSON array
    created_at    TEXT NOT NULL,           -- ISO 8601
    updated_at    TEXT NOT NULL,
    optimized_at  TEXT,
    source_ids    TEXT,                    -- JSON array for combined notes
    content_type  TEXT NOT NULL DEFAULT 'markdown',
    search_text   TEXT                     -- Stripped text for FTS5 (html notes)
);

-- Add columns for existing databases (idempotent via error suppression)
-- SQLite does not support ADD COLUMN IF NOT EXISTS, so catch the error.
-- Using INSERT OR IGNORE into a pragma-based check is unreliable across
-- SQLite versions. init_db() wraps this in a try/except, so these are
-- safe to run unconditionally.
-- The column additions below are intentionally left here for documentation;
-- the idempotency is handled by the init_db migration logic.

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title, body, category, tags,
    content='notes', content_rowid='id',
    tokenize='porter unicode61'
);

-- Triggers to keep FTS5 in sync with notes table.
-- For body, use COALESCE(search_text, body): html notes store stripped text
-- in search_text; markdown notes leave it NULL and index body directly.
DROP TRIGGER IF EXISTS notes_ai;
CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(rowid, title, body, category, tags)
    VALUES (new.id, new.title, COALESCE(new.search_text, new.body),
            new.category, new.tags);
END;

DROP TRIGGER IF EXISTS notes_au;
CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, body, category, tags)
    VALUES ('delete', old.id, old.title,
            COALESCE(old.search_text, old.body), old.category, old.tags);
    INSERT INTO notes_fts(rowid, title, body, category, tags)
    VALUES (new.id, new.title, COALESCE(new.search_text, new.body),
            new.category, new.tags);
END;

DROP TRIGGER IF EXISTS notes_ad;
CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, body, category, tags)
    VALUES ('delete', old.id, old.title,
            COALESCE(old.search_text, old.body), old.category, old.tags);
END;

-- Note revisions table for undo functionality
CREATE TABLE IF NOT EXISTS note_revisions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id     INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    reason      TEXT NOT NULL,             -- 'optimize' | 'combine' | 'manual'
    created_at  TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_revisions_note ON note_revisions(note_id);
CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category);
CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at DESC);
