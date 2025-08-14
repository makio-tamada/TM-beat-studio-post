import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import json
from pydub import AudioSegment

# テスト対象のモジュールをインポート
import sys
from pathlib import Path as _Path
PROJECT_ROOT = _Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from auto_post.combine_audio import (
    get_audio_files,
    human_minutes,
    load_ambient,
    combine_tracks,
    main
)


class TestCombineAudio(unittest.TestCase):
    """combine_audioモジュールの単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_dir = Path(self.temp_dir) / "test_audio"
        self.test_audio_dir.mkdir()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)
    
    def test_get_audio_files_empty_directory(self):
        """空のディレクトリでの音声ファイル取得テスト"""
        files = get_audio_files(self.test_audio_dir)
        self.assertEqual(files, [])
    
    def test_get_audio_files_with_mp3_files(self):
        """MP3ファイルがある場合のテスト"""
        # テスト用のダミーファイルを作成
        test_files = ["track1.mp3", "track2.mp3", "combined_audio.mp3", "not_audio.txt"]
        for filename in test_files:
            (self.test_audio_dir / filename).touch()
        
        files = get_audio_files(self.test_audio_dir)
        expected_files = [
            self.test_audio_dir / "track1.mp3",
            self.test_audio_dir / "track2.mp3"
        ]
        
        self.assertEqual(len(files), 2)
        self.assertIn(expected_files[0], files)
        self.assertIn(expected_files[1], files)
    
    def test_human_minutes(self):
        """時間フォーマット関数のテスト"""
        test_cases = [
            (0, "0:00"),
            (30, "0:30"),
            (60, "1:00"),
            (90, "1:30"),
            (125, "2:05"),
            (3600, "60:00")
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = human_minutes(seconds)
                self.assertEqual(result, expected)
    
    @patch('auto_post.combine_audio.AudioSegment.from_file')
    def test_load_ambient_short_track(self, mock_from_file):
        """短い環境音トラックの読み込みテスト"""
        # モックの設定
        mock_audio = Mock(spec=AudioSegment)
        mock_audio.__len__ = Mock(return_value=5000)  # 5秒
        mock_audio.__sub__ = Mock(return_value=mock_audio)  # 音量調整
        mock_audio.__mul__ = Mock(return_value=mock_audio)  # ループ
        mock_audio.__getitem__ = Mock(return_value=mock_audio)  # スライス
        mock_from_file.return_value = mock_audio
        
        result = load_ambient(Path("test.mp3"), 15000)  # 15秒の目標長
        
        # 音量調整が適用されているかチェック
        mock_from_file.assert_called_once()
        mock_audio.__sub__.assert_called_once_with(10)
    
    @patch('auto_post.combine_audio.AudioSegment.from_file')
    def test_combine_tracks_empty_list(self, mock_from_file):
        """空のトラックリストでの結合テスト"""
        with self.assertRaises(ValueError):
            combine_tracks([])
    
    @patch('auto_post.combine_audio.AudioSegment.from_file')
    def test_combine_tracks_single_track(self, mock_from_file):
        """単一トラックの結合テスト"""
        # モックの設定
        mock_audio = Mock(spec=AudioSegment)
        mock_audio.__len__ = Mock(return_value=10000)  # 10秒
        mock_from_file.return_value = mock_audio
        
        test_track = self.test_audio_dir / "test.mp3"
        test_track.touch()
        
        combined, info = combine_tracks([test_track])
        
        self.assertEqual(len(info), 1)
        self.assertEqual(info[0]['title'], 'test')
        self.assertEqual(info[0]['start_time'], 0.0)
        self.assertEqual(info[0]['end_time'], 10.0)
    
    @patch('auto_post.combine_audio.AudioSegment.from_file')
    def test_combine_tracks_multiple_tracks(self, mock_from_file):
        """複数トラックの結合テスト"""
        # モックの設定
        mock_audio = Mock(spec=AudioSegment)
        mock_audio.__len__ = Mock(return_value=10000)  # 10秒
        mock_audio.fade_out = Mock(return_value=mock_audio)
        mock_audio.fade_in = Mock(return_value=mock_audio)
        mock_audio.overlay = Mock(return_value=mock_audio)
        mock_audio.__getitem__ = Mock(return_value=mock_audio)  # スライス
        mock_audio.__add__ = Mock(return_value=mock_audio)  # 結合
        mock_from_file.return_value = mock_audio
        
        # テストファイルを作成
        tracks = []
        for i in range(3):
            track = self.test_audio_dir / f"track{i}.mp3"
            track.touch()
            tracks.append(track)
        
        combined, info = combine_tracks(tracks, fade_ms=2000)
        
        self.assertEqual(len(info), 3)
        # 実際のコードでは、ファイル名の順序が異なる可能性があるため、
        # タイトルが存在することを確認
        titles = [track['title'] for track in info]
        self.assertIn('track0', titles)
        self.assertIn('track1', titles)
        self.assertIn('track2', titles)


if __name__ == '__main__':
    unittest.main()
