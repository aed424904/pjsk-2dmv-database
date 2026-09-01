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
        self.assertEqual(normalize_role_label("Video Direction"), "direction")

    def test_extracts_audio_credit_roles(self):
        parsed = parse_staff_lines("Vocal: 初音ミク\nGuitar: テスト\nMix & Mastering: エンジニア")

        self.assertEqual(
            {item["role"] for item in parsed["contributors"]},
            {"vocalist", "musician", "mixing", "mastering"},
        )
        self.assertEqual(parsed["unknownRoleLines"], [])

    def test_extracts_combined_lyrics_music_and_arrangement(self):
        parsed = parse_staff_lines("作詞・作曲・編曲：Example")

        self.assertEqual(
            {item["role"] for item in parsed["contributors"]},
            {"lyricist", "composer", "arranger"},
        )

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

    def test_prefers_role_delimiter_when_contributor_name_contains_by(self):
        description = "動画：AKITO(CASANE. by THINGS.)"
        result = parse_staff_lines(description)

        self.assertEqual(result["contributors"][0]["role"], "pvCreator")
        self.assertEqual(result["contributors"][0]["name"], "AKITO(CASANE. by THINGS.)")

    def test_skips_copyright_notice_with_by_wording(self):
        result = parse_staff_lines("(C) Craft Egg Inc. Developed by Colorful Palette")

        self.assertEqual(result["contributors"], [])
        self.assertEqual(result["unknownRoleLines"], [])

    def test_duplicate_credit_line_is_not_reported_as_unparsed(self):
        result = parse_staff_lines("背景：Studio A\n背景：Studio A")

        self.assertEqual(len(result["contributors"]), 1)
        self.assertEqual(result["unparsedLines"], [])


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

    def test_attaches_continuation_names_to_previous_role(self):
        result = parse_staff_lines(
            "動画：Creator A https://example.com/a\n"
            "Creator B https://example.com/b"
        )

        self.assertEqual(
            [item["name"] for item in result["contributors"]],
            ["Creator A", "Creator B"],
        )
        self.assertTrue(all(item["role"] == "pvCreator" for item in result["contributors"]))

    def test_parses_role_header_followed_by_multiple_people(self):
        result = parse_staff_lines("作画：\n衣谷ソーシ\n長野 新平")

        self.assertEqual(
            [item["name"] for item in result["contributors"]],
            ["衣谷ソーシ", "長野 新平"],
        )
        self.assertTrue(all(item["role"] == "animation" for item in result["contributors"]))

    def test_parses_known_music_role_prefix_without_colon(self):
        result = parse_staff_lines("1st Trumpet Player A")

        self.assertEqual(result["contributors"][0]["role"], "musician")
        self.assertEqual(result["contributors"][0]["name"], "Player A")

    def test_does_not_treat_lyrics_body_as_lyricist_names(self):
        result = parse_staff_lines(
            "Lyrics: Sena Kiryuin / monii / KIRA\n"
            "\n"
            "LYRICS:\n"
            "Uhuh\n"
            "Make 'em move right now"
        )

        self.assertEqual(
            [item["name"] for item in result["contributors"]],
            ["Sena Kiryuin", "monii", "KIRA"],
        )


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

    def test_groups_music_credits_without_losing_raw_roles(self):
        result = build_video_staff(
            "作詞・作曲：Producer\nGuitar：Player A / Player B\nMastering：Engineer"
        )

        self.assertEqual(result["otherRoles"]["lyricist"], ["Producer"])
        self.assertEqual(result["otherRoles"]["composer"], ["Producer"])
        self.assertEqual(result["otherRoles"]["musician"], ["Player A", "Player B"])
        self.assertEqual(result["otherRoles"]["mastering"], ["Engineer"])
        self.assertTrue(any(item["roleRaw"] == "Guitar" for item in result["contributors"]))


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
