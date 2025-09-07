import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from auto_post.upload_to_youtube import main, upload_thumbnail

# テスト環境を設定
os.environ["TESTING"] = "true"


class TestUploadToYouTubeAdditional(unittest.TestCase):
    """upload_to_youtube.pyの追加テスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_video_id = "test_video_id_123"
        self.test_thumbnail_path = "/tmp/test_thumbnail.jpg"

        # テスト用のサムネイルファイルを作成
        Path(self.test_thumbnail_path).touch()

    def tearDown(self):
        """テストのクリーンアップ"""
        if Path(self.test_thumbnail_path).exists():
            Path(self.test_thumbnail_path).unlink()

    @patch("auto_post.upload_to_youtube.get_authenticated_service")
    def test_upload_thumbnail_success(self, mock_get_service):
        """サムネイルアップロード成功のテスト"""
        # モックの設定
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # サムネイルアップロードのレスポンスをモック
        mock_service.thumbnails.return_value.set.return_value.execute.return_value = {
            "kind": "youtube#thumbnailSetResponse"
        }

        result = upload_thumbnail(self.test_video_id, self.test_thumbnail_path)

        self.assertTrue(result)
        mock_service.thumbnails.assert_called_once()

    @patch("auto_post.upload_to_youtube.get_authenticated_service")
    def test_upload_thumbnail_failure(self, mock_get_service):
        """サムネイルアップロード失敗のテスト"""
        # モックの設定
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # サムネイルアップロードで例外を発生させる
        mock_service.thumbnails.return_value.set.return_value.execute.side_effect = (
            Exception("Upload failed")
        )

        result = upload_thumbnail(self.test_video_id, self.test_thumbnail_path)

        self.assertFalse(result)

    @patch("auto_post.upload_to_youtube.get_authenticated_service")
    def test_upload_thumbnail_file_not_found(self, mock_get_service):
        """サムネイルファイルが存在しない場合のテスト"""
        # モックの設定
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        result = upload_thumbnail(self.test_video_id, "/nonexistent/thumbnail.jpg")

        self.assertFalse(result)

    @patch("auto_post.upload_to_youtube.upload_video")
    @patch("auto_post.upload_to_youtube.upload_thumbnail")
    @patch(
        "sys.argv",
        [
            "upload_to_youtube.py",
            "--video",
            "test.mp4",
            "--title",
            "Test Video",
            "--description",
            "Test Description",
        ],
    )
    def test_main_function_success(self, mock_upload_thumbnail, mock_upload_video):
        """main関数の成功テスト"""
        # モックの設定
        mock_upload_video.return_value = self.test_video_id
        mock_upload_thumbnail.return_value = True

        # main関数を実行
        with patch(
            "builtins.open",
            mock_open(
                read_data='{"title": "Test Video", "description": "Test Description", "tracklist": "Track 1, Track 2"}'
            ),
        ):
            with patch("pathlib.Path.exists", return_value=True):
                main()

        mock_upload_video.assert_called_once()

    @patch("auto_post.upload_to_youtube.upload_video")
    @patch(
        "sys.argv",
        [
            "upload_to_youtube.py",
            "--video",
            "test.mp4",
            "--title",
            "Test Video",
            "--description",
            "Test Description",
            "--thumbnail",
            "test.jpg",
        ],
    )
    def test_main_function_with_thumbnail(self, mock_upload_video):
        """サムネイル付きのmain関数テスト"""
        # モックの設定
        mock_upload_video.return_value = self.test_video_id

        # main関数を実行
        with patch(
            "builtins.open",
            mock_open(
                read_data='{"title": "Test Video", "description": "Test Description", "tracklist": "Track 1, Track 2"}'
            ),
        ):
            with patch("pathlib.Path.exists", return_value=True):
                with patch(
                    "auto_post.upload_to_youtube.upload_thumbnail", return_value=True
                ) as mock_upload_thumbnail:
                    main()

        mock_upload_video.assert_called_once()
        mock_upload_thumbnail.assert_called_once_with(self.test_video_id, "test.jpg")

    @patch("auto_post.upload_to_youtube.upload_video")
    @patch(
        "sys.argv",
        [
            "upload_to_youtube.py",
            "--video",
            "test.mp4",
            "--title",
            "Test Video",
            "--description",
            "Test Description",
            "--tags",
            "lofi,music,chill",
        ],
    )
    def test_main_function_with_tags(self, mock_upload_video):
        """タグ付きのmain関数テスト"""
        # モックの設定
        mock_upload_video.return_value = self.test_video_id

        # main関数を実行
        with patch(
            "builtins.open",
            mock_open(
                read_data='{"title": "Test Video", "description": "Test Description", "tracklist": "Track 1, Track 2"}'
            ),
        ):
            with patch("pathlib.Path.exists", return_value=True):
                main()

        # タグが正しく処理されていることを確認
        call_args = mock_upload_video.call_args
        self.assertEqual(call_args[1]["tags"], ["lofi", "music", "chill"])

    @patch("auto_post.upload_to_youtube.upload_video")
    @patch(
        "sys.argv",
        [
            "upload_to_youtube.py",
            "--video",
            "test.mp4",
            "--title",
            "Test Video",
            "--description",
            "Test Description",
            "--privacy",
            "public",
        ],
    )
    def test_main_function_public_privacy(self, mock_upload_video):
        """公開設定のmain関数テスト"""
        # モックの設定
        mock_upload_video.return_value = self.test_video_id

        # main関数を実行
        with patch(
            "builtins.open",
            mock_open(
                read_data='{"title": "Test Video", "description": "Test Description", "tracklist": "Track 1, Track 2"}'
            ),
        ):
            with patch("pathlib.Path.exists", return_value=True):
                main()

        # プライバシー設定が正しく処理されていることを確認
        call_args = mock_upload_video.call_args
        self.assertEqual(call_args[1]["privacy_status"], "public")

    @patch("auto_post.upload_to_youtube.upload_video")
    @patch(
        "sys.argv",
        [
            "upload_to_youtube.py",
            "--video",
            "test.mp4",
            "--title",
            "Test Video",
            "--description",
            "Test Description",
        ],
    )
    def test_main_function_upload_failure(self, mock_upload_video):
        """アップロード失敗時のmain関数テスト"""
        # モックの設定
        mock_upload_video.return_value = None

        # main関数を実行
        with patch(
            "builtins.open",
            mock_open(
                read_data='{"title": "Test Video", "description": "Test Description", "tracklist": "Track 1, Track 2"}'
            ),
        ):
            with patch("pathlib.Path.exists", return_value=True):
                main()  # SystemExitは発生しない

        # アップロードが失敗したことを確認
        mock_upload_video.assert_called_once()


if __name__ == "__main__":
    unittest.main()
