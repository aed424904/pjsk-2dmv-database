# Editor Modularization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the unified editor into separately testable and deployable style and JavaScript resources without changing runtime behavior.

**Architecture:** Keep `editor.html` as the semantic shell. Load one stylesheet and four classic scripts in dependency order so the existing globals and file/server compatibility remain unchanged.

**Tech Stack:** Static HTML/CSS/JavaScript, Python `unittest`, allowlisted static-site builder, Playwright/Chrome browser QA.

---

### Task 1: Lock the desired asset boundaries with tests

**Files:**
- Modify: `tests/test_frontend_entrypoints.py`
- Modify: `tests/test_build_site.py`

**Steps:**
1. Add a test asserting `editor.html` loads `editor.css` and four scripts in exact dependency order.
2. Add assertions that editor behavior markers are located in the matching external scripts.
3. Add a test asserting the editor has no inline `<style>` or executable inline `<script>` blocks.
4. Add build-site assertions for all five new files.
5. Run `python -m unittest tests.test_frontend_entrypoints tests.test_build_site -v` and confirm the new tests fail because assets have not been extracted yet.

### Task 2: Extract the editor resources without rewriting behavior

**Files:**
- Create: `assets/editor.css`
- Create: `assets/editor_shared.js`
- Create: `assets/manual_video_editor.js`
- Create: `assets/alias_editor.js`
- Create: `assets/editor_bootstrap.js`
- Modify: `editor.html`

**Steps:**
1. Move the existing `<style>` body verbatim into `assets/editor.css`.
2. Move each of the four existing script bodies verbatim into the corresponding asset.
3. Replace the inline blocks with one stylesheet link and four ordered script tags.
4. Compare normalized source block fingerprints before and after extraction to confirm no executable code was lost.
5. Run the focused tests and confirm they pass.

### Task 3: Publish the new resources

**Files:**
- Modify: `scripts/build_site.py`
- Test: `tests/test_build_site.py`

**Steps:**
1. Add all five editor assets to `SITE_FILES`.
2. Build `dist/` and assert each asset is present.
3. Confirm project-only files remain excluded.

### Task 4: Browser and responsive verification

**Files:**
- Generated/ignored: `output/playwright/editor-*.png`

**Steps:**
1. Build the site and start a localhost-only server for `dist/`.
2. Open the editor in Chrome at `?tab=video` and snapshot before interacting.
3. Switch to the alias tab, re-snapshot, and confirm URL/ARIA state.
4. Repeat direct-load checks at a mobile viewport and capture screenshots.
5. Verify legacy routes still preserve parameters and that no first-party script errors occur.
6. Stop the exact temporary server process.

### Task 5: Full regression and handoff

**Files:**
- Modify if required: `README_使用说明.md`

**Steps:**
1. Run `python -m unittest discover -s tests -v`.
2. Run `python -m compileall -q scripts tests`.
3. Run `python scripts/validate_data.py`.
4. Run `python scripts/build_site.py` and `git diff --check`.
5. Review `git status --short`, preserving all pre-existing user changes.

No Git commit is created unless the user explicitly requests one.
