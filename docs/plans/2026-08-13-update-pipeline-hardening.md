# Update Pipeline Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make data refreshes transactional, reject suspicious source regressions, validate final data deeply, and serve/deploy only an explicit static-site artifact.

**Architecture:** Existing generators remain standalone scripts but honor `PROJECT_SEKAI_OUTPUT_DIR`. `auto_update.py` builds into a temporary directory, validates there, then publishes the complete output set with rollback. A small site builder creates an allowlisted `dist/` consumed by both GitHub Pages and the local launcher.

**Tech Stack:** Python 3 standard library, `unittest`, GitHub Actions, Windows batch files.

---

### Task 1: Add regression tests for source and validator safeguards

**Files:**
- Modify: `tests/test_auto_update.py`
- Modify: `tests/test_validate_data.py`
- Modify: `tests/test_video_source_registry.py`

**Steps:**
1. Add tests proving a large playlist count drop is rejected and a small intentional drop is accepted.
2. Add tests proving duplicate video IDs, invalid video URLs and inconsistent breakdown statistics fail validation.
3. Run `python -m unittest tests.test_auto_update tests.test_validate_data tests.test_video_source_registry -v` and confirm the new tests fail.

### Task 2: Implement staged output generation and rollback

**Files:**
- Modify: `scripts/auto_update.py`
- Modify: `scripts/build_musics_base.py`
- Modify: `scripts/build_database.py`
- Modify: `scripts/combine_music_data.py`
- Modify: `scripts/sync_aliases.py`

**Steps:**
1. Add `PROJECT_SEKAI_OUTPUT_DIR` support while preserving current defaults.
2. Change regeneration order to build the base catalog, database and combined view inside one temporary directory.
3. Validate the staged database before publication.
4. Publish the seven required outputs with rollback on any replacement error.
5. Run the focused unit tests and confirm they pass.

### Task 3: Harden playlist refresh and manual enrichment

**Files:**
- Modify: `scripts/auto_update.py`
- Modify: `scripts/enrich_playlist_channels.py`
- Modify: `scripts/video_source_registry.py`

**Steps:**
1. Reject a non-empty snapshot when its item count falls more than 20% below the current valid snapshot.
2. Validate snapshot metadata count against the actual list.
3. Resolve only the latest valid snapshot per enabled source for manual enrichment.
4. Skip writing when merged video data is unchanged.
5. Run playlist-related tests.

### Task 4: Deepen database validation

**Files:**
- Modify: `scripts/validate_data.py`
- Modify: `tests/test_validate_data.py`

**Steps:**
1. Validate top-level and collection types before traversal.
2. Require non-empty song/video identifiers and titles.
3. Validate YouTube IDs, URLs, video types and uniqueness.
4. Recompute matched-song, video-type and unit statistics and compare them with metadata.
5. Run validation against `output/database_v2.json`.

### Task 5: Build and serve an explicit site artifact

**Files:**
- Create: `scripts/build_site.py`
- Create: `tests/test_build_site.py`
- Modify: `启动本地服务器.bat`
- Modify: `start_server.bat`
- Modify: `.gitignore`
- Modify: `.github/workflows/update-data.yml`

**Steps:**
1. Add an allowlist-based builder for HTML, required output JSON, editor manual JSON and character lookup JSON.
2. Test that required assets are copied and private/project-only files are absent.
3. Update both launchers to build `dist/`, bind to `127.0.0.1`, and serve only `dist/`.
4. Update CI to check out submodules, run tests, use the unified updater, build `dist/`, and deploy `dist/`.
5. Add ignores for staging, `dist/`, `node_modules/` and generated document outputs.

### Task 6: Final verification

**Steps:**
1. Run `python -m unittest discover -s tests -v`; expect all tests to pass.
2. Run `python scripts/validate_data.py`; expect validation success.
3. Run `python scripts/build_site.py`; confirm `dist/index.html` and required JSON files exist while `dist/.git` does not.
4. Run `git diff --check` and review `git status --short` to confirm only scoped files changed.
