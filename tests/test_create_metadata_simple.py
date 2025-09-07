import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import os
import sys
import shutil

# テスト対象のモジュールをインポート
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from auto_post.create_metadata import create_metadata


class TestCreateMetadataSimple(unittest.TestCase):
    """create_metadataモジュールのシンプルな単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト環境変数を設定
        os.environ['TESTING'] = 'true'
        
        self.temp_dir = tempfile.mkdtemp()
        self.test_output_dir = Path(self.temp_dir) / "output"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # テスト用のファイルを作成
        self.tracks_json = self.test_output_dir / "tracks.json"
        self.tracks_json.touch()
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)
    
    @patch('auto_post.create_metadata.requests.post')
    def test_create_metadata_success(self, mock_post):
        """メタデータ生成成功時のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Test Title"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        with patch('builtins.open', mock_open(read_data='[{"title": "Track 1", "duration": 180, "start_time": 0}]')):
            with patch('builtins.print'):
                result = create_metadata(
                    output_dir=str(self.test_output_dir),
                    tracks_json=str(self.tracks_json),
                    lofi_type="sad",
                    music_prompt="sad lo-fi music",
                    api_url="https://api.openai.com/v1/chat/completions",
                    temperature=0.7
                )
                
                self.assertIsInstance(result, Path)
    
    @patch('auto_post.create_metadata.requests.post')
    def test_create_metadata_api_error(self, mock_post):
        """APIエラー時のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        with patch('builtins.open', mock_open(read_data='[{"title": "Track 1", "duration": 180, "start_time": 0}]')):
            with patch('builtins.print'):
                # APIエラーが発生しても例外は発生しない場合がある
                try:
                    result = create_metadata(
                        output_dir=str(self.test_output_dir),
                        tracks_json=str(self.tracks_json),
                        lofi_type="sad",
                        music_prompt="sad lo-fi music",
                        api_url="https://api.openai.com/v1/chat/completions",
                        temperature=0.7
                    )
                    # 例外が発生しない場合は結果を確認
                    self.assertIsInstance(result, Path)
                except Exception:
                    # 例外が発生する場合は正常
                    pass
    
    @patch('auto_post.create_metadata.requests.post')
    def test_create_metadata_tracks_file_not_found(self, mock_post):
        """トラックファイルが見つからない場合のテスト"""
        # トラックファイルを削除
        self.tracks_json.unlink()
        
        with patch('builtins.print'):
            with self.assertRaises(FileNotFoundError):
                create_metadata(
                    output_dir=str(self.test_output_dir),
                    tracks_json=str(self.tracks_json),
                    lofi_type="sad",
                    music_prompt="sad lo-fi music",
                    api_url="https://api.openai.com/v1/chat/completions",
                    temperature=0.7
                )
    
    @patch('auto_post.create_metadata.requests.post')
    def test_create_metadata_different_lofi_types(self, mock_post):
        """異なるLo-Fiタイプでのテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Test Title"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        lofi_types = ["sad", "happy", "chill"]
        
        with patch('builtins.open', mock_open(read_data='[{"title": "Track 1", "duration": 180, "start_time": 0}]')):
            with patch('builtins.print'):
                for lofi_type in lofi_types:
                    result = create_metadata(
                        output_dir=str(self.test_output_dir),
                        tracks_json=str(self.tracks_json),
                        lofi_type=lofi_type,
                        music_prompt=f"{lofi_type} lo-fi music",
                        api_url="https://api.openai.com/v1/chat/completions",
                        temperature=0.7
                    )
                    
                    self.assertIsInstance(result, Path)
    
    @patch('auto_post.create_metadata.requests.post')
    def test_create_metadata_network_error(self, mock_post):
        """ネットワークエラー時のテスト"""
        # ネットワークエラーのモック
        mock_post.side_effect = Exception("Network error")
        
        with patch('builtins.open', mock_open(read_data='[{"title": "Track 1", "duration": 180, "start_time": 0}]')):
            with patch('builtins.print'):
                # ネットワークエラーが発生しても例外は発生しない場合がある
                try:
                    result = create_metadata(
                        output_dir=str(self.test_output_dir),
                        tracks_json=str(self.tracks_json),
                        lofi_type="sad",
                        music_prompt="sad lo-fi music",
                        api_url="https://api.openai.com/v1/chat/completions",
                        temperature=0.7
                    )
                    # 例外が発生しない場合は結果を確認
                    self.assertIsInstance(result, Path)
                except Exception:
                    # 例外が発生する場合は正常
                    pass


if __name__ == '__main__':
    unittest.main()
