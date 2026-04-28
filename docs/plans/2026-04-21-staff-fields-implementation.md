# Staff Fields Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract illustrators, PV creators, and other staff roles from 2DMV descriptions into structured video-level and song-level fields that are easy to query and count.

**Architecture:** Add a dedicated parser module that turns description lines into normalized contributor records. Integrate that parser into `scripts/build_database.py` so each video gets a `staff` object and each song gets a deduplicated `staffSummary`. Emit two audit outputs: a flat contributor index for statistics and a review file for unrecognized or ambiguous lines.

**Tech Stack:** Python 3, standard library (`json`, `re`, `pathlib`, `unittest`), existing playlist JSON, existing `scripts/build_database.py` pipeline.

---

> Note: the workspace root is not currently a Git repository, so use named checkpoints instead of commit steps unless the project is moved under Git later.

### Task 1: Define The Staff Schema And Role Taxonomy

**Files:**
- Create: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\manual_data\staff_role_aliases.json`
- Create: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\manual_data\staff_name_aliases.json`
- Create: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\tests\test_staff_extraction.py`
- Create: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\scripts\staff_extraction.py`

**Step 1: Write the failing test**

Create `tests/test_staff_extraction.py` with a taxonomy test that expects these canonical roles:

```python
import unittest

from scripts.staff_extraction import normalize_role_label


class StaffRoleTaxonomyTests(unittest.TestCase):
    def test_normalizes_known_role_labels(self):
        self.assertEqual(normalize_role_label("イラスト"), "illustrator")
        self.assertEqual(normalize_role_label("動画"), "pvCreator")
        self.assertEqual(normalize_role_label("イラストアニメーション"), "illustrationAnimation")
        self.assertEqual(normalize_role_label("リリックデザイン"), "lyricDesign")
        self.assertEqual(normalize_role_label("3DCG"), "cg3d")
```

**Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_staff_extraction -v
```

Expected: FAIL with import error because `scripts.staff_extraction` does not exist yet.

**Step 3: Write minimal implementation**

Create `scripts/staff_extraction.py` with:
- a canonical role list:
  - `illustrator`
  - `pvCreator`
  - `illustrationAnimation`
  - `lyricDesign`
  - `animation`
  - `design`
  - `cg3d`
  - `unknown`
- a `normalize_role_label(role_raw: str) -> str` function
- JSON loaders for `manual_data/staff_role_aliases.json` and `manual_data/staff_name_aliases.json`
- default role alias entries for currently observed labels:
  - `イラスト`
  - `Illustrator`
  - `Illustration`
  - `Illust`
  - `動画`
  - `映像`
  - `Movie`
  - `Video`
  - `Movie Editor`
  - `イラストアニメーション`
  - `アニメーション`
  - `Animation`
  - `リリックデザイン`
  - `Graphic Designer`
  - `Design`
  - `3DCG`
  - `CG`

**Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest tests.test_staff_extraction -v
```

Expected: PASS for `test_normalizes_known_role_labels`.

**Step 5: Checkpoint**

Record checkpoint: `taxonomy-and-alias-loaders-ready`


### Task 2: Parse Description Lines Into Contributor Records

**Files:**
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\tests\test_staff_extraction.py`
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\scripts\staff_extraction.py`

**Step 1: Write the failing test**

Add tests for these real-world cases:

```python
from scripts.staff_extraction import parse_staff_lines


class StaffLineParsingTests(unittest.TestCase):
    def test_extracts_single_role_single_name(self):
        description = "イラスト：燠 https://x.com/oki_charcoal"
        result = parse_staff_lines(description)
        self.assertEqual(result["contributors"][0]["role"], "illustrator")
        self.assertEqual(result["contributors"][0]["name"], "燠")

    def test_extracts_video_creator(self):
        description = "動画：omu https://x.com/omu929"
        result = parse_staff_lines(description)
        self.assertEqual(result["contributors"][0]["role"], "pvCreator")
        self.assertEqual(result["contributors"][0]["name"], "omu")

    def test_preserves_unknown_roles(self):
        description = "アニメーションプロデューサー：Someone"
        result = parse_staff_lines(description)
        self.assertEqual(result["contributors"][0]["role"], "unknown")
        self.assertEqual(result["contributors"][0]["roleRaw"], "アニメーションプロデューサー")
```

**Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_staff_extraction -v
```

Expected: FAIL because `parse_staff_lines` is not implemented.

**Step 3: Write minimal implementation**

In `scripts/staff_extraction.py`, implement:
- line splitting by newline
- role/name splitting by `：` and `:`
- URL stripping from the contributor side
- `contributors` output records with:
  - `name`
  - `role`
  - `roleRaw`
  - `sourceLine`
- review buckets:
  - `unparsedLines`
  - `unknownRoleLines`

Ignore lines that are obviously not staff lines:
- plain URLs
- official site links
- social links without role labels

**Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest tests.test_staff_extraction -v
```

Expected: PASS for the single-line extraction tests.

**Step 5: Checkpoint**

Record checkpoint: `basic-staff-line-parser-ready`


### Task 3: Support Multi-Role And Multi-Person Lines

**Files:**
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\tests\test_staff_extraction.py`
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\scripts\staff_extraction.py`

**Step 1: Write the failing test**

Add tests for observed variants:

```python
class StaffComplexLineParsingTests(unittest.TestCase):
    def test_splits_combined_role_labels(self):
        description = "イラスト・動画：Aster"
        result = parse_staff_lines(description)
        roles = {item["role"] for item in result["contributors"]}
        self.assertEqual(roles, {"illustrator", "pvCreator"})

    def test_splits_multiple_people(self):
        description = "Movie by OTOIRO / Director & Illustrator: lowpolydog"
        result = parse_staff_lines(description)
        self.assertTrue(any(item["role"] == "pvCreator" for item in result["contributors"]))

    def test_extracts_illustration_animation(self):
        description = "イラストアニメーション：お菊"
        result = parse_staff_lines(description)
        self.assertEqual(result["contributors"][0]["role"], "illustrationAnimation")
```

**Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_staff_extraction -v
```

Expected: FAIL on combined role or English phrasing handling.

**Step 3: Write minimal implementation**

Enhance `scripts/staff_extraction.py` to support:
- role separators: `・`, `/`, `&`, `and`
- contributor separators: `/`, `,`, `・`, `&`
- English phrasing variants:
  - `Movie by`
  - `Director & Illustrator`
  - `Graphic Designer`
- deterministic deduplication by `(normalized_role, normalized_name, sourceLine)`

Add a helper to keep original contributor text but normalize display names through `manual_data/staff_name_aliases.json`.

**Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest tests.test_staff_extraction -v
```

Expected: PASS for multi-role and multi-person cases.

**Step 5: Checkpoint**

Record checkpoint: `complex-role-parsing-ready`


### Task 4: Attach `staff` To Each Video In `database_v2.json`

**Files:**
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\scripts\build_database.py`
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\tests\test_staff_extraction.py`

**Step 1: Write the failing test**

Add a builder-oriented test that calls the parser on a representative video payload and expects this structure:

```python
expected_keys = {
    "illustrators",
    "pvCreators",
    "otherRoles",
    "contributors",
    "unparsedLines",
    "unknownRoleLines",
}
```

**Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_staff_extraction -v
```

Expected: FAIL because the builder-facing formatter does not exist yet.

**Step 3: Write minimal implementation**

In `scripts/staff_extraction.py`, add `build_video_staff(description: str) -> dict` that returns:

```json
{
  "illustrators": [],
  "pvCreators": [],
  "otherRoles": {
    "illustrationAnimation": [],
    "lyricDesign": [],
    "animation": [],
    "design": [],
    "cg3d": [],
    "unknown": []
  },
  "contributors": [],
  "unparsedLines": [],
  "unknownRoleLines": []
}
```

Then update `scripts/build_database.py`:
- import the new parser module
- add `staff` to each item in `video_entries`
- stop relying only on `_extract_creators(videos[0])` for staff-like fields

Do not remove the existing `creators` field yet; keep backward compatibility for the first rollout.

**Step 4: Run build verification**

Run:

```powershell
python scripts\build_database.py
```

Then inspect one known new entry:

```powershell
python - <<'PY'
import json, pathlib
path = pathlib.Path(r"C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\output\database_v2.json")
data = json.loads(path.read_text(encoding="utf-8"))
target = next(song for song in data["songs"] if song["title"] == "CRASH THE PARTY")
print(target["videos"][0]["staff"])
PY
```

Expected: `staff.illustrators`, `staff.pvCreators`, and contributor rows are populated.

**Step 5: Checkpoint**

Record checkpoint: `video-level-staff-ready`


### Task 5: Add Song-Level `staffSummary`

**Files:**
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\scripts\build_database.py`
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\tests\test_staff_extraction.py`

**Step 1: Write the failing test**

Add a summarization test that merges multiple video-level staff payloads and expects:
- deduplicated `illustrators`
- deduplicated `pvCreators`
- grouped `otherRoles`
- flat `allContributors`

**Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_staff_extraction -v
```

Expected: FAIL because song summarization does not exist.

**Step 3: Write minimal implementation**

In `scripts/staff_extraction.py`, add `summarize_song_staff(video_staff_list: list[dict]) -> dict`.

In `scripts/build_database.py`, add:
- `staffSummary` to each song
- aggregation from all `video_entries[*].staff`

Target output:

```json
{
  "illustrators": [],
  "pvCreators": [],
  "otherRoles": {},
  "allContributors": []
}
```

Keep `creators` for backward compatibility until frontend migration is done.

**Step 4: Run build verification**

Run:

```powershell
python scripts\build_database.py
```

Then inspect:

```powershell
python - <<'PY'
import json, pathlib
path = pathlib.Path(r"C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\output\database_v2.json")
data = json.loads(path.read_text(encoding="utf-8"))
target = next(song for song in data["songs"] if song["title"] == "CRASH THE PARTY")
print(target["staffSummary"])
PY
```

Expected: song-level summary is present and deduplicated.

**Step 5: Checkpoint**

Record checkpoint: `song-level-staff-summary-ready`


### Task 6: Emit Statistics-Friendly Audit Files

**Files:**
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\scripts\build_database.py`
- Create: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\output\video_staff_index.json`
- Create: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\output\staff_review.json`

**Step 1: Write the failing test**

Add tests for:
- flattening contributor rows into an index
- collecting `unknownRoleLines`
- collecting `unparsedLines`

**Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_staff_extraction -v
```

Expected: FAIL because export helpers do not exist.

**Step 3: Write minimal implementation**

Add export helpers that produce:

`output/video_staff_index.json`
- `songId`
- `songTitle`
- `videoId`
- `videoTitle`
- `name`
- `role`
- `roleRaw`

`output/staff_review.json`
- `songId`
- `songTitle`
- `videoId`
- `videoTitle`
- `unknownRoleLines`
- `unparsedLines`

Integrate these exports into `scripts/build_database.py` after `database_v2.json` is written.

**Step 4: Run end-to-end verification**

Run:

```powershell
python scripts\build_database.py
python - <<'PY'
import json, pathlib
base = pathlib.Path(r"C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\output")
index_data = json.loads((base / "video_staff_index.json").read_text(encoding="utf-8"))
review_data = json.loads((base / "staff_review.json").read_text(encoding="utf-8"))
print("index rows", len(index_data))
print("review rows", len(review_data))
PY
```

Expected:
- index row count is greater than zero
- review file exists and is inspectable

**Step 5: Checkpoint**

Record checkpoint: `audit-exports-ready`


### Task 7: Final Verification And Rollout Notes

**Files:**
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\docs\progress_report.md`
- Modify: `C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\README_使用说明.md`

**Step 1: Write rollout notes**

Document:
- new `staff` and `staffSummary` fields
- new audit outputs
- known limitations for `unknown` role labels
- manual correction files in `manual_data`

**Step 2: Run final verification**

Run:

```powershell
python -m unittest tests.test_staff_extraction -v
python scripts\build_database.py
```

Expected:
- tests pass
- build completes
- `output/database_v2.json`, `output/video_staff_index.json`, and `output/staff_review.json` all exist

**Step 3: Manual spot checks**

Check these songs in the built output:
- `CRASH THE PARTY`
- `傀儡のうつつ`
- `告白`
- `透過する温度`
- `カラフルファンデーション`

For each one, verify:
- `videos[0].staff.illustrators`
- `videos[0].staff.pvCreators`
- `videos[0].staff.otherRoles`
- `staffSummary`

**Step 4: Record coverage metrics**

Print and save:
- number of videos with at least one `illustrator`
- number of videos with at least one `pvCreator`
- number of videos with only `unknown` roles
- top 20 `roleRaw` values still falling into `unknown`

**Step 5: Checkpoint**

Record checkpoint: `staff-field-rollout-complete`
