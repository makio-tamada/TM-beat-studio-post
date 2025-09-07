import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import os
import sys
import numpy as np

# テスト対象のモジュールをインポート
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from auto_post.create_video import (
    WaveformClip,
    create_waveform_clip,
    build_video,
    create_video,
    main
)


class TestWaveformClip(unittest.TestCase):
    """WaveformClipクラスの単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_waveform_clip_initialization(self):
        """WaveformClipの初期化テスト"""
        # モック音声クリップ
        mock_audio_clip = Mock()
        mock_audio_clip.duration = 10.0
        mock_audio_clip.to_soundarray.return_value = np.random.rand(441000)  # 10秒分のサンプル
        
        # WaveformClipを作成
        waveform_clip = WaveformClip(mock_audio_clip, 1920, 1080, 24)
        
        # アサーション
        self.assertEqual(waveform_clip.duration, 10.0)
        self.assertEqual(waveform_clip.width, 1920)
        self.assertEqual(waveform_clip.height, 1080)
        self.assertEqual(waveform_clip.size, (1920, 1080))
        self.assertEqual(waveform_clip.bars, 30)
        self.assertEqual(waveform_clip.fps, 24)
    
    def test_waveform_clip_make_frame(self):
        """WaveformClipのmake_frameメソッドテスト"""
        # モック音声クリップ
        mock_audio_clip = Mock()
        mock_audio_clip.duration = 10.0
        mock_audio_clip.to_soundarray.return_value = np.random.rand(441000)
        
        # WaveformClipを作成
        waveform_clip = WaveformClip(mock_audio_clip, 1920, 1080, 24)
        
        # フレームを生成
        frame = waveform_clip.make_frame(5.0)  # 5秒目のフレーム
        
        # アサーション
        self.assertEqual(frame.shape, (1080, 1920, 4))  # RGBA
        self.assertEqual(frame.dtype, np.uint8)
    
    def test_waveform_clip_stereo_audio(self):
        """ステレオ音声の処理テスト"""
        # ステレオ音声のモック
        mock_audio_clip = Mock()
        mock_audio_clip.duration = 10.0
        mock_audio_clip.to_soundarray.return_value = np.random.rand(441000, 2)  # ステレオ
        
        # WaveformClipを作成
        waveform_clip = WaveformClip(mock_audio_clip, 1920, 1080, 24)
        
        # アサーション
        self.assertEqual(waveform_clip.samples.ndim, 1)  # モノラルに変換されている


class TestCreateWaveformClip(unittest.TestCase):
    """create_waveform_clip関数の単体テスト"""
    
    def test_create_waveform_clip(self):
        """create_waveform_clip関数のテスト"""
        # モック音声クリップ
        mock_audio_clip = Mock()
        mock_audio_clip.duration = 10.0
        mock_audio_clip.to_soundarray.return_value = np.random.rand(441000)
        
        # 関数を実行
        result = create_waveform_clip(mock_audio_clip, 1920, 1080, 24)
        
        # アサーション
        self.assertIsInstance(result, WaveformClip)
        self.assertEqual(result.fps, 24)


class TestBuildVideo(unittest.TestCase):
    """build_video関数の単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # テスト用ファイルを作成
        self.test_image = self.temp_path / "test_image.png"
        self.test_audio = self.temp_path / "test_audio.mp3"
        self.test_image.touch()
        self.test_audio.touch()
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('auto_post.config.Config')
    @patch('auto_post.create_video.AudioSegment')
    @patch('auto_post.create_video.AudioFileClip')
    @patch('auto_post.create_video.VideoFileClip')
    @patch('auto_post.create_video.ImageClip')
    @patch('auto_post.create_video.create_waveform_clip')
    @patch('auto_post.create_video.CompositeVideoClip')
    @patch('auto_post.create_video.concatenate_videoclips')
    @patch('auto_post.create_video.ColorClip')
    def test_build_video_success(self, mock_color_clip, mock_concat, mock_composite, 
                                mock_waveform, mock_image_clip, mock_video_clip, 
                                mock_audio_clip, mock_audio_segment, mock_config):
        """動画生成成功時のテスト"""
        # モックの設定
        mock_config.FINAL_VIDEO_FILENAME = "final_video.mp4"
        mock_config.OPENING_VIDEO_PATH = self.temp_path / "opening.mov"
        mock_config.OPENING_VIDEO_PATH.touch()
        
        # 音声関連のモック
        mock_audio_segment.from_file.return_value.export.return_value = None
        mock_audio = Mock()
        mock_audio.duration = 10.0
        mock_audio.subclip.return_value = mock_audio
        mock_audio_clip.return_value = mock_audio
        
        # 動画関連のモック
        mock_opening = Mock()
        mock_opening.duration = 3.0
        mock_opening.with_effects.return_value = mock_opening
        mock_video_clip.return_value = mock_opening
        
        mock_image = Mock()
        mock_image.with_effects.return_value.with_position.return_value.with_duration.return_value = mock_image
        mock_image_clip.return_value = mock_image
        
        mock_waveform_clip = Mock()
        mock_waveform_clip.with_position.return_value = mock_waveform_clip
        mock_waveform.return_value = mock_waveform_clip
        
        mock_composite_clip = Mock()
        mock_composite_clip.with_duration.return_value = mock_composite_clip
        mock_composite.return_value = mock_composite_clip
        
        mock_final = Mock()
        mock_final.duration = 13.0
        mock_final.with_audio.return_value = mock_final
        mock_final.write_videofile.return_value = None
        mock_concat.return_value = mock_final
        
        # 関数を実行
        result = build_video(self.test_image, self.test_audio, self.temp_path)
        
        # アサーション
        self.assertEqual(result, self.temp_path / "final_video.mp4")
        mock_audio_segment.from_file.assert_called_once()
        mock_audio_clip.assert_called_once()
        mock_video_clip.assert_called_once()
        mock_image_clip.assert_called_once()
        mock_waveform.assert_called_once()
        mock_composite.assert_called_once()
        mock_concat.assert_called_once()
        mock_final.write_videofile.assert_called_once()
    
    @patch('auto_post.config.Config')
    def test_build_video_audio_file_not_found(self, mock_config):
        """音声ファイルが見つからない場合のテスト"""
        # モックの設定
        mock_config.FINAL_VIDEO_FILENAME = "final_video.mp4"
        
        # 存在しない音声ファイル
        non_existent_audio = self.temp_path / "non_existent.mp3"
        
        # 関数を実行
        result = build_video(self.test_image, non_existent_audio, self.temp_path)
        
        # アサーション
        self.assertIsNone(result)
    
    @patch('auto_post.config.Config')
    @patch('auto_post.create_video.AudioSegment')
    @patch('auto_post.create_video.AudioFileClip')
    @patch('auto_post.create_video.VideoFileClip')
    @patch('auto_post.create_video.ImageClip')
    @patch('auto_post.create_video.create_waveform_clip')
    @patch('auto_post.create_video.CompositeVideoClip')
    @patch('auto_post.create_video.concatenate_videoclips')
    @patch('auto_post.create_video.ColorClip')
    def test_build_video_no_opening_video(self, mock_color_clip, mock_concat, mock_composite,
                                         mock_waveform, mock_image_clip, mock_video_clip,
                                         mock_audio_clip, mock_audio_segment, mock_config):
        """オープニング動画がない場合のテスト"""
        # モックの設定
        mock_config.FINAL_VIDEO_FILENAME = "final_video.mp4"
        mock_config.OPENING_VIDEO_PATH = self.temp_path / "non_existent.mov"
        
        # 音声関連のモック
        mock_audio_segment.from_file.return_value.export.return_value = None
        mock_audio = Mock()
        mock_audio.duration = 10.0
        mock_audio.subclip.return_value = mock_audio
        mock_audio_clip.return_value = mock_audio
        
        # 動画関連のモック
        mock_color = Mock()
        mock_color_clip.return_value = mock_color
        
        mock_image = Mock()
        mock_image.with_effects.return_value.with_position.return_value.with_duration.return_value = mock_image
        mock_image_clip.return_value = mock_image
        
        mock_waveform_clip = Mock()
        mock_waveform_clip.with_position.return_value = mock_waveform_clip
        mock_waveform.return_value = mock_waveform_clip
        
        mock_composite_clip = Mock()
        mock_composite_clip.with_duration.return_value = mock_composite_clip
        mock_composite.return_value = mock_composite_clip
        
        mock_final = Mock()
        mock_final.duration = 13.0
        mock_final.with_audio.return_value = mock_final
        mock_final.write_videofile.return_value = None
        mock_concat.return_value = mock_final
        
        # 関数を実行
        result = build_video(self.test_image, self.test_audio, self.temp_path)
        
        # アサーション
        self.assertEqual(result, self.temp_path / "final_video.mp4")
        mock_color_clip.assert_called_once_with((1920, 1080), color=(0, 0, 0), duration=3)
    
    @patch('auto_post.config.Config')
    @patch('auto_post.create_video.AudioSegment')
    @patch('auto_post.create_video.AudioFileClip')
    @patch('auto_post.create_video.VideoFileClip')
    @patch('auto_post.create_video.ImageClip')
    @patch('auto_post.create_video.create_waveform_clip')
    @patch('auto_post.create_video.CompositeVideoClip')
    @patch('auto_post.create_video.concatenate_videoclips')
    @patch('auto_post.create_video.ColorClip')
    def test_build_video_exception_handling(self, mock_color_clip, mock_concat, mock_composite,
                                           mock_waveform, mock_image_clip, mock_video_clip,
                                           mock_audio_clip, mock_audio_segment, mock_config):
        """例外処理のテスト"""
        # モックの設定
        mock_config.FINAL_VIDEO_FILENAME = "final_video.mp4"
        mock_config.OPENING_VIDEO_PATH = self.temp_path / "opening.mov"
        mock_config.OPENING_VIDEO_PATH.touch()
        
        # 音声関連のモック（例外を発生させる）
        mock_audio_segment.from_file.side_effect = Exception("Audio processing error")
        
        # 関数を実行
        result = build_video(self.test_image, self.test_audio, self.temp_path)
        
        # アサーション
        self.assertIsNone(result)


class TestCreateVideo(unittest.TestCase):
    """create_video関数の単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('auto_post.create_video.build_video')
    def test_create_video_success(self, mock_build_video):
        """create_video関数成功時のテスト"""
        # モックの設定
        expected_output = self.temp_path / "final_video.mp4"
        mock_build_video.return_value = expected_output
        
        # 関数を実行
        result = create_video(self.temp_path, "test_image.png", "test_audio.mp3")
        
        # アサーション
        self.assertEqual(result, str(expected_output))
        mock_build_video.assert_called_once()
    
    @patch('auto_post.create_video.build_video')
    def test_create_video_failure(self, mock_build_video):
        """create_video関数失敗時のテスト"""
        # モックの設定
        mock_build_video.return_value = None
        
        # 関数を実行
        result = create_video(self.temp_path, "test_image.png", "test_audio.mp3")
        
        # アサーション
        self.assertIsNone(result)
        mock_build_video.assert_called_once()


class TestMain(unittest.TestCase):
    """main関数の単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('auto_post.create_video.build_video')
    @patch('sys.argv', ['create_video.py', '--image', 'test.png', '--audio', 'test.mp3', '--output', 'output'])
    def test_main_success(self, mock_build_video):
        """main関数成功時のテスト"""
        # モックの設定
        expected_output = self.temp_path / "final_video.mp4"
        mock_build_video.return_value = expected_output
        
        # 関数を実行
        with patch('builtins.print'):
            main()
        
        # アサーション
        mock_build_video.assert_called_once()
    
    @patch('auto_post.create_video.build_video')
    @patch('sys.argv', ['create_video.py', '--image', 'test.png', '--audio', 'test.mp3'])
    def test_main_failure(self, mock_build_video):
        """main関数失敗時のテスト"""
        # モックの設定
        mock_build_video.return_value = None
        
        # 関数を実行
        with patch('builtins.print'):
            main()
        
        # アサーション
        mock_build_video.assert_called_once()


if __name__ == '__main__':
    unittest.main()
