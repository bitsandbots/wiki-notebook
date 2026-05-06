/** Wiki Notebook - Vanilla JS Application */

// Security: Sanitize HTML with DOMPurify before rendering
const purify =
  typeof DOMPurify !== "undefined" ? DOMPurify : { sanitize: (html) => html };

// Extended configuration for HTML notes — preserve formatting elements
const purifyCfg = {
  ALLOWED_ATTR: [
    "style", "class", "id", "href", "src", "alt", "title",
    "width", "height", "colspan", "rowspan", "target", "rel",
  ],
  ADD_TAGS: ["table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption",
    "colgroup", "col", "figure", "figcaption", "section", "article",
    "header", "footer", "nav", "main", "aside"],
  ALLOW_DATA_ATTR: false,
};

const api = {
  list: ({ category, limit, offset, order } = {}) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (limit) params.set("limit", limit);
    if (offset) params.set("offset", offset);
    if (order) params.set("order", order);
    return fetch(`/api/notes?${params.toString()}`).then((r) => r.json());
  },

  get: (id) => {
    return fetch(`/api/notes/${id}`).then((r) => r.json());
  },

  create: (payload) => {
    return fetch("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json());
  },

  update: (id, payload) => {
    return fetch(`/api/notes/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json());
  },

  remove: (id) => {
    return fetch(`/api/notes/${id}`, { method: "DELETE" });
  },

  search: ({ q, category, limit, offset }) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (category) params.set("category", category);
    if (limit) params.set("limit", limit);
    if (offset) params.set("offset", offset);
    return fetch(`/api/search?${params.toString()}`).then((r) => r.json());
  },

  combine: (noteIds, mode, title) => {
    return fetch("/api/notes/combine", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note_ids: noteIds, mode, title }),
    }).then((r) => r.json());
  },

  undo: (noteId) => {
    return fetch(`/api/notes/${noteId}/undo`, {
      method: "POST",
    }).then((r) => r.json());
  },

  categorize: (noteId) => {
    return fetch(`/api/notes/${noteId}/categorize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    }).then((r) => r.json());
  },

  categories: () => {
    return fetch("/api/categories").then((r) => r.json());
  },

  health: () => {
    return fetch("/api/health").then((r) => r.json());
  },
};

const state = {
  currentId: null,
  query: "",
  category: null,
  notes: [],
  categories: [],
  selectedIds: new Set(),
  editing: false,
  isPreviewMode: false, // true = viewing rendered markdown, false = editing
  view: "grid",         // "grid" | "detail" | "import-preview"
  gridScrollY: 0,       // saved scroll position for grid restore
  hasUnsavedChanges: false,
  importChunks: [],     // proposed chunks from /api/notes/import
  importAbort: null,    // AbortController for import-preview event listeners
};

function updateNoteStats(autosaveStatus = "") {
  const statsEl = document.getElementById("note-stats");
  const bodyEl = document.getElementById("note-body");
  if (!statsEl || !bodyEl) return;
  const text = bodyEl.value;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const chars = text.length;
  const countPart = `${words.toLocaleString()} words · ${chars.toLocaleString()} chars`;
  statsEl.textContent = autosaveStatus ? `${countPart}  ${autosaveStatus}` : countPart;
}

let _autosaveTimer = null;

function scheduleAutosave() {
  // Only autosave existing notes (new notes need a manual first save)
  if (!state.currentId) return;
  clearTimeout(_autosaveTimer);
  _autosaveTimer = setTimeout(autosave, 2000);
}

async function autosave() {
  const titleEl = document.getElementById("note-title");
  const bodyEl = document.getElementById("note-body");
  const title = titleEl?.value?.trim();
  const body = bodyEl?.value?.trim();
  if (!title || !state.currentId || !state.hasUnsavedChanges) return;

  updateNoteStats("Saving…");
  try {
    await api.update(state.currentId, { title, body, category: state.category, tags: [] });
    state.hasUnsavedChanges = false;
    updateNoteStats("Saved");
    setTimeout(() => updateNoteStats(), 2000);
  } catch {
    updateNoteStats("Save failed");
  }
}

function renderView() {
  const gridEl = document.getElementById("notes-list-container");
  const detailEl = document.getElementById("editor-container");
  const importEl = document.getElementById("import-preview-container");

  if (gridEl) gridEl.style.display = state.view === "grid" ? "" : "none";
  if (detailEl) detailEl.style.display = state.view === "detail" ? "" : "none";
  if (importEl) importEl.style.display = state.view === "import-preview" ? "" : "none";
}

function confirmLeaveEdit() {
  if (state.hasUnsavedChanges) {
    return confirm("You have unsaved changes. Discard?");
  }
  return true;
}

function navigateTo(view) {
  if (view !== "grid") {
    state.gridScrollY = window.scrollY;
  }
  // Clean up import-preview listeners when leaving that view
  if (view !== "import-preview" && state.importAbort) {
    state.importAbort.abort();
    state.importAbort = null;
  }
  state.view = view;
  if (view === "grid") {
    state.currentId = null;
    state.hasUnsavedChanges = false;
    renderApp();
    renderView();
    window.scrollTo({ top: state.gridScrollY, behavior: "instant" });
  } else {
    window.scrollTo({ top: 0, behavior: "instant" });
    renderView();
  }
}

async function uploadForChunking(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  const response = await fetch("/api/notes/import", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || "Import failed");
  }
  return response.json();
}

function renderImportPreview(data, files) {
  state.importChunks = data.chunks;

  const headerEl = document.getElementById("import-preview-header");
  const listEl = document.getElementById("import-chunk-list");
  const toolbarEl = document.getElementById("import-chunk-toolbar");
  if (!headerEl || !listEl || !toolbarEl) return;

  // Abort previous listeners to prevent accumulation across re-renders
  if (state.importAbort) state.importAbort.abort();
  state.importAbort = new AbortController();
  const signal = state.importAbort.signal;

  headerEl.replaceChildren();
  const heading = document.createElement("h2");
  heading.className = "section-title";
  const fileNames = [...files].map((f) => f.name).join(", ");
  heading.textContent = `Import Preview — ${fileNames} (${data.chunks.length} chunk${data.chunks.length !== 1 ? "s" : ""})`;
  headerEl.appendChild(heading);

  // Show toolbar and reset search
  toolbarEl.style.display = "";
  const chunkSearchEl = document.getElementById("import-chunk-search");
  if (chunkSearchEl) chunkSearchEl.value = "";

  // Select-all / deselect-all toggle — re-query fresh to avoid detached-node clone
  const selectAllBtnEl = document.getElementById("import-select-all-btn");
  if (selectAllBtnEl?.parentNode) {
    const fresh = selectAllBtnEl.cloneNode(true);
    selectAllBtnEl.parentNode.replaceChild(fresh, selectAllBtnEl);
    fresh.addEventListener("click", () => {
      const deselecting = fresh.textContent === "Deselect All";
      const allCheckboxes = document.querySelectorAll(
        "#import-chunk-list .import-chunk-card input[type=\"checkbox\"]"
      );
      for (const cb of allCheckboxes) {
        const card = cb.closest(".import-chunk-card");
        if (card && card.style.display !== "none") {
          cb.checked = !deselecting;
        }
      }
      updateImportSelectionCount();
    });
  }

  // Chunk search filter — re-query fresh to avoid detached-node clone
  const chunkSearchCurrent = document.getElementById("import-chunk-search");
  if (chunkSearchCurrent?.parentNode) {
    const fresh = chunkSearchCurrent.cloneNode(true);
    chunkSearchCurrent.parentNode.replaceChild(fresh, chunkSearchCurrent);
    fresh.addEventListener("input", debounce(() => filterImportChunks(fresh.value), 150));
  }

  // Delegate checkbox changes to update selection count
  listEl.addEventListener("change", (e) => {
    if (e.target.matches("input[type=\"checkbox\"]")) {
      updateImportSelectionCount();
    }
  }, { signal });

  listEl.replaceChildren();

  const groups = {};
  for (const chunk of data.chunks) {
    if (!groups[chunk.source_file]) groups[chunk.source_file] = [];
    groups[chunk.source_file].push(chunk);
  }

  const fileCount = Object.keys(groups).length;
  for (const [sourceFile, chunks] of Object.entries(groups)) {
    if (fileCount > 1) {
      const subheading = document.createElement("h3");
      subheading.className = "import-source-heading";
      subheading.textContent = sourceFile;
      listEl.appendChild(subheading);
    }

    for (const chunk of chunks) {
      const card = document.createElement("div");
      card.className = "import-chunk-card";
      card.dataset.chunkIndex = chunk.index;
      card.draggable = true;

      // Drag handle
      const dragHandle = document.createElement("span");
      dragHandle.className = "import-chunk-drag-handle";
      dragHandle.textContent = "⠿";
      dragHandle.setAttribute("aria-hidden", "true");

      const label = document.createElement("label");
      label.className = "import-chunk-label";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = true;
      checkbox.dataset.chunkIndex = chunk.index;
      checkbox.setAttribute("aria-label", `Include: ${chunk.title}`);

      const titleInput = document.createElement("input");
      titleInput.type = "text";
      titleInput.className = "import-chunk-title";
      titleInput.value = chunk.title;
      titleInput.dataset.chunkIndex = chunk.index;
      titleInput.setAttribute("aria-label", "Chunk title");

      // AI suggest button
      const suggestBtn = document.createElement("button");
      suggestBtn.type = "button";
      suggestBtn.className = "import-chunk-suggest-btn";
      suggestBtn.textContent = "✦";
      suggestBtn.title = "Suggest title with AI";
      suggestBtn.setAttribute("aria-label", "Suggest title with AI");
      suggestBtn.addEventListener("click", async () => {
        suggestBtn.disabled = true;
        suggestBtn.textContent = "…";
        try {
          const res = await fetch("/api/notes/suggest-title", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ body: chunk.body }),
          });
          const json = await res.json();
          if (res.ok && json.title) {
            titleInput.value = json.title;
            // Sync back to state so confirm-import uses the new title
            const idx = state.importChunks.findIndex((c) => c.index === chunk.index);
            if (idx !== -1) state.importChunks[idx].title = json.title;
          } else {
            suggestBtn.title = json.error?.message || "AI unavailable";
          }
        } catch {
          console.error("AI suggest-title failed");
          suggestBtn.title = "Request failed";
        } finally {
          suggestBtn.disabled = false;
          suggestBtn.textContent = "✦";
        }
      });

      label.appendChild(checkbox);
      label.appendChild(titleInput);
      label.appendChild(suggestBtn);

      const preview = document.createElement("p");
      preview.className = "import-chunk-preview";
      if (chunk.content_type === "html") {
        const sanitized = purify.sanitize(chunk.body.substring(0, 500));
        preview.innerHTML = sanitized;
      } else {
        preview.textContent = chunk.body.substring(0, 200);
      }

      const charCount = document.createElement("span");
      charCount.className = "import-chunk-charcount";
      charCount.textContent = `${chunk.body.length} chars`;

      card.appendChild(dragHandle);
      card.appendChild(label);
      card.appendChild(preview);
      card.appendChild(charCount);
      listEl.appendChild(card);
    }
  }

  // Drag-to-reorder
  let dragSrc = null;
  listEl.addEventListener("dragstart", (e) => {
    dragSrc = e.target.closest(".import-chunk-card");
    if (dragSrc) dragSrc.classList.add("dragging");
  }, { signal });
  listEl.addEventListener("dragover", (e) => {
    e.preventDefault();
    const target = e.target.closest(".import-chunk-card");
    if (!target || target === dragSrc) return;
    const rect = target.getBoundingClientRect();
    const after = e.clientY > rect.top + rect.height / 2;
    listEl.insertBefore(dragSrc, after ? target.nextSibling : target);
  }, { signal });
  listEl.addEventListener("dragend", () => {
    if (dragSrc) dragSrc.classList.remove("dragging");
    // Sync state.importChunks order to match DOM
    const newOrder = [...listEl.querySelectorAll(".import-chunk-card")].map((el) =>
      parseInt(el.dataset.chunkIndex)
    );
    state.importChunks.sort(
      (a, b) => newOrder.indexOf(a.index) - newOrder.indexOf(b.index)
    );
    dragSrc = null;
  }, { signal });

  updateImportSelectionCount();
  navigateTo("import-preview");
}

function updateImportSelectionCount() {
  const toolbar = document.getElementById("import-chunk-toolbar");
  const countEl = document.getElementById("import-selection-count");
  const selectAllBtn = document.getElementById("import-select-all-btn");
  if (!toolbar || !countEl) return;

  const allCheckboxes = document.querySelectorAll("#import-chunk-list .import-chunk-card input[type=\"checkbox\"]");
  const visibleCheckboxes = [...allCheckboxes].filter(cb => {
    const card = cb.closest(".import-chunk-card");
    return card && card.style.display !== "none";
  });
  const checkedCount = visibleCheckboxes.filter(cb => cb.checked).length;
  const totalCount = visibleCheckboxes.length;

  countEl.textContent = `${checkedCount} of ${totalCount} selected`;
  if (selectAllBtn) {
    selectAllBtn.textContent = checkedCount === totalCount ? "Deselect All" : "Select All";
  }

  // Update confirm button text
  const confirmBtn = document.getElementById("import-confirm-btn");
  if (confirmBtn) {
    confirmBtn.textContent = checkedCount === 0 ? "Import Selected" : `Import ${checkedCount} Selected`;
  }
}

function filterImportChunks(query) {
  const cards = document.querySelectorAll("#import-chunk-list .import-chunk-card");
  const q = query.toLowerCase().trim();

  for (const card of cards) {
    const idx = parseInt(card.dataset.chunkIndex, 10);
    if (isNaN(idx)) continue;
    const chunk = state.importChunks.find(c => c.index === idx);
    if (!q) {
      card.style.display = "";
    } else {
      const titleMatch = chunk?.title?.toLowerCase().includes(q);
      const bodyMatch = chunk?.body?.toLowerCase().includes(q);
      card.style.display = (titleMatch || bodyMatch) ? "" : "none";
    }
  }
  updateImportSelectionCount();
}

async function handleImportSelected() {
  const cards = document.querySelectorAll("#import-chunk-list .import-chunk-card");
  const selected = [];

  for (const card of cards) {
    if (card.style.display === "none") continue;
    const idx = parseInt(card.dataset.chunkIndex, 10);
    if (isNaN(idx)) continue;
    const checkbox = card.querySelector('input[type="checkbox"]');
    if (!checkbox?.checked) continue;

    const chunk = state.importChunks.find((c) => c.index === idx);
    if (!chunk) continue;

    const titleInput = card.querySelector(".import-chunk-title");
    const title = titleInput?.value?.trim() || chunk.title;
    selected.push({ title, body: chunk.body, content_type: chunk.content_type, card });
  }

  if (selected.length === 0) {
    alert("No chunks selected.");
    return;
  }

  const confirmBtn = document.getElementById("import-confirm-btn");
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Importing\u2026";
  }

  let successCount = 0;
  const errors = [];
  for (let i = 0; i < selected.length; i++) {
    try {
      await api.create({
        title: selected[i].title,
        body: selected[i].body,
        tags: [],
        content_type: selected[i].content_type,
      });
      successCount++;
      // Uncheck successfully imported card to prevent duplicates on retry
      const cb = selected[i].card?.querySelector('input[type="checkbox"]');
      if (cb) cb.checked = false;
    } catch (err) {
      console.error(`Import error on note ${i + 1}:`, err);
      errors.push(err);
    }
  }

  if (errors.length === 0) {
    state.importChunks = [];
    navigateTo("grid");
    api.categories().then((data) => renderCategories(data.items, state.category));
  } else {
    updateImportSelectionCount();
    const remaining = selected.length - successCount;
    alert(
      `Import partially failed: ${successCount} of ${selected.length} notes created. ` +
      `${remaining} remaining — you can retry.`
    );
  }

  if (confirmBtn) {
    confirmBtn.disabled = false;
    updateImportSelectionCount();
  }
}

// Debounce function
function debounce(fn, delay) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

// Display category and tags in editor
function displayEditorCategory(note) {
  const categorySection = document.getElementById("editor-category-section");
  const categoryBadge = document.getElementById("editor-category-badge");
  const tagsList = document.getElementById("editor-tags-list");
  const pendingIndicator = document.getElementById("editor-enrichment-pending");

  if (note.category) {
    // Show category section, hide pending
    categorySection.style.display = "block";
    pendingIndicator.style.display = "none";

    // Update category badge with safe textContent
    categoryBadge.textContent = note.category;
    categoryBadge.className = `category-badge category-${note.category
      .replace(/\s+/g, "-")
      .toLowerCase()}`;

    // Add confidence as tooltip if available
    if (note.confidence !== undefined) {
      categoryBadge.title = `Confidence: ${note.confidence}%`;
    }

    // Display tags using safe DOM methods
    if (note.tags && note.tags.length > 0) {
      // Clear tags list safely
      while (tagsList.firstChild) {
        tagsList.removeChild(tagsList.firstChild);
      }
      note.tags.forEach((tag) => {
        const tagEl = document.createElement("span");
        tagEl.className = "tag";
        tagEl.textContent = tag;
        tagsList.appendChild(tagEl);
      });
    } else {
      // Clear tags list if no tags
      while (tagsList.firstChild) {
        tagsList.removeChild(tagsList.firstChild);
      }
    }
  } else if (note.enrichment_pending) {
    // Show pending indicator
    pendingIndicator.style.display = "block";
    categorySection.style.display = "none";
  } else {
    // No category yet
    categorySection.style.display = "none";
    pendingIndicator.style.display = "none";
  }
}

// Recategorize a note
async function handleRecategorize() {
  const noteId = state.currentId;
  if (!noteId) return;

  const categorizBtn = document.getElementById("categorize-btn");
  const pendingIndicator = document.getElementById("editor-enrichment-pending");

  // Guard: prevent double-click
  if (categorizBtn.disabled) return;

  try {
    // Show pending indicator
    pendingIndicator.style.display = "block";
    categorizBtn.disabled = true;

    const note = await api.categorize(noteId);

    // Update display with new category
    displayEditorCategory(note);

    // Refresh the notes list to show updated category
    renderApp();
    api
      .categories()
      .then((data) => renderCategories(data.items, state.category));
  } catch (err) {
    console.error("Categorization error:", err);
    pendingIndicator.style.display = "none";

    // Improve error parsing to handle structured API errors
    const errorMsg =
      err.message ||
      (err.error?.message) ||
      (typeof err === "object" && err.error) ||
      "Unable to categorize note";
    alert("Failed to categorize note: " + errorMsg);
  } finally {
    categorizBtn.disabled = false;
  }
}

// Render functions
function renderCategories(categories, activeCategory) {
  const list = document.getElementById("category-list");
  if (!list) return;

  let html = "";
  // "All" category — total across all categories
  const totalCount = categories.reduce((sum, c) => sum + (c.count || 0), 0);
  html += `<li class="category-item ${!activeCategory ? "active" : ""}" data-category="">
        <span class="category-name">All</span>
        <span class="category-count">${totalCount}</span>
    </li>`;

  for (const cat of categories) {
    const sanitizedName = purify.sanitize(cat.name);
    html += `<li class="category-item ${cat.name === activeCategory ? "active" : ""}" data-category="${sanitizedName}">
            <span class="category-name">${sanitizedName}</span>
            <span class="category-count">${cat.count}</span>
        </li>`;
  }

  list.innerHTML = html;
}

function renderNotes(notes, isSearch = false) {
  const container = document.getElementById("notes-list");
  const emptyState = document.getElementById("empty-state");
  if (!container) return;

  if (notes.length === 0) {
    container.innerHTML = "";
    emptyState.style.display = "block";
    return;
  }

  emptyState.style.display = "none";

  const html = notes
    .map((note) => {
      const category = purify.sanitize(note.category || "uncategorized");
      const tagsHtml = note.tags?.length
        ? `<div class="note-card-tags" aria-label="Tags">${note.tags.map((t) => `<span class="note-card-tag">${purify.sanitize(t)}</span>`).join("")}</div>`
        : "";
      const titleHtml = purify.sanitize(note.title || "Untitled");
      const rawSnippet = note.body?.substring(0, 200) || "";
      // Search results provide pre-formatted HTML snippets; regular cards render markdown
      const snippet = isSearch
        ? note.snippet || rawSnippet
        : note.content_type === "html"
          ? purify.sanitize(rawSnippet, purifyCfg)
          : purify.sanitize(marked.parse(rawSnippet));
      const formattedDate = formatDateTime(note.updated_at);

      const isSelected = state.selectedIds.has(note.id);
      const checkboxHtml = !isSearch
        ? `<label class="note-card-checkbox">
                <input type="checkbox" ${isSelected ? "checked" : ""} data-note-id="${note.id}" aria-label="Select ${titleHtml}">
                <span class="checkbox-icon" aria-hidden="true"></span>
            </label>`
        : "";

      return `<li class="note-card ${isSelected ? "selected" : ""}" data-id="${note.id}" role="listitem" tabindex="0">
            <article>
                ${checkboxHtml}
                <div class="note-card-header">
                    <div class="note-card-title" id="note-title-${note.id}">${titleHtml}</div>
                </div>
                <div class="note-card-meta">
                    <span class="note-card-category" aria-label="Category">${category}</span>
                    ${tagsHtml}
                    <span aria-label="Last updated">${formattedDate}</span>
                </div>
                <div class="note-card-body">
                    ${snippet || "<em>No content</em>"}
                </div>
                <div class="note-card-actions" role="group" aria-label="Actions">
                    <button class="note-card-action" onclick="editNote(${note.id})" aria-label="Edit ${titleHtml}">Edit</button>
                </div>
            </article>
        </li>`;
    })
    .join("");

  container.innerHTML = html;
}

function formatDateTime(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  return date.toLocaleString();
}

function renderApp() {
  const searchInput = document.getElementById("search-input");
  const query = searchInput ? searchInput.value : "";

  if (query) {
    api
      .search({ q: query, category: state.category })
      .then((data) => {
        if (data.error || !data.items) {
          renderNotes([], true);
          return;
        }
        renderNotes(data.items, true);
      })
      .catch(() => renderNotes([], true));
  } else {
    api.list({ category: state.category }).then((data) => {
      state.notes = data.items;
      renderNotes(data.items);
    });
  }
}

// Event handlers
function handleCategoryClick(e) {
  const item = e.target.closest(".category-item");
  if (!item) return;

  // Update active state
  document
    .querySelectorAll(".category-item")
    .forEach((el) => el.classList.remove("active"));
  item.classList.add("active");

  const category = item.dataset.category || null;
  state.category = category;
  state.query = "";

  // Clear search
  const searchInput = document.getElementById("search-input");
  if (searchInput) searchInput.value = "";

  renderApp();
}

function handleSearchInput(e) {
  state.query = e.target.value;
  renderApp();
}

function handleSave() {
  const titleEl = document.getElementById("note-title");
  const bodyEl = document.getElementById("note-body");
  const saveBtn = document.getElementById("save-btn");
  const btnText = saveBtn?.querySelector(".btn-text");
  const btnSpinner = saveBtn?.querySelector(".btn-spinner");

  const title = titleEl?.value?.trim();
  const body = bodyEl?.value?.trim();

  if (!title) {
    alert("Title is required");
    return;
  }

  // Show saving state
  if (btnText) btnText.style.display = "none";
  if (btnSpinner) btnSpinner.style.display = "inline-flex";

  const payload = {
    title,
    body,
    category: state.category,
    tags: [],
  };

  const promise = state.currentId
    ? api.update(state.currentId, payload)
    : api.create(payload);

  promise
    .then((note) => {
      state.currentId = note.id;
      state.hasUnsavedChanges = false;
      renderApp();
      api.categories().then((data) => renderCategories(data.items, state.category));
      displayEditorCategory(note);
      switchToPreviewMode();
    })
    .catch((err) => {
      console.error("Save error:", err);
      alert("Failed to save note");
    })
    .finally(() => {
      if (btnText) btnText.style.display = "inline-flex";
      if (btnSpinner) btnSpinner.style.display = "none";
    });
}

function handleDelete() {
  if (!state.currentId) return;

  if (!confirm("Delete this note?")) return;

  api.remove(state.currentId).then(() => {
    navigateTo("grid");
    api.categories().then((data) => renderCategories(data.items, state.category));
  });
}

function handleUndo() {
  if (!state.currentId) return;

  api
    .undo(state.currentId)
    .then(() => {
      alert("Undo successful! Note restored to previous state.");
      renderApp();
      // Reload current note to show restored state
      api.get(state.currentId).then((note) => {
        document.getElementById("note-title").value = note.title;
        document.getElementById("note-body").value = note.body;
      });
    })
    .catch((err) => {
      console.error("Undo error:", err);
      alert("Failed to undo - no revision available");
    });
}

function handleCombine(mode) {
  const selected = Array.from(state.selectedIds);
  if (selected.length < 2) {
    alert("Please select at least 2 notes to combine.");
    return;
  }

  const title = prompt("Enter title for combined note:", `Combined (${mode})`);
  if (!title) return;

  api
    .combine(selected, mode, title)
    .then((note) => {
      alert(`Note combined successfully! ID: ${note.id}`);
      clearSelection();
      // Refresh the notes list
      renderApp();
      // Scroll to the new note
      setTimeout(() => {
        const noteCard = document.querySelector(`[data-id="${note.id}"]`);
        if (noteCard) noteCard.scrollIntoView({ behavior: "smooth" });
      }, 100);
    })
    .catch((err) => {
      console.error("Combine error:", err);
      alert("Failed to combine notes");
    });
}

function editNote(id) {
  api.get(id).then((note) => {
    state.currentId = note.id;
    state.category = note.category || null;

    const titleEl = document.getElementById("note-title");
    const bodyEl = document.getElementById("note-body");
    const deleteBtn = document.getElementById("delete-btn");
    const undoBtn = document.getElementById("undo-btn");
    const categorizeBtn = document.getElementById("categorize-btn");

    titleEl.value = note.title;
    bodyEl.value = note.body;
    updateNoteStats();

    if (deleteBtn) deleteBtn.style.display = "inline-block";
    // Show undo button if note has been optimized (has optimized_at)
    if (undoBtn && note.optimized_at) {
      undoBtn.style.display = "inline-block";
    }
    // Show categorize button
    if (categorizeBtn) categorizeBtn.style.display = "inline-block";

    // Display category and tags
    displayEditorCategory(note);

    // Switch to edit mode
    state.hasUnsavedChanges = false;
    switchToEditMode();
    navigateTo("detail");
  });
}

/**
 * View a note in preview mode (rendered markdown)
 * This is the default action when clicking a note card.
 */
function viewNote(id) {
  console.log("viewNote called with id:", id);
  api.get(id).then((note) => {
    state.currentId = note.id;
    state.category = note.category || null;

    const titleEl = document.getElementById("note-title");
    const bodyEl = document.getElementById("note-body");
    const deleteBtn = document.getElementById("delete-btn");
    const undoBtn = document.getElementById("undo-btn");
    const categorizeBtn = document.getElementById("categorize-btn");

    titleEl.value = note.title;
    bodyEl.value = note.body;
    updateNoteStats();

    if (deleteBtn) deleteBtn.style.display = "inline-block";
    if (undoBtn && note.optimized_at) {
      undoBtn.style.display = "inline-block";
    }
    // Show categorize button
    if (categorizeBtn) categorizeBtn.style.display = "inline-block";

    // Display category and tags
    displayEditorCategory(note);

    // Switch to preview mode (rendered markdown)
    console.log("Switching to preview mode for:", note.title);
    state.hasUnsavedChanges = false;
    switchToPreviewMode();
    navigateTo("detail");
  });
}

/**
 * Switch to edit mode (show textarea, hide preview)
 */
function switchToEditMode() {
  state.isPreviewMode = false;
  const bodyEl = document.getElementById("note-body");
  const previewContainer = document.getElementById("preview-container");
  const previewToggle = document.getElementById("preview-toggle");
  const titleEl = document.getElementById("note-title");
  const titleDisplay = document.getElementById("note-title-display");

  if (bodyEl) bodyEl.style.display = "";
  if (previewContainer) previewContainer.style.display = "none";
  if (previewToggle) previewToggle.textContent = "Preview";
  // Show title input, hide title display
  if (titleEl) {
    titleEl.style.display = "";
    titleEl.readOnly = false;
  }
  if (titleDisplay) titleDisplay.style.display = "none";
  if (titleEl) titleEl.focus();
}

/**
 * Switch to preview mode (show rendered markdown, hide textarea)
 */
function switchToPreviewMode() {
  state.isPreviewMode = true;
  const bodyEl = document.getElementById("note-body");
  const titleEl = document.getElementById("note-title");
  const titleDisplay = document.getElementById("note-title-display");
  let previewContainer = document.getElementById("preview-container");
  const previewToggle = document.getElementById("preview-toggle");

  // Create preview container if it doesn't exist
  if (!previewContainer) {
    const container = document.createElement("div");
    container.id = "preview-container";
    container.className = "preview-container";
    bodyEl.parentNode.insertBefore(container, bodyEl.nextSibling);
    previewContainer = container;
  }

  // Render body - bypass marked.parse for html notes
  const content = bodyEl?.value || "";
  const noteType = state.currentNote?.content_type;
  const html = noteType === "html" ? content : marked.parse(content);
  const sanitized = purify.sanitize(html, noteType === "html" ? purifyCfg : undefined);
  previewContainer.innerHTML = sanitized;
  previewContainer.style.display = "block";
  if (bodyEl) bodyEl.style.display = "none";

  // Update button text
  if (previewToggle) previewToggle.textContent = "Edit";

  // Show title as text, hide input
  if (titleEl) titleEl.style.display = "none";
  if (titleDisplay) {
    titleDisplay.textContent = titleEl?.value || "Untitled";
    titleDisplay.style.display = "";
  }
}

function toggleSelection(noteId) {
  if (state.selectedIds.has(noteId)) {
    state.selectedIds.delete(noteId);
  } else {
    state.selectedIds.add(noteId);
  }
  updateActionBar();
  renderApp();
}

function clearSelection() {
  state.selectedIds.clear();
  updateActionBar();
  renderApp();
}

function updateActionBar() {
  const actionBar = document.getElementById("action-bar");
  const countEl = document.getElementById("selection-count");

  if (!actionBar) return;

  if (state.selectedIds.size > 0) {
    actionBar.style.display = "flex";
    if (countEl) {
      const plural = state.selectedIds.size !== 1 ? "s" : "";
      countEl.textContent = `${state.selectedIds.size} note${plural} selected`;
      countEl.setAttribute("aria-live", "polite");
      countEl.setAttribute("aria-atomic", "true");
    }
  } else {
    actionBar.style.display = "none";
  }
}

// Keyboard shortcuts
function handleKeydown(e) {
  // Don't intercept shortcuts when user is typing in an input
  const tag = document.activeElement?.tagName;
  const isEditing = tag === "INPUT" || tag === "TEXTAREA";

  // Ctrl+Enter to save (works everywhere)
  if (e.ctrlKey && e.key === "Enter") {
    e.preventDefault();
    handleSave();
    return;
  }

  // / to focus search (only when not already in an input)
  if (e.key === "/" && !isEditing) {
    e.preventDefault();
    const searchInput = document.getElementById("search-input");
    searchInput?.focus();
    return;
  }

  // ? to show keyboard shortcuts help (only when not editing)
  if (e.key === "?" && !isEditing) {
    e.preventDefault();
    showShortcutHelp();
    return;
  }

  // Import preview — Ctrl+A select all, Ctrl+Shift+A deselect all, Ctrl+F filter
  if (state.view === "import-preview" && !isEditing) {
    if (e.ctrlKey && e.shiftKey && e.key === "A") {
      e.preventDefault();
      const allCb = document.querySelectorAll(
        "#import-chunk-list .import-chunk-card input[type=\"checkbox\"]"
      );
      for (const cb of allCb) {
        const card = cb.closest(".import-chunk-card");
        if (card.style.display !== "none") cb.checked = false;
      }
      updateImportSelectionCount();
      return;
    }
    if (e.ctrlKey && e.key === "a") {
      e.preventDefault();
      const allCb = document.querySelectorAll(
        "#import-chunk-list .import-chunk-card input[type=\"checkbox\"]"
      );
      for (const cb of allCb) {
        const card = cb.closest(".import-chunk-card");
        if (card.style.display !== "none") cb.checked = true;
      }
      updateImportSelectionCount();
      return;
    }
    if (e.ctrlKey && e.key === "f") {
      e.preventDefault();
      document.getElementById("import-chunk-search")?.focus();
      return;
    }
  }

  // Grid view — N or Ctrl+N to create new note
  if (state.view === "grid" && !isEditing) {
    if (e.key === "n" || (e.ctrlKey && e.key === "n")) {
      e.preventDefault();
      document.getElementById("new-note-btn")?.click();
      return;
    }
    return;
  }

  // Detail view — E to toggle edit/preview
  if (state.view === "detail" && !isEditing) {
    if (e.key === "e") {
      e.preventDefault();
      document.getElementById("preview-toggle")?.click();
      return;
    }
  }

  // Escape to close editor / reset
  if (e.key === "Escape") {
    const searchInput = document.getElementById("search-input");
    if (searchInput?.value && searchInput === document.activeElement) {
      searchInput.value = "";
      renderApp();
      return;
    } else if (state.view === "detail") {
      if (confirmLeaveEdit()) navigateTo("grid");
    } else if (state.view === "import-preview") {
      const chunkSearch = document.getElementById("import-chunk-search");
      if (chunkSearch === document.activeElement) {
        // Let Escape clear the filter first, then second Escape exits preview
        chunkSearch.value = "";
        filterImportChunks("");
        chunkSearch.blur();
        return;
      }
      navigateTo("grid");
    }
    return;
  }
}

// Keyboard shortcut help modal — static trusted HTML, no user data
function showShortcutHelp() {
  let modal = document.getElementById("shortcut-help-modal");
  if (modal) {
    modal.style.display = "flex";
    modal.querySelector(".shortcut-help-close")?.focus();
    return;
  }
  modal = document.createElement("div");
  modal.id = "shortcut-help-modal";
  modal.className = "shortcut-help-overlay";
  modal.setAttribute("role", "dialog");
  modal.setAttribute("aria-label", "Keyboard shortcuts");

  const buildRow = (key, desc) => {
    const tr = document.createElement("tr");
    const tdKey = document.createElement("td");
    const kbd = document.createElement("kbd");
    kbd.textContent = key;
    tdKey.appendChild(kbd);
    const tdDesc = document.createElement("td");
    tdDesc.textContent = desc;
    tr.appendChild(tdKey);
    tr.appendChild(tdDesc);
    return tr;
  };

  const buildSection = (label) => {
    const tr = document.createElement("tr");
    tr.className = "shortcut-context";
    const td = document.createElement("td");
    td.setAttribute("colspan", "2");
    td.textContent = label;
    tr.appendChild(td);
    return tr;
  };

  const content = document.createElement("div");
  content.className = "shortcut-help-content";
  const h2 = document.createElement("h2");
  h2.textContent = "Keyboard Shortcuts";
  content.appendChild(h2);

  const table = document.createElement("table");
  table.className = "shortcut-help-table";
  const tbody = document.createElement("tbody");
  [
    buildRow("Ctrl+Enter", "Save note"),
    buildRow("/", "Focus search"),
    buildRow("Escape", "Close / go back"),
    buildRow("?", "Show this help"),
    buildSection("Grid view"),
    buildRow("N / Ctrl+N", "New note"),
    buildRow("Enter / Space", "Open focused note"),
    buildSection("Detail view"),
    buildRow("E", "Toggle edit / preview"),
    buildSection("Import preview"),
    buildRow("Ctrl+A", "Select all chunks"),
    buildRow("Ctrl+Shift+A", "Deselect all chunks"),
    buildRow("Ctrl+F", "Filter chunks"),
  ].forEach((tr) => tbody.appendChild(tr));
  table.appendChild(tbody);
  content.appendChild(table);

  const closeBtn = document.createElement("button");
  closeBtn.className = "btn btn-primary shortcut-help-close";
  closeBtn.textContent = "Close";
  content.appendChild(closeBtn);
  modal.appendChild(content);
  document.body.appendChild(modal);

  modal.addEventListener("click", (e) => {
    if (e.target === modal || e.target.closest(".shortcut-help-close")) {
      modal.remove();
    }
  });
  modal.addEventListener("keydown", (e) => {
    if (e.key === "Escape") modal.remove();
  });
  modal.style.display = "flex";
  closeBtn.focus();
}

// Initialize
function init() {
  // Load categories then render notes
  api.categories().then((data) => {
    renderCategories(data.items, null);
    renderApp();
  });

  // Load health and check Ollama
  api.health().then((data) => {
    const aiBtn = document.getElementById("combine-ai-btn");
    if (aiBtn && !data.ollama.reachable) {
      aiBtn.disabled = true;
      aiBtn.title = "Ollama is not available";
    }
  });

  // Event listeners
  document.addEventListener("click", (e) => {
    if (e.target.closest(".category-item")) {
      handleCategoryClick(e);
    }
    // Handle note card click (load note in preview mode)
    const noteCard = e.target.closest(".note-card");
    if (noteCard) {
      // Exclude clicks on checkbox, Edit button, and their containers
      const isCheckbox = e.target.closest(".note-card-checkbox");
      const isEditButton = e.target.closest(".note-card-action");
      const isCardActions = e.target.closest(".note-card-actions");
      if (!isCheckbox && !isEditButton && !isCardActions) {
        const noteId = parseInt(noteCard.dataset.id);
        viewNote(noteId);
      }
    }
    // Handle checkbox click
    const checkbox = e.target.closest(".note-card-checkbox input");
    if (checkbox) {
      e.stopPropagation();
      toggleSelection(parseInt(checkbox.dataset.noteId));
    }
    // Handle checkbox icon click (for the visual checkbox)
    const checkboxIcon = e.target.closest(".note-card-checkbox");
    if (checkboxIcon) {
      const input = checkboxIcon.querySelector("input");
      if (input) {
        e.stopPropagation();
        toggleSelection(parseInt(input.dataset.noteId));
      }
    }
  });

  // Keyboard activation for focused note cards (Enter/Space)
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const noteCard = document.activeElement?.closest(".note-card");
    if (!noteCard) return;
    // Don't intercept keys on interactive children (checkbox, button, textarea)
    const tag = document.activeElement.tagName;
    if (tag === "INPUT" || tag === "BUTTON" || tag === "TEXTAREA") return;
    e.preventDefault();
    viewNote(parseInt(noteCard.dataset.id));
  });

  const searchInput = document.getElementById("search-input");
  if (searchInput) {
    searchInput.addEventListener("input", debounce(handleSearchInput, 200));
  }

  document.addEventListener("keydown", handleKeydown);

  // Track unsaved changes
  const titleInput = document.getElementById("note-title");
  const bodyTextarea = document.getElementById("note-body");
  if (titleInput) {
    titleInput.addEventListener("input", () => {
      if (state.view === "detail" && !state.isPreviewMode) {
        state.hasUnsavedChanges = true;
        scheduleAutosave();
      }
    });
  }
  if (bodyTextarea) {
    bodyTextarea.addEventListener("input", () => {
      if (state.view === "detail" && !state.isPreviewMode) {
        state.hasUnsavedChanges = true;
        scheduleAutosave();
      }
      updateNoteStats();
    });
  }

  // Back and close buttons
  document.getElementById("detail-back-btn")?.addEventListener("click", () => {
    if (confirmLeaveEdit()) navigateTo("grid");
  });
  document.getElementById("detail-close-btn")?.addEventListener("click", () => {
    if (confirmLeaveEdit()) navigateTo("grid");
  });

  // New Note button
  document.getElementById("new-note-btn")?.addEventListener("click", () => {
    state.currentId = null;
    state.hasUnsavedChanges = false;
    const ids = [
      "note-title", "note-body", "delete-btn", "undo-btn",
      "categorize-btn", "editor-category-section", "editor-enrichment-pending",
    ];
    for (const id of ids) {
      const el = document.getElementById(id);
      if (!el) continue;
      if (id === "note-title" || id === "note-body") {
        el.value = "";
      } else {
        el.style.display = "none";
      }
    }
    switchToEditMode();
    navigateTo("detail");
  });

  // Dropdown caret
  const caretBtn = document.getElementById("new-note-caret");
  const noteMenu = document.getElementById("new-note-menu");
  if (caretBtn && noteMenu) {
    caretBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = noteMenu.style.display !== "none";
      noteMenu.style.display = isOpen ? "none" : "block";
      caretBtn.setAttribute("aria-expanded", isOpen ? "false" : "true");
    });
    document.addEventListener("click", () => {
      if (noteMenu.style.display !== "none") {
        noteMenu.style.display = "none";
        caretBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Import menu item — open file picker
  document.getElementById("import-file-btn")?.addEventListener("click", () => {
    if (noteMenu) {
      noteMenu.style.display = "none";
      caretBtn?.setAttribute("aria-expanded", "false");
    }
    document.getElementById("import-file-input")?.click();
  });

  // File input change → upload and show preview
  const fileInput = document.getElementById("import-file-input");
  if (fileInput) {
    fileInput.addEventListener("change", async () => {
      const files = fileInput.files;
      if (!files || files.length === 0) return;
      try {
        const data = await uploadForChunking(files);
        renderImportPreview(data, files);
      } catch (err) {
        console.error("Import upload error:", err);
        alert("Failed to parse files: " + (err.message || "Unknown error"));
      }
      fileInput.value = "";
    });
  }

  document.getElementById("import-confirm-btn")?.addEventListener("click", handleImportSelected);

  const cancelImport = () => {
    state.importChunks = [];
    navigateTo("grid");
  };
  document.getElementById("import-cancel-top-btn")?.addEventListener("click", cancelImport);
  document.getElementById("import-cancel-bottom-btn")?.addEventListener("click", cancelImport);

  // Save button
  document.getElementById("save-btn")?.addEventListener("click", handleSave);

  // Delete button
  document
    .getElementById("delete-btn")
    ?.addEventListener("click", handleDelete);

  // Undo button
  const undoBtn = document.getElementById("undo-btn");
  if (undoBtn) {
    undoBtn.addEventListener("click", handleUndo);
  }

  // Categorize button
  const categorizeBtn = document.getElementById("categorize-btn");
  if (categorizeBtn) {
    categorizeBtn.addEventListener("click", handleRecategorize);
  }

  // Clear selection
  document
    .getElementById("clear-selection-btn")
    ?.addEventListener("click", clearSelection);

  // Combine buttons
  const combineConcatBtn = document.getElementById("combine-concat-btn");
  if (combineConcatBtn) {
    combineConcatBtn.addEventListener("click", () =>
      handleCombine("concatenate"),
    );
  }

  const combineAiBtn = document.getElementById("combine-ai-btn");
  if (combineAiBtn) {
    combineAiBtn.addEventListener("click", () => handleCombine("ai"));
  }

  // Preview toggle - switches between edit and preview mode
  const previewToggle = document.getElementById("preview-toggle");
  if (previewToggle) {
    previewToggle.addEventListener("click", function () {
      if (state.isPreviewMode) {
        switchToEditMode();
      } else {
        state.hasUnsavedChanges = false;
        switchToPreviewMode();
      }
    });
  }

  renderView();
  console.log("Wiki Notebook initialized");
}

// Expose functions to window for onclick handlers
window.renderApp = renderApp;
window.editNote = editNote;
window.viewNote = viewNote;
window.api = api;
window.state = state;
window.navigateTo = navigateTo;
window.handleImportSelected = handleImportSelected;

// Start when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
