import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
import tempfile
import os
import sys
import json
import requests

# テスト対象のモジュールをインポート
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from auto_post.piapi_music_generation import (
    get_existing_filenames,
    generate_unique_filename,
    choose_random_prompt,
    fetch_track_title,
    create_music_task,
    wait_for_task,
    extract_audio_url,
    download_audio,
    piapi_music_generation
)


class TestPiapiMusicGenerationExtended(unittest.TestCase):
    """piapi_music_generationモジュールの拡張単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # テスト用のJSONLファイルを作成
        self.test_jsonl_path = self.temp_path / "test_lofi_types.jsonl"
        test_data = [
            {"type": "sad", "music_prompt": "melancholic lo-fi beats", "thumbnail_title": "Sad Lo-Fi"},
            {"type": "happy", "music_prompt": "upbeat lo-fi vibes", "thumbnail_title": "Happy Lo-Fi"}
        ]
        with open(self.test_jsonl_path, 'w', encoding='utf-8') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_existing_filenames(self):
        """既存ファイル名取得のテスト"""
        # テスト用のファイルを作成
        test_files = ["track1.mp3", "track2.mp3", "other.txt"]
        for filename in test_files:
            (self.temp_path / filename).touch()
        
        result = get_existing_filenames(str(self.temp_path))
        
        expected = {"track1", "track2"}
        self.assertEqual(result, expected)
    
    def test_get_existing_filenames_empty_directory(self):
        """空のディレクトリでの既存ファイル名取得テスト"""
        result = get_existing_filenames(str(self.temp_path))
        self.assertEqual(result, set())
    
    @patch('auto_post.piapi_music_generation.get_existing_filenames')
    @patch('auto_post.piapi_music_generation.fetch_track_title')
    def test_generate_unique_filename_no_conflict(self, mock_fetch_title, mock_get_existing):
        """ファイル名生成（重複なし）のテスト"""
        mock_get_existing.return_value = set()
        mock_fetch_title.return_value = "Test Track"
        
        result = generate_unique_filename("Test Track", str(self.temp_path), "test prompt")
        
        self.assertEqual(result, "Test_Track.mp3")
    
    @patch('auto_post.piapi_music_generation.get_existing_filenames')
    @patch('auto_post.piapi_music_generation.fetch_track_title')
    def test_generate_unique_filename_with_conflict(self, mock_fetch_title, mock_get_existing):
        """ファイル名生成（重複あり）のテスト"""
        mock_get_existing.return_value = {"Test_Track"}
        mock_fetch_title.return_value = "New Track"
        
        result = generate_unique_filename("Test Track", str(self.temp_path), "test prompt")
        
        self.assertEqual(result, "New_Track.mp3")
    
    @patch('auto_post.piapi_music_generation.get_existing_filenames')
    @patch('auto_post.piapi_music_generation.fetch_track_title')
    def test_generate_unique_filename_fallback_to_counter(self, mock_fetch_title, mock_get_existing):
        """ファイル名生成（フォールバック）のテスト"""
        mock_get_existing.return_value = {"Test_Track", "New_Track"}
        mock_fetch_title.return_value = "Test Track"  # 既存と同じ
        
        result = generate_unique_filename("Test Track", str(self.temp_path), "test prompt")
        
        self.assertEqual(result, "Test_Track_1.mp3")
    
    @patch('auto_post.piapi_music_generation.LOFI_TYPES_JSONL')
    def test_choose_random_prompt(self, mock_jsonl_path):
        """ランダムプロンプト選択のテスト"""
        mock_jsonl_path.__str__ = Mock(return_value=str(self.test_jsonl_path))
        
        with patch('builtins.open', mock_open(read_data=json.dumps({"type": "sad", "music_prompt": "test"}) + '\n')):
            result = choose_random_prompt()
            
            self.assertIn('type', result)
            self.assertIn('music_prompt', result)
    
    @patch('auto_post.piapi_music_generation.OPENAI_API_KEY', 'test_key')
    @patch('auto_post.piapi_music_generation.requests.post')
    def test_fetch_track_title_success(self, mock_post):
        """タイトル取得成功時のテスト"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test Title"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = fetch_track_title("test prompt", str(self.temp_path))
        
        self.assertEqual(result, "Test Title")
        mock_post.assert_called_once()
    
    @patch('auto_post.piapi_music_generation.OPENAI_API_KEY', None)
    def test_fetch_track_title_no_api_key(self):
        """APIキーなしでのタイトル取得テスト"""
        result = fetch_track_title("test prompt")
        
        self.assertEqual(result, "Untitled")
    
    @patch('auto_post.piapi_music_generation.OPENAI_API_KEY', 'test_key')
    @patch('auto_post.piapi_music_generation.requests.post')
    def test_fetch_track_title_api_error(self, mock_post):
        """APIエラー時のタイトル取得テスト"""
        mock_post.side_effect = requests.RequestException("API Error")
        
        result = fetch_track_title("test prompt")
        
        self.assertEqual(result, "Untitled")
    
    @patch('auto_post.piapi_music_generation.requests.post')
    def test_create_music_task_success(self, mock_post):
        """音楽タスク作成成功時のテスト"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"task_id": "test_task_id"}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = create_music_task("test prompt")
        
        self.assertEqual(result, "test_task_id")
        mock_post.assert_called_once()
    
    @patch('auto_post.piapi_music_generation.requests.post')
    def test_create_music_task_no_task_id(self, mock_post):
        """タスクIDなしでの音楽タスク作成テスト"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status.return_value = None
        mock_response.text = "No task_id"
        mock_post.return_value = mock_response
        
        with self.assertRaises(RuntimeError):
            create_music_task("test prompt")
    
    @patch('auto_post.piapi_music_generation.requests.get')
    @patch('auto_post.piapi_music_generation.time.sleep')
    def test_wait_for_task_success(self, mock_sleep, mock_get):
        """タスク待機成功時のテスト"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"status": "completed", "output": {}}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = wait_for_task("test_task_id")
        
        self.assertEqual(result["status"], "completed")
        mock_get.assert_called_once()
    
    @patch('auto_post.piapi_music_generation.requests.get')
    @patch('auto_post.piapi_music_generation.time.sleep')
    def test_wait_for_task_failed(self, mock_sleep, mock_get):
        """タスク失敗時のテスト"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"status": "failed", "error": "Task failed"}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with self.assertRaises(RuntimeError):
            wait_for_task("test_task_id")
    
    @patch('auto_post.piapi_music_generation.requests.get')
    @patch('auto_post.piapi_music_generation.time.sleep')
    def test_wait_for_task_timeout(self, mock_sleep, mock_get):
        """タスクタイムアウト時のテスト"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"status": "processing"}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with self.assertRaises(TimeoutError):
            wait_for_task("test_task_id", timeout=1)  # 短いタイムアウト
    
    def test_extract_audio_url_audio_url(self):
        """audio_urlフィールドからのURL抽出テスト"""
        task_data = {"output": {"audio_url": "http://example.com/audio.mp3"}}
        
        result = extract_audio_url(task_data)
        
        self.assertEqual(result, "http://example.com/audio.mp3")
    
    def test_extract_audio_url_audio_urls(self):
        """audio_urlsフィールドからのURL抽出テスト"""
        task_data = {"output": {"audio_urls": ["http://example.com/audio.mp3"]}}
        
        result = extract_audio_url(task_data)
        
        self.assertEqual(result, "http://example.com/audio.mp3")
    
    def test_extract_audio_url_songs(self):
        """songsフィールドからのURL抽出テスト"""
        task_data = {"output": {"songs": [{"song_path": "http://example.com/audio.mp3"}]}}
        
        result = extract_audio_url(task_data)
        
        self.assertEqual(result, "http://example.com/audio.mp3")
    
    def test_extract_audio_url_not_found(self):
        """URLが見つからない場合のテスト"""
        task_data = {"output": {}}
        
        result = extract_audio_url(task_data)
        
        self.assertIsNone(result)
    
    @patch('auto_post.piapi_music_generation.requests.get')
    def test_download_audio_success(self, mock_get):
        """音声ダウンロード成功時のテスト"""
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'audio_data']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__enter__.return_value = mock_response
        
        test_file = self.temp_path / "test_audio.mp3"
        
        with patch('builtins.open', mock_open()) as mock_file:
            download_audio("http://example.com/audio.mp3", str(test_file))
            
            mock_get.assert_called_once()
            mock_file.assert_called_once()
    
    @patch('auto_post.piapi_music_generation.API_KEY', 'YOUR_API_KEY_HERE')
    def test_piapi_music_generation_no_api_key(self):
        """APIキーなしでの音楽生成テスト"""
        with self.assertRaises(SystemExit):
            piapi_music_generation(str(self.temp_path), "test prompt", 60)


if __name__ == '__main__':
    unittest.main()
