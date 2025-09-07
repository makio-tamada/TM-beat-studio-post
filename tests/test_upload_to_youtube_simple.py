import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from auto_post.upload_to_youtube import upload_video_to_youtube

# テスト対象のモジュールをインポート


class TestUploadToYouTubeSimple(unittest.TestCase):
    """upload_to_youtubeモジュールのシンプルな単体テスト"""

    def setUp(self):
        """テスト前の準備"""
        # テスト環境変数を設定
        os.environ["TESTING"] = "true"

        self.temp_dir = tempfile.mkdtemp()
        self.test_output_dir = Path(self.temp_dir) / "output"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

        # テスト用のファイルを作成
        self.video_path = self.test_output_dir / "test_video.mp4"
        self.thumbnail_path = self.test_output_dir / "test_thumbnail.png"
        self.metadata_path = self.test_output_dir / "test_metadata.json"

        self.video_path.touch()
        self.thumbnail_path.touch()
        self.metadata_path.touch()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)

    @patch("auto_post.config.Config.validate_config")
    @patch("auto_post.upload_to_youtube.upload_video")
    @patch("auto_post.upload_to_youtube.InstalledAppFlow")
    @patch("auto_post.upload_to_youtube.build")
    def test_upload_video_to_youtube_success(
        self, mock_build, mock_flow, mock_upload_video, mock_validate_config
    ):
        """YouTubeアップロード成功時のテスト"""
        # モックの設定
        mock_credentials = MagicMock()
        mock_flow.return_value.run_local_server.return_value = mock_credentials

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # アップロードレスポンスのモック
        mock_response = {"id": "test_video_id"}
        mock_service.videos.return_value.insert.return_value.execute.return_value = (
            mock_response
        )

        # サムネイルアップロードのモック
        mock_service.thumbnails.return_value.set.return_value.execute.return_value = {}

        # upload_video関数のモック
        mock_upload_video.return_value = "test_video_id"

        with patch(
            "builtins.open",
            mock_open(
                read_data='{"title": "Test Video", "description": "Test Description", "tracklist": "Track 1, Track 2"}'
            ),
        ):
            with patch("pathlib.Path.read_text", return_value="Post detail content"):
                with patch("builtins.print"):
                    result = upload_video_to_youtube(
                        video_path=self.video_path,
                        thumbnail_path=self.thumbnail_path,
                        metadata_path=self.metadata_path,
                        privacy="public",
                        tags=["lofi", "music"],
                    )

                    self.assertEqual(result, "test_video_id")
                    mock_upload_video.assert_called_once()

    @patch("auto_post.config.Config.validate_config")
    @patch("auto_post.upload_to_youtube.InstalledAppFlow")
    @patch("auto_post.upload_to_youtube.build")
    def test_upload_video_to_youtube_upload_error(
        self, mock_build, mock_flow, mock_validate_config
    ):
        """アップロードエラー時のテスト"""
        # モックの設定
        mock_credentials = MagicMock()
        mock_flow.return_value.run_local_server.return_value = mock_credentials

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # アップロードエラーのモック
        mock_service.videos.return_value.insert.return_value.execute.side_effect = (
            Exception("Upload failed")
        )

        with patch(
            "builtins.open",
            mock_open(
                read_data='{"title": "Test Video", "description": "Test Description", "tracklist": "Track 1, Track 2"}'
            ),
        ):
            with patch("pathlib.Path.read_text", return_value="Post detail content"):
                with patch("builtins.print"):
                    with self.assertRaises(Exception):
                        upload_video_to_youtube(
                            video_path=self.video_path,
                            thumbnail_path=self.thumbnail_path,
                            metadata_path=self.metadata_path,
                            privacy="public",
                            tags=["lofi", "music"],
                        )

    @patch("auto_post.config.Config.validate_config")
    @patch("auto_post.upload_to_youtube.InstalledAppFlow")
    @patch("auto_post.upload_to_youtube.build")
    def test_upload_video_to_youtube_metadata_error(
        self, mock_build, mock_flow, mock_validate_config
    ):
        """メタデータ読み込みエラー時のテスト"""
        # モックの設定
        mock_credentials = MagicMock()
        mock_flow.return_value.run_local_server.return_value = mock_credentials

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch("builtins.print"):
                with self.assertRaises(FileNotFoundError):
                    upload_video_to_youtube(
                        video_path=self.video_path,
                        thumbnail_path=self.thumbnail_path,
                        metadata_path=self.metadata_path,
                        privacy="public",
                        tags=["lofi", "music"],
                    )

    @patch("auto_post.config.Config.validate_config")
    @patch("auto_post.upload_to_youtube.InstalledAppFlow")
    @patch("auto_post.upload_to_youtube.build")
    def test_upload_video_to_youtube_authentication_error(
        self, mock_build, mock_flow, mock_validate_config
    ):
        """認証エラー時のテスト"""
        # 認証エラーのモック
        mock_flow.return_value.run_local_server.side_effect = Exception(
            "Authentication failed"
        )

        with patch(
            "builtins.open",
            mock_open(
                read_data='{"title": "Test Video", "description": "Test Description", "tracklist": "Track 1, Track 2"}'
            ),
        ):
            with patch("pathlib.Path.read_text", return_value="Post detail content"):
                with patch("builtins.print"):
                    with self.assertRaises(Exception):
                        upload_video_to_youtube(
                            video_path=self.video_path,
                            thumbnail_path=self.thumbnail_path,
                            metadata_path=self.metadata_path,
                            privacy="public",
                            tags=["lofi", "music"],
                        )

    @patch("auto_post.config.Config.validate_config")
    @patch("auto_post.upload_to_youtube.upload_video")
    @patch("auto_post.upload_to_youtube.InstalledAppFlow")
    @patch("auto_post.upload_to_youtube.build")
    def test_upload_video_to_youtube_different_privacy_settings(
        self, mock_build, mock_flow, mock_upload_video, mock_validate_config
    ):
        """異なる公開設定でのアップロードテスト"""
        # モックの設定
        mock_credentials = MagicMock()
        mock_flow.return_value.run_local_server.return_value = mock_credentials

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # アップロードレスポンスのモック
        mock_response = {"id": "test_video_id"}
        mock_service.videos.return_value.insert.return_value.execute.return_value = (
            mock_response
        )

        # サムネイルアップロードのモック
        mock_service.thumbnails.return_value.set.return_value.execute.return_value = {}

        # upload_video関数のモック
        mock_upload_video.return_value = "test_video_id"

        privacy_settings = ["public", "private", "unlisted"]

        with patch(
            "builtins.open",
            mock_open(
                read_data='{"title": "Test Video", "description": "Test Description", "tracklist": "Track 1, Track 2"}'
            ),
        ):
            with patch("pathlib.Path.read_text", return_value="Post detail content"):
                with patch("builtins.print"):
                    for privacy in privacy_settings:
                        result = upload_video_to_youtube(
                            video_path=self.video_path,
                            thumbnail_path=self.thumbnail_path,
                            metadata_path=self.metadata_path,
                            privacy=privacy,
                            tags=["lofi", "music"],
                        )

                        self.assertEqual(result, "test_video_id")


if __name__ == "__main__":
    unittest.main()
