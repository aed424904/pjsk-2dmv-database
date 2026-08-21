import unittest
from unittest import mock

from scripts.staff_extraction import (
    build_staff_review_rows,
    build_staff_index_rows,
    build_video_staff,
    load_role_aliases,
    normalize_role_label,
    parse_staff_lines,
    summarize_song_staff,
)


class StaffRoleTaxonomyTests(unittest.TestCase):
    def test_normalizes_known_role_labels(self):
        self.assertEqual(normalize_role_label("イラスト"), "illustrator")
        self.assertEqual(normalize_role_label("動画"), "pvCreator")
        self.assertEqual(normalize_role_label("イラストアニメーション"), "illustrationAnimation")
        self.assertEqual(normalize_role_label("リリックデザイン"), "lyricDesign")
        self.assertEqual(normalize_role_label("3DCG"), "cg3d")

    def test_normalizes_manual_visual_role_aliases(self):
        load_role_aliases.cache_clear()
        self.assertEqual(normalize_role_label("Graphic Design"), "design")
        self.assertEqual(normalize_role_label("原画"), "animation")
        self.assertEqual(normalize_role_label("Video Direction"), "pvCreator")

    def test_skips_audio_credit_roles(self):
        parsed = parse_staff_lines("Vocal: 初音ミク\nGuitar: テスト\nMix & Mastering: テスト")

        self.assertEqual(parsed["contributors"], [])
        self.assertEqual(parsed["unknownRoleLines"], [])

    def test_skips_roles_explicitly_mapped_to_ignore(self):
        with mock.patch("scripts.staff_extraction.load_role_aliases", return_value={"制作": "ignore"}):
            parsed = parse_staff_lines("制作：Studio Example")

        self.assertEqual(parsed["contributors"], [])
        self.assertEqual(parsed["unknownRoleLines"], [])


class StaffLineParsingTests(unittest.TestCase):
    def test_skips_exact_lines_from_manual_ignore_list(self):
        line = "X(旧twitter)：https://x.com/example"
        with mock.patch("scripts.staff_extraction.load_ignored_staff_lines", return_value={line}):
            result = parse_staff_lines(line)

        self.assertEqual(result["contributors"], [])
        self.assertEqual(result["unparsedLines"], [])

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
        description = "未知役職：Someone"
        result = parse_staff_lines(description)
        self.assertEqual(result["contributors"][0]["role"], "unknown")
        self.assertEqual(result["contributors"][0]["roleRaw"], "未知役職")

    def test_strips_dangling_fullwidth_parenthesis_after_url_cleanup(self):
        description = "イラスト：おかざきおか（https://twitter.com/okazakiokaa）"
        result = parse_staff_lines(description)
        self.assertEqual(result["contributors"][0]["name"], "おかざきおか")

    def test_preserves_balanced_parenthetical_name_parts(self):
        description = "動画：ZIIEK（THINGS.）（https://twitter.com/smoken4129）"
        result = parse_staff_lines(description)
        self.assertEqual(result["contributors"][0]["name"], "ZIIEK（THINGS.）")


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


class VideoStaffBuilderTests(unittest.TestCase):
    def test_build_video_staff_shape(self):
        description = "\n".join(
            [
                "イラスト：燠 https://x.com/oki_charcoal",
                "動画：omu https://x.com/omu929",
                "アニメーションプロデューサー：Someone",
            ]
        )
        result = build_video_staff(description)
        expected_keys = {
            "illustrators",
            "pvCreators",
            "otherRoles",
            "contributors",
            "unparsedLines",
            "unknownRoleLines",
        }
        self.assertEqual(set(result.keys()), expected_keys)


class SongStaffSummaryTests(unittest.TestCase):
    def test_summarizes_multiple_video_staff_payloads(self):
        video_staff_list = [
            build_video_staff("イラスト：燠\n動画：omu\nリリックデザイン：Heetami"),
            build_video_staff("イラスト：燠\n動画：春望かなめ\n3DCG：Yostar Pictures"),
        ]
        result = summarize_song_staff(video_staff_list)
        self.assertEqual(result["illustrators"], ["燠"])
        self.assertEqual(result["pvCreators"], ["omu", "春望かなめ"])
        self.assertEqual(result["otherRoles"]["lyricDesign"], ["Heetami"])
        self.assertEqual(result["otherRoles"]["cg3d"], ["Yostar Pictures"])
        self.assertTrue(result["allContributors"])


class StaffAuditExportTests(unittest.TestCase):
    def test_flattens_contributors_and_collects_review_rows(self):
        songs = [
            {
                "id": "song_test",
                "title": "Test Song",
                "videos": [
                    {
                        "videoId": "video_1",
                        "title": "Test Video",
                        "staff": build_video_staff(
                            "\n".join(
                                [
                                    "イラスト：燠",
                                    "未知役職：Someone",
                                    "Graphic Designer:",
                                ]
                            )
                        ),
                    }
                ],
            }
        ]
        index_rows = build_staff_index_rows(songs)
        review_rows = build_staff_review_rows(songs)
        self.assertEqual(index_rows[0]["songId"], "song_test")
        self.assertEqual(index_rows[0]["videoId"], "video_1")
        self.assertEqual(review_rows[0]["songTitle"], "Test Song")
        self.assertIn("未知役職：Someone", review_rows[0]["unknownRoleLines"])
        self.assertIn("Graphic Designer:", review_rows[0]["unparsedLines"])
