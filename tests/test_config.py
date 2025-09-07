import unittest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import tempfile
import os
import sys

# テスト対象のモジュールをインポート
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from auto_post.config import Config


class TestConfig(unittest.TestCase):
    """Configクラスの単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_config_attributes(self):
        """Configクラスの属性テスト"""
        # 基本的な属性が存在することを確認
        self.assertIsNotNone(Config.SLACK_WEBHOOK_URL)
        self.assertIsInstance(Config.STOCK_AUDIO_BASE_DIR, Path)
        self.assertIsInstance(Config.STOCK_IMAGE_BASE_DIR, Path)
        self.assertIsInstance(Config.JSONL_PATH, Path)
        self.assertIsInstance(Config.OPENING_VIDEO_PATH, Path)
        self.assertIsInstance(Config.AMBIENT_DIR, Path)
        self.assertIsInstance(Config.CLIENT_SECRETS_PATH, Path)
        self.assertIsInstance(Config.POST_DETAIL_PATH, Path)
        
        # 出力ファイル名設定
        self.assertIsInstance(Config.COMBINED_AUDIO_FILENAME, str)
        self.assertIsInstance(Config.TRACKS_INFO_FILENAME, str)
        self.assertIsInstance(Config.METADATA_FILENAME, str)
        self.assertIsInstance(Config.FINAL_VIDEO_FILENAME, str)
        self.assertIsInstance(Config.THUMBNAIL_PATTERN, str)
    
    @patch('auto_post.config.os.getenv')
    def test_config_with_custom_env_vars(self, mock_getenv):
        """カスタム環境変数でのConfigテスト"""
        # モックの設定
        mock_getenv.side_effect = lambda key, default=None: {
            'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test',
            'STOCK_AUDIO_BASE_DIR': '/custom/audio',
            'STOCK_IMAGE_BASE_DIR': '/custom/image',
            'JSONL_PATH': '/custom/lofi.jsonl',
            'OPENING_VIDEO_PATH': '/custom/opening.mov',
            'AMBIENT_DIR': '/custom/ambient',
            'CLIENT_SECRETS_PATH': '/custom/client_secrets.json',
            'POST_DETAIL_PATH': '/custom/post_detail.txt',
            'COMBINED_AUDIO_FILENAME': 'custom_audio.mp3',
            'TRACKS_INFO_FILENAME': 'custom_tracks.json',
            'METADATA_FILENAME': 'custom_metadata.json',
            'FINAL_VIDEO_FILENAME': 'custom_video.mp4',
            'THUMBNAIL_PATTERN': 'custom_thumb.png'
        }.get(key, default)
        
        # Configクラスを再読み込み
        import importlib
        import auto_post.config
        importlib.reload(auto_post.config)
        
        # アサーション
        self.assertEqual(auto_post.config.Config.SLACK_WEBHOOK_URL, 'https://hooks.slack.com/test')
        self.assertEqual(str(auto_post.config.Config.STOCK_AUDIO_BASE_DIR), '/custom/audio')
        self.assertEqual(str(auto_post.config.Config.STOCK_IMAGE_BASE_DIR), '/custom/image')
        self.assertEqual(str(auto_post.config.Config.JSONL_PATH), '/custom/lofi.jsonl')
        self.assertEqual(str(auto_post.config.Config.OPENING_VIDEO_PATH), '/custom/opening.mov')
        self.assertEqual(str(auto_post.config.Config.AMBIENT_DIR), '/custom/ambient')
        self.assertEqual(str(auto_post.config.Config.CLIENT_SECRETS_PATH), '/custom/client_secrets.json')
        self.assertEqual(str(auto_post.config.Config.POST_DETAIL_PATH), '/custom/post_detail.txt')
        self.assertEqual(auto_post.config.Config.COMBINED_AUDIO_FILENAME, 'custom_audio.mp3')
        self.assertEqual(auto_post.config.Config.TRACKS_INFO_FILENAME, 'custom_tracks.json')
        self.assertEqual(auto_post.config.Config.METADATA_FILENAME, 'custom_metadata.json')
        self.assertEqual(auto_post.config.Config.FINAL_VIDEO_FILENAME, 'custom_video.mp4')
        self.assertEqual(auto_post.config.Config.THUMBNAIL_PATTERN, 'custom_thumb.png')
    
    @patch('auto_post.config.os.getenv')
    def test_validate_config_success(self, mock_getenv):
        """設定検証成功時のテスト"""
        # モックの設定
        mock_getenv.return_value = 'test_value'
        
        # ファイルとディレクトリの存在をモック
        with patch.object(Path, 'exists', return_value=True):
            # 例外が発生しないことを確認
            Config.validate_config()
    
    @patch('auto_post.config.os.getenv')
    def test_validate_config_missing_required_vars(self, mock_getenv):
        """必須環境変数が不足している場合のテスト"""
        # モックの設定（SLACK_WEBHOOK_URLをNoneにする）
        def mock_getenv_side_effect(key, default=None):
            if key == 'SLACK_WEBHOOK_URL':
                return None
            return 'test_value'
        
        mock_getenv.side_effect = mock_getenv_side_effect
        
        # 例外が発生することを確認
        with self.assertRaises(ValueError) as context:
            Config.validate_config()
        
        self.assertIn('SLACK_WEBHOOK_URL', str(context.exception))
    
    @patch('auto_post.config.os.getenv')
    @patch('builtins.print')
    def test_validate_config_missing_directories(self, mock_print, mock_getenv):
        """ディレクトリが存在しない場合のテスト"""
        # モックの設定
        mock_getenv.return_value = 'test_value'
        
        # ディレクトリが存在しないことをモック
        with patch.object(Path, 'exists', return_value=False):
            Config.validate_config()
        
        # 警告メッセージが出力されることを確認
        self.assertEqual(mock_print.call_count, 7)  # 2つのディレクトリ + 5つのファイル
    
    @patch('auto_post.config.os.getenv')
    @patch('builtins.print')
    def test_validate_config_missing_files(self, mock_print, mock_getenv):
        """ファイルが存在しない場合のテスト"""
        # モックの設定
        mock_getenv.return_value = 'test_value'
        
        # ファイルが存在しないことをモック
        with patch.object(Path, 'exists', return_value=False):
            Config.validate_config()
        
        # 警告メッセージが出力されることを確認
        self.assertEqual(mock_print.call_count, 7)  # 2つのディレクトリ + 5つのファイル
    
    @patch('auto_post.config.os.getenv')
    @patch('builtins.print')
    def test_validate_config_all_missing(self, mock_print, mock_getenv):
        """全てのファイルとディレクトリが存在しない場合のテスト"""
        # モックの設定
        mock_getenv.return_value = 'test_value'
        
        # 全てのファイルとディレクトリが存在しないことをモック
        with patch.object(Path, 'exists', return_value=False):
            Config.validate_config()
        
        # 全ての警告メッセージが出力されることを確認
        self.assertEqual(mock_print.call_count, 7)  # 2つのディレクトリ + 5つのファイル
    
    def test_config_default_values(self):
        """デフォルト値のテスト"""
        # 環境変数が設定されていない場合のデフォルト値を確認
        def mock_getenv(key, default=None):
            return default
        
        with patch('auto_post.config.os.getenv', side_effect=mock_getenv):
            import importlib
            import auto_post.config
            importlib.reload(auto_post.config)
            
            # デフォルト値が正しく設定されていることを確認
            self.assertEqual(str(auto_post.config.Config.STOCK_AUDIO_BASE_DIR), '/tmp/music/lofi')
            self.assertEqual(str(auto_post.config.Config.STOCK_IMAGE_BASE_DIR), '/tmp/image')
            self.assertEqual(str(auto_post.config.Config.JSONL_PATH), 'src/auto_post/lofi_type_with_variations.jsonl')
            self.assertEqual(str(auto_post.config.Config.OPENING_VIDEO_PATH), 'src/auto_post/openning.mov')
            self.assertEqual(str(auto_post.config.Config.AMBIENT_DIR), 'data/ambient')
            self.assertEqual(str(auto_post.config.Config.CLIENT_SECRETS_PATH), 'src/auto_post/client_secrets.json')
            self.assertEqual(str(auto_post.config.Config.POST_DETAIL_PATH), 'src/auto_post/post_detail.txt')
            self.assertEqual(auto_post.config.Config.COMBINED_AUDIO_FILENAME, 'combined_audio.mp3')
            self.assertEqual(auto_post.config.Config.TRACKS_INFO_FILENAME, 'tracks_info.json')
            self.assertEqual(auto_post.config.Config.METADATA_FILENAME, 'metadata.json')
            self.assertEqual(auto_post.config.Config.FINAL_VIDEO_FILENAME, 'final_video.mp4')
            self.assertEqual(auto_post.config.Config.THUMBNAIL_PATTERN, '*thumb.png')


if __name__ == '__main__':
    unittest.main()
