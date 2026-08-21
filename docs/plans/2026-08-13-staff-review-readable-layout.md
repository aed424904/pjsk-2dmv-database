# Staff Review Readable Layout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the Staff review workbench wider, taller, and easier to read while using one offline font stack for Chinese, English, Japanese kanji, and kana.

**Architecture:** Mark the active editor tab on `body` and scope all density changes to the Staff tab. Define reusable CJK and monospace font variables at the editor root, then extend existing browser acceptance with measurable typography and layout thresholds.

**Tech Stack:** Static HTML/CSS/JavaScript, Python `unittest`, Node.js and Playwright.

---

### Task 1: Add failing layout-contract tests

**Files:**
- Modify: `tests/test_staff_review_editor.py`
- Modify: `tests/test_frontend_entrypoints.py`

**Steps:**
1. Assert the editor defines a `--font-cjk` stack beginning with `Noto Sans SC` and including Chinese/Japanese system fallbacks.
2. Assert Staff-scoped layout uses `max-width: 1760px` and a wider queue column.
3. Assert issue text, source text and form controls meet the new minimum sizes.
4. Assert bootstrap writes `document.body.dataset.editorTab = nextTab`.
5. Run focused tests and confirm failure.

### Task 2: Apply the font and Staff layout scale

**Files:**
- Modify: `assets/editor_bootstrap.js`
- Modify: `assets/editor.css`

**Steps:**
1. Set the active-tab data attribute before rendering tab content.
2. Replace the editor body font with the offline CJK variable.
3. Add Staff-scoped header and app maximum widths.
4. Increase queue/card, panel, detail, form, button and correction-list typography and spacing.
5. Use the CJK body font for mixed-script source lines.
6. Reduce Staff mobile page gutters while retaining the larger typography.
7. Run CSS contract tests and JavaScript syntax checks.

### Task 3: Measure the result in a real browser

**Files:**
- Modify: `scripts/browser_smoke_check.mjs`
- Generated/ignored: `output/playwright/staff-review-workbench.png`
- Generated/ignored: `output/playwright/staff-review-mobile.png`

**Steps:**
1. Capture desktop computed font family, queue width, issue font size, source font size and input height.
2. Assert the CJK font stack and new readable thresholds.
3. Capture mobile app width and confirm no overflow or regression in auto-scroll.
4. Generate fresh desktop/mobile screenshots and inspect mixed-script rendering.
5. Fix any wrapping, clipping or excessive density problem.

### Task 4: Regression verification

**Files:**
- Modify: `README_使用说明.md`

**Steps:**
1. Document the offline CJK font choice and Staff-specific comfortable layout.
2. Run all Python tests, JavaScript syntax checks, data validation, site build, browser smoke and `git diff --check`.
3. Preserve all existing user data and do not stage or commit without explicit approval.
