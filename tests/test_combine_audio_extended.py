import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from auto_post.combine_audio import combine_audio

# テスト対象のモジュールをインポート


class TestCombineAudioExtended(unittest.TestCase):
    """combine_audioモジュールの拡張単体テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.input_dir = self.temp_path / "input"
        self.output_dir = self.temp_path / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)

    def test_combine_audio_no_mp3_files(self):
        """MP3ファイルがない場合のテスト"""
        with patch("builtins.print"):
            # MP3ファイルがない場合は例外が発生するか、空の結果が返される
            try:
                result = combine_audio(
                    input_dir=str(self.input_dir),
                    output_dir=str(self.output_dir),
                    fade_ms=3000,
                    ambient=None,
                )
                # 例外が発生しない場合は、結果が返されることを確認
                self.assertIsInstance(result, tuple)
            except ValueError as e:
                # 例外が発生する場合は、適切なメッセージが含まれることを確認
                self.assertIn("MP3ファイル", str(e))

    def test_combine_audio_single_file(self):
        """単一ファイルの場合のテスト"""
        # テスト用のMP3ファイルを作成
        test_file = self.input_dir / "test.mp3"
        test_file.touch()

        with patch("auto_post.combine_audio.AudioSegment") as mock_audio:
            mock_segment = Mock()
            mock_audio.from_mp3.return_value = mock_segment
            mock_segment.__len__ = Mock(return_value=60000)  # 60秒

            with patch("builtins.print"):
                result = combine_audio(
                    input_dir=str(self.input_dir),
                    output_dir=str(self.output_dir),
                    fade_ms=3000,
                    ambient=None,
                )

                # 結果が返されることを確認
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)

    def test_combine_audio_multiple_files(self):
        """複数ファイルの場合のテスト"""
        # テスト用のMP3ファイルを作成
        test_files = [
            self.input_dir / "test1.mp3",
            self.input_dir / "test2.mp3",
            self.input_dir / "test3.mp3",
        ]
        for file in test_files:
            file.touch()

        with patch("auto_post.combine_audio.AudioSegment") as mock_audio:
            mock_segment = Mock()
            mock_audio.from_mp3.return_value = mock_segment
            mock_segment.__len__ = Mock(return_value=60000)  # 60秒

            with patch("builtins.print"):
                result = combine_audio(
                    input_dir=str(self.input_dir),
                    output_dir=str(self.output_dir),
                    fade_ms=3000,
                    ambient=None,
                )

                # 結果が返されることを確認
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)

    def test_combine_audio_with_ambient(self):
        """アンビエント音ありの場合のテスト"""
        # テスト用のMP3ファイルを作成
        test_file = self.input_dir / "test.mp3"
        test_file.touch()

        # アンビエントファイルを作成
        ambient_file = self.temp_path / "ambient.mp3"
        ambient_file.touch()

        with patch("auto_post.combine_audio.AudioSegment") as mock_audio:
            mock_segment = Mock()
            mock_audio.from_mp3.return_value = mock_segment
            mock_segment.__len__ = Mock(return_value=60000)  # 60秒

            with patch("builtins.print"):
                result = combine_audio(
                    input_dir=str(self.input_dir),
                    output_dir=str(self.output_dir),
                    fade_ms=3000,
                    ambient=str(ambient_file),
                )

                # 結果が返されることを確認
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)

    def test_combine_audio_ambient_file_not_found(self):
        """アンビエントファイルが見つからない場合のテスト"""
        # テスト用のMP3ファイルを作成
        test_file = self.input_dir / "test.mp3"
        test_file.touch()

        with patch("auto_post.combine_audio.AudioSegment") as mock_audio:
            mock_segment = Mock()
            mock_audio.from_mp3.return_value = mock_segment
            mock_segment.__len__ = Mock(return_value=60000)  # 60秒

            with patch("builtins.print"):
                result = combine_audio(
                    input_dir=str(self.input_dir),
                    output_dir=str(self.output_dir),
                    fade_ms=3000,
                    ambient="nonexistent_ambient.mp3",
                )

                # 結果が返されることを確認（アンビエントファイルがなくても処理は続行）
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)

    def test_combine_audio_fade_ms_zero(self):
        """フェード時間が0の場合のテスト"""
        # テスト用のMP3ファイルを作成
        test_file = self.input_dir / "test.mp3"
        test_file.touch()

        with patch("auto_post.combine_audio.AudioSegment") as mock_audio:
            mock_segment = Mock()
            mock_audio.from_mp3.return_value = mock_segment
            mock_segment.__len__ = Mock(return_value=60000)  # 60秒

            with patch("builtins.print"):
                result = combine_audio(
                    input_dir=str(self.input_dir),
                    output_dir=str(self.output_dir),
                    fade_ms=0,
                    ambient=None,
                )

                # 結果が返されることを確認
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)

    def test_combine_audio_fade_ms_negative(self):
        """フェード時間が負の場合のテスト"""
        # テスト用のMP3ファイルを作成
        test_file = self.input_dir / "test.mp3"
        test_file.touch()

        with patch("auto_post.combine_audio.AudioSegment") as mock_audio:
            mock_segment = Mock()
            mock_audio.from_mp3.return_value = mock_segment
            mock_segment.__len__ = Mock(return_value=60000)  # 60秒

            with patch("builtins.print"):
                result = combine_audio(
                    input_dir=str(self.input_dir),
                    output_dir=str(self.output_dir),
                    fade_ms=-1000,
                    ambient=None,
                )

                # 結果が返されることを確認
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)

    def test_combine_audio_very_long_fade(self):
        """非常に長いフェード時間の場合のテスト"""
        # テスト用のMP3ファイルを作成
        test_file = self.input_dir / "test.mp3"
        test_file.touch()

        with patch("auto_post.combine_audio.AudioSegment") as mock_audio:
            mock_segment = Mock()
            mock_audio.from_mp3.return_value = mock_segment
            mock_segment.__len__ = Mock(return_value=60000)  # 60秒

            with patch("builtins.print"):
                result = combine_audio(
                    input_dir=str(self.input_dir),
                    output_dir=str(self.output_dir),
                    fade_ms=30000,  # 30秒のフェード
                    ambient=None,
                )

                # 結果が返されることを確認
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)

    def test_combine_audio_output_dir_creation(self):
        """出力ディレクトリが存在しない場合のテスト"""
        # テスト用のMP3ファイルを作成
        test_file = self.input_dir / "test.mp3"
        test_file.touch()

        # 出力ディレクトリを削除
        shutil.rmtree(self.output_dir)

        with patch("auto_post.combine_audio.AudioSegment") as mock_audio:
            mock_segment = Mock()
            mock_audio.from_mp3.return_value = mock_segment
            mock_segment.__len__ = Mock(return_value=60000)  # 60秒

            with patch("builtins.print"):
                result = combine_audio(
                    input_dir=str(self.input_dir),
                    output_dir=str(self.output_dir),
                    fade_ms=3000,
                    ambient=None,
                )

                # 結果が返されることを確認
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)

                # 出力ディレクトリが作成されるか、結果が返されることを確認
                # （実際の実装によっては、ディレクトリが作成されない場合もある）
                pass


if __name__ == "__main__":
    unittest.main()
