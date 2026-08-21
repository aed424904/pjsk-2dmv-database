import unittest
from pathlib import Path


BASE_PATH = Path(__file__).resolve().parents[1]


class StaffReviewEditorTests(unittest.TestCase):
    def test_staff_workbench_uses_cjk_font_stack_and_readable_scale(self):
        css = (BASE_PATH / "assets" / "editor.css").read_text(encoding="utf-8")
        self.assertIn("--font-cjk: 'Noto Sans SC', 'Source Han Sans SC'", css)
        self.assertIn("'Microsoft YaHei UI', 'Yu Gothic UI', 'Meiryo'", css)
        readable_scale = css.split("/* Staff comfortable reading scale */", 1)[1]
        self.assertIn('body[data-editor-tab="staff"] .app', readable_scale)
        self.assertIn("max-width: 1760px", readable_scale)
        self.assertIn("grid-template-columns: 320px minmax(0, 1fr)", readable_scale)
        self.assertIn("font-size: 15px", readable_scale)
        self.assertIn("min-height: 48px", readable_scale)
        self.assertIn("font-family: var(--font-cjk)", readable_scale)

    def test_staff_issue_song_titles_wrap_without_being_compressed(self):
        css = (BASE_PATH / "assets" / "editor.css").read_text(encoding="utf-8")
        readable_scale = css.split("/* Staff comfortable reading scale */", 1)[1]
        self.assertIn("flex: 0 0 auto", readable_scale)
        song_rule = readable_scale.split('body[data-editor-tab="staff"] .staff-issue-song {', 1)[1].split("}", 1)[0]
        self.assertIn("white-space: normal", song_rule)
        self.assertIn("overflow-wrap: anywhere", song_rule)
        self.assertIn("line-height: 1.55", song_rule)
        self.assertIn("flex: 0 0 auto", song_rule)

    def test_staff_editor_loads_review_and_complete_manual_corrections(self):
        script = (BASE_PATH / "assets" / "staff_review_editor.js").read_text(encoding="utf-8")
        self.assertIn("const StaffReviewEditor = (function()", script)
        for source in (
            "output/staff_review.json",
            "manual_data/staff_role_aliases.json",
            "manual_data/staff_name_aliases.json",
            "manual_data/staff_line_ignores.json",
        ):
            with self.subTest(source=source):
                self.assertIn(f"fetchJson('{source}'", script)

    def test_staff_editor_supports_triage_corrections_and_stable_exports(self):
        script = (BASE_PATH / "assets" / "staff_review_editor.js").read_text(encoding="utf-8")
        for marker in (
            "function extractCandidateRole(",
            "function getIssueStatus(",
            "function saveRoleMapping(",
            "function saveNameAlias(",
            "function toggleIgnoredLine(",
            "function exportRoleAliases(",
            "function exportNameAliases(",
            "function exportIgnoredLines(",
            ".slice(0, ISSUE_RENDER_LIMIT)",
            "localeCompare",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, script)

    def test_staff_editor_uses_accessible_issue_buttons_and_labeled_forms(self):
        script = (BASE_PATH / "assets" / "staff_review_editor.js").read_text(encoding="utf-8")
        self.assertIn('class="staff-issue-card', script)
        self.assertIn('aria-pressed="${selected}"', script)
        self.assertIn('for="staff-role-value"', script)
        self.assertIn('for="staff-name-raw"', script)
        self.assertIn('id="staff-save-role-btn"', script)
        self.assertIn('id="staff-save-name-btn"', script)


if __name__ == "__main__":
    unittest.main()
