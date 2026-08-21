# Mobile Video Cards Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make video records readable and information-complete on phones, then provide one repeatable browser smoke-check command.

**Architecture:** Keep the desktop seven-column grid. Wrap the four metadata spans so CSS can switch them from desktop grid items to a mobile flex region; use a standalone Playwright library script with a temporary built-in HTTP server for browser checks.

**Tech Stack:** Static HTML/CSS/JavaScript, Node.js, Playwright library, Python `unittest`.

---

### Task 1: Add failing mobile-layout tests

**Files:**
- Create: `tests/test_mobile_video_layout.py`

**Steps:**
1. Assert video row markup contains `.video-meta` and four `data-label` values.
2. Assert desktop CSS uses `.video-meta { display: contents; }`.
3. Assert the mobile media query hides `.list-header`, defines named card grid areas and restores all metadata fields.
4. Assert mobile title text can wrap to two lines.
5. Run the focused test and confirm failure.

### Task 2: Implement the responsive cards

**Files:**
- Modify: `assets/video_viewer.js`
- Modify: `assets/video_viewer.css`

**Steps:**
1. Wrap the existing version/channel/views/date spans in `.video-meta` and add labels.
2. Preserve the desktop grid with `display: contents`.
3. Replace the narrow-screen compressed grid with the three-area card layout.
4. Style readable title, metadata pills, expansion state and attached details.
5. Run focused tests and JavaScript syntax checks.

### Task 3: Add the reusable browser smoke script

**Files:**
- Create: `package.json`
- Create: `scripts/browser_smoke_check.mjs`
- Create: `tests/test_browser_smoke_script.py`

**Steps:**
1. Declare a private `check:browser` script and exact Playwright development dependency.
2. Build `dist/`, serve it from a temporary localhost port and launch Chrome.
3. Check song alias search/detail, video search/keyboard detail, editor tabs and legacy routing.
4. Check 390px card layout, visible metadata and no horizontal overflow.
5. Collect first-party HTTP, console and page errors; always close resources.
6. Run the script with the bundled Node runtime and confirm a zero exit code.

### Task 4: Visual and regression verification

**Files:**
- Generated/ignored: `output/playwright/mobile-video-cards.png`
- Modify: `README_使用说明.md`

**Steps:**
1. Build the site and capture the mobile video page using Playwright CLI.
2. Inspect the screenshot and fix any hierarchy, truncation or detail-attachment problem.
3. Document `npm run check:browser` and its dependency requirement.
4. Run all Python tests, JavaScript syntax checks, data validation, site build and `git diff --check`.
5. Preserve all pre-existing user changes and do not create a Git commit without explicit approval.
