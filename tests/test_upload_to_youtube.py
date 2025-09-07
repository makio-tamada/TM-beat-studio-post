import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import shutil
import json
import os

# テスト対象のモジュールをインポート
import sys
from pathlib import Path as _Path
PROJECT_ROOT = _Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from auto_post.upload_to_youtube import (
    get_authenticated_service,
    upload_video_to_youtube,
    main
)


class TestUploadToYoutube(unittest.TestCase):
    """upload_to_youtubeモジュールの単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_video_path = Path(self.temp_dir) / "test_video.mp4"
        self.test_video_path.touch()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)
    
    @patch('auto_post.upload_to_youtube.os.getenv')
    def test_get_authenticated_service_missing_env_vars(self, mock_getenv):
        """環境変数が不足している場合のテスト"""
        # 必要な環境変数を設定しない
        mock_getenv.return_value = None
        
        with self.assertRaises(Exception) as context:
            get_authenticated_service()
        
        self.assertIn("必要な環境変数が設定されていません", str(context.exception))
    
    @patch('auto_post.upload_to_youtube.os.getenv')
    @patch('auto_post.upload_to_youtube.Credentials')
    @patch('auto_post.upload_to_youtube.build')
    def test_get_authenticated_service_with_refresh_token(self, mock_build, mock_credentials, mock_getenv):
        """リフレッシュトークンでの認証テスト"""
        # 環境変数を設定
        mock_getenv.side_effect = lambda key: {
            'GOOGLE_REFRESH_TOKEN': 'test_refresh_token',
            'GOOGLE_CLIENT_ID': 'test_client_id',
            'GOOGLE_CLIENT_SECRET': 'test_client_secret'
        }.get(key)
        
        # モックの設定
        mock_cred_instance = Mock()
        mock_credentials.return_value = mock_cred_instance
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        result = get_authenticated_service()
        
        self.assertEqual(result, mock_service)
        mock_credentials.assert_called_once()
        mock_build.assert_called_once_with('youtube', 'v3', credentials=mock_cred_instance)
    
    @patch('auto_post.upload_to_youtube.os.getenv')
    @patch('auto_post.upload_to_youtube.Credentials')
    @patch('auto_post.upload_to_youtube.InstalledAppFlow')
    @patch('auto_post.upload_to_youtube.build')
    @patch('auto_post.config.Config')
    def test_get_authenticated_service_new_auth(self, mock_config, mock_build, mock_flow, mock_credentials, mock_getenv):
        """新規認証のテスト"""
        # リフレッシュトークン認証を失敗させる
        mock_getenv.side_effect = lambda key: {
            'GOOGLE_REFRESH_TOKEN': 'test_refresh_token',
            'GOOGLE_CLIENT_ID': 'test_client_id',
            'GOOGLE_CLIENT_SECRET': 'test_client_secret'
        }.get(key)
        
        # リフレッシュトークン認証で例外を発生させる
        mock_credentials.side_effect = Exception("Auth failed")
        
        # Configのモック
        mock_config.CLIENT_SECRETS_PATH.exists.return_value = True
        
        # 新規認証のモック
        mock_flow_instance = Mock()
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance
        mock_flow_instance.run_local_server.return_value = Mock(refresh_token="new_refresh_token")
        
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = get_authenticated_service()
        
        self.assertEqual(result, mock_service)
        mock_flow.from_client_secrets_file.assert_called_once()
        mock_flow_instance.run_local_server.assert_called_once()
    
    @patch('auto_post.upload_to_youtube.get_authenticated_service')
    @patch('auto_post.upload_to_youtube.MediaFileUpload')
    @patch('auto_post.upload_to_youtube.upload_video')
    @patch('auto_post.config.Config')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_video_to_youtube_success(self, mock_file, mock_config, mock_upload_video, mock_media_upload, mock_get_service):
        """動画アップロード成功時のテスト"""
        # モックの設定
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_media = Mock()
        mock_media_upload.return_value = mock_media
        
        # upload_videoのモック
        mock_upload_video.return_value = "test_video_id"
        
        # Configのモック
        mock_post_detail_path = Mock()
        mock_post_detail_path.read_text.return_value = "Test post detail content"
        mock_config.POST_DETAIL_PATH = mock_post_detail_path
        
        # メタデータファイルのモック
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps({
            "title": "Test Video",
            "description": "Test Description",
            "tracklist": "Test Tracklist"
        })
        
        result = upload_video_to_youtube(
            video_path=self.test_video_path,
            thumbnail_path=self.test_video_path,  # テスト用に同じファイルを使用
            metadata_path=self.test_video_path,   # テスト用に同じファイルを使用
            privacy="private",
            tags=None
        )
        
        self.assertEqual(result, "test_video_id")
        mock_upload_video.assert_called_once()
    
    @patch('auto_post.upload_to_youtube.get_authenticated_service')
    def test_upload_video_to_youtube_service_failure(self, mock_get_service):
        """YouTubeサービス取得失敗時のテスト"""
        mock_get_service.side_effect = Exception("Service creation failed")
        
        with self.assertRaises(Exception):
            upload_video_to_youtube(
                video_path=self.test_video_path,
                thumbnail_path=self.test_video_path,
                metadata_path=self.test_video_path,
                privacy="private",
                tags=None
            )
    
    @patch('auto_post.upload_to_youtube.get_authenticated_service')
    @patch('auto_post.upload_to_youtube.MediaFileUpload')
    @patch('auto_post.upload_to_youtube.upload_video')
    @patch('auto_post.config.Config')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_video_to_youtube_upload_failure(self, mock_file, mock_config, mock_upload_video, mock_media_upload, mock_get_service):
        """動画アップロード失敗時のテスト"""
        # モックの設定
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_media = Mock()
        mock_media_upload.return_value = mock_media
        
        # upload_videoのモック（失敗）
        mock_upload_video.return_value = None
        
        # Configのモック
        mock_post_detail_path = Mock()
        mock_post_detail_path.read_text.return_value = "Test post detail content"
        mock_config.POST_DETAIL_PATH = mock_post_detail_path
        
        # メタデータファイルのモック
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps({
            "title": "Test Video",
            "description": "Test Description",
            "tracklist": "Test Tracklist"
        })
        
        with self.assertRaises(Exception):
            upload_video_to_youtube(
                video_path=self.test_video_path,
                thumbnail_path=self.test_video_path,
                metadata_path=self.test_video_path,
                privacy="private",
                tags=None
            )
    
    def test_upload_video_to_youtube_file_not_exists(self):
        """存在しないファイルでのアップロードテスト"""
        non_existent_path = self.test_video_path.parent / "non_existent.mp4"
        
        # メタデータファイルも存在しないため、FileNotFoundErrorが発生する
        with self.assertRaises(FileNotFoundError):
            upload_video_to_youtube(
                video_path=non_existent_path,
                thumbnail_path=self.test_video_path,
                metadata_path=non_existent_path,  # 存在しないメタデータファイル
                privacy="private",
                tags=None
            )


if __name__ == '__main__':
    unittest.main()
