import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import sys
from pathlib import Path

# テスト環境を設定
os.environ['TESTING'] = 'true'

from auto_post.piapi_music_generation import (
    extract_audio_url, 
    download_audio, 
    main, 
    piapi_music_generation,
    fetch_track_title
)


class TestPiapiMusicGenerationAdditional(unittest.TestCase):
    """piapi_music_generation.pyの追加テスト"""
    
    def setUp(self):
        """テストのセットアップ"""
        self.test_folder = "/tmp/test_piapi"
        self.test_audio_url = "https://example.com/test_audio.mp3"
        self.test_save_path = "/tmp/test_audio.mp3"
        
        # テスト用のディレクトリを作成
        Path(self.test_folder).mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """テストのクリーンアップ"""
        import shutil
        if Path(self.test_folder).exists():
            shutil.rmtree(self.test_folder)
        if Path(self.test_save_path).exists():
            Path(self.test_save_path).unlink()
    
    def test_extract_audio_url_audio_url(self):
        """extract_audio_url - audio_urlフィールドのテスト"""
        task_data = {"output": {"audio_url": self.test_audio_url}}
        result = extract_audio_url(task_data)
        self.assertEqual(result, self.test_audio_url)
    
    def test_extract_audio_url_audio_urls(self):
        """extract_audio_url - audio_urlsフィールドのテスト"""
        task_data = {"output": {"audio_urls": [self.test_audio_url, "https://example.com/other.mp3"]}}
        result = extract_audio_url(task_data)
        self.assertEqual(result, self.test_audio_url)
    
    def test_extract_audio_url_files(self):
        """extract_audio_url - filesフィールドのテスト"""
        task_data = {
            "output": {
                "files": [
                    {"url": self.test_audio_url},
                    {"url": "https://example.com/other.mp3"}
                ]
            }
        }
        result = extract_audio_url(task_data)
        self.assertEqual(result, self.test_audio_url)
    
    def test_extract_audio_url_songs(self):
        """extract_audio_url - songsフィールドのテスト"""
        task_data = {
            "output": {
                "songs": [
                    {"song_path": self.test_audio_url},
                    {"song_path": "https://example.com/other.mp3"}
                ]
            }
        }
        result = extract_audio_url(task_data)
        self.assertEqual(result, self.test_audio_url)
    
    def test_extract_audio_url_not_found(self):
        """extract_audio_url - 該当するURLが見つからない場合のテスト"""
        task_data = {"output": {"other_field": "value"}}
        result = extract_audio_url(task_data)
        self.assertIsNone(result)
    
    def test_extract_audio_url_empty_songs(self):
        """extract_audio_url - 空のsongsリストのテスト"""
        task_data = {"output": {"songs": []}}
        result = extract_audio_url(task_data)
        self.assertIsNone(result)
    
    def test_extract_audio_url_empty_audio_urls(self):
        """extract_audio_url - 空のaudio_urlsリストのテスト"""
        task_data = {"output": {"audio_urls": []}}
        result = extract_audio_url(task_data)
        self.assertIsNone(result)
    
    @patch('auto_post.piapi_music_generation.requests.get')
    def test_download_audio_success(self, mock_get):
        """download_audio - 成功時のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b'audio_data_chunk1', b'audio_data_chunk2']
        mock_get.return_value.__enter__.return_value = mock_response
        
        with patch('builtins.open', mock_open()) as mock_file:
            download_audio(self.test_audio_url, self.test_save_path)
        
        mock_get.assert_called_once_with(self.test_audio_url, stream=True, timeout=120)
        mock_file.assert_called_once_with(self.test_save_path, "wb")
    
    @patch('auto_post.piapi_music_generation.requests.get')
    def test_download_audio_failure(self, mock_get):
        """download_audio - 失敗時のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Download failed")
        mock_get.return_value.__enter__.return_value = mock_response
        
        with self.assertRaises(Exception):
            download_audio(self.test_audio_url, self.test_save_path)
    
    @patch('auto_post.piapi_music_generation.API_KEY', 'YOUR_API_KEY_HERE')
    def test_main_no_api_key(self):
        """main - APIキーが設定されていない場合のテスト"""
        with self.assertRaises(SystemExit):
            main()
    
    @patch('auto_post.piapi_music_generation.API_KEY', 'test_api_key')
    @patch('auto_post.piapi_music_generation.choose_random_prompt')
    @patch('auto_post.piapi_music_generation.create_music_task')
    @patch('auto_post.piapi_music_generation.wait_for_task')
    @patch('auto_post.piapi_music_generation.extract_audio_url')
    @patch('auto_post.piapi_music_generation.fetch_track_title')
    @patch('auto_post.piapi_music_generation.generate_unique_filename')
    @patch('auto_post.piapi_music_generation.download_audio')
    @patch('os.makedirs')
    def test_main_success(self, mock_makedirs, mock_download, mock_filename, 
                         mock_title, mock_extract, mock_wait, mock_create, mock_prompt):
        """main - 成功時のテスト"""
        # モックの設定
        mock_prompt.return_value = {"music_prompt": "test prompt"}
        mock_create.return_value = "task_123"
        mock_wait.return_value = {"output": {"songs": [{"duration": 120}]}}
        mock_extract.return_value = self.test_audio_url
        mock_title.return_value = "Test Track"
        mock_filename.return_value = "test_track.mp3"
        
        # main関数を実行
        main()
        
        # 各関数が呼ばれたことを確認
        mock_prompt.assert_called_once()
        mock_create.assert_called()  # ループで複数回呼ばれる
        mock_wait.assert_called()    # ループで複数回呼ばれる
        mock_extract.assert_called() # ループで複数回呼ばれる
        mock_title.assert_called()   # ループで複数回呼ばれる
        mock_filename.assert_called() # ループで複数回呼ばれる
        mock_download.assert_called() # ループで複数回呼ばれる
    
    @patch('auto_post.piapi_music_generation.API_KEY', 'test_api_key')
    @patch('auto_post.piapi_music_generation.choose_random_prompt')
    @patch('auto_post.piapi_music_generation.create_music_task')
    @patch('auto_post.piapi_music_generation.wait_for_task')
    @patch('auto_post.piapi_music_generation.extract_audio_url')
    @patch('auto_post.piapi_music_generation.fetch_track_title')
    @patch('auto_post.piapi_music_generation.generate_unique_filename')
    @patch('auto_post.piapi_music_generation.download_audio')
    @patch('os.makedirs')
    def test_piapi_music_generation_success(self, mock_makedirs, mock_download, mock_filename, 
                                          mock_title, mock_extract, mock_wait, mock_create, mock_prompt):
        """piapi_music_generation - 成功時のテスト"""
        # モックの設定
        mock_prompt.return_value = {"music_prompt": "test prompt"}
        mock_create.return_value = "task_123"
        mock_wait.return_value = {"output": {"songs": [{"duration": 120}]}}
        mock_extract.return_value = self.test_audio_url
        mock_title.return_value = "Test Track"
        mock_filename.return_value = "test_track.mp3"
        
        # piapi_music_generation関数を実行
        piapi_music_generation(self.test_folder, "test prompt", 120)
        
        # 各関数が呼ばれたことを確認
        mock_create.assert_called_once()
        mock_wait.assert_called_once()
        mock_extract.assert_called_once()
        mock_title.assert_called_once()
        mock_filename.assert_called_once()
        mock_download.assert_called_once()
    
    @patch('auto_post.piapi_music_generation.API_KEY', 'YOUR_API_KEY_HERE')
    def test_piapi_music_generation_no_api_key(self):
        """piapi_music_generation - APIキーが設定されていない場合のテスト"""
        with self.assertRaises(SystemExit):
            piapi_music_generation(self.test_folder, "test prompt", 120)
    
    @patch('auto_post.piapi_music_generation.requests.post')
    def test_fetch_track_title_success(self, mock_post):
        """fetch_track_title - 成功時のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated Track Title"}}]
        }
        mock_post.return_value = mock_response
        
        result = fetch_track_title("test prompt", self.test_folder)
        
        self.assertEqual(result, "Generated Track Title")
        mock_post.assert_called_once()
    
    @patch('auto_post.piapi_music_generation.requests.post')
    def test_fetch_track_title_failure(self, mock_post):
        """fetch_track_title - 失敗時のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        result = fetch_track_title("test prompt", self.test_folder)
        
        self.assertEqual(result, "Untitled")
        mock_post.assert_called_once()
    
    @patch('auto_post.piapi_music_generation.requests.post')
    def test_fetch_track_title_no_api_key(self, mock_post):
        """fetch_track_title - APIキーがない場合のテスト"""
        # モックの設定
        mock_post.side_effect = Exception("API key not found")
        
        result = fetch_track_title("test prompt", self.test_folder)
        
        self.assertEqual(result, "Untitled")
        mock_post.assert_called_once()


if __name__ == '__main__':
    unittest.main()
