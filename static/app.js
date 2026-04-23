/** Wiki Notebook - Vanilla JS Application */

// Security: Sanitize HTML with DOMPurify before rendering
const purify =
  typeof DOMPurify !== "undefined" ? DOMPurify : { sanitize: (html) => html };

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
  hasUnsavedChanges: false,
  importChunks: [],     // proposed chunks from /api/notes/import
};

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
  state.view = view;
  if (view === "grid") {
    state.currentId = null;
    state.hasUnsavedChanges = false;
    renderApp();
  }
  renderView();
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
        : purify.sanitize(marked.parse(rawSnippet));
      const formattedDate = formatDateTime(note.updated_at);

      const isSelected = state.selectedIds.has(note.id);
      const checkboxHtml = !isSearch
        ? `<label class="note-card-checkbox">
                <input type="checkbox" ${isSelected ? "checked" : ""} data-note-id="${note.id}" aria-label="Select ${titleHtml}">
                <span class="checkbox-icon" aria-hidden="true"></span>
            </label>`
        : "";

      return `<li class="note-card ${isSelected ? "selected" : ""}" data-id="${note.id}" role="listitem">
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
    api.search({ q: query, category: state.category }).then((data) => {
      renderNotes(data.items, true);
    });
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
      renderApp();
      // Clear search and refresh
      api
        .categories()
        .then((data) => renderCategories(data.items, state.category));
      alert("Note saved!");
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
    state.currentId = null;
    document.getElementById("note-title").value = "";
    document.getElementById("note-body").value = "";
    document.getElementById("delete-btn").style.display = "none";
    document.getElementById("undo-btn").style.display = "none";
    renderApp();
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
    switchToEditMode();

    // Scroll to editor
    document
      .getElementById("editor-container")
      ?.scrollIntoView({ behavior: "smooth" });
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
    switchToPreviewMode();

    // Scroll to editor
    document
      .getElementById("editor-container")
      ?.scrollIntoView({ behavior: "smooth" });
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

  // Render markdown - sanitized by DOMPurify to prevent XSS
  const content = bodyEl?.value || "";
  const html = marked.parse(content);
  const sanitized = purify.sanitize(html);
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
  // Ctrl+Enter to save
  if (e.ctrlKey && e.key === "Enter") {
    e.preventDefault();
    handleSave();
    return;
  }

  // / to focus search (prevent default to avoid typing / in search)
  if (e.key === "/" && document.activeElement?.tagName !== "INPUT") {
    e.preventDefault();
    const searchInput = document.getElementById("search-input");
    searchInput?.focus();
    return;
  }

  // Escape to close editor / reset
  if (e.key === "Escape") {
    const searchInput = document.getElementById("search-input");
    if (searchInput?.value && searchInput === document.activeElement) {
      searchInput.value = "";
      renderApp();
    } else if (state.currentId) {
      // Reset to new note
      state.currentId = null;
      document.getElementById("note-title").value = "";
      document.getElementById("note-body").value = "";
      document.getElementById("delete-btn").style.display = "none";
      document.getElementById("undo-btn").style.display = "none";
      // Switch to edit mode for new note
      switchToEditMode();
    }
  }
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

  const searchInput = document.getElementById("search-input");
  if (searchInput) {
    searchInput.addEventListener("input", debounce(handleSearchInput, 200));
  }

  document.addEventListener("keydown", handleKeydown);

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

// Start when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
