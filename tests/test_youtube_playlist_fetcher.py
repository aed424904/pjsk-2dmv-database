import unittest
from unittest.mock import Mock, patch

from fetch_youtube_playlist.fetch_youtube_playlist import YouTubePlaylistFetcher


class YouTubePlaylistFetcherTests(unittest.TestCase):
    @patch("fetch_youtube_playlist.fetch_youtube_playlist.time.sleep")
    def test_request_api_retries_retryable_status_with_timeout(self, mock_sleep):
        retry_response = Mock(status_code=503, headers={"Retry-After": "0"})
        success_response = Mock(status_code=200, headers={})
        fake_requests = Mock()
        fake_requests.RequestException = Exception
        mock_get = fake_requests.get
        mock_get.side_effect = [retry_response, success_response]
        fetcher = YouTubePlaylistFetcher(api_key="test", max_retries=2)

        with patch("fetch_youtube_playlist.fetch_youtube_playlist.requests", fake_requests):
            response = fetcher.request_api("playlistItems", {"key": "test"})

        self.assertIs(response, success_response)
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(mock_get.call_args.kwargs["timeout"], (5, 30))
        mock_sleep.assert_called_once_with(0.0)

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
