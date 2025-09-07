import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from auto_post.thumbnail_generation import (
    LOBSTER_FONT_PATH,
    LOBSTER_FONT_URL,
    THUMB_HEIGHT,
    THUMB_WIDTH,
    create_thumbnail,
    ensure_font,
    load_random_prompt,
    main,
    thumbnail_generation,
)


class TestThumbnailGeneration(unittest.TestCase):
    """thumbnail_generationモジュールの単体テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # テスト用のJSONLファイルを作成
        self.test_jsonl = self.temp_path / "test.jsonl"
        test_data = [
            {
                "type": "sad",
                "image_prompt": "melancholic scene",
                "thumbnail_title": "Sad Lo-Fi",
            },
            {
                "type": "happy",
                "image_prompt": "cheerful scene",
                "thumbnail_title": ["Happy Lo-Fi", "Joyful Music"],
            },
        ]
        with open(self.test_jsonl, "w", encoding="utf-8") as f:
            for item in test_data:
                f.write(json.dumps(item) + "\n")

    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_constants(self):
        """定数のテスト"""
        self.assertEqual(THUMB_WIDTH, 1280)
        self.assertEqual(THUMB_HEIGHT, 720)
        self.assertIn("Lobster-Regular.ttf", LOBSTER_FONT_URL)
        self.assertIsInstance(LOBSTER_FONT_PATH, Path)

    def test_load_random_prompt_string_title(self):
        """文字列のthumbnail_titleを読み込むテスト"""
        lofi_type, image_prompt, thumbnail_title = load_random_prompt(self.test_jsonl)

        # アサーション
        self.assertIn(lofi_type, ["sad", "happy"])
        self.assertIn(image_prompt, ["melancholic scene", "cheerful scene"])
        self.assertIsInstance(thumbnail_title, str)

    def test_load_random_prompt_list_title(self):
        """配列のthumbnail_titleを読み込むテスト"""
        # 複数回実行して配列のタイトルが選択されることを確認
        found_list_title = False
        for _ in range(10):  # 複数回実行
            lofi_type, image_prompt, thumbnail_title = load_random_prompt(
                self.test_jsonl
            )
            if lofi_type == "happy":
                self.assertIn(thumbnail_title, ["Happy Lo-Fi", "Joyful Music"])
                found_list_title = True
                break

        # 少なくとも1回は配列のタイトルが選択されることを確認
        self.assertTrue(found_list_title)

    def test_load_random_prompt_file_not_found(self):
        """存在しないファイルを読み込む場合のテスト"""
        non_existent_file = self.temp_path / "non_existent.jsonl"

        with self.assertRaises(FileNotFoundError):
            load_random_prompt(non_existent_file)

    def test_load_random_prompt_empty_file(self):
        """空のファイルを読み込む場合のテスト"""
        empty_file = self.temp_path / "empty.jsonl"
        empty_file.touch()

        with self.assertRaises(IndexError):
            load_random_prompt(empty_file)

    @patch("auto_post.thumbnail_generation.requests.get")
    @patch("builtins.open", new_callable=Mock)
    def test_ensure_font_download(self, mock_file, mock_get):
        """フォントダウンロードのテスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.content = b"fake_font_data"
        mock_get.return_value = mock_response

        # フォントファイルが存在しないことをモック
        with patch.object(Path, "exists", return_value=False):
            result = ensure_font()

        # アサーション
        self.assertEqual(result, str(LOBSTER_FONT_PATH))
        mock_get.assert_called_once_with(LOBSTER_FONT_URL, timeout=30)
        mock_file.assert_called_once()

    @patch("builtins.open", new_callable=Mock)
    def test_ensure_font_already_exists(self, mock_file):
        """フォントが既に存在する場合のテスト"""
        # フォントファイルが存在することをモック
        with patch.object(Path, "exists", return_value=True):
            result = ensure_font()

        # アサーション
        self.assertEqual(result, str(LOBSTER_FONT_PATH))
        mock_file.assert_not_called()

    @patch("auto_post.thumbnail_generation.Image")
    @patch("auto_post.thumbnail_generation.ImageDraw")
    @patch("auto_post.thumbnail_generation.ImageFont")
    @patch("auto_post.thumbnail_generation.ImageEnhance")
    def test_create_thumbnail(self, mock_enhance, mock_font, mock_draw, mock_image):
        """サムネイル作成のテスト"""
        # モックの設定
        mock_img = Mock()
        mock_image.open.return_value.convert.return_value = mock_img
        mock_img.resize.return_value = mock_img

        mock_enhance_instance = Mock()
        mock_enhance_instance.enhance.return_value = mock_img
        mock_enhance.Brightness.return_value = mock_enhance_instance

        mock_draw_instance = Mock()
        mock_draw.Draw.return_value = mock_draw_instance

        mock_font_instance = Mock()
        mock_font.truetype.return_value = mock_font_instance

        # 関数を実行
        create_thumbnail(
            bg_image_path="test_bg.png",
            title="Test Title",
            output_path="test_output.png",
            font_path="test_font.ttf",
            font_size=180,
        )

        # アサーション
        mock_image.open.assert_called_once_with("test_bg.png")
        mock_enhance.Brightness.assert_called_once_with(mock_img)
        mock_enhance_instance.enhance.assert_called_once_with(0.85)
        mock_img.resize.assert_called_once_with(
            (THUMB_WIDTH, THUMB_HEIGHT), mock_image.LANCZOS
        )
        mock_draw.Draw.assert_called_once_with(mock_img)
        mock_font.truetype.assert_called_once_with("test_font.ttf", 180)
        mock_img.save.assert_called_once_with("test_output.png")

    @patch("auto_post.thumbnail_generation.Image")
    @patch("auto_post.thumbnail_generation.ImageDraw")
    @patch("auto_post.thumbnail_generation.ImageFont")
    @patch("auto_post.thumbnail_generation.ImageEnhance")
    def test_create_thumbnail_multiline_title(
        self, mock_enhance, mock_font, mock_draw, mock_image
    ):
        """複数行タイトルのサムネイル作成テスト"""
        # モックの設定
        mock_img = Mock()
        mock_image.open.return_value.convert.return_value = mock_img
        mock_img.resize.return_value = mock_img

        mock_enhance_instance = Mock()
        mock_enhance_instance.enhance.return_value = mock_img
        mock_enhance.Brightness.return_value = mock_enhance_instance

        mock_draw_instance = Mock()
        mock_draw.Draw.return_value = mock_draw_instance

        mock_font_instance = Mock()
        mock_font.truetype.return_value = mock_font_instance

        # 関数を実行（複数行タイトル）
        create_thumbnail(
            bg_image_path="test_bg.png",
            title="Line 1\\nLine 2",
            output_path="test_output.png",
            font_path="test_font.ttf",
            font_size=180,
        )

        # アサーション
        mock_draw_instance.text.assert_called()  # 複数回呼ばれることを確認

    @patch("auto_post.thumbnail_generation.DiffusionPipeline")
    @patch("auto_post.thumbnail_generation.ensure_font")
    @patch("auto_post.thumbnail_generation.create_thumbnail")
    def test_thumbnail_generation_success(
        self, mock_create_thumb, mock_ensure_font, mock_pipeline
    ):
        """サムネイル生成成功時のテスト"""
        # モックの設定
        mock_pipe = Mock()
        mock_image = Mock()
        mock_pipe.return_value.images = [mock_image]
        mock_pipeline.from_pretrained.return_value.to.return_value = mock_pipe

        mock_ensure_font.return_value = "test_font.ttf"
        mock_create_thumb.return_value = None

        # 関数を実行
        result = thumbnail_generation(
            output_dir=str(self.temp_path),
            lofi_type="sad",
            prompt="melancholic scene",
            thumb_title="Sad Lo-Fi",
        )

        # アサーション
        self.assertEqual(len(result), 2)
        self.assertIn("sad_1280x720_", result[0])
        self.assertIn("_thumb.png", result[1])

        mock_pipeline.from_pretrained.assert_called_once()
        mock_pipe.assert_called_once()
        mock_ensure_font.assert_called_once()
        mock_create_thumb.assert_called_once()

    @patch("auto_post.thumbnail_generation.DiffusionPipeline")
    def test_thumbnail_generation_pipeline_error(self, mock_pipeline):
        """パイプラインエラー時のテスト"""
        # モックの設定（エラーを発生させる）
        mock_pipeline.from_pretrained.side_effect = Exception("Pipeline error")

        # 関数を実行
        with self.assertRaises(Exception):
            thumbnail_generation(
                output_dir=str(self.temp_path),
                lofi_type="sad",
                prompt="melancholic scene",
                thumb_title="Sad Lo-Fi",
            )

    @patch("auto_post.thumbnail_generation.DiffusionPipeline")
    @patch("auto_post.thumbnail_generation.ensure_font")
    @patch("auto_post.thumbnail_generation.create_thumbnail")
    def test_thumbnail_generation_safe_filename(
        self, mock_create_thumb, mock_ensure_font, mock_pipeline
    ):
        """安全なファイル名生成のテスト"""
        # モックの設定
        mock_pipe = Mock()
        mock_image = Mock()
        mock_pipe.return_value.images = [mock_image]
        mock_pipeline.from_pretrained.return_value.to.return_value = mock_pipe

        mock_ensure_font.return_value = "test_font.ttf"
        mock_create_thumb.return_value = None

        # 特殊文字を含むlofi_typeでテスト
        result = thumbnail_generation(
            output_dir=str(self.temp_path),
            lofi_type="sad/melancholic: type",
            prompt="melancholic scene",
            thumb_title="Sad Lo-Fi",
        )

        # アサーション（特殊文字がアンダースコアに置換されることを確認）
        self.assertIn("sad_melancholic_type_1280x720_", result[0])

    @patch("auto_post.thumbnail_generation.DiffusionPipeline")
    @patch("auto_post.thumbnail_generation.load_random_prompt")
    @patch("auto_post.thumbnail_generation.ensure_font")
    @patch("auto_post.thumbnail_generation.create_thumbnail")
    def test_main_function(
        self, mock_create_thumb, mock_ensure_font, mock_load_prompt, mock_pipeline
    ):
        """main関数のテスト"""
        # モックの設定
        mock_load_prompt.return_value = ("sad", "melancholic scene", "Sad Lo-Fi")

        mock_pipe = Mock()
        mock_image = Mock()
        mock_pipe.return_value.images = [mock_image]
        mock_pipeline.from_pretrained.return_value.to.return_value = mock_pipe

        mock_ensure_font.return_value = "test_font.ttf"
        mock_create_thumb.return_value = None

        # 関数を実行
        with patch("builtins.print"):
            main()

        # アサーション
        mock_load_prompt.assert_called_once()
        mock_pipeline.from_pretrained.assert_called_once()
        mock_pipe.assert_called_once()
        mock_ensure_font.assert_called_once()
        mock_create_thumb.assert_called_once()

    @patch("auto_post.thumbnail_generation.torch")
    def test_device_selection(self, mock_torch):
        """デバイス選択のテスト"""
        # MPSが利用可能な場合
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.cuda.is_available.return_value = False

        with patch("auto_post.thumbnail_generation.DiffusionPipeline") as mock_pipeline:
            mock_pipe = Mock()
            mock_image = Mock()
            mock_pipe.return_value.images = [mock_image]
            mock_pipeline.from_pretrained.return_value.to.return_value = mock_pipe

            with patch("auto_post.thumbnail_generation.ensure_font"), patch(
                "auto_post.thumbnail_generation.create_thumbnail"
            ), patch("builtins.print"):

                thumbnail_generation(
                    output_dir=str(self.temp_path),
                    lofi_type="sad",
                    prompt="melancholic scene",
                    thumb_title="Sad Lo-Fi",
                )

            # MPSデバイスが使用されることを確認
            mock_pipeline.from_pretrained.return_value.to.assert_called_with("mps")


if __name__ == "__main__":
    unittest.main()
