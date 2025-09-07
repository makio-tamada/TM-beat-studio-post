import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from auto_post.combine_audio import combine_audio, load_ambient


class TestCombineAudio(unittest.TestCase):
    """combine_audioモジュールの単体テスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.input_dir = self.test_dir / "input"
        self.output_dir = self.test_dir / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()

    def tearDown(self):
        """テストのクリーンアップ"""
        import shutil

        shutil.rmtree(self.test_dir)

    @patch("auto_post.combine_audio.AudioSegment")
    def test_load_ambient_short_file(self, mock_audio_segment):
        """短い環境音ファイルのload_ambientテスト"""
        # モックの設定
        mock_ambient = Mock()
        mock_ambient.__sub__ = Mock(return_value=mock_ambient)
        mock_ambient.__mul__ = Mock(return_value=mock_ambient)
        mock_ambient.__getitem__ = Mock(return_value=mock_ambient)
        mock_ambient.__len__ = Mock(return_value=5000)  # 5秒
        mock_audio_segment.from_file.return_value = mock_ambient

        # 関数を実行
        load_ambient(Path("test_ambient.mp3"), 15000)  # 15秒

        # アサーション
        mock_audio_segment.from_file.assert_called_once_with(
            "test_ambient.mp3", format="mp3"
        )
        mock_ambient.__sub__.assert_called_once_with(10)  # 音量を下げる
        mock_ambient.__mul__.assert_called()  # ループ処理
        mock_ambient.__getitem__.assert_called_with(
            slice(None, 15000)
        )  # 目標長さに切り詰め

    @patch("auto_post.combine_audio.AudioSegment")
    def test_load_ambient_long_file(self, mock_audio_segment):
        """長い環境音ファイルのload_ambientテスト"""
        # モックの設定
        mock_ambient = Mock()
        mock_ambient.__sub__ = Mock(return_value=mock_ambient)
        mock_ambient.__getitem__ = Mock(return_value=mock_ambient)
        mock_ambient.__len__ = Mock(return_value=20000)  # 20秒
        mock_audio_segment.from_file.return_value = mock_ambient

        # 関数を実行
        load_ambient(Path("test_ambient.mp3"), 15000)  # 15秒

        # アサーション
        mock_audio_segment.from_file.assert_called_once_with(
            "test_ambient.mp3", format="mp3"
        )
        mock_ambient.__sub__.assert_called_once_with(10)  # 音量を下げる
        mock_ambient.__getitem__.assert_called_with(
            slice(None, 15000)
        )  # 目標長さに切り詰め

    @patch("auto_post.combine_audio.AudioSegment")
    def test_combine_audio_basic(self, mock_audio_segment):
        """基本的な音声結合テスト"""
        # テスト用の音声ファイルを作成
        test_file = self.input_dir / "test.mp3"
        test_file.touch()

        # モックの設定
        mock_music = Mock()
        mock_audio_segment.from_mp3.return_value = mock_music
        mock_music.export.return_value = None

        # 関数を実行
        result = combine_audio(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            ambient=None,
        )

        # アサーション
        self.assertIsNotNone(result)
        mock_audio_segment.from_mp3.assert_called_once_with(str(test_file))

    @patch("auto_post.combine_audio.AudioSegment")
    def test_combine_audio_with_ambient(self, mock_audio_segment):
        """環境音付きの音声結合テスト"""
        # テスト用の音声ファイルを作成
        test_file = self.input_dir / "test.mp3"
        test_file.touch()

        # モックの設定
        mock_music = Mock()
        mock_ambient = Mock()
        mock_combined = Mock()
        mock_audio_segment.from_mp3.return_value = mock_music
        mock_audio_segment.from_file.return_value = mock_ambient
        mock_music.overlay.return_value = mock_combined
        mock_combined.export.return_value = None

        # 関数を実行
        result = combine_audio(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            ambient="rain.mp3",
        )

        # アサーション
        self.assertIsNotNone(result)
        mock_audio_segment.from_mp3.assert_called_once_with(str(test_file))
        mock_audio_segment.from_file.assert_called_once_with("rain.mp3", format="mp3")

    def test_combine_audio_no_files(self):
        """音声ファイルがない場合のテスト"""
        # 関数を実行
        result = combine_audio(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            ambient=None,
        )

        # アサーション
        self.assertIsNone(result)

    @patch("auto_post.combine_audio.AudioSegment")
    def test_combine_audio_error_handling(self, mock_audio_segment):
        """エラーハンドリングのテスト"""
        # テスト用の音声ファイルを作成
        test_file = self.input_dir / "test.mp3"
        test_file.touch()

        # モックでエラーを発生させる
        mock_audio_segment.from_mp3.side_effect = Exception("Test error")

        # 関数を実行
        result = combine_audio(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            ambient=None,
        )

        # アサーション
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
