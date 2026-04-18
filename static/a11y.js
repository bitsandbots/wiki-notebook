/**
 * Accessibility Preferences Handler
 * WCAG 2.2 compliant preference management for CoreConduit Brand v2.1
 */

class A11yPreferences {
  constructor() {
    this.storageKey = 'wiki-notebook-a11y-prefs';
    this.defaults = {
      'text-size': 'default',
      'contrast': false,
      'font': false,
      'motion': false,
    };
    this.init();
  }

  /**
   * Initialize accessibility preferences
   */
  init() {
    // Load saved preferences
    this.loadPreferences();

    // Apply saved preferences
    this.applyPreferences();

    // Bind UI controls
    this.bindControls();

    // Respect system preferences
    this.respectSystemPreferences();
  }

  /**
   * Load preferences from localStorage
   */
  loadPreferences() {
    const saved = localStorage.getItem(this.storageKey);
    if (saved) {
      try {
        this.prefs = { ...this.defaults, ...JSON.parse(saved) };
      } catch (e) {
        this.prefs = { ...this.defaults };
      }
    } else {
      this.prefs = { ...this.defaults };
    }
  }

  /**
   * Save preferences to localStorage
   */
  savePreferences() {
    localStorage.setItem(this.storageKey, JSON.stringify(this.prefs));
  }

  /**
   * Apply preferences to document
   */
  applyPreferences() {
    const html = document.documentElement;

    // Text size
    html.setAttribute('data-text-size', this.prefs['text-size']);

    // High contrast
    html.setAttribute('data-contrast', this.prefs.contrast ? 'high' : 'default');

    // Dyslexia-friendly font
    html.setAttribute('data-font', this.prefs.font ? 'legible' : 'default');

    // Reduced motion
    html.setAttribute('data-motion', this.prefs.motion ? 'reduced' : 'default');

    // Update UI controls
    this.updateControls();
  }

  /**
   * Update UI control states
   */
  updateControls() {
    const textSizeSelect = document.getElementById('text-size-control');
    const contrastToggle = document.getElementById('contrast-toggle');
    const fontToggle = document.getElementById('font-toggle');
    const motionToggle = document.getElementById('motion-toggle');

    if (textSizeSelect) {
      textSizeSelect.value = this.prefs['text-size'];
    }

    if (contrastToggle) {
      contrastToggle.checked = this.prefs.contrast;
    }

    if (fontToggle) {
      fontToggle.checked = this.prefs.font;
    }

    if (motionToggle) {
      motionToggle.checked = this.prefs.motion;
    }
  }

  /**
   * Bind event listeners to accessibility controls
   */
  bindControls() {
    const textSizeSelect = document.getElementById('text-size-control');
    const contrastToggle = document.getElementById('contrast-toggle');
    const fontToggle = document.getElementById('font-toggle');
    const motionToggle = document.getElementById('motion-toggle');

    if (textSizeSelect) {
      textSizeSelect.addEventListener('change', (e) => {
        this.prefs['text-size'] = e.target.value;
        this.savePreferences();
        this.applyPreferences();
      });
    }

    if (contrastToggle) {
      contrastToggle.addEventListener('change', (e) => {
        this.prefs.contrast = e.target.checked;
        this.savePreferences();
        this.applyPreferences();
        this.announceChange('High contrast mode ' + (e.target.checked ? 'enabled' : 'disabled'));
      });
    }

    if (fontToggle) {
      fontToggle.addEventListener('change', (e) => {
        this.prefs.font = e.target.checked;
        this.savePreferences();
        this.applyPreferences();
        this.announceChange('Dyslexia-friendly font ' + (e.target.checked ? 'enabled' : 'disabled'));
      });
    }

    if (motionToggle) {
      motionToggle.addEventListener('change', (e) => {
        this.prefs.motion = e.target.checked;
        this.savePreferences();
        this.applyPreferences();
        this.announceChange('Reduced motion ' + (e.target.checked ? 'enabled' : 'disabled'));
      });
    }
  }

  /**
   * Respect system preferences for motion
   */
  respectSystemPreferences() {
    // Check if user prefers reduced motion at OS level
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    // Apply system preference if user hasn't set explicit preference
    if (mediaQuery.matches && !this.hasExplicitMotionPref()) {
      this.prefs.motion = true;
      this.applyPreferences();
    }

    // Listen for changes to system preference
    mediaQuery.addEventListener('change', (e) => {
      if (!this.hasExplicitMotionPref()) {
        this.prefs.motion = e.matches;
        this.applyPreferences();
      }
    });
  }

  /**
   * Check if user has explicitly set motion preference
   */
  hasExplicitMotionPref() {
    const saved = localStorage.getItem(this.storageKey);
    if (!saved) return false;
    try {
      const parsed = JSON.parse(saved);
      return 'motion' in parsed;
    } catch {
      return false;
    }
  }

  /**
   * Announce accessibility changes to screen readers
   */
  announceChange(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.textContent = message;
    document.body.appendChild(announcement);

    // Remove after announcement
    setTimeout(() => announcement.remove(), 1000);
  }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.a11yPrefs = new A11yPreferences();
  });
} else {
  window.a11yPrefs = new A11yPreferences();
}
