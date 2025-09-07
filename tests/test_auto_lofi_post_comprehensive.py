import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
import tempfile
import os
import sys
import json
import argparse
import shutil

# テスト対象のモジュールをインポート
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from auto_post.auto_lofi_post import LofiPostGenerator


class TestLofiPostGeneratorComprehensive(unittest.TestCase):
    """LofiPostGeneratorクラスの包括的単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト環境変数を設定
        os.environ['TESTING'] = 'true'
        
        self.temp_dir = tempfile.mkdtemp()
        self.test_output_dir = Path(self.temp_dir) / "output"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # テスト用の引数を作成（実際のコードに合わせて修正）
        self.args = argparse.Namespace(
            output_dir=str(self.test_output_dir),
            jsonl_path="test_lofi_type.jsonl",
            skip_type_selection=False,
            skip_music_gen=False,
            skip_thumbnail_gen=False,
            skip_video_creation=False,
            skip_youtube_upload=False,
            skip_audio_combine=False,
            skip_upload=False,
            target_duration_sec=300,
            lofi_type=None,
            ambient_dir=None
        )
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)
    
    @patch('auto_post.auto_lofi_post.Config.validate_config')
    def test_find_latest_file_success(self, mock_validate_config):
        """最新ファイル検索成功時のテスト"""
        generator = LofiPostGenerator(self.args)
        
        # テスト用のファイルを作成
        test_file1 = self.test_output_dir / "test_20240101.txt"
        test_file2 = self.test_output_dir / "test_20240102.txt"
        test_file1.touch()
        test_file2.touch()
        
        with patch('builtins.print'):
            result = generator._find_latest_file("test_*.txt")
            
            # 最新のファイルが返されることを確認
            self.assertIsNotNone(result)
            self.assertEqual(result, test_file2)
    
    @patch('auto_post.auto_lofi_post.Config.validate_config')
    def test_find_latest_file_not_found(self, mock_validate_config):
        """最新ファイル検索でファイルが見つからない場合のテスト"""
        generator = LofiPostGenerator(self.args)
        
        with patch('builtins.print'):
            result = generator._find_latest_file("nonexistent_*.txt")
            
            # Noneが返されることを確認
            self.assertIsNone(result)
    
    @patch('auto_post.auto_lofi_post.Config.validate_config')
    def test_send_slack_notification_testing_mode(self, mock_validate_config):
        """テスト環境でのSlack通知テスト"""
        generator = LofiPostGenerator(self.args)
        
        with patch('builtins.print') as mock_print:
            generator.send_slack_notification("Test message")
            
            # テスト環境ではprintが呼ばれることを確認
            mock_print.assert_called_with("[TEST] Slack通知: Test message")
    
    @patch('auto_post.auto_lofi_post.Config.validate_config')
    def test_send_slack_notification_error_mode(self, mock_validate_config):
        """エラーモードでのSlack通知テスト"""
        generator = LofiPostGenerator(self.args)
        
        with patch('builtins.print') as mock_print:
            generator.send_slack_notification("Error message", is_error=True)
            
            # テスト環境ではprintが呼ばれることを確認
            mock_print.assert_called_with("[TEST] Slack通知: Error message")
    
    @patch('auto_post.auto_lofi_post.Config.validate_config')
    def test_extract_type_from_thumbnail_success(self, mock_validate_config):
        """サムネイルからタイプ抽出成功時のテスト"""
        generator = LofiPostGenerator(self.args)
        
        # テスト用のサムネイルファイルを作成
        thumbnail_file = self.test_output_dir / "sad_1280x720_20240101_thumb.png"
        thumbnail_file.touch()
        
        with patch.object(generator, '_find_latest_file', return_value=thumbnail_file):
            with patch('builtins.print'):
                result = generator._extract_type_from_thumbnail()
                
                self.assertEqual(result, "sad")
    
    @patch('auto_post.auto_lofi_post.Config.validate_config')
    def test_extract_type_from_thumbnail_not_found(self, mock_validate_config):
        """サムネイルが見つからない場合のテスト"""
        generator = LofiPostGenerator(self.args)
        
        with patch.object(generator, '_find_latest_file', return_value=None):
            with patch.object(generator, 'send_slack_notification') as mock_notify:
                with patch('builtins.print'):
                    with self.assertRaises(SystemExit):
                        generator._extract_type_from_thumbnail()
                    
                    mock_notify.assert_called_once()


if __name__ == '__main__':
    unittest.main()
