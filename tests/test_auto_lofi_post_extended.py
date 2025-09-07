import argparse
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from auto_post.auto_lofi_post import LofiPostGenerator

# テスト対象のモジュールをインポート


class TestLofiPostGeneratorExtended(unittest.TestCase):
    """LofiPostGeneratorクラスの拡張単体テスト"""

    def setUp(self):
        """テスト前の準備"""
        # テスト環境変数を設定
        os.environ["TESTING"] = "true"

        self.temp_dir = tempfile.mkdtemp()
        self.test_output_dir = Path(self.temp_dir) / "output"

        # テスト用の引数を作成（実際のコードに合わせて修正）
        self.args = argparse.Namespace(
            output_dir=str(self.test_output_dir),
            jsonl_path="test_lofi_type.jsonl",
            skip_type_selection=False,
            skip_music_gen=False,
            skip_thumbnail_gen=False,
            skip_video_creation=False,
            skip_youtube_upload=False,
            target_duration_sec=300,
            lofi_type=None,
        )

    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    def test_init(self, mock_validate_config):
        """LofiPostGeneratorの初期化テスト"""
        generator = LofiPostGenerator(self.args)

        self.assertEqual(generator.args, self.args)
        self.assertEqual(generator.output_dir, self.test_output_dir)
        self.assertTrue(generator.success_music_gen)
        self.assertEqual(generator.selected_prompt, {})
        self.assertEqual(generator.selected_image_prompt, "")
        self.assertEqual(generator.newly_generated_files, [])
        mock_validate_config.assert_called_once()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    def test_setup(self, mock_validate_config):
        """setupメソッドのテスト"""
        generator = LofiPostGenerator(self.args)

        with patch("builtins.print"):
            generator.setup()

        # 出力ディレクトリが作成されることを確認
        self.assertTrue(self.test_output_dir.exists())

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_send_slack_notification_success(self, mock_post, mock_validate_config):
        """Slack通知成功時のテスト"""
        generator = LofiPostGenerator(self.args)

        # テスト環境でない場合のモック
        with patch.dict(os.environ, {"TESTING": "false"}):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            generator.send_slack_notification("Test message")

            mock_post.assert_called_once()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_send_slack_notification_error(self, mock_post, mock_validate_config):
        """Slack通知エラー時のテスト"""
        generator = LofiPostGenerator(self.args)

        # テスト環境でない場合のモック
        with patch.dict(os.environ, {"TESTING": "false"}):
            mock_post.side_effect = Exception("Network error")

            with patch("builtins.print"):
                generator.send_slack_notification("Test message", is_error=True)

            mock_post.assert_called_once()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    def test_send_slack_notification_testing_mode(self, mock_validate_config):
        """テスト環境でのSlack通知スキップテスト"""
        generator = LofiPostGenerator(self.args)

        with patch("builtins.print") as mock_print:
            generator.send_slack_notification("Test message")

            mock_print.assert_called_with("[TEST] Slack通知: Test message")

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.Config.THUMBNAIL_PATTERN")
    def test_extract_type_from_thumbnail_success(
        self, mock_pattern, mock_validate_config
    ):
        """サムネイルからタイプ抽出成功時のテスト"""
        generator = LofiPostGenerator(self.args)

        # テスト用のサムネイルファイルを作成
        thumbnail_file = self.test_output_dir / "sad_1280x720_20240101_thumb.png"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_file.touch()

        # _find_latest_fileのモック
        with patch.object(generator, "_find_latest_file", return_value=thumbnail_file):
            with patch("builtins.print"):
                result = generator._extract_type_from_thumbnail()

                self.assertEqual(result, "sad")

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    def test_extract_type_from_thumbnail_not_found(self, mock_validate_config):
        """サムネイルが見つからない場合のテスト"""
        generator = LofiPostGenerator(self.args)

        # _find_latest_fileがNoneを返すようにモック
        with patch.object(generator, "_find_latest_file", return_value=None):
            with patch.object(generator, "send_slack_notification") as mock_notify:
                with patch("builtins.print"):
                    with self.assertRaises(SystemExit):
                        generator._extract_type_from_thumbnail()

                    mock_notify.assert_called_once()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    def test_select_prompt_file_not_found(self, mock_validate_config):
        """JSONLファイルが見つからない場合のテスト"""
        generator = LofiPostGenerator(self.args)

        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch("builtins.print"):
                with self.assertRaises(SystemExit):
                    generator.select_prompt()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    def test_generate_music_skip(self, mock_validate_config):
        """音楽生成をスキップする場合のテスト"""
        self.args.skip_music_gen = True
        generator = LofiPostGenerator(self.args)

        with patch("builtins.print"):
            generator.generate_music()

            # スキップされた場合は何も実行されない
            pass

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    def test_find_latest_file(self, mock_validate_config):
        """最新ファイル検索のテスト"""
        generator = LofiPostGenerator(self.args)

        # テスト用のファイルを作成
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        file1 = self.test_output_dir / "test_20240101.txt"
        file2 = self.test_output_dir / "test_20240102.txt"
        file1.touch()
        file2.touch()

        # ファイルの更新時刻を設定
        import time

        time.sleep(0.1)  # ファイル2をより新しくする
        file2.touch()

        with patch("auto_post.auto_lofi_post.Config.THUMBNAIL_PATTERN", "test_*.txt"):
            result = generator._find_latest_file("test_*.txt")

            # 最新のファイルが返されることを確認
            self.assertEqual(result, file2)

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    def test_find_latest_file_not_found(self, mock_validate_config):
        """ファイルが見つからない場合のテスト"""
        generator = LofiPostGenerator(self.args)

        with patch(
            "auto_post.auto_lofi_post.Config.THUMBNAIL_PATTERN", "nonexistent_*.txt"
        ):
            result = generator._find_latest_file("nonexistent_*.txt")

            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
