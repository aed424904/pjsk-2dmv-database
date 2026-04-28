import unittest

from fetch_youtube_playlist.fetch_youtube_playlist import YouTubePlaylistFetcher


class YouTubePlaylistFetcherTests(unittest.TestCase):
    def test_api_snippet_prefers_video_owner_channel(self):
        fetcher = YouTubePlaylistFetcher(api_key=None)

        video = fetcher.build_video_info_from_api_snippet(
            {
                "resourceId": {"videoId": "AbCdEfGhI12"},
                "title": "测试视频",
                "channelTitle": "播放列表频道",
                "channelId": "playlist-channel",
                "videoOwnerChannelTitle": "真实投稿账号",
                "videoOwnerChannelId": "owner-channel",
                "publishedAt": "2026-04-24T00:00:00Z",
                "thumbnails": {},
                "position": 3,
            }
        )

        self.assertEqual(video["channelTitle"], "真实投稿账号")
        self.assertEqual(video["channelId"], "owner-channel")

    def test_merge_video_details_preserves_playlist_position(self):
        fetcher = YouTubePlaylistFetcher(api_key=None)

        merged = fetcher.merge_video_details(
            [
                {
                    "videoId": "AbCdEfGhI12",
                    "title": "playlist title",
                    "channelTitle": "播放列表频道",
                    "channelId": "playlist-channel",
                    "publishedAt": "2026-04-20T00:00:00Z",
                    "position": 7,
                    "sourceKey": "commissioned_original_mv",
                }
            ],
            {
                "AbCdEfGhI12": {
                    "title": "actual title",
                    "description": "actual description",
                    "channelTitle": "真实投稿账号",
                    "channelId": "owner-channel",
                    "publishedAt": "2026-04-21T00:00:00Z",
                    "thumbnails": {"high": "https://example.com/high.jpg"},
                }
            },
        )

        self.assertEqual(merged[0]["channelTitle"], "真实投稿账号")
        self.assertEqual(merged[0]["channelId"], "owner-channel")
        self.assertEqual(merged[0]["position"], 7)
        self.assertEqual(merged[0]["sourceKey"], "commissioned_original_mv")


if __name__ == "__main__":
    unittest.main()
