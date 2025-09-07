import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from auto_post.piapi_music_generation import (
    create_music_task,
    download_audio,
    generate_unique_filename,
    get_existing_filenames,
    piapi_music_generation,
    wait_for_task,
)


class TestPiapiMusicGeneration(unittest.TestCase):
    """piapi_music_generationモジュールの単体テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_music_dir = Path(self.temp_dir) / "music"
        self.test_music_dir.mkdir()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)

    def test_get_existing_filenames_empty_directory(self):
        """空のディレクトリでのファイル名取得テスト"""
        filenames = get_existing_filenames(str(self.test_music_dir))
        self.assertEqual(filenames, set())

    def test_get_existing_filenames_with_mp3_files(self):
        """MP3ファイルがある場合のテスト"""
        # テストファイルを作成
        test_files = ["track1.mp3", "track2.mp3", "not_audio.txt", "track3.wav"]
        for filename in test_files:
            (self.test_music_dir / filename).touch()

        filenames = get_existing_filenames(str(self.test_music_dir))
        expected = {"track1", "track2"}

        self.assertEqual(filenames, expected)

    def test_generate_unique_filename_no_duplicate(self):
        """重複がない場合のファイル名生成テスト"""
        title = "Test Track"
        prompt = "melancholic piano"

        result = generate_unique_filename(title, str(self.test_music_dir), prompt)
        expected = "Test_Track.mp3"

        self.assertEqual(result, expected)

    def test_generate_unique_filename_with_duplicate(self):
        """重複がある場合のファイル名生成テスト"""
        # 既存ファイルを作成
        (self.test_music_dir / "Test_Track.mp3").touch()

        title = "Test Track"
        prompt = "melancholic piano"

        with patch("auto_post.piapi_music_generation.fetch_track_title") as mock_title:
            mock_title.return_value = "New Track"
            result = generate_unique_filename(title, str(self.test_music_dir), prompt)

        # 重複を避けるため、異なるファイル名が生成される
        self.assertEqual(result, "New_Track.mp3")

    def test_generate_unique_filename_special_characters(self):
        """特殊文字を含むタイトルのファイル名生成テスト"""
        title = "Test Track (Remix) [2024]"
        prompt = "melancholic piano"

        result = generate_unique_filename(title, str(self.test_music_dir), prompt)
        expected = "Test_Track_Remix_2024.mp3"

        self.assertEqual(result, expected)

    def test_generate_unique_filename_empty_title(self):
        """空のタイトルのファイル名生成テスト"""
        title = ""
        prompt = "melancholic piano"

        result = generate_unique_filename(title, str(self.test_music_dir), prompt)
        expected = "track.mp3"

        self.assertEqual(result, expected)

    @patch("auto_post.piapi_music_generation.requests.post")
    def test_create_music_task_success(self, mock_post):
        """音楽生成タスク作成成功時のテスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": "test_task_123",
            "status": "Pending",
        }
        mock_post.return_value = mock_response

        task_id = create_music_task("melancholic piano")

        self.assertEqual(task_id, "test_task_123")
        mock_post.assert_called_once()

    @patch("auto_post.piapi_music_generation.requests.post")
    def test_create_music_task_failure(self, mock_post):
        """音楽生成タスク作成失敗時のテスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = Exception("Bad Request")
        mock_post.return_value = mock_response

        with self.assertRaises(Exception):
            create_music_task("melancholic piano")

    @patch("auto_post.piapi_music_generation.requests.get")
    def test_wait_for_task_completed(self, mock_get):
        """タスク完了待機テスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "Completed",
            "output": {
                "songs": [{"duration": 120, "url": "https://example.com/audio.mp3"}]
            },
        }
        mock_get.return_value = mock_response

        result = wait_for_task("test_task_123")

        self.assertEqual(result["status"], "Completed")
        self.assertIn("songs", result["output"])

    @patch("auto_post.piapi_music_generation.requests.get")
    def test_wait_for_task_failed(self, mock_get):
        """タスク失敗待機テスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "Failed",
            "error": "Generation failed",
        }
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            wait_for_task("test_task_123")

    @patch("auto_post.piapi_music_generation.requests.get")
    def test_download_audio_success(self, mock_get):
        """音声ファイルダウンロード成功時のテスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake_audio_content"
        mock_response.iter_content.return_value = [b"fake_audio_content"]
        mock_get.return_value.__enter__.return_value = mock_response

        output_path = self.test_music_dir / "test_audio.mp3"
        download_audio("https://example.com/audio.mp3", str(output_path))

        self.assertTrue(output_path.exists())

    @patch("auto_post.piapi_music_generation.requests.get")
    def test_download_audio_failure(self, mock_get):
        """音声ファイルダウンロード失敗時のテスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not Found")
        mock_get.return_value.__enter__.return_value = mock_response

        output_path = self.test_music_dir / "test_audio.mp3"

        with self.assertRaises(Exception):
            download_audio("https://example.com/audio.mp3", str(output_path))

    @patch("auto_post.piapi_music_generation.create_music_task")
    @patch("auto_post.piapi_music_generation.wait_for_task")
    @patch("auto_post.piapi_music_generation.download_audio")
    @patch("auto_post.piapi_music_generation.fetch_track_title")
    @patch("auto_post.piapi_music_generation.generate_unique_filename")
    @patch("auto_post.piapi_music_generation.extract_audio_url")
    def test_piapi_music_generation_success(
        self,
        mock_extract_url,
        mock_filename,
        mock_title,
        mock_download,
        mock_wait,
        mock_create,
    ):
        """音楽生成全体の成功フローテスト"""
        # モックの設定
        mock_create.return_value = "test_task_123"
        mock_wait.return_value = {
            "status": "Completed",
            "output": {
                "songs": [{"duration": 120, "url": "https://example.com/audio.mp3"}]
            },
        }
        mock_extract_url.return_value = "https://example.com/audio.mp3"
        mock_title.return_value = "Test Track"
        mock_filename.return_value = "test_track.mp3"

        piapi_music_generation(
            today_folder=str(self.test_music_dir),
            prompt="melancholic piano",
            target_duration_sec=120,
        )

        mock_create.assert_called()
        mock_wait.assert_called()
        mock_download.assert_called()


if __name__ == "__main__":
    unittest.main()
