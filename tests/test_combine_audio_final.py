import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from auto_post.combine_audio import combine_audio

# テスト対象のモジュールをインポート


class TestCombineAudioFinal(unittest.TestCase):
    """combine_audioモジュールの最終単体テスト"""

    def setUp(self):
        """テスト前の準備"""
        # テスト環境変数を設定
        os.environ["TESTING"] = "true"

        self.temp_dir = tempfile.mkdtemp()
        self.test_output_dir = Path(self.temp_dir) / "output"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

        # テスト用のファイルを作成
        self.ambient_file = self.test_output_dir / "ambient.mp3"
        self.music_file = self.test_output_dir / "music.mp3"
        self.output_file = self.test_output_dir / "combined.mp3"

        self.ambient_file.touch()
        self.music_file.touch()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)

    @patch("auto_post.combine_audio.AudioSegment")
    def test_combine_audio_success(self, mock_audio_segment):
        """音声結合成功時のテスト"""
        # モックの設定
        mock_ambient = MagicMock()
        mock_music = MagicMock()
        mock_combined = MagicMock()

        mock_audio_segment.from_mp3.side_effect = [mock_ambient, mock_music]
        mock_ambient.overlay.return_value = mock_combined
        mock_combined.export.return_value = None

        with patch("builtins.print"):
            result = combine_audio(
                input_dir=self.test_output_dir,
                output_dir=self.test_output_dir,
                ambient="ambient.mp3",
            )

            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)

    @patch("auto_post.combine_audio.AudioSegment")
    def test_combine_audio_no_mp3_files(self, mock_audio_segment):
        """MP3ファイルがない場合のテスト"""
        # MP3ファイルを削除
        self.ambient_file.unlink()
        self.music_file.unlink()

        with patch("builtins.print"):
            result = combine_audio(
                input_dir=self.test_output_dir,
                output_dir=self.test_output_dir,
                ambient="ambient.mp3",
            )

            # ファイルがない場合は空の結果が返される
            self.assertIsInstance(result, tuple)

    @patch("auto_post.combine_audio.AudioSegment")
    def test_combine_audio_with_ambient(self, mock_audio_segment):
        """環境音付きの音声結合テスト"""
        # モックの設定
        mock_ambient = MagicMock()
        mock_music = MagicMock()
        mock_combined = MagicMock()

        mock_audio_segment.from_mp3.side_effect = [mock_ambient, mock_music]
        mock_ambient.overlay.return_value = mock_combined
        mock_combined.export.return_value = None

        with patch("builtins.print"):
            result = combine_audio(
                input_dir=self.test_output_dir,
                output_dir=self.test_output_dir,
                ambient="ambient.mp3",
            )

            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)

    @patch("auto_post.combine_audio.AudioSegment")
    def test_combine_audio_without_ambient(self, mock_audio_segment):
        """環境音なしの音声結合テスト"""
        # モックの設定
        mock_music = MagicMock()

        mock_audio_segment.from_mp3.return_value = mock_music
        mock_music.export.return_value = None

        with patch("builtins.print"):
            result = combine_audio(
                input_dir=self.test_output_dir,
                output_dir=self.test_output_dir,
                ambient=None,
            )

            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
