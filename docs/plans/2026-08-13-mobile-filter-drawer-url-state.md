# Mobile Filter Drawer and URL State Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restore all viewer filters on phones and make viewer search, filters, and sorting refreshable, shareable, and reversible through the browser URL.

**Architecture:** Add one shared responsive control shell used by both static viewers. Page scripts keep ownership of filtering and sorting, while the shared helper owns drawer accessibility and generic URL serialization/restoration through small configuration objects.

**Tech Stack:** Static HTML/CSS/JavaScript, History API, Python `unittest`, Node.js and Playwright.

---

### Task 1: Specify the shared viewer controls

**Files:**
- Create: `tests/test_viewer_controls.py`
- Modify: `tests/test_browser_smoke_script.py`

**Steps:**
1. Assert both canonical viewers load the same control stylesheet and script.
2. Assert both pages expose the trigger, backdrop, accessible sidebar header and result button.
3. Assert the shared helper uses `pushState`, `popstate`, repeated parameters, `inert`, Escape handling and focus restoration.
4. Extend browser-script markers for URL restoration and mobile drawer behavior.
5. Run the focused tests and confirm they fail before implementation.

### Task 2: Build the shared mobile control shell

**Files:**
- Create: `assets/viewer_controls.css`
- Create: `assets/viewer_controls.js`

**Steps:**
1. Define desktop-hidden mobile controls and a 900px right-side drawer.
2. Add backdrop, fixed header/footer, scroll behavior and reduced-motion support.
3. Implement open/close, viewport synchronization, focus trapping, Escape and focus return.
4. Expose an update method for active-filter and result counts.
5. Implement configurable URL read/write while preserving unrelated parameters.
6. Filter restored values against filter options currently rendered in the DOM.
7. Run JavaScript syntax and focused static tests.

### Task 3: Integrate the song viewer

**Files:**
- Modify: `index.html`
- Modify: `assets/index.js`

**Steps:**
1. Add shared resources and semantic drawer controls.
2. Configure query parameters for tag, category, vocal, version and Staff filters.
3. Refactor sort-indicator rendering into one reusable function.
4. Restore URL state after filter options exist, then render the initial result.
5. Sync user changes and handle browser history without creating restoration loops.
6. Update mobile counts after every result change.
7. Run focused tests and syntax checks.

### Task 4: Integrate the video viewer

**Files:**
- Modify: `video_viewer.html`
- Modify: `assets/video_viewer.js`

**Steps:**
1. Add the same shared drawer structure and assets.
2. Configure tag, type, version and channel parameters.
3. Restore search and descending upload-date defaults correctly.
4. Reuse the same sort UI and history flow as the song viewer.
5. Preserve mobile video-card layout and row expansion.
6. Run focused tests and syntax checks.

### Task 5: Expand real-browser coverage

**Files:**
- Modify: `scripts/browser_smoke_check.mjs`

**Steps:**
1. Verify a song search updates the URL and survives reload.
2. Verify sort field and direction appear in the URL and restore.
3. Open the filter drawer at 390px and validate its accessibility state.
4. Select a video type, validate result/count/URL changes, close the drawer and go back.
5. Keep checking mobile metadata, details, overflow and console/HTTP errors.
6. Run `npm run check:browser` and inspect the JSON result.

### Task 6: Regression verification and documentation

**Files:**
- Modify: `README_使用说明.md`
- Modify: `docs/progress_report.md`
- Generated/ignored: `output/playwright/mobile-filter-drawer.png`

**Steps:**
1. Capture and inspect the open drawer and filtered mobile result.
2. Fix any clipping, scroll, contrast, focus or overflow issue before delivery.
3. Document shareable viewer URLs and mobile filtering.
4. Run all Python tests, all JavaScript syntax checks, data validation, site build, browser smoke and `git diff --check`.
5. Preserve pre-existing user data and document changes; do not stage or commit without explicit approval.
