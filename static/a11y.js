/**
 * Accessibility Preferences Handler — Wiki Notebook
 * Manages: high contrast (btn-contrast), legible font (btn-font), reduced motion (system)
 * Storage key: 'wiki-notebook-a11y-prefs'
 */
(function () {
  const STORAGE_KEY = "wiki-notebook-a11y-prefs";
  const html = document.documentElement;

  function loadPrefs() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    } catch (e) {
      if (e instanceof SyntaxError) {
        console.warn(
          "[a11y] Stored preferences corrupted, resetting:",
          e.message,
        );
      }
      // SecurityError (private browsing) falls through — savePrefs will also fail gracefully
      return {};
    }
  }

  function savePrefs(prefs) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    } catch (e) {
      console.warn(
        "[a11y] Could not save accessibility preferences:",
        e.message,
      );
    }
  }

  function applyPrefs(prefs) {
    html.setAttribute("data-contrast", prefs.contrast ? "high" : "default");
    html.setAttribute("data-font", prefs.font ? "legible" : "default");
    html.setAttribute("data-motion", prefs.motion ? "reduced" : "default");

    const btnContrast = document.getElementById("btn-contrast");
    const btnFont = document.getElementById("btn-font");
    if (btnContrast)
      btnContrast.setAttribute(
        "aria-pressed",
        prefs.contrast ? "true" : "false",
      );
    if (btnFont)
      btnFont.setAttribute("aria-pressed", prefs.font ? "true" : "false");
  }

  function announceChange(message) {
    const el = document.createElement("div");
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", "polite");
    el.style.cssText = "position:absolute;left:-10000px;";
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1000);
  }

  function init() {
    const prefs = loadPrefs();

    // Respect system reduced-motion if not explicitly set
    if (
      !("motion" in prefs) &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      prefs.motion = true;
      savePrefs(prefs); // persist so initial load is symmetric with the change handler
    }
    window
      .matchMedia("(prefers-reduced-motion: reduce)")
      .addEventListener("change", (e) => {
        const p = loadPrefs();
        if (!("motion" in p)) {
          p.motion = e.matches;
          savePrefs(p);
          applyPrefs(p);
        }
      });

    applyPrefs(prefs);

    const btnContrast = document.getElementById("btn-contrast");
    if (!btnContrast) {
      console.error(
        "[a11y] #btn-contrast not found — high contrast toggle disabled",
      );
    } else {
      btnContrast.addEventListener("click", function () {
        const p = loadPrefs();
        p.contrast = !p.contrast;
        savePrefs(p);
        applyPrefs(p);
        announceChange(
          "High contrast mode " + (p.contrast ? "enabled" : "disabled"),
        );
      });
    }

    const btnFont = document.getElementById("btn-font");
    if (!btnFont) {
      console.error(
        "[a11y] #btn-font not found — legible font toggle disabled",
      );
    } else {
      btnFont.addEventListener("click", function () {
        const p = loadPrefs();
        p.font = !p.font;
        savePrefs(p);
        applyPrefs(p);
        announceChange(
          "Dyslexia-friendly font " + (p.font ? "enabled" : "disabled"),
        );
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
