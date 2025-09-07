import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from auto_post.create_video import (
    build_video,
    create_video,
    create_waveform_clip,
)


class TestCreateVideo(unittest.TestCase):
    """create_videoモジュールの単体テスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.image_path = self.test_dir / "test_image.png"
        self.audio_path = self.test_dir / "test_audio.mp3"
        self.output_path = self.test_dir / "output.mp4"

    def tearDown(self):
        """テストのクリーンアップ"""
        import shutil

        shutil.rmtree(self.test_dir)

    @patch("auto_post.create_video.ImageClip")
    @patch("auto_post.create_video.AudioFileClip")
    def test_create_video_basic(self, mock_audio_clip, mock_image_clip):
        """基本的な動画作成テスト"""
        # モックの設定
        mock_image = Mock()
        mock_audio = Mock()
        mock_image_clip.return_value = mock_image
        mock_audio_clip.return_value = mock_audio
        mock_image.duration = 10.0
        mock_audio.duration = 10.0

        # 関数を実行
        result = create_video(
            output_dir=self.test_dir,
            still_path=self.image_path,
            audio_path=self.audio_path,
        )

        # アサーション
        self.assertIsNotNone(result)
        mock_image_clip.assert_called_once_with(str(self.image_path))
        mock_audio_clip.assert_called_once_with(str(self.audio_path))

    @patch("auto_post.create_video.ImageClip")
    @patch("auto_post.create_video.AudioFileClip")
    def test_create_video_different_durations(self, mock_audio_clip, mock_image_clip):
        """異なる長さの動画作成テスト"""
        # モックの設定
        mock_image = Mock()
        mock_audio = Mock()
        mock_image_clip.return_value = mock_image
        mock_audio_clip.return_value = mock_audio
        mock_image.duration = 5.0
        mock_audio.duration = 10.0

        # 関数を実行
        result = create_video(
            output_dir=self.test_dir,
            still_path=self.image_path,
            audio_path=self.audio_path,
        )

        # アサーション
        self.assertIsNotNone(result)

    @patch("auto_post.create_video.ImageClip")
    @patch("auto_post.create_video.AudioFileClip")
    def test_create_video_error_handling(self, mock_audio_clip, mock_image_clip):
        """エラーハンドリングのテスト"""
        # モックでエラーを発生させる
        mock_image_clip.side_effect = Exception("Test error")

        # 関数を実行
        result = create_video(
            output_dir=self.test_dir,
            still_path=self.image_path,
            audio_path=self.audio_path,
        )

        # アサーション
        self.assertIsNone(result)

    def test_waveform_clip_creation(self):
        """波形クリップ作成のテスト"""
        # テスト用の音声データ
        audio_data = np.random.randn(1000)

        # 関数を実行
        clip = create_waveform_clip(audio_data, duration=10.0)

        # アサーション
        self.assertIsNotNone(clip)

    def test_build_video(self):
        """動画ビルドのテスト"""
        # モックの設定
        mock_clip = Mock()
        mock_clip.write_videofile.return_value = None

        # 関数を実行
        result = build_video(mock_clip, self.output_path)

        # アサーション
        self.assertIsNotNone(result)
        mock_clip.write_videofile.assert_called_once()


if __name__ == "__main__":
    unittest.main()
