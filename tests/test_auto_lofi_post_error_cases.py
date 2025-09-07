import argparse
import json
import os
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from auto_post.auto_lofi_post import LofiPostGenerator

# テスト環境を設定
os.environ["TESTING"] = "true"


class TestAutoLofiPostErrorCases(unittest.TestCase):
    """auto_lofi_post.pyのエラーケースとエッジケースをテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_output_dir = Path("/tmp/test_output")
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

        # テスト用のargsを作成
        self.args = argparse.Namespace(
            output_dir=str(self.test_output_dir),
            jsonl_path=None,
            lofi_type=None,
            skip_type_selection=False,
            target_duration_sec=720,
            ambient_dir=None,
            skip_music_gen=False,
            skip_audio_combine=False,
            skip_thumbnail_gen=False,
            temperature=0.7,
            skip_metadata_gen=False,
            skip_video_gen=False,
            privacy="private",
            tags="lofi,music",
            skip_upload=False,
        )

        # テスト用のJSONLデータ
        self.test_jsonl_data = [
            {
                "type": "ambient",
                "music_prompt": "ambient music",
                "thumbnail_title": "Ambient Title",
                "image_prompts": ["ambient image"],
            },
            {
                "type": "jazz",
                "music_prompt": "jazz music",
                "thumbnail_title": "Jazz Title",
                "image_prompts": ["jazz image"],
            },
        ]

    def tearDown(self):
        """テストのクリーンアップ"""
        import shutil

        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir)

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_select_prompt_type_not_found_error(self, mock_requests, mock_validate):
        """指定されたタイプが見つからない場合のエラーハンドリング"""
        mock_requests.return_value.status_code = 200

        # 存在しないタイプを指定
        self.args.lofi_type = "nonexistent_type"

        generator = LofiPostGenerator(self.args)

        # JSONLファイルのモック
        jsonl_content = "\n".join([json.dumps(item) for item in self.test_jsonl_data])

        with patch("builtins.open", mock_open(read_data=jsonl_content)):
            with self.assertRaises(ValueError):
                generator._select_specific_prompt()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_select_prompt_extracted_type_not_found(self, mock_requests, mock_validate):
        """抽出したタイプに対応するプロンプトが見つからない場合のエラーハンドリング"""
        mock_requests.return_value.status_code = 200

        generator = LofiPostGenerator(self.args)

        # 抽出されたタイプが存在しない場合のテスト
        with patch.object(
            generator, "_extract_type_from_thumbnail", return_value="nonexistent_type"
        ):
            jsonl_content = "\n".join(
                [json.dumps(item) for item in self.test_jsonl_data]
            )

            with patch("builtins.open", mock_open(read_data=jsonl_content)):
                with self.assertRaises(SystemExit):
                    generator.select_prompt()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_generate_music_failure_handling(self, mock_requests, mock_validate):
        """音楽生成失敗時のエラーハンドリング"""
        mock_requests.return_value.status_code = 200

        generator = LofiPostGenerator(self.args)
        generator.selected_prompt = {"type": "ambient", "music_prompt": "test prompt"}

        # 音楽生成を失敗させる
        with patch(
            "auto_post.auto_lofi_post.piapi_music_generation",
            side_effect=Exception("Music generation failed"),
        ):
            with self.assertRaises(SystemExit):
                generator.generate_music()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_combine_audio_tracks_failure_handling(self, mock_requests, mock_validate):
        """音声結合失敗時のエラーハンドリング"""
        mock_requests.return_value.status_code = 200

        generator = LofiPostGenerator(self.args)
        generator.selected_prompt = {"type": "ambient", "ambient": True}

        # 音声結合を失敗させる
        with patch(
            "auto_post.auto_lofi_post.combine_audio",
            side_effect=Exception("Audio combination failed"),
        ):
            with self.assertRaises(SystemExit):
                generator.combine_audio_tracks()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_generate_thumbnail_failure_handling(self, mock_requests, mock_validate):
        """サムネイル生成失敗時のエラーハンドリング"""
        mock_requests.return_value.status_code = 200

        generator = LofiPostGenerator(self.args)
        generator.selected_prompt = {"type": "ambient", "thumbnail_title": "Test Title"}
        generator.selected_image_prompt = "test image prompt"

        # サムネイル生成を失敗させる
        with patch(
            "auto_post.auto_lofi_post.thumbnail_generation",
            side_effect=Exception("Thumbnail generation failed"),
        ):
            with self.assertRaises(SystemExit):
                generator.generate_thumbnail()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_generate_metadata_skip_file_not_found(self, mock_requests, mock_validate):
        """メタデータ生成スキップ時にファイルが見つからない場合のエラーハンドリング"""
        mock_requests.return_value.status_code = 200

        self.args.skip_metadata_gen = True
        generator = LofiPostGenerator(self.args)

        # ファイルが見つからない場合をシミュレート
        with patch.object(generator, "_find_latest_file", return_value=None):
            with self.assertRaises(SystemExit):
                generator.generate_metadata("test_tracks.json")

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_generate_metadata_failure_handling(self, mock_requests, mock_validate):
        """メタデータ生成失敗時のエラーハンドリング"""
        mock_requests.return_value.status_code = 200

        generator = LofiPostGenerator(self.args)
        generator.selected_prompt = {"type": "ambient", "music_prompt": "test prompt"}

        # メタデータ生成を失敗させる
        with patch(
            "auto_post.auto_lofi_post.create_metadata",
            side_effect=Exception("Metadata generation failed"),
        ):
            with self.assertRaises(SystemExit):
                generator.generate_metadata("test_tracks.json")

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_generate_video_failure_handling(self, mock_requests, mock_validate):
        """動画生成失敗時のエラーハンドリング"""
        mock_requests.return_value.status_code = 200

        generator = LofiPostGenerator(self.args)

        # 動画生成を失敗させる
        with patch(
            "auto_post.auto_lofi_post.create_video",
            side_effect=Exception("Video generation failed"),
        ):
            with self.assertRaises(SystemExit):
                generator.generate_video("test_image.jpg", "test_audio.mp3")

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_upload_to_youtube_failure_handling(self, mock_requests, mock_validate):
        """YouTubeアップロード失敗時のエラーハンドリング"""
        mock_requests.return_value.status_code = 200

        generator = LofiPostGenerator(self.args)

        # YouTubeアップロードを失敗させる
        with patch(
            "auto_post.auto_lofi_post.upload_video_to_youtube",
            side_effect=Exception("Upload failed"),
        ):
            with self.assertRaises(SystemExit):
                generator.upload_to_youtube(
                    "test_video.mp4", "test_thumbnail.jpg", "test_metadata.json"
                )

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_run_method_exception_handling(self, mock_requests, mock_validate):
        """runメソッドでの予期せぬエラーハンドリング"""
        mock_requests.return_value.status_code = 200

        generator = LofiPostGenerator(self.args)

        # setupメソッドで例外を発生させる
        with patch.object(generator, "setup", side_effect=Exception("Setup failed")):
            with self.assertRaises(SystemExit):
                generator.run()

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_thumbnail_title_list_handling(self, mock_requests, mock_validate):
        """thumbnail_titleがリストの場合の処理"""
        mock_requests.return_value.status_code = 200

        generator = LofiPostGenerator(self.args)

        # thumbnail_titleがリストのデータ
        test_data = {
            "type": "ambient",
            "music_prompt": "ambient music",
            "thumbnail_title": ["Title 1", "Title 2", "Title 3"],
            "image_prompts": ["image1", "image2"],
        }

        jsonl_content = json.dumps(test_data)

        with patch("builtins.open", mock_open(read_data=jsonl_content)):
            generator._select_random_prompt()

            # thumbnail_titleが文字列に変換されていることを確認
            self.assertIsInstance(generator.selected_prompt["thumbnail_title"], str)
            self.assertIn(
                generator.selected_prompt["thumbnail_title"],
                ["Title 1", "Title 2", "Title 3"],
            )

    @patch("auto_post.auto_lofi_post.Config.validate_config")
    @patch("auto_post.auto_lofi_post.requests.post")
    def test_image_prompts_fallback_to_image_prompt(self, mock_requests, mock_validate):
        """image_promptsが存在しない場合のimage_promptへのフォールバック"""
        mock_requests.return_value.status_code = 200

        generator = LofiPostGenerator(self.args)

        # image_promptsが存在せず、image_promptが存在するデータ
        test_data = {
            "type": "ambient",
            "music_prompt": "ambient music",
            "thumbnail_title": "Test Title",
            "image_prompt": "fallback image prompt",
        }

        jsonl_content = json.dumps(test_data)

        with patch("builtins.open", mock_open(read_data=jsonl_content)):
            generator._select_random_prompt()

            # image_promptが選択されていることを確認
            self.assertEqual(generator.selected_image_prompt, "fallback image prompt")


if __name__ == "__main__":
    unittest.main()
