# Frontend Entry Consolidation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace duplicate legacy frontends with compatibility redirects and make the unified editor directly addressable by URL tab.

**Architecture:** Canonical implementations remain `index.html`, `video_viewer.html`, and `editor.html`. Legacy pages become tiny accessible redirect shells; `editor.html` owns tab selection through URL state and History API.

**Tech Stack:** Static HTML/CSS/JavaScript, Python `unittest`, local HTTP server.

---

### Task 1: Specify compatibility behavior with tests

**Files:**
- Create: `tests/test_frontend_entrypoints.py`

**Steps:**
1. Test the three legacy-path mappings.
2. Test that redirect construction preserves query strings and fragments.
3. Test that the editor recognizes `video` and `alias`, with invalid values falling back to `video`.
4. Run the focused tests and confirm failure.

### Task 2: Add URL-driven tab state to the unified editor

**Files:**
- Modify: `editor.html`

**Steps:**
1. Add tab semantics and stable panel identity.
2. Read initial state from `URLSearchParams`.
3. Centralize tab activation and update the URL without reload.
4. Add ArrowLeft/ArrowRight/Home/End keyboard behavior.
5. Run focused tests.

### Task 3: Replace legacy implementations with compatibility shells

**Files:**
- Modify: `music_viewer.html`
- Modify: `manual_video_editor.html`
- Modify: `alias_editor.html`

**Steps:**
1. Add a consistent accessible redirect page design.
2. Preserve existing query parameters and hash fragments.
3. Avoid duplicate `tab` values when mapping editor pages.
4. Include meta-refresh and manual links as no-script fallbacks.

### Task 4: Documentation and verification

**Files:**
- Modify: `README_使用说明.md`
- Modify: `tests/test_build_site.py`

**Steps:**
1. Document canonical and compatibility entrypoints.
2. Confirm site build retains legacy paths.
3. Run all unit tests.
4. Build `dist/`, serve it locally, and verify the three redirects and active editor tabs.
5. Run `git diff --check` and review status.
