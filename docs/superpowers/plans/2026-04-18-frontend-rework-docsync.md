# Wiki Notebook — Frontend Rework (docsync Design System) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework wiki-notebook's frontend (`static/`) to match the docsync design system: self-hosted fonts, `--cc-*` CSS tokens, dark navy sidebar, compact a11y icon buttons in the header, dark mode toggle, mobile sidebar, and card-bar note components.

**Architecture:** Pure frontend change — no Python/backend files touched. All changes are in `static/styles.css`, `static/index.html`, `static/a11y.js`, and `static/app.js` (minor). Font woff2 files are copied from `~/docsync/docsync/static/fonts/`. Inline JS (dark mode, mobile sidebar) replaces the separate `a11y.js` file.

**Tech Stack:** Vanilla HTML/CSS/JS (no build step), docsync CSS design system, woff2 self-hosted fonts.

---

## Reference Files

| Source (docsync) | Role |
|---|---|
| `~/docsync/docsync/static/style.css` | CSS token names, component patterns to adopt |
| `~/docsync/docsync/templates/base.html` | Header structure, sidebar markup, inline JS patterns |
| `~/docsync/docsync/static/fonts/` | 4 woff2 files to copy |

| Target (wiki-notebook) | What changes |
|---|---|
| `static/styles.css` | Full rework: tokens → `--cc-*`, new components |
| `static/index.html` | New header, remove a11y toolbar, add dark mode + mobile sidebar |
| `static/a11y.js` | Simplified: remove text-size select; match new button IDs |
| `static/app.js` | Minor: `.category-item` class retained; no selector changes needed |

---

## File Structure

```
static/
├── fonts/                          CREATE (copy from docsync)
│   ├── exo-2-latin-700-normal.woff2
│   ├── plus-jakarta-sans-latin-400-normal.woff2
│   ├── plus-jakarta-sans-latin-600-normal.woff2
│   └── ibm-plex-mono-latin-400-normal.woff2
├── styles.css                      MODIFY (full rework)
├── index.html                      MODIFY (header, layout, inline JS)
├── a11y.js                         MODIFY (new button IDs, drop text-size)
└── app.js                          MODIFY (minor: `.section-title` ref)
```

---

## Task 1: Copy Self-Hosted Fonts

**Files:**
- Create: `static/fonts/` (4 woff2 files)

- [ ] **Step 1: Copy font files**

```bash
cp -r ~/docsync/docsync/static/fonts ~/wiki-notebook/static/fonts
```

- [ ] **Step 2: Verify**

```bash
ls ~/wiki-notebook/static/fonts/
```

Expected output:
```
exo-2-latin-700-normal.woff2
ibm-plex-mono-latin-400-normal.woff2
plus-jakarta-sans-latin-400-normal.woff2
plus-jakarta-sans-latin-600-normal.woff2
```

- [ ] **Step 3: Commit**

```bash
cd ~/wiki-notebook
git add static/fonts/
git commit -m "chore: add self-hosted fonts from docsync"
```

---

## Task 2: CSS — Design Tokens Layer

Replace the entire `:root` block in `static/styles.css` and add `@font-face` declarations. This is the foundation all other CSS tasks build on.

**Files:**
- Modify: `static/styles.css:1-83`

- [ ] **Step 1: Replace the top of styles.css**

Replace everything from line 1 through the closing brace of the `:root` block (approximately line 83) with:

```css
/* Wiki Notebook — CoreConduit Brand System v2.1 Silver
   Tokens mirror ~/docsync — keep in sync.
   Fonts: Exo 2 · Plus Jakarta Sans · IBM Plex Mono (self-hosted)
*/

/* Self-hosted fonts — no external CDN */
@font-face { font-family:"Exo 2"; src:url("fonts/exo-2-latin-700-normal.woff2") format("woff2"); font-weight:700; font-display:swap; }
@font-face { font-family:"Plus Jakarta Sans"; src:url("fonts/plus-jakarta-sans-latin-400-normal.woff2") format("woff2"); font-weight:400; font-display:swap; }
@font-face { font-family:"Plus Jakarta Sans"; src:url("fonts/plus-jakarta-sans-latin-600-normal.woff2") format("woff2"); font-weight:600; font-display:swap; }
@font-face { font-family:"IBM Plex Mono"; src:url("fonts/ibm-plex-mono-latin-400-normal.woff2") format("woff2"); font-weight:400; font-display:swap; }

/* ── Reduced Motion Support ─────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* ── Reset ──────────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── CoreConduit Brand Tokens ───────────────────────────────────────────── */
:root {
  --cc-bg-base:           #c5c9d0;
  --cc-bg-panel:          #cdd1d8;
  --cc-bg-card:           #d8dbe1;
  --cc-bg-elevated:       #e2e5ea;
  --cc-bg-input:          #bcc0c8;
  --cc-bg-hover:          #b5b9c2;
  --cc-border-subtle:     #b8bcc4;
  --cc-border:            #a8adb6;
  --cc-border-strong:     #969ba5;
  --cc-text-primary:      #1e232b;
  --cc-text-secondary:    #3a404a;
  --cc-text-muted:        #636a76;
  --cc-text-faint:        #7d8491;
  --cc-text-on-dark:      #eaecf0;
  --cc-text-on-accent:    #ffffff;
  --cc-blue-600:          #1b6ad4;
  --cc-blue-500:          #2b7de9;
  --cc-blue-400:          #4a9eff;
  --cc-blue-300:          #6bb3ff;
  --cc-blue-glow:         rgba(43,125,233,0.12);
  --cc-blue-glow-strong:  rgba(43,125,233,0.22);
  --cc-orange-600:        #c55d0a;
  --cc-orange-500:        #e07018;
  --cc-orange-400:        #f08030;
  --cc-orange-glow:       rgba(224,112,24,0.12);
  --cc-navy-900:          #0b1220;
  --cc-navy-800:          #0f1a2e;
  --cc-navy-700:          #152240;
  --cc-navy-600:          #1c2d52;
  --cc-success:           #1a9a4a;
  --cc-success-bg:        rgba(26,154,74,0.1);
  --cc-warning:           #c08a15;
  --cc-warning-bg:        rgba(192,138,21,0.1);
  --cc-error:             #d43030;
  --cc-error-bg:          rgba(212,48,48,0.1);
  --cc-font-display:      "Exo 2", sans-serif;
  --cc-font-body:         "Plus Jakarta Sans", sans-serif;
  --cc-font-mono:         "IBM Plex Mono", monospace;
  --cc-radius-sm:         6px;
  --cc-radius-md:         10px;
  --cc-radius-lg:         14px;
  --cc-shadow-sm:         0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06);
  --cc-shadow-card:       0 2px 8px rgba(0,0,0,.10), 0 1px 3px rgba(0,0,0,.06);
  --cc-shadow-elevated:   0 8px 24px rgba(0,0,0,.12), 0 2px 6px rgba(0,0,0,.08);

  /* Accessibility tokens */
  --cc-focus-ring:        #0f3c78;
  --cc-focus-ring-halo:   #ffd34d;
  --cc-link-color:        #164a94;

  /* Layout */
  --sidebar-w: 220px;
  --header-h:  52px;
}

/* ── User Preference Modes ──────────────────────────────────────────────── */
:root[data-text-size="large"]  { font-size: 112.5%; }
:root[data-text-size="xlarge"] { font-size: 125%;   }

:root[data-contrast="high"] {
  --cc-bg-base:           #ffffff;
  --cc-bg-card:           #f5f5f5;
  --cc-bg-panel:          #f0f0f0;
  --cc-bg-elevated:       #e8e8e8;
  --cc-bg-input:          #ffffff;
  --cc-text-primary:      #000000;
  --cc-text-secondary:    #1a1a1a;
  --cc-text-muted:        #333333;
  --cc-text-faint:        #4d4d4d;
  --cc-text-on-dark:      #ffffff;
  --cc-blue-600:          #0f4c91;
  --cc-blue-500:          #0052cc;
  --cc-blue-400:          #0066ff;
  --cc-orange-600:        #7a3808;
  --cc-orange-500:        #b85a00;
  --cc-border:            #333333;
  --cc-border-strong:     #000000;
  --cc-border-subtle:     #666666;
  --cc-navy-800:          #000033;
  --cc-navy-700:          #000052;
}

:root[data-font="legible"] {
  --cc-font-body: 'Atkinson Hyperlegible', system-ui, sans-serif;
}

:root[data-motion="reduced"] *,
:root[data-motion="reduced"] *::before,
:root[data-motion="reduced"] *::after {
  animation: none !important;
  transition: none !important;
}

/* ── Dark Mode ──────────────────────────────────────────────────────────── */
[data-theme="dark"] {
  --cc-bg-base:       #0b1220;
  --cc-bg-panel:      #080e1a;
  --cc-bg-card:       #0f1a2e;
  --cc-bg-elevated:   #152240;
  --cc-bg-input:      #0b1220;
  --cc-bg-hover:      #1c2d52;
  --cc-border-subtle: #1c2d52;
  --cc-border:        #243558;
  --cc-border-strong: #2e436a;
  --cc-text-primary:  #eaecf0;
  --cc-text-secondary:#c5c9d0;
  --cc-text-muted:    #8892a4;
  --cc-text-faint:    #636a76;
  --cc-blue-glow:     rgba(43,125,233,0.18);
  --cc-orange-glow:   rgba(224,112,24,0.15);
  --cc-success-bg:    rgba(26,154,74,0.15);
  --cc-warning-bg:    rgba(192,138,21,0.15);
  --cc-error-bg:      rgba(212,48,48,0.15);
}
```

- [ ] **Step 2: Verify CSS parses (no syntax errors)**

```bash
cd ~/wiki-notebook
python -m wiki_notebook &
sleep 2
curl -s http://localhost:5000/static/styles.css | head -5
kill %1
```

Expected: CSS starts with `/* Wiki Notebook —` (server serves it).

- [ ] **Step 3: Commit**

```bash
cd ~/wiki-notebook
git add static/styles.css
git commit -m "refactor(css): migrate to cc-* design tokens, dark mode, self-hosted fonts"
```

---

## Task 3: CSS — Base, Focus, Skip Link

Replace the base/reset/focus/skip-link section (after the tokens block, formerly lines ~84–220) with the docsync pattern.

**Files:**
- Modify: `static/styles.css` — base section

- [ ] **Step 1: Replace base styles**

Find and replace the section from `/* === BASE ===` (or `/* ============ BASE`) through the `.skip-link` block with:

```css
/* ── Base ──────────────────────────────────────────────────────────────── */
html { font-size: 16px; scroll-behavior: smooth; scroll-padding-top: 68px; }

body {
  font-family: var(--cc-font-body);
  background: var(--cc-bg-base);
  color: var(--cc-text-primary);
  line-height: 1.6;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--cc-font-display);
  color: var(--cc-text-primary);
  line-height: 1.25;
}
h1 { font-size: 1.6rem; font-weight: 700; letter-spacing: -.3px; }
h2 { font-size: 1.2rem; font-weight: 600; }
h3 { font-size: 1.05rem; font-weight: 600; }
h4 { font-size: .95rem; font-weight: 600; }

p { color: var(--cc-text-secondary); margin-bottom: 1rem; }

a {
  color: var(--cc-link-color);
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 2px;
  transition: color 0.15s ease;
}
a:hover { color: var(--cc-blue-600); text-decoration-thickness: 3px; }

/* ── Focus Indicators (WCAG 2.4.7) ─────────────────────────────────────── */
:focus-visible {
  outline: 3px solid var(--cc-focus-ring) !important;
  outline-offset: 2px;
  border-radius: 4px;
  box-shadow: 0 0 0 5px var(--cc-focus-ring-halo) !important;
}

/* ── Skip Link (WCAG 2.4.1) ─────────────────────────────────────────────── */
.skip-link {
  position: absolute;
  top: 8px;
  left: 8px;
  background: var(--cc-navy-900);
  color: #fff;
  padding: 12px 20px;
  border-radius: var(--cc-radius-sm);
  font-family: var(--cc-font-display);
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  z-index: 1001;
  transform: translateY(-150%);
  transition: transform 0.15s ease;
}
.skip-link:focus { transform: translateY(0); }
```

- [ ] **Step 2: Run backend tests to verify no regressions**

```bash
cd ~/wiki-notebook
pytest -q
```

Expected: `82 passed` (or current count).

- [ ] **Step 3: Commit**

```bash
git add static/styles.css
git commit -m "refactor(css): update base, focus, skip-link to cc-* tokens"
```

---

## Task 4: CSS — Header and A11y Controls

Replace the `.topbar` and `.a11y-toolbar` sections with docsync's `.site-header` pattern.

**Files:**
- Modify: `static/styles.css` — header and a11y toolbar sections

- [ ] **Step 1: Remove old .a11y-toolbar and .topbar blocks**

Delete these sections entirely (search for `.a11y-toolbar` and `.topbar` CSS blocks).

- [ ] **Step 2: Add new header CSS**

Add after the skip-link block:

```css
/* ── Header ─────────────────────────────────────────────────────────────── */
.site-header {
  position: sticky; top: 0; z-index: 100;
  height: var(--header-h);
  background: var(--cc-navy-800);
  border-bottom: 1px solid var(--cc-navy-700);
  display: flex; align-items: center; gap: 1rem;
  padding: 0 1.25rem;
  box-shadow: 0 1px 0 rgba(255,255,255,.05), 0 2px 8px rgba(0,0,0,.35);
}

.site-logo {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-family: var(--cc-font-display);
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: .02em;
  color: var(--cc-text-on-dark);
  white-space: nowrap;
  text-decoration: none;
}
.site-logo:hover { text-decoration: none; color: #fff; }
.site-logo .logo-mark {
  width: 32px; height: 32px;
  background: var(--cc-blue-500);
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.site-logo .cc-inner { font-size: 0.8rem; font-weight: 800; color: #fff; letter-spacing: 0; }
.site-logo .accent { color: var(--cc-orange-400); }

.header-search {
  flex: 1; max-width: 380px; margin-left: auto;
  position: relative;
}
.header-search input {
  width: 100%;
  background: rgba(255,255,255,.07);
  border: 1px solid rgba(255,255,255,.10);
  border-radius: var(--cc-radius-sm);
  color: var(--cc-text-on-dark);
  font-family: var(--cc-font-body);
  font-size: .875rem;
  padding: .38rem .75rem .38rem 2rem;
  outline: none;
  transition: border-color .15s, background .15s;
}
.header-search input::placeholder { color: rgba(234,236,240,.35); }
.header-search input:focus {
  border-color: var(--cc-blue-400);
  background: rgba(255,255,255,.10);
  box-shadow: 0 0 0 3px var(--cc-blue-glow);
}
.header-search .search-icon {
  position: absolute; left: .6rem; top: 50%; transform: translateY(-50%);
  width: 14px; height: 14px;
  color: rgba(234,236,240,.35);
  pointer-events: none;
}

.header-a11y-controls { display: flex; gap: 0.5rem; align-items: center; }

.a11y-toggle, .theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px; height: 44px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: var(--cc-radius-sm);
  color: rgba(234,236,240,.55);
  cursor: pointer;
  flex-shrink: 0;
  transition: color .12s, background .12s;
  padding: 0;
}
.a11y-toggle:hover, .theme-toggle:hover {
  color: var(--cc-text-on-dark);
  background: rgba(255,255,255,.10);
}
.a11y-toggle[aria-pressed="true"] {
  background: rgba(255,255,255,.15);
  color: var(--cc-text-on-dark);
  border-color: rgba(255,255,255,.2);
}
.a11y-toggle svg, .theme-toggle svg { width: 16px; height: 16px; }

/* Mobile sidebar toggle */
.sidebar-toggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 44px; height: 44px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: var(--cc-radius-sm);
  color: rgba(234,236,240,.7);
  cursor: pointer;
  flex-shrink: 0;
}
.sidebar-toggle svg { width: 16px; height: 16px; }
```

- [ ] **Step 3: Run backend tests**

```bash
cd ~/wiki-notebook && pytest -q
```

Expected: 82 passed.

- [ ] **Step 4: Commit**

```bash
git add static/styles.css
git commit -m "refactor(css): replace topbar/a11y-toolbar with site-header pattern"
```

---

## Task 5: CSS — Dark Navy Sidebar

Replace the `.sidebar` and `.category-list` / `.category-item` blocks with the docsync sidebar pattern. The sidebar items are still rendered by `app.js` with `.category-item` class — CSS maps that class to docsync's visual style.

**Files:**
- Modify: `static/styles.css` — sidebar section

- [ ] **Step 1: Replace sidebar CSS**

Find and replace the `.sidebar`, `.sidebar-title`, `.category-list`, `.category-item` blocks with:

```css
/* ── Layout ──────────────────────────────────────────────────────────────── */
.layout {
  display: grid;
  grid-template-columns: var(--sidebar-w) 1fr;
  min-height: calc(100vh - var(--header-h));
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
.sidebar {
  background: var(--cc-navy-800);
  border-right: 1px solid var(--cc-navy-700);
  padding: 1rem 0;
  position: sticky;
  top: var(--header-h);
  height: calc(100vh - var(--header-h));
  overflow-y: auto;
  overflow-x: hidden;
}
.sidebar::-webkit-scrollbar { width: 3px; }
.sidebar::-webkit-scrollbar-track { background: transparent; }
.sidebar::-webkit-scrollbar-thumb { background: rgba(255,255,255,.08); border-radius: 2px; }

.sidebar-label {
  font-family: var(--cc-font-mono);
  font-size: .62rem;
  font-weight: 500;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: rgba(234,236,240,.3);
  padding: .7rem 1rem .2rem;
  display: block;
}

/* category-item maps to docsync sidebar-link */
.category-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .5rem 1rem;
  min-height: 44px;
  font-size: .825rem;
  color: rgba(234,236,240,.5);
  border-left: 3px solid transparent;
  border-radius: 0 var(--cc-radius-sm) var(--cc-radius-sm) 0;
  transition: color .12s, background .12s, border-color .12s;
  cursor: pointer;
  font-weight: 400;
  list-style: none;
}
.category-item:hover {
  color: var(--cc-text-on-dark);
  background: rgba(255,255,255,.04);
}
.category-item.active {
  color: var(--cc-blue-300);
  border-left-color: var(--cc-blue-400);
  background: var(--cc-blue-glow);
  font-weight: 600;
}
.category-name { font-size: .825rem; }
.category-count {
  font-family: var(--cc-font-mono);
  font-size: .65rem;
  opacity: .5;
}
.category-item.active .category-count { opacity: .8; }

.sidebar-divider {
  height: 1px;
  background: var(--cc-navy-700);
  margin: .5rem 0;
}

/* Mobile sidebar overlay */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  z-index: 89;
  background: rgba(0,0,0,.4);
}
.sidebar-overlay.open { display: block; }
```

- [ ] **Step 2: Run backend tests**

```bash
cd ~/wiki-notebook && pytest -q
```

Expected: 82 passed.

- [ ] **Step 3: Commit**

```bash
git add static/styles.css
git commit -m "refactor(css): dark navy sidebar with cc-* docsync pattern"
```

---

## Task 6: CSS — Main Content, Note Cards, Editor, Prose

Replace the main content area, note card, and editor CSS.

**Files:**
- Modify: `static/styles.css` — content, note-card, editor sections

- [ ] **Step 1: Replace main content and note cards**

Find and replace the `.content`, `.note-card*`, `.editor*` blocks with:

```css
/* ── Main ───────────────────────────────────────────────────────────────── */
.main { min-width: 0; display: flex; flex-direction: column; }
.page-content { flex: 1; padding: 2rem 2.25rem; max-width: 940px; }

/* ── Section header ─────────────────────────────────────────────────────── */
.section-title {
  font-family: var(--cc-font-display);
  font-size: 1.05rem;
  font-weight: 500;
  color: var(--cc-text-primary);
  margin: 1.5rem 0 .75rem;
}

/* ── Note cards (card pattern with gradient bar) ────────────────────────── */
.notes-list {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 16px;
  margin: 0 0 1.5rem;
}

.note-card {
  background: var(--cc-bg-card);
  border: 1px solid var(--cc-border-subtle);
  border-radius: var(--cc-radius-md);
  box-shadow: var(--cc-shadow-card);
  overflow: hidden;
  transition: box-shadow .2s, transform .2s, border-color .15s;
  cursor: pointer;
}
.note-card:hover, .note-card:focus-within {
  box-shadow: var(--cc-shadow-elevated);
  border-color: var(--cc-border-strong);
  transform: translateY(-2px);
}
.note-card.selected {
  border-color: var(--cc-blue-500);
  box-shadow: 0 0 0 3px var(--cc-blue-glow), var(--cc-shadow-card);
}

/* 3px gradient top bar — the brand signature */
.note-card::before {
  content: '';
  display: block;
  height: 3px;
  background: linear-gradient(90deg, var(--cc-blue-500), var(--cc-orange-500));
}

.note-card-header { padding: 14px 16px 0; }
.note-card-title {
  font-family: var(--cc-font-display);
  font-size: .95rem;
  font-weight: 600;
  color: var(--cc-text-primary);
  margin-bottom: .2rem;
}
.note-card-meta {
  display: flex; align-items: center; gap: .5rem;
  font-family: var(--cc-font-mono);
  font-size: .7rem;
  color: var(--cc-text-faint);
  margin-bottom: .4rem;
}
.note-card-category {
  background: var(--cc-blue-glow);
  color: var(--cc-blue-600);
  border-radius: 4px;
  padding: .1rem .4rem;
  font-size: .68rem;
  font-weight: 500;
}
.note-card-body {
  padding: 0 16px 10px;
  font-size: .8rem;
  color: var(--cc-text-muted);
  line-height: 1.5;
  max-height: 3.6em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
.note-card-actions {
  display: flex;
  gap: .35rem;
  padding: .5rem .75rem;
  border-top: 1px solid var(--cc-border-subtle);
}
.note-card-action {
  font-family: var(--cc-font-mono);
  font-size: .68rem;
  font-weight: 600;
  padding: .25rem .6rem;
  min-height: 32px;
  border-radius: 4px;
  border: 1px solid var(--cc-border-subtle);
  background: var(--cc-bg-elevated);
  color: var(--cc-text-muted);
  cursor: pointer;
  transition: background .12s, color .12s;
}
.note-card-action:hover { background: var(--cc-blue-500); color: white; border-color: var(--cc-blue-500); }

.note-card-tags { padding: 0 16px 8px; display: flex; flex-wrap: wrap; gap: .25rem; }
.note-card-tag {
  font-family: var(--cc-font-mono);
  font-size: .65rem;
  background: var(--cc-bg-elevated);
  color: var(--cc-text-muted);
  border: 1px solid var(--cc-border-subtle);
  border-radius: 4px;
  padding: .1rem .35rem;
}

.note-card-checkbox {
  display: flex; align-items: center; gap: .4rem;
  padding: .5rem 1rem 0;
  font-size: .78rem;
  color: var(--cc-text-muted);
  cursor: pointer;
}
.note-card-checkbox input { accent-color: var(--cc-blue-500); }

/* ── Editor ─────────────────────────────────────────────────────────────── */
.editor-container {
  background: var(--cc-bg-card);
  border: 1px solid var(--cc-border-subtle);
  border-radius: var(--cc-radius-md);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--cc-shadow-card);
}
.note-title {
  width: 100%;
  font-family: var(--cc-font-display);
  font-size: 1.25rem;
  font-weight: 700;
  background: transparent;
  border: none;
  border-bottom: 2px solid var(--cc-border-subtle);
  padding: .5rem 0;
  margin-bottom: 1rem;
  color: var(--cc-text-primary);
  outline: none;
  transition: border-color .15s;
}
.note-title:focus { border-bottom-color: var(--cc-blue-500); }
.note-title::placeholder { color: var(--cc-text-faint); }

.note-body {
  width: 100%;
  min-height: 200px;
  font-family: var(--cc-font-mono);
  font-size: .875rem;
  background: var(--cc-bg-input);
  border: 1px solid var(--cc-border-subtle);
  border-radius: var(--cc-radius-sm);
  padding: .75rem 1rem;
  color: var(--cc-text-primary);
  resize: vertical;
  outline: none;
  transition: border-color .15s;
  line-height: 1.6;
}
.note-body:focus { border-color: var(--cc-blue-500); box-shadow: 0 0 0 3px var(--cc-blue-glow); }

.editor-actions {
  display: flex; gap: .5rem; align-items: center;
  margin-top: .75rem;
  flex-wrap: wrap;
}
.editor-shortcut {
  font-family: var(--cc-font-mono);
  font-size: .7rem;
  color: var(--cc-text-faint);
  margin-top: .4rem;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.btn {
  font-family: var(--cc-font-mono);
  font-size: .78rem;
  font-weight: 600;
  padding: .5rem 1rem;
  min-height: 40px;
  border-radius: var(--cc-radius-sm);
  border: 1px solid transparent;
  cursor: pointer;
  display: inline-flex; align-items: center; gap: .3rem;
  transition: background .12s, color .12s, border-color .12s;
}
.btn-primary {
  background: var(--cc-blue-500);
  color: white;
  border-color: var(--cc-blue-500);
}
.btn-primary:hover { background: var(--cc-blue-600); }
.btn-secondary {
  background: var(--cc-bg-elevated);
  color: var(--cc-text-primary);
  border-color: var(--cc-border-subtle);
}
.btn-secondary:hover { background: var(--cc-blue-500); color: white; border-color: var(--cc-blue-500); }
.btn-danger {
  background: var(--cc-error-bg);
  color: var(--cc-error);
  border-color: var(--cc-error);
}
.btn-danger:hover { background: var(--cc-error); color: white; }
.btn-link {
  background: transparent;
  color: var(--cc-blue-500);
  border-color: transparent;
  text-decoration: underline;
}
.btn-link:hover { color: var(--cc-blue-600); }

/* ── Markdown prose (preview) ───────────────────────────────────────────── */
.prose { max-width: 72ch; }
.prose h1, .prose h2, .prose h3, .prose h4 {
  font-family: var(--cc-font-display);
  font-weight: 700;
  color: var(--cc-text-primary);
  line-height: 1.25;
  margin: 1.75em 0 .5em;
}
.prose h1 { font-size: 1.5rem; margin-top: 0; }
.prose h2 { font-size: 1.2rem; border-bottom: 1px solid var(--cc-border-subtle); padding-bottom: .4rem; }
.prose h3 { font-size: 1.05rem; }
.prose h4 { font-size: .95rem; }
.prose p { margin: .75em 0; color: var(--cc-text-secondary); }
.prose ul, .prose ol { margin: .75em 0 .75em 1.5rem; }
.prose li { margin: .25em 0; color: var(--cc-text-secondary); }
.prose code {
  font-family: var(--cc-font-mono);
  font-size: .82em;
  background: var(--cc-blue-glow);
  color: var(--cc-blue-600);
  border-radius: 4px;
  padding: .1em .35em;
  border: 1px solid rgba(43,125,233,.15);
}
.prose pre {
  background: var(--cc-navy-800);
  border-radius: var(--cc-radius-md);
  padding: 1rem 1.25rem;
  overflow-x: auto;
  margin: 1em 0;
  border-left: 3px solid var(--cc-blue-500);
  box-shadow: var(--cc-shadow-card);
}
.prose pre code {
  font-family: var(--cc-font-mono);
  font-size: .82rem;
  background: none;
  color: var(--cc-text-on-dark);
  padding: 0; border: none; border-radius: 0;
}
.prose blockquote {
  border-left: 3px solid var(--cc-orange-500);
  margin: 1em 0;
  padding: .5rem 1rem;
  background: var(--cc-orange-glow);
  color: var(--cc-text-muted);
  border-radius: 0 var(--cc-radius-sm) var(--cc-radius-sm) 0;
}
.prose table {
  width: 100%;
  border-collapse: collapse;
  background: var(--cc-bg-card);
  border-radius: var(--cc-radius-md);
  overflow: hidden;
  border: 1px solid var(--cc-border-subtle);
  margin: 1em 0;
  font-size: .875rem;
}
.prose th {
  text-align: left;
  font-family: var(--cc-font-mono);
  font-size: .68rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: .08em;
  color: var(--cc-text-faint);
  padding: 12px 16px;
  background: var(--cc-bg-elevated);
  border-bottom: 1px solid var(--cc-border-subtle);
}
.prose td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--cc-border-subtle);
  color: var(--cc-text-secondary);
}
.prose tr:last-child td { border-bottom: none; }
.prose tr:hover td { background: var(--cc-bg-elevated); }

/* ── Empty state ─────────────────────────────────────────────────────────── */
.empty-state {
  background: var(--cc-bg-card);
  border: 1.5px dashed var(--cc-border);
  border-radius: var(--cc-radius-md);
  padding: 2.5rem;
  text-align: center;
  color: var(--cc-text-muted);
  font-size: .875rem;
}
```

- [ ] **Step 2: Run backend tests**

```bash
cd ~/wiki-notebook && pytest -q
```

Expected: 82 passed.

- [ ] **Step 3: Commit**

```bash
git add static/styles.css
git commit -m "refactor(css): note cards with gradient bar, editor, prose preview"
```

---

## Task 7: CSS — Action Bar, Footer, Responsive

Add the action bar (multi-select footer), site footer, and responsive breakpoints.

**Files:**
- Modify: `static/styles.css` — action bar, footer, responsive sections

- [ ] **Step 1: Add action bar, footer, responsive CSS**

Append to the end of `styles.css`:

```css
/* ── Action Bar (multi-select) ──────────────────────────────────────────── */
.action-bar {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  background: var(--cc-navy-800);
  border-top: 1px solid var(--cc-navy-700);
  padding: .75rem 1.25rem;
  z-index: 50;
  box-shadow: 0 -2px 12px rgba(0,0,0,.3);
}
.action-bar-content {
  display: flex; align-items: center; gap: .75rem;
  max-width: 1200px;
  flex-wrap: wrap;
}
.action-bar-count {
  font-family: var(--cc-font-mono);
  font-size: .78rem;
  color: var(--cc-text-on-dark);
  margin-right: auto;
}

/* ── Site Footer ─────────────────────────────────────────────────────────── */
.site-footer {
  border-top: 1px solid var(--cc-border-subtle);
  padding: .875rem 2.25rem;
  font-family: var(--cc-font-mono);
  font-size: .72rem;
  color: var(--cc-text-faint);
  display: flex; align-items: center; justify-content: space-between;
}
.footer-logo { font-family: var(--cc-font-display); font-weight: 700; color: var(--cc-text-primary); }
.footer-logo .accent { color: var(--cc-orange-500); }

/* ── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  :root { --sidebar-w: 190px; }
}

@media (max-width: 700px) {
  :root { --sidebar-w: 240px; }

  .layout { grid-template-columns: 1fr; }

  .sidebar {
    position: fixed;
    top: var(--header-h);
    left: 0; bottom: 0;
    z-index: 90;
    width: var(--sidebar-w);
    transform: translateX(-100%);
    transition: transform .22s ease;
    border-right: 1px solid var(--cc-navy-700);
    overflow-y: auto;
    box-shadow: 4px 0 16px rgba(0,0,0,.3);
  }
  .sidebar.open { transform: translateX(0); }
  .sidebar-toggle { display: flex; }

  .page-content { padding: 1.25rem; }
  .notes-list { grid-template-columns: 1fr; }
  .editor-container { padding: 1rem; }
}

@media (max-width: 480px) {
  .header-a11y-controls { display: none; }
}
```

- [ ] **Step 2: Run backend tests**

```bash
cd ~/wiki-notebook && pytest -q
```

Expected: 82 passed.

- [ ] **Step 3: Commit**

```bash
git add static/styles.css
git commit -m "refactor(css): action bar, footer, responsive breakpoints"
```

---

## Task 8: Rework index.html

Replace the header structure and layout in `static/index.html`. The backend API routes and note-rendering divs do not change — only the chrome (header, sidebar wrapper, footer).

**Files:**
- Modify: `static/index.html:1-128`

- [ ] **Step 1: Write the new index.html**

Replace the entire contents of `static/index.html` with:

```html
<!DOCTYPE html>
<html lang="en" data-text-size="default" data-contrast="default" data-motion="default" data-font="default">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wiki|Note</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>

<!-- Skip to main content (WCAG 2.4.1) -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- Header -->
<header class="site-header" role="banner">
    <button class="sidebar-toggle" id="sidebar-toggle" aria-label="Toggle navigation">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
    </button>

    <a href="/" class="site-logo" aria-label="Wiki Notebook home">
        <div class="logo-mark"><span class="cc-inner">WN</span></div>
        <span>Wiki<span class="accent">Note</span></span>
    </a>

    <div class="header-search" role="search">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <input type="search" id="search-input" placeholder="Search notes…" aria-label="Search notes" autocomplete="off">
    </div>

    <div class="header-a11y-controls">
        <!-- Dark mode toggle -->
        <button class="theme-toggle" id="theme-toggle" aria-label="Toggle dark mode" aria-pressed="false">
            <svg id="theme-icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
            <svg id="theme-icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
        </button>
        <!-- High contrast toggle -->
        <button class="a11y-toggle" id="btn-contrast" aria-label="Toggle high contrast" aria-pressed="false" title="High contrast">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><path d="M12 2v20M2 12h20"/>
            </svg>
        </button>
        <!-- Dyslexia-friendly font toggle -->
        <button class="a11y-toggle" id="btn-font" aria-label="Toggle dyslexia-friendly font" aria-pressed="false" title="Legible font">
            <svg viewBox="0 0 24 24" fill="currentColor">
                <text x="2" y="18" font-size="16" font-weight="bold">A</text>
            </svg>
        </button>
    </div>
</header>

<!-- Mobile sidebar overlay -->
<div class="sidebar-overlay" id="sidebar-overlay"></div>

<!-- App layout -->
<div class="layout">

    <!-- Sidebar / Categories -->
    <aside class="sidebar" id="sidebar" aria-label="Categories">
        <span class="sidebar-label">Categories</span>
        <ul id="category-list" class="category-list" role="navigation" aria-label="Note categories">
            <li class="category-item active" data-category="">
                <span class="category-name">All</span>
                <span class="category-count" aria-live="polite">0</span>
            </li>
        </ul>
    </aside>

    <!-- Main content -->
    <main class="main" id="main-content">
        <div class="page-content">

            <!-- Editor / Note view -->
            <section id="editor-container" class="editor-container" aria-label="Note editor">
                <input type="text" id="note-title" class="note-title" placeholder="Note title…" aria-label="Note title">
                <textarea id="note-body" class="note-body" placeholder="Write your note here… (Markdown supported)" aria-label="Note body (Markdown supported)"></textarea>
                <div class="editor-actions" role="group" aria-label="Editor actions">
                    <button type="button" id="preview-toggle" class="btn btn-secondary" aria-label="Toggle preview">Preview</button>
                    <button type="button" id="save-btn" class="btn btn-primary" aria-label="Save note (Ctrl+Enter)">
                        <span class="btn-text">Save</span>
                        <span class="btn-spinner" style="display:none;" aria-hidden="true">Saving…</span>
                    </button>
                    <button type="button" id="delete-btn" class="btn btn-danger" style="display:none;" aria-label="Delete this note">Delete</button>
                    <button type="button" id="undo-btn" class="btn btn-link" style="display:none;" aria-label="Undo last AI optimization">Undo</button>
                </div>
                <div class="editor-shortcut" aria-hidden="true">Ctrl+Enter to save</div>
            </section>

            <!-- Notes list -->
            <section id="notes-list-container" class="notes-list-container" aria-label="Notes list">
                <h2 class="section-title">Recent</h2>
                <ul id="notes-list" class="notes-list" role="list"></ul>
                <div id="empty-state" class="empty-state" role="status" aria-live="polite">
                    <p>No notes yet. Create your first note!</p>
                </div>
            </section>

        </div>

        <footer class="site-footer">
            <span class="footer-logo">Wiki<span class="accent">Note</span></span>
            <span>Self-hosted · Offline-first</span>
        </footer>
    </main>

</div><!-- .layout -->

<!-- Action bar (multi-select) -->
<footer id="action-bar" class="action-bar" style="display:none;" aria-label="Multi-select actions">
    <div class="action-bar-content">
        <span class="action-bar-count" id="selection-count" aria-live="polite">0 notes selected</span>
        <button type="button" class="btn btn-primary" id="combine-concat-btn" aria-label="Combine selected notes by concatenating">Combine (concatenate)</button>
        <button type="button" class="btn btn-secondary" id="combine-ai-btn" disabled title="Ollama unavailable" aria-label="Combine selected notes using AI (Ollama)">Combine (AI)</button>
        <button type="button" class="btn btn-link" id="clear-selection-btn" aria-label="Clear selection">Clear</button>
    </div>
</footer>

<!-- Scripts -->
<script src="/static/vendor/marked.min.js"></script>
<script src="/static/vendor/dompurify.min.js"></script>
<script src="/static/a11y.js"></script>
<script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Run backend tests to verify server still serves the page**

```bash
cd ~/wiki-notebook
python -m wiki_notebook &
sleep 2
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/
kill %1
```

Expected: `200`

- [ ] **Step 3: Commit**

```bash
git add static/index.html
git commit -m "refactor(html): site-header with dark mode, mobile sidebar, docsync layout"
```

---

## Task 9: Update a11y.js for New Button IDs

The a11y toolbar HTML is gone. `a11y.js` must bind to the new `btn-contrast` and `btn-font` icon buttons instead of checkbox inputs. Text-size preference (`data-text-size`) is preserved via localStorage but the select UI is removed (can be re-added later if needed).

**Files:**
- Modify: `static/a11y.js`

- [ ] **Step 1: Write updated a11y.js**

Replace the contents of `static/a11y.js` with:

```javascript
/**
 * Accessibility Preferences Handler — Wiki Notebook
 * Manages: high contrast (btn-contrast), legible font (btn-font), reduced motion (system)
 * Storage key: 'wiki-notebook-a11y-prefs'
 */
(function () {
  const STORAGE_KEY = 'wiki-notebook-a11y-prefs';
  const html = document.documentElement;

  function loadPrefs() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch {
      return {};
    }
  }

  function savePrefs(prefs) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  }

  function applyPrefs(prefs) {
    html.setAttribute('data-contrast', prefs.contrast ? 'high' : 'default');
    html.setAttribute('data-font', prefs.font ? 'legible' : 'default');
    html.setAttribute('data-motion', prefs.motion ? 'reduced' : 'default');

    const btnContrast = document.getElementById('btn-contrast');
    const btnFont = document.getElementById('btn-font');
    if (btnContrast) btnContrast.setAttribute('aria-pressed', prefs.contrast ? 'true' : 'false');
    if (btnFont) btnFont.setAttribute('aria-pressed', prefs.font ? 'true' : 'false');
  }

  function announceChange(message) {
    const el = document.createElement('div');
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', 'polite');
    el.style.cssText = 'position:absolute;left:-10000px;';
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1000);
  }

  function init() {
    const prefs = loadPrefs();

    // Respect system reduced-motion if not explicitly set
    if (!('motion' in prefs) && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      prefs.motion = true;
    }
    window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
      const p = loadPrefs();
      if (!('motion' in p)) {
        p.motion = e.matches;
        savePrefs(p);
        applyPrefs(p);
      }
    });

    applyPrefs(prefs);

    document.getElementById('btn-contrast')?.addEventListener('click', function () {
      const p = loadPrefs();
      p.contrast = !p.contrast;
      savePrefs(p);
      applyPrefs(p);
      announceChange('High contrast mode ' + (p.contrast ? 'enabled' : 'disabled'));
    });

    document.getElementById('btn-font')?.addEventListener('click', function () {
      const p = loadPrefs();
      p.font = !p.font;
      savePrefs(p);
      applyPrefs(p);
      announceChange('Dyslexia-friendly font ' + (p.font ? 'enabled' : 'disabled'));
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
```

- [ ] **Step 2: Add dark mode + mobile sidebar inline JS to index.html**

Add this `<script>` block in `static/index.html` just before the closing `</body>` tag (after the existing script tags):

```html
<script>
(function () {
  var html = document.documentElement;

  // ── Dark mode ──
  var toggle = document.getElementById('theme-toggle');
  var moon = document.getElementById('theme-icon-moon');
  var sun  = document.getElementById('theme-icon-sun');

  function applyTheme(dark) {
    html.setAttribute('data-theme', dark ? 'dark' : 'light');
    if (moon) moon.style.display = dark ? 'none' : '';
    if (sun)  sun.style.display  = dark ? '' : 'none';
    if (toggle) toggle.setAttribute('aria-pressed', dark ? 'true' : 'false');
  }

  var savedTheme = localStorage.getItem('wiki-note-theme');
  var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(savedTheme ? savedTheme === 'dark' : prefersDark);

  if (toggle) {
    toggle.addEventListener('click', function () {
      var isDark = html.getAttribute('data-theme') === 'dark';
      applyTheme(!isDark);
      localStorage.setItem('wiki-note-theme', !isDark ? 'dark' : 'light');
    });
  }

  // ── Mobile sidebar ──
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  var sidebarBtn = document.getElementById('sidebar-toggle');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (overlay) overlay.classList.add('open');
  }
  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
  }

  if (sidebarBtn) sidebarBtn.addEventListener('click', function () {
    sidebar && sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
  });
  if (overlay) overlay.addEventListener('click', closeSidebar);
})();
</script>
```

- [ ] **Step 3: Run backend tests**

```bash
cd ~/wiki-notebook && pytest -q
```

Expected: 82 passed.

- [ ] **Step 4: Commit**

```bash
git add static/a11y.js static/index.html
git commit -m "refactor(js): a11y icon buttons, dark mode toggle, mobile sidebar"
```

---

## Task 10: Visual Verification

Verify the rework looks correct in the browser.

**Files:** (no changes — read-only verification)

- [ ] **Step 1: Start the server**

```bash
cd ~/wiki-notebook
python -m wiki_notebook &
sleep 2
echo "Server started"
```

- [ ] **Step 2: Take a screenshot of the main page**

Use Playwright or Chrome DevTools MCP to navigate to `http://localhost:5000` and take a screenshot.

Verify visually:
- Dark navy header with "WN" logo mark + "WikiNote" split name
- Search input with magnifier icon
- Dark mode, contrast, font icon buttons visible in header
- Dark navy sidebar with "CATEGORIES" label
- Note cards with 3px blue→orange gradient top bar
- Silver/card background in content area

- [ ] **Step 3: Test dark mode**

Click the dark mode toggle. Verify the content area switches to dark backgrounds while the sidebar and header remain dark navy.

- [ ] **Step 4: Test responsive (mobile)**

Resize to 500px width. Verify:
- Sidebar is hidden
- Hamburger toggle button appears
- Clicking toggle opens sidebar with overlay

- [ ] **Step 5: Test a11y toggles**

Click the contrast button — page should switch to high-contrast (white backgrounds).
Click the font button — body text should switch to Atkinson Hyperlegible.
Both should persist on page reload.

- [ ] **Step 6: Kill server and commit**

```bash
kill %1
cd ~/wiki-notebook
git add -A
git status  # should be clean
```

- [ ] **Step 7: Final backend test run**

```bash
pytest -q
```

Expected: 82 passed (or current count).

---

## Self-Review Checklist

### Spec Coverage

| Requirement | Task |
|---|---|
| Self-hosted fonts (no CDN) | Task 1, 2 |
| `--cc-*` token naming | Task 2 |
| Dark mode toggle | Task 4, 9 |
| Dark navy sidebar | Task 5 |
| Site-header with logo mark | Task 8 |
| Compact a11y icon buttons in header | Task 4, 8, 9 |
| Remove a11y toolbar | Task 4, 8 |
| 3px gradient card bar on note cards | Task 6 |
| Mobile sidebar + overlay | Task 5, 8, 9 |
| Site footer | Task 7, 8 |
| Prose styles for markdown preview | Task 6 |
| Backend tests unbroken | Tasks 3,4,5,6,7,9,10 |

### Type Consistency Check

- `category-item` class: generated by `app.js:99,105` — CSS target at Task 5. ✓
- Button IDs (`btn-contrast`, `btn-font`): set in Task 8 HTML, bound in Task 9 JS. ✓
- Dark mode IDs (`theme-toggle`, `theme-icon-moon`, `theme-icon-sun`): set in Task 8 HTML, used in Task 9 inline JS. ✓
- Mobile sidebar IDs (`sidebar-toggle`, `sidebar`, `sidebar-overlay`): set in Task 8 HTML, used in Task 9 inline JS. ✓
- All `app.js` selectors (e.g. `#search-input`, `#notes-list`, `#editor-container`) retained in Task 8 HTML. ✓
