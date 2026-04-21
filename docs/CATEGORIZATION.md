# Automatic Categorization

Wiki Notebook automatically categorizes notes using AI (Ollama) or keyword heuristics.

## How It Works

### Automatic Categorization (On Create/Update)

When you create a note **without** specifying category and tags, the app automatically:
1. Enqueues the note for background enrichment
2. Calls Ollama (if available) or falls back to keyword analysis
3. Updates the note with category and tags

The frontend shows a "Categorizing..." indicator until enrichment completes.

### Manual Categorization

Click the **"Re-categorize"** button on any note to manually trigger categorization, even if the note already has a category.

This is useful if you've updated the note content and want to refresh the categorization.

### Categories

The system recognizes these categories (via keyword matching or AI):

- **meetings** - Team discussions, sync meetings, calls
- **project ideas** - Features, concepts, proposals
- **journal** - Personal reflections, daily entries
- **recipes** - Cooking, meal prep, food
- **notes** - General notes, reminders, tasks
- **learning** - Study materials, tutorials, courses
- **uncategorized** - Notes that don't fit other categories

## API Endpoints

### POST /api/notes

Create a note. If you don't provide `category` and `tags`, enrichment is enqueued:

```json
{
  "title": "Team Meeting Notes",
  "body": "Discussed Q1 roadmap and timelines"
}
```

Response: Note with `enrichment_pending: true` if enrichment is in progress.

### POST /api/notes/<id>/categorize

Manually trigger categorization for a note:

```bash
curl -X POST http://localhost:5000/api/notes/42/categorize
```

Response: Updated note with new category and tags.

### GET /api/notes?category=meetings

Filter notes by category. Example:

```bash
curl http://localhost:5000/api/notes?category=meetings
```

Returns all notes in the "meetings" category.

### GET /api/health

Check enrichment queue metrics:

```bash
curl http://localhost:5000/api/health
```

Response includes `enrichment_queue_size` - number of notes pending categorization.

## Configuration

### Enabling/Disabling AI Enrichment

Ensure Ollama is running on `localhost:11434`:

```bash
ollama pull qwen2.5-coder  # or any model
ollama serve
```

If Ollama is unavailable, the app automatically falls back to keyword-based categorization.

### Customizing Categories

Edit the category keywords in `wiki_notebook/ai/categorize.py`:

```python
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "meetings": ["meeting", "call", "zoom", ...],
    "project ideas": ["project", "feature", ...],
    # ... add or modify as needed
}
```

Then restart the app for changes to take effect.

## Troubleshooting

### "Categorizing..." indicator never disappears

**Check enrichment queue status:**
```bash
curl http://localhost:5000/api/health | jq .enrichment_queue_size
```

If the queue is > 0, the worker may be overloaded. Restart the app.

### Notes always categorized as "uncategorized"

**Ollama is likely unavailable.** Verify:
```bash
curl http://localhost:11434/api/tags
```

If Ollama isn't running, switch to keyword-based categorization or start Ollama.

### Want to disable auto-categorization

Set `category` and `tags` explicitly when creating notes. The worker only processes notes without explicit categorization.
```json
{
  "title": "My Note",
  "body": "Content",
  "category": "meetings",
  "tags": ["important"]
}
```
