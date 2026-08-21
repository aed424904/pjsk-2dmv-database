# Staff Review Workbench Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn `staff_review.json` into an actionable editor tab that exports role aliases, name aliases, and explicitly ignored source lines.

**Architecture:** Keep the review UI as an isolated `StaffReviewEditor` namespace loaded by the existing editor shell. Extend the Python Staff parser with one exact-line ignore source and an `ignore` role alias, while preserving the current audit outputs and rebuild workflow.

**Tech Stack:** Static HTML/CSS/JavaScript, Python, JSON, History API, `unittest`, Node.js and Playwright.

---

### Task 1: Define parser and rebuild behavior

**Files:**
- Modify: `tests/test_staff_extraction.py`
- Modify: `tests/test_auto_update.py`

**Steps:**
1. Add a failing test that an exact ignored line produces no contributor or review entry.
2. Add a failing test that a role alias mapped to `ignore` is skipped.
3. Add a failing test that changing `staff_line_ignores.json` triggers regeneration.
4. Run the focused tests and confirm the new cases fail.

### Task 2: Specify the editor tab contract

**Files:**
- Create: `tests/test_staff_review_editor.py`
- Modify: `tests/test_frontend_entrypoints.py`
- Modify: `tests/test_browser_smoke_script.py`

**Steps:**
1. Assert `editor.html` exposes a third accessible Staff tab and Staff statistics.
2. Assert `assets/staff_review_editor.js` owns its namespace and loads all four JSON inputs.
3. Assert role mapping, name normalization, exact-line ignore, stable export and queue filtering functions exist.
4. Assert bootstrap accepts `staff`, switches the correct stats bar and initializes the namespace.
5. Assert the browser smoke script contains a Staff-review workflow.
6. Run focused tests and confirm failure before implementation.

### Task 3: Add ignored-line parser support

**Files:**
- Create: `manual_data/staff_line_ignores.json`
- Modify: `scripts/staff_extraction.py`
- Modify: `scripts/auto_update.py`

**Steps:**
1. Load a JSON array of exact ignored lines with a cached helper.
2. Skip matching description lines before parsing.
3. Treat canonical role `ignore` as a skipped clause instead of a contributor.
4. Include the ignore file in regeneration inputs.
5. Run focused parser and updater tests.

### Task 4: Implement the Staff review namespace

**Files:**
- Create: `assets/staff_review_editor.js`

**Steps:**
1. Load review rows and existing manual corrections with `no-store`.
2. Flatten rows into stable issue objects and derive status from correction state.
3. Implement search, type, status and 200-row rendering limit.
4. Render the selected source line, video context, role mapping form and name form.
5. Implement save/remove role mappings, name aliases and ignored lines.
6. Keep state alive across editor tab switches.
7. Export complete sorted JSON files and update Staff statistics.
8. Run syntax and namespace tests.

### Task 5: Integrate the tab and responsive design

**Files:**
- Modify: `editor.html`
- Modify: `assets/editor_bootstrap.js`
- Modify: `assets/editor.css`
- Modify: `scripts/build_site.py`
- Modify: `tests/test_build_site.py`

**Steps:**
1. Add the third tab and dedicated Staff stats bar.
2. Load `staff_review_editor.js` before bootstrap.
3. Extend tab routing, arrow-key navigation and stats switching to `staff`.
4. Add scoped queue, detail, status and correction-list styles.
5. Collapse the workbench to one column on narrow screens.
6. Add the new script and four Staff JSON inputs to the safe site allowlist.
7. Run editor and build tests.

### Task 6: Extend real-browser acceptance

**Files:**
- Modify: `scripts/browser_smoke_check.mjs`
- Generated/ignored: `output/playwright/staff-review-workbench.png`

**Steps:**
1. Open `editor.html?tab=staff` and wait for at least 200 review rows.
2. Search a known song and select the `■絵` issue.
3. Save an `illustrator` role mapping and verify correction statistics.
4. Ignore one unparsed line and verify queue status.
5. Switch tabs and return to confirm in-memory edits survive.
6. Capture desktop and mobile screenshots, inspect them, and fix visual issues.
7. Run the complete browser smoke script.

### Task 7: Documentation and full regression

**Files:**
- Modify: `README_使用说明.md`
- Modify: `docs/progress_report.md`

**Steps:**
1. Document the Staff review workflow and exported filenames.
2. Record current review counts and browser acceptance results.
3. Run all Python tests, JavaScript syntax checks, compileall, data validation, site build, browser smoke and `git diff --check`.
4. Preserve user data and unrelated document changes; do not stage or commit without explicit approval.
