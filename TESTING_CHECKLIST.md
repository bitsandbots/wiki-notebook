# Wiki Notebook — Accessibility Testing Checklist

This document provides a comprehensive testing checklist for verifying all accessibility features in Wiki Notebook. Use this before release and for regression testing.

---

## Pre-Testing Setup

### Browser Setup
- [ ] Chrome 90+ (or latest)
- [ ] Firefox 88+ (or latest)
- [ ] Safari 14+ (or latest, if on Mac)
- [ ] Mobile browser (iOS Safari or Chrome Android)

### Assistive Technology Setup

**Screen Reader (Pick One):**
- [ ] **NVDA** (Windows) — [Download](https://www.nvaccess.org/)
  - Start: Press Ctrl+Alt+N
  - Stop: Press Ctrl+Alt+N

- [ ] **VoiceOver** (Mac/iOS) — Built-in
  - Enable: Cmd+F5
  - Navigate: VO+Right Arrow (next), VO+Left Arrow (previous)

- [ ] **TalkBack** (Android) — Built-in
  - Enable: Settings → Accessibility → TalkBack
  - Navigate: Swipe right (next), swipe left (previous)

**Tools:**
- [ ] Keyboard (mouse unplugged for keyboard-only testing)
- [ ] Color contrast checker ([WebAIM](https://webaim.org/resources/contrastchecker/))
- [ ] Browser DevTools (F12)

---

## Section 1: Keyboard Navigation

### 1.1 Tab Order
- [ ] Press Tab to start — skip link appears first
- [ ] Tab → Accessibility toolbar (text size dropdown)
- [ ] Tab → High contrast checkbox
- [ ] Tab → Legible font checkbox
- [ ] Tab → Reduce motion checkbox
- [ ] Tab → Search input
- [ ] Tab → Category list items
- [ ] Tab → Note editor (title input)
- [ ] Tab → Note body textarea
- [ ] Tab → Preview button
- [ ] Tab → Save button
- [ ] Tab → Notes list items (when displayed)
- [ ] Tab → Edit buttons on note cards

**✓ Success Criteria:** Tab order follows visual layout logically

### 1.2 Skip Link
- [ ] Press Tab once — "Skip to main content" link appears
- [ ] Press Enter — Page jumps to `#main-content`
- [ ] Link is keyboard-focused (visible outline)
- [ ] Link has high contrast (dark background, light text)

**✓ Success Criteria:** Skip link works and is clearly visible

### 1.3 Focus Visibility
- [ ] Tab through all elements — focus ring is **always visible**
- [ ] Focus ring is **dark blue outline** (not too subtle)
- [ ] Focus ring has **yellow halo** around it (for high visibility)
- [ ] Focus ring works on light backgrounds (main content)
- [ ] Focus ring works on dark backgrounds (topbar, sidebar)
- [ ] Focus ring is at least **3px wide**

**✓ Success Criteria:** Focus ring is always clearly visible

### 1.4 Keyboard Shortcuts
- [ ] Press `/` (when not typing) → Search input gets focus
- [ ] In note editor, press Ctrl+Enter → Note saves
- [ ] Focus automatically moves to saved state or next field
- [ ] Shortcuts don't interfere with text input

**✓ Success Criteria:** All keyboard shortcuts work correctly

### 1.5 No Keyboard Traps
- [ ] Use only Tab to navigate entire page
- [ ] Focus can move out of every element
- [ ] No elements "trap" focus (require mouse to escape)
- [ ] Dialog/modals (if any) have visible close mechanism

**✓ Success Criteria:** Can navigate entire app with keyboard only

---

## Section 2: Text Sizing

### 2.1 Text Size Dropdown
- [ ] Dropdown shows 3 options: Default, Large, Extra Large
- [ ] Select "Large" — all text increases 112.5%
- [ ] Select "Extra Large" — all text increases 125%
- [ ] Select "Default" — returns to normal size

**✓ Success Criteria:** All three text size levels work

### 2.2 Text Size Persistence
- [ ] Change text size to "Large"
- [ ] Refresh the page — text size remains "Large"
- [ ] Close browser and reopen — text size is still "Large"
- [ ] Change to "Extra Large"
- [ ] In new browser tab, text size matches previous setting

**✓ Success Criteria:** Text size persists across sessions

### 2.3 Layout at All Text Sizes
- [ ] At default size — layout looks good, no broken text
- [ ] At large (112.5%) — text readable, buttons expand to 44px+
- [ ] At extra large (125%) — text readable, no overlapping elements
- [ ] At extra large + browser zoom 200% — still readable (no tiny text)

**✓ Success Criteria:** Layout works at all text sizes

### 2.4 Button & Input Sizing
- [ ] At default size — buttons are at least 40px tall
- [ ] At large size — buttons are at least 44px tall
- [ ] At extra large — buttons are at least 48px tall
- [ ] Text inputs expand proportionally
- [ ] Form controls are still usable and spaced correctly

**✓ Success Criteria:** Touch targets meet 44px minimum at all sizes

---

## Section 3: High Contrast Mode

### 3.1 High Contrast Toggle
- [ ] Uncheck "High Contrast" — normal colors appear
- [ ] Check "High Contrast" — white background, black text
- [ ] Toggle multiple times — mode switches correctly

**✓ Success Criteria:** High contrast mode toggles correctly

### 3.2 High Contrast Colors
- [ ] Background is pure white (#ffffff)
- [ ] Primary text is pure black (#000000)
- [ ] Links are darker blue (readable on white)
- [ ] Buttons are darker colors
- [ ] Focus ring is still visible (dark outline + yellow halo)

**✓ Success Criteria:** High contrast colors are proper and readable

### 3.3 Color Contrast Ratios in High Contrast Mode
- [ ] Primary text on white: Test with WebAIM → **21:1** ✓ AAA
- [ ] Secondary text on white: Test → **~9:1** ✓ AAA
- [ ] Links: Test → **meets AA minimum** ✓
- [ ] Buttons: Test → **meets AA minimum** ✓
- [ ] Focus ring: Test → **meets AA minimum** ✓

**✓ Success Criteria:** All text meets AA or AAA contrast

### 3.4 High Contrast Persistence
- [ ] Enable high contrast
- [ ] Refresh page — high contrast stays enabled
- [ ] Close and reopen browser — setting persists

**✓ Success Criteria:** High contrast setting persists

---

## Section 4: Dyslexia-Friendly Font

### 4.1 Legible Font Toggle
- [ ] Uncheck "Legible Font" — uses default font (Plus Jakarta Sans)
- [ ] Check "Legible Font" — uses Atkinson Hyperlegible
- [ ] Toggle multiple times — font switches correctly

**✓ Success Criteria:** Font toggle works

### 4.2 Font Characteristics
- [ ] With legible font enabled — "b" and "d" look distinctly different
- [ ] Numbers "1", "l", and "I" are clearly different
- [ ] Zero "0" is clearly different from letter "O"
- [ ] Text is slightly larger and more spaced out

**✓ Success Criteria:** Atkinson Hyperlegible font displays correctly

### 4.3 Readability with Legible Font
- [ ] Text is easier to read (subjective, but verify no errors)
- [ ] No scrambled letters or reversed characters
- [ ] Font loads correctly (not falling back to default)

**✓ Success Criteria:** Legible font improves readability

### 4.4 Font Persistence
- [ ] Enable legible font
- [ ] Refresh page — font setting persists
- [ ] Close and reopen browser — setting is remembered

**✓ Success Criteria:** Font setting persists

---

## Section 5: Reduced Motion

### 5.1 Reduce Motion Toggle
- [ ] Uncheck "Reduce Motion" — normal animations
- [ ] Check "Reduce Motion" — no animations
- [ ] Toggle multiple times — motion preference changes correctly

**✓ Success Criteria:** Reduce motion toggle works

### 5.2 Animation Removal
- [ ] With reduce motion OFF — buttons fade smoothly, hover effects appear
- [ ] With reduce motion ON — buttons appear instantly (no fade)
- [ ] With reduce motion ON — focus ring appears instantly (no glow)
- [ ] With reduce motion ON — scrolling jumps (no smooth scroll)
- [ ] All transitions are instant (0ms, not 200ms)

**✓ Success Criteria:** All animations disabled when reduce motion is ON

### 5.3 System Preference Respect
- [ ] In OS settings, enable "Reduce Motion" or similar
- [ ] Reload Wiki Notebook — reduce motion is automatically enabled
- [ ] Verify by checking reduce motion checkbox — should be checked
- [ ] Disable OS-level reduce motion — Wiki Notebook reverts

**✓ Success Criteria:** OS-level preference is respected

### 5.4 Motion Persistence
- [ ] Enable "Reduce Motion"
- [ ] Refresh page — setting persists
- [ ] Close and reopen browser — setting is remembered

**✓ Success Criteria:** Motion preference persists

---

## Section 6: Screen Reader Support

### 6.1 Page Structure (NVDA / VoiceOver / TalkBack)

**Using your screen reader:**
- [ ] Page has proper heading hierarchy (H1 → H2 → H3)
- [ ] Main content area is identified as "main"
- [ ] Navigation areas are identified as "navigation"
- [ ] Form controls have labels (not just placeholder text)

**✓ Success Criteria:** Page structure is semantic and logical

### 6.2 Form Controls
- [ ] Text inputs have associated labels
- [ ] Buttons announce their purpose ("Save", "Delete", etc.)
- [ ] Checkboxes announce checked/unchecked state
- [ ] Dropdown indicates it's a listbox with options
- [ ] Button for "Preview" announces what it does

**✓ Success Criteria:** All form controls are properly labeled

### 6.3 Dynamic Content Announcements
- [ ] Create a new note — screen reader announces it (live region)
- [ ] Select multiple notes — selection count is announced
- [ ] Save a note — success is announced
- [ ] Change category — changes are announced

**✓ Success Criteria:** Important changes are announced

### 6.4 Note Cards
- [ ] Screen reader announces: Title, category, date, snippet
- [ ] Buttons on cards are announced: "Edit [Note Title]"
- [ ] Cards are marked as list items
- [ ] Selection checkboxes are labeled properly

**✓ Success Criteria:** Note cards are fully accessible

### 6.5 Skip Link
- [ ] Screen reader finds skip link (usually first item)
- [ ] Activating skip link jumps to main content
- [ ] Main content area begins with "main" landmark

**✓ Success Criteria:** Skip link works with screen readers

---

## Section 7: Color & Contrast

### 7.1 Color Contrast in Default Mode

**Test colors with WebAIM Contrast Checker:**
- [ ] Body text (#3a404a) on silver (#c5c9d0): **6.1:1** ✓ AA
- [ ] Muted text (#4d545f) on silver (#c5c9d0): **5.0:1** ✓ AA
- [ ] Primary text (#1e232b) on silver (#c5c9d0): **9.3:1** ✓ AAA
- [ ] Links (#1b6ad4) on silver: **3.5:1** (AA for large text) ✓
- [ ] Focus ring dark blue on light bg: **7:1** ✓ AAA
- [ ] Focus ring yellow halo on light bg: **3:1** ✓ AA
- [ ] Buttons: Test primary, secondary, danger → all **meet AA** ✓

**✓ Success Criteria:** All text meets AA or AAA contrast

### 7.2 Color-Only Indicators
- [ ] Links are underlined (not just colored)
- [ ] Error states show text (not just red)
- [ ] Success states show text (not just green)
- [ ] Selected items show border/background (not just color)

**✓ Success Criteria:** No color-only indicators

### 7.3 Focus Indicator Contrast
- [ ] Focus outline (dark blue): **meets AA on light backgrounds**
- [ ] Focus outline: **meets AA on dark backgrounds**
- [ ] Focus halo (yellow): **visible on all backgrounds**

**✓ Success Criteria:** Focus indicators meet contrast requirements

---

## Section 8: Mobile & Responsive

### 8.1 Mobile Keyboard
- [ ] On-screen keyboard appears on mobile (as expected)
- [ ] All form controls are usable on touch screen
- [ ] Buttons are at least 44px × 44px (tap target)
- [ ] Text is readable without zooming

**✓ Success Criteria:** Mobile interface is usable

### 8.2 Mobile Accessibility Features
- [ ] Text size control works on mobile
- [ ] High contrast toggle works on mobile
- [ ] Dyslexia font works on mobile
- [ ] Reduce motion works on mobile
- [ ] Preferences persist on mobile

**✓ Success Criteria:** All features work on mobile

### 8.3 Screen Reader on Mobile
- [ ] **iOS:** VoiceOver swipe gestures work (right for next, left for prev)
- [ ] **Android:** TalkBack gestures work (swipe right for next, left for prev)
- [ ] Content is announced clearly
- [ ] Page structure is understandable with screen reader

**✓ Success Criteria:** Screen reader works on mobile

---

## Section 9: Visual Regression Testing

### 9.1 Default Appearance
- [ ] Topbar displays correctly (navy background, white text)
- [ ] Sidebar is visible and styled correctly
- [ ] Main content area has proper spacing
- [ ] Buttons are styled consistently
- [ ] No broken layouts or overlapping elements

**✓ Success Criteria:** Default appearance is correct

### 9.2 High Contrast Appearance
- [ ] Topbar appears different (darker navy or changed colors)
- [ ] Text is clearly legible
- [ ] Buttons have visible borders
- [ ] Focus indicators are bright and visible
- [ ] No elements are invisible or unreadable

**✓ Success Criteria:** High contrast layout is correct

### 9.3 Large Text Appearance
- [ ] All text scales proportionally
- [ ] No text is cut off
- [ ] Buttons expand to accommodate text
- [ ] Inputs expand proportionally
- [ ] No horizontal scrolling needed (responsive)

**✓ Success Criteria:** Large text layout is correct

### 9.4 Dark Mode (Browser)
- [ ] If browser is in dark mode, test appearance
- [ ] Text remains readable
- [ ] Focus indicators are visible
- [ ] Colors adapt appropriately

**✓ Success Criteria:** Works with browser dark mode

---

## Section 10: API & Backend

### 10.1 No JavaScript Errors
- [ ] Open DevTools console (F12)
- [ ] Load wiki-notebook.html
- [ ] Check console for errors (should be clean)
- [ ] No warnings about accessibility issues

**✓ Success Criteria:** Console is clean

### 10.2 a11y.js Loading
- [ ] Check Network tab — `a11y.js` is loaded
- [ ] Check console — no JS errors related to a11y
- [ ] Preferences are set in localStorage

**✓ Success Criteria:** a11y.js loads and works

### 10.3 HTML Validation
- [ ] Use [W3C Validator](https://validator.w3.org/)
- [ ] Upload HTML or URL
- [ ] Check for errors (should be none)
- [ ] Check for warnings (should be minimal)

**✓ Success Criteria:** HTML validates as valid

### 10.4 Accessibility Validation
- [ ] Use [Deque axe DevTools](https://www.deque.com/axe/devtools/)
- [ ] Run scan on page
- [ ] Check for violations (should be minimal)
- [ ] Review best practices

**✓ Success Criteria:** Automated scan shows good results

---

## Section 11: User Workflows

### 11.1 Create Note (Full Workflow)
- [ ] Use keyboard only: Tab to "Note Title" input
- [ ] Type note title
- [ ] Tab to "Note Body" textarea
- [ ] Type note content (includes Markdown)
- [ ] Tab to "Save" button
- [ ] Press Enter or Ctrl+Enter to save
- [ ] Note appears in list (with screen reader announcement)

**✓ Success Criteria:** Full create workflow is keyboard accessible

### 11.2 Search Notes (Keyboard Only)
- [ ] Press `/` to focus search
- [ ] Type search query
- [ ] Results appear below
- [ ] Tab through results
- [ ] Tab to "Edit" button on result
- [ ] Press Enter to open note

**✓ Success Criteria:** Search is fully keyboard accessible

### 11.3 Multi-Select & Combine (Keyboard Only)
- [ ] Tab to first note card
- [ ] Press Space to select note (checkbox gets focus)
- [ ] Continue selecting notes with Space
- [ ] Action bar appears at bottom
- [ ] Tab to "Combine (concatenate)" button
- [ ] Press Enter to combine

**✓ Success Criteria:** Multi-select workflow is keyboard accessible

### 11.4 Category Filter (Keyboard Only)
- [ ] Tab to category list
- [ ] Use arrow keys or Tab to select category
- [ ] Press Enter to filter
- [ ] Notes list updates (screen reader announces)
- [ ] Focus returns to category that was selected

**✓ Success Criteria:** Category filtering is keyboard accessible

---

## Section 12: Browser Compatibility

### 12.1 Chrome/Chromium
- [ ] All accessibility features work
- [ ] Preferences persist
- [ ] Screen reader works (if extension installed)
- [ ] Focus indicators visible
- [ ] Text sizing works

**✓ Success Criteria:** Chrome passes all tests

### 12.2 Firefox
- [ ] All accessibility features work
- [ ] Preferences persist
- [ ] Screen reader works (NVDA on Windows)
- [ ] Focus indicators visible
- [ ] Text sizing works

**✓ Success Criteria:** Firefox passes all tests

### 12.3 Safari (Mac)
- [ ] All accessibility features work
- [ ] Preferences persist
- [ ] VoiceOver works
- [ ] Focus indicators visible
- [ ] Text sizing works

**✓ Success Criteria:** Safari passes all tests

### 12.4 Edge (Windows)
- [ ] All accessibility features work
- [ ] Preferences persist
- [ ] Focus indicators visible
- [ ] Text sizing works

**✓ Success Criteria:** Edge passes all tests

---

## Section 13: Performance

### 13.1 Font Loading Performance
- [ ] Open Network tab (DevTools)
- [ ] Reload page
- [ ] Check font file loads (google fonts preconnect)
- [ ] Page loads in under 3 seconds
- [ ] Atkinson font loads when enabled

**✓ Success Criteria:** Font loading is performant

### 13.2 Preference Performance
- [ ] localStorage keys present: `wiki-notebook-a11y-prefs`
- [ ] Preferences load instantly on page load
- [ ] No lag when toggling preferences
- [ ] CSS variables update immediately

**✓ Success Criteria:** Preferences load and apply instantly

---

## Final Sign-Off Checklist

### Must Have (Blocking)
- [ ] All 4 accessibility controls work (text size, contrast, font, motion)
- [ ] Keyboard navigation works completely (Tab, skip link, shortcuts)
- [ ] Focus indicators visible on all interactive elements
- [ ] Text contrast meets AA minimum
- [ ] Screen reader announces important content
- [ ] All 82 unit tests passing

### Should Have (Important)
- [ ] Preferences persist across sessions
- [ ] Works on mobile devices
- [ ] Works with VoiceOver/TalkBack
- [ ] No JavaScript errors in console
- [ ] HTML validates cleanly

### Nice to Have (Enhancement)
- [ ] Zero violations in axe DevTools scan
- [ ] Lighthouse accessibility score 95+
- [ ] Works with magnification software
- [ ] Performance optimized

---

## Regression Testing (Before Each Release)

When making changes, re-run these critical tests:

- [ ] Tab navigation still works (no keyboard traps)
- [ ] Focus indicators still visible
- [ ] All 4 preference controls still work
- [ ] Preferences persist
- [ ] All unit tests pass (82/82)
- [ ] No new console errors
- [ ] Text contrast still meets AA

---

## Notes Section

Use this space to document any issues found during testing:

```
Test Date: __________
Tester: __________
Browser: __________
Assistive Tech: __________

Issues Found:
1.
2.
3.

Resolution:
```

---

## Resources

- [ACCESSIBILITY.md](ACCESSIBILITY.md) — Technical implementation details
- [A11Y_QUICK_START.md](A11Y_QUICK_START.md) — User guide
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Deque axe DevTools](https://www.deque.com/axe/devtools/)

---

**Last Updated:** 2026-04-17
**WCAG Compliance Level:** 2.2 Level AA
**Expected Duration:** 2-3 hours for complete testing
