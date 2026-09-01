# Song Filters, Publication Date, and Excel Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a sortable source-video publication date, exact Virtual Singer filtering, character and song-type filters, and export the complete song dataset as one verified Excel workbook.

**Architecture:** Extend `combined_music_data.json` with a canonical `songType` derived from `isNewlyWrittenMusic`, then keep all presentation logic in the song viewer. Build a reproducible artifact-tool exporter that joins the complete song catalog with supplemental video/staff data into normalized worksheets.

**Tech Stack:** Python 3/unittest, vanilla JavaScript/CSS/HTML, Playwright, `@oai/artifact-tool`.

---

### Task 1: Canonical song metadata

**Files:**
- Modify: `scripts/combine_music_data.py`
- Create: `tests/test_combine_music_data.py`
- Regenerate: `output/combined_music_data.json`

**Steps:**
1. Add failing tests for `resolve_song_type(True/False)` and earliest original-MV upload resolution.
2. Run `python -m unittest tests.test_combine_music_data -v` and confirm failure.
3. Add `songType` to every combined song and document the field.
4. Regenerate the combined output and assert every row is `original` or `cover`.
5. Re-run the focused test.

### Task 2: Viewer columns and filters

**Files:**
- Modify: `index.html`
- Modify: `assets/index.js`
- Modify: `assets/index.css`
- Modify: `tests/test_viewer_assets.py`

**Steps:**
1. Add assertions for the new publication-date sort key, character filter, song-type filter, and exact-V.S. predicate.
2. Add the new sidebar groups and table column.
3. Implement stable character keys/labels/counts, song-type matching, and exact Virtual Singer team matching.
4. Add `releasedAt` to sorting and URL state; preserve the compact mobile layout.
5. Run viewer asset tests.

### Task 3: End-to-end browser coverage

**Files:**
- Modify: `scripts/browser_smoke_check.mjs`
- Modify: `tests/test_browser_smoke_script.py`

**Steps:**
1. Assert the browser script covers all four new behaviors.
2. Exercise sorting, V.S.-only results, a single-character selection, original/cover selection, refresh restoration, and console errors.
3. Run the browser smoke test and inspect the desktop screenshot.

### Task 4: Full Excel workbook

**Files:**
- Create: `scripts/export_song_workbook.mjs`
- Create: `outputs/01a04204-c1bd-7b00-ab5c-9510ebda0184/Project_Sekai_歌曲全量数据.xlsx`

**Steps:**
1. Mark one spreadsheet-create operation and link the bundled dependency directory into the artifact work directory.
2. Create the Songs, Vocals, Videos, and Staff sheets with typed dates, filters, frozen headers, consistent styles, and bounded widths.
3. Inspect representative ranges and scan formula errors.
4. Render every sheet, visually inspect the previews, repair any clipping, and export exactly one final workbook.

### Task 5: Final regression

**Files:**
- Verify all files modified above without changing unrelated working-tree edits.

**Steps:**
1. Run the full Python test suite.
2. Rebuild the allowlisted static site and run Playwright.
3. Confirm row counts reconcile across JSON and workbook sheets.
4. Review `git diff --check` and report the final workbook plus verification results.
