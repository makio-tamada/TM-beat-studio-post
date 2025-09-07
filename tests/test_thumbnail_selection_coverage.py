import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from auto_post.test_thumbnail_selection import run_thumbnail_selection_test

# テスト対象のモジュールをインポート


class TestThumbnailSelection(unittest.TestCase):
    """test_thumbnail_selectionモジュールの単体テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("builtins.open", new_callable=mock_open)
    def test_thumbnail_selection_with_mock_file(self, mock_file):
        """モックファイルを使用したthumbnail_selectionテスト"""
        # モックデータ
        mock_data = [
            {
                "type": "sad",
                "thumbnail_title": ["Sad Lo-Fi", "Melancholic Vibes"],
                "image_prompts": ["melancholic scene", "rainy window"],
                "music_prompt": "sad lo-fi beats",
            },
            {
                "type": "happy",
                "thumbnail_title": "Happy Lo-Fi",
                "image_prompt": "cheerful scene",
                "music_prompt": "upbeat lo-fi vibes",
            },
        ]

        mock_file.return_value.__enter__.return_value.readlines.return_value = [
            json.dumps(item) + "\n" for item in mock_data
        ]

        with patch("builtins.print"):
            run_thumbnail_selection_test()

            # ファイルが開かれることを確認
            mock_file.assert_called_once()

    def test_thumbnail_selection_with_real_file(self):
        """実際のファイルを使用したthumbnail_selectionテスト"""
        with patch(
            "builtins.open",
            mock_open(
                read_data="".join(
                    [
                        json.dumps(
                            {
                                "type": "sad",
                                "thumbnail_title": ["Sad Lo-Fi", "Melancholic Vibes"],
                                "image_prompts": ["melancholic scene", "rainy window"],
                                "music_prompt": "sad lo-fi beats",
                            }
                        )
                        + "\n",
                        json.dumps(
                            {
                                "type": "happy",
                                "thumbnail_title": "Happy Lo-Fi",
                                "image_prompt": "cheerful scene",
                                "music_prompt": "upbeat lo-fi vibes",
                            }
                        )
                        + "\n",
                    ]
                )
            ),
        ):
            with patch("builtins.print") as mock_print:
                run_thumbnail_selection_test()

                # 出力が呼ばれることを確認
                self.assertGreater(mock_print.call_count, 0)

                # 特定の出力内容を確認
                print_calls = [str(call) for call in mock_print.call_args_list]

                # ヘッダーが出力されることを確認
                header_found = any(
                    "=== thumbnail_title ランダム選択テスト ===" in call
                    for call in print_calls
                )
                self.assertTrue(header_found)

                # タイプ数が出力されることを確認
                type_count_found = any("総タイプ数:" in call for call in print_calls)
                self.assertTrue(type_count_found)

    def test_thumbnail_selection_array_thumbnail_title(self):
        """配列のthumbnail_titleのテスト"""
        with patch(
            "builtins.open",
            mock_open(
                read_data="".join(
                    [
                        json.dumps(
                            {
                                "type": "sad",
                                "thumbnail_title": ["Sad Lo-Fi", "Melancholic Vibes"],
                                "image_prompts": ["melancholic scene", "rainy window"],
                                "music_prompt": "sad lo-fi beats",
                            }
                        )
                        + "\n"
                    ]
                )
            ),
        ):
            with patch("builtins.print") as mock_print:
                run_thumbnail_selection_test()

                print_calls = [str(call) for call in mock_print.call_args_list]

                # 配列のthumbnail_titleが処理されることを確認
                array_found = any(
                    "thumbnail_title (配列)" in call for call in print_calls
                )
                self.assertTrue(array_found)

                # ランダム選択テストが実行されることを確認
                random_test_found = any(
                    "ランダム選択テスト" in call for call in print_calls
                )
                self.assertTrue(random_test_found)

    def test_thumbnail_selection_string_thumbnail_title(self):
        """文字列のthumbnail_titleのテスト"""
        with patch(
            "builtins.open",
            mock_open(
                read_data="".join(
                    [
                        json.dumps(
                            {
                                "type": "happy",
                                "thumbnail_title": "Happy Lo-Fi",
                                "image_prompt": "cheerful scene",
                                "music_prompt": "upbeat lo-fi vibes",
                            }
                        )
                        + "\n"
                    ]
                )
            ),
        ):
            with patch("builtins.print") as mock_print:
                run_thumbnail_selection_test()

                print_calls = [str(call) for call in mock_print.call_args_list]

                # 文字列のthumbnail_titleが処理されることを確認
                string_found = any(
                    "thumbnail_title (文字列)" in call for call in print_calls
                )
                self.assertTrue(string_found)

    def test_thumbnail_selection_image_prompts_array(self):
        """配列のimage_promptsのテスト"""
        with patch(
            "builtins.open",
            mock_open(
                read_data="".join(
                    [
                        json.dumps(
                            {
                                "type": "sad",
                                "thumbnail_title": "Sad Lo-Fi",
                                "image_prompts": ["melancholic scene", "rainy window"],
                                "music_prompt": "sad lo-fi beats",
                            }
                        )
                        + "\n"
                    ]
                )
            ),
        ):
            with patch("builtins.print") as mock_print:
                run_thumbnail_selection_test()

                print_calls = [str(call) for call in mock_print.call_args_list]

                # 配列のimage_promptsが処理されることを確認
                array_found = any(
                    "image_prompts (配列)" in call for call in print_calls
                )
                self.assertTrue(array_found)

    def test_thumbnail_selection_image_prompt_string(self):
        """文字列のimage_promptのテスト"""
        with patch(
            "builtins.open",
            mock_open(
                read_data="".join(
                    [
                        json.dumps(
                            {
                                "type": "happy",
                                "thumbnail_title": "Happy Lo-Fi",
                                "image_prompt": "cheerful scene",
                                "music_prompt": "upbeat lo-fi vibes",
                            }
                        )
                        + "\n"
                    ]
                )
            ),
        ):
            with patch("builtins.print") as mock_print:
                run_thumbnail_selection_test()

                print_calls = [str(call) for call in mock_print.call_args_list]

                # 文字列のimage_promptが処理されることを確認
                string_found = any(
                    "image_prompt (文字列)" in call for call in print_calls
                )
                self.assertTrue(string_found)

    def test_thumbnail_selection_empty_lines_handling(self):
        """空行の処理テスト"""
        # 空行を含むモックデータ
        mock_data_with_empty_lines = [
            json.dumps({"type": "sad", "thumbnail_title": "Sad Lo-Fi"}) + "\n",
            "\n",  # 空行
            json.dumps({"type": "happy", "thumbnail_title": "Happy Lo-Fi"}) + "\n",
            "   \n",  # 空白のみの行
        ]

        with patch(
            "builtins.open", mock_open(read_data="".join(mock_data_with_empty_lines))
        ):
            with patch("builtins.print"):
                run_thumbnail_selection_test()

                # エラーが発生しないことを確認（空行が適切に処理される）
                pass

    def test_thumbnail_selection_random_choice_functionality(self):
        """ランダム選択機能のテスト"""
        with patch(
            "builtins.open",
            mock_open(
                read_data="".join(
                    [
                        json.dumps(
                            {
                                "type": "sad",
                                "thumbnail_title": ["Sad Lo-Fi", "Melancholic Vibes"],
                                "image_prompts": ["melancholic scene", "rainy window"],
                                "music_prompt": "sad lo-fi beats",
                            }
                        )
                        + "\n"
                    ]
                )
            ),
        ):
            with patch(
                "auto_post.test_thumbnail_selection.random.choice"
            ) as mock_choice:
                mock_choice.return_value = "Test Selection"

                with patch("builtins.print") as mock_print:
                    run_thumbnail_selection_test()

                    # random.choiceが呼ばれることを確認
                    self.assertGreater(mock_choice.call_count, 0)

                    print_calls = [str(call) for call in mock_print.call_args_list]

                    # ランダム選択の結果が出力されることを確認
                    selection_found = any(
                        "Test Selection" in call for call in print_calls
                    )
                    self.assertTrue(selection_found)

    def test_thumbnail_selection_direct_call(self):
        """直接呼び出しでのthumbnail_selectionテスト"""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                run_thumbnail_selection_test()


if __name__ == "__main__":
    unittest.main()
