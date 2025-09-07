import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from auto_post.get_refresh_token import SCOPES, get_refresh_token

# テスト対象のモジュールをインポート


class TestGetRefreshToken(unittest.TestCase):
    """get_refresh_tokenモジュールの単体テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_scopes_definition(self):
        """SCOPESの定義をテスト"""
        expected_scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
        ]
        self.assertEqual(SCOPES, expected_scopes)

    @patch("auto_post.config.Config")
    @patch("auto_post.get_refresh_token.InstalledAppFlow")
    @patch("builtins.open", new_callable=mock_open)
    @patch("auto_post.get_refresh_token.Path")
    def test_get_refresh_token_success(
        self, mock_path, mock_file, mock_flow_class, mock_config
    ):
        """リフレッシュトークン取得成功時のテスト"""
        # モックの設定
        mock_client_secrets_path = Mock()
        mock_client_secrets_path.exists.return_value = True
        mock_config.CLIENT_SECRETS_PATH = mock_client_secrets_path

        # 認証情報のモック
        mock_credentials = Mock()
        mock_credentials.token = "test_access_token"
        mock_credentials.refresh_token = "test_refresh_token"
        mock_credentials.expiry = "2024-12-31T23:59:59Z"
        mock_credentials.scopes = SCOPES
        mock_credentials.client_id = "test_client_id"
        mock_credentials.client_secret = "test_client_secret"

        # フローのモック
        mock_flow = Mock()
        mock_flow.run_local_server.return_value = mock_credentials
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        # Pathのモック
        mock_env_path = Mock()
        mock_env_path.__truediv__ = Mock(return_value=mock_env_path)
        mock_path.return_value = mock_env_path
        mock_path.parent = mock_env_path
        # Path(__file__)のモック
        mock_path_instance = Mock()
        mock_path_instance.parent = mock_env_path
        mock_path.return_value = mock_path_instance

        # 関数を実行
        get_refresh_token()

        # アサーション
        mock_flow_class.from_client_secrets_file.assert_called_once_with(
            mock_client_secrets_path, scopes=SCOPES
        )
        mock_flow.run_local_server.assert_called_once_with(port=0)
        # openは.envファイルの書き込みで1回呼ばれる（読み込みはload_dotenvで行われる）
        self.assertEqual(mock_file.call_count, 1)

    @patch("auto_post.config.Config")
    @patch("builtins.print")
    def test_get_refresh_token_client_secrets_not_found(self, mock_print, mock_config):
        """クライアントシークレットファイルが見つからない場合のテスト"""
        # モックの設定
        mock_client_secrets_path = Mock()
        mock_client_secrets_path.exists.return_value = False
        mock_config.CLIENT_SECRETS_PATH = mock_client_secrets_path

        # 関数を実行
        get_refresh_token()

        # アサーション
        mock_print.assert_any_call(
            f"エラー: {mock_client_secrets_path} が見つかりません"
        )
        mock_print.assert_any_call(
            "Google Cloud Consoleからclient_secrets.jsonをダウンロードして、このディレクトリに配置してください"
        )

    @patch("auto_post.config.Config")
    @patch("auto_post.get_refresh_token.InstalledAppFlow")
    @patch("builtins.open", new_callable=mock_open)
    @patch("auto_post.get_refresh_token.Path")
    def test_get_refresh_token_flow_exception(
        self, mock_path, mock_file, mock_flow_class, mock_config
    ):
        """認証フローで例外が発生した場合のテスト"""
        # モックの設定
        mock_client_secrets_path = Mock()
        mock_client_secrets_path.exists.return_value = True
        mock_config.CLIENT_SECRETS_PATH = mock_client_secrets_path

        # フローのモック（例外を発生させる）
        mock_flow = Mock()
        mock_flow.run_local_server.side_effect = Exception("Authentication failed")
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        # Pathのモック
        mock_env_path = Mock()
        mock_env_path.__truediv__ = Mock(return_value=mock_env_path)
        mock_path.return_value = mock_env_path

        # 関数を実行（例外が発生しても処理が続行されることを確認）
        try:
            get_refresh_token()
        except Exception:
            pass  # 例外は期待される動作

        # アサーション
        mock_flow_class.from_client_secrets_file.assert_called_once_with(
            mock_client_secrets_path, scopes=SCOPES
        )
        mock_flow.run_local_server.assert_called_once_with(port=0)

    @patch("auto_post.config.Config")
    @patch("auto_post.get_refresh_token.InstalledAppFlow")
    @patch("builtins.open", new_callable=mock_open)
    @patch("auto_post.get_refresh_token.Path")
    def test_get_refresh_token_file_write_exception(
        self, mock_path, mock_file, mock_flow_class, mock_config
    ):
        """ファイル書き込みで例外が発生した場合のテスト"""
        # モックの設定
        mock_client_secrets_path = Mock()
        mock_client_secrets_path.exists.return_value = True
        mock_config.CLIENT_SECRETS_PATH = mock_client_secrets_path

        # 認証情報のモック
        mock_credentials = Mock()
        mock_credentials.token = "test_access_token"
        mock_credentials.refresh_token = "test_refresh_token"
        mock_credentials.expiry = "2024-12-31T23:59:59Z"
        mock_credentials.scopes = SCOPES
        mock_credentials.client_id = "test_client_id"
        mock_credentials.client_secret = "test_client_secret"

        # フローのモック
        mock_flow = Mock()
        mock_flow.run_local_server.return_value = mock_credentials
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        # ファイル書き込みで例外を発生させる
        mock_file.side_effect = IOError("Permission denied")

        # Pathのモック
        mock_env_path = Mock()
        mock_env_path.__truediv__ = Mock(return_value=mock_env_path)
        mock_path.return_value = mock_env_path

        # 関数を実行（例外が発生しても処理が続行されることを確認）
        try:
            get_refresh_token()
        except Exception:
            pass  # 例外は期待される動作

        # アサーション
        mock_flow_class.from_client_secrets_file.assert_called_once_with(
            mock_client_secrets_path, scopes=SCOPES
        )
        mock_flow.run_local_server.assert_called_once_with(port=0)


if __name__ == "__main__":
    unittest.main()
