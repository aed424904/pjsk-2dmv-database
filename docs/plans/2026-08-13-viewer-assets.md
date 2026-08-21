# Viewer Asset Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Externalize the song and video viewer styles and scripts without changing their runtime behavior.

**Architecture:** Keep each HTML file as a semantic shell and preserve page-specific classic JavaScript. Publish four explicit assets through the existing allowlisted site builder.

**Tech Stack:** Static HTML/CSS/JavaScript, Python `unittest`, allowlisted site builder, Playwright/Chrome QA.

---

### Task 1: Add failing resource-boundary tests

**Files:**
- Create: `tests/test_viewer_assets.py`
- Modify: `tests/test_build_site.py`

**Steps:**
1. Assert `index.html` loads only `assets/index.css` and `assets/index.js` for page code.
2. Assert `video_viewer.html` loads only `assets/video_viewer.css` and `assets/video_viewer.js`.
3. Assert both HTML files contain no inline `<style>` or executable inline `<script>` blocks.
4. Assert page-specific behavior markers remain in the matching scripts.
5. Assert all four assets are in `SITE_FILES`.
6. Run `python -m unittest tests.test_viewer_assets tests.test_build_site -v` and confirm failure before extraction.

### Task 2: Extract the song viewer assets

**Files:**
- Create: `assets/index.css`
- Create: `assets/index.js`
- Modify: `index.html`

**Steps:**
1. Move the existing style body verbatim to `assets/index.css`.
2. Move the existing script body verbatim to `assets/index.js`.
3. Replace inline blocks with ordered external references.
4. Run JavaScript syntax and focused static tests.

### Task 3: Extract the video viewer assets

**Files:**
- Create: `assets/video_viewer.css`
- Create: `assets/video_viewer.js`
- Modify: `video_viewer.html`

**Steps:**
1. Move the existing style body verbatim to `assets/video_viewer.css`.
2. Move the existing script body verbatim to `assets/video_viewer.js`.
3. Replace inline blocks with ordered external references.
4. Run JavaScript syntax and focused static tests.

### Task 4: Publish and exercise browser flows

**Files:**
- Modify: `scripts/build_site.py`
- Generated/ignored: `output/playwright/viewer-*.png`

**Steps:**
1. Add the four assets to the site allowlist and rebuild `dist/`.
2. Use Chrome to verify song counts, alias search, filtering and detail expansion.
3. Verify video counts, search and detail expansion.
4. Check both pages at 390px width for horizontal overflow.
5. Collect first-party response and page error information, then stop the exact local server.

### Task 5: Full regression and documentation

**Files:**
- Modify: `README_使用说明.md`
- Modify: `docs/progress_report.md`

**Steps:**
1. Document the viewer assets under `assets/`.
2. Run all Python tests, Python compilation, JavaScript syntax checks and data validation.
3. Rebuild `dist/` and run `git diff --check`.
4. Review the dirty worktree without touching pre-existing user changes.

No Git commit is created unless the user explicitly requests one.
