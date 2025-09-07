import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from auto_post.create_metadata import (
    build_tracklist,
    call_openai,
    create_metadata,
    format_timestamp,
    load_random_lofi,
    load_tracks,
)


class TestCreateMetadata(unittest.TestCase):
    """create_metadataモジュールの単体テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "data"
        self.test_data_dir.mkdir()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir)

    def test_format_timestamp(self):
        """タイムスタンプフォーマット関数のテスト"""
        test_cases = [
            (0, "0:00"),
            (30, "0:30"),
            (60, "1:00"),
            (90, "1:30"),
            (125, "2:05"),
            (3600, "60:00"),
        ]

        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_timestamp(seconds)
                self.assertEqual(result, expected)

    def test_build_tracklist_empty(self):
        """空のトラックリストでのビルドテスト"""
        result = build_tracklist([])
        expected = "TRACKLIST:\n[No track information available]"
        self.assertEqual(result, expected)

    def test_build_tracklist_with_tracks(self):
        """トラックがある場合のビルドテスト"""
        tracks = [
            {"title": "Track 1", "start_time": 0.0},
            {"title": "Track 2", "start_time": 120.0},
            {"title": "Track 3", "start_time": 240.0},
        ]

        result = build_tracklist(tracks)
        expected_lines = [
            "TRACKLIST:",
            "0:00 - Track 1",
            "2:00 - Track 2",
            "4:00 - Track 3",
        ]
        expected = "\n".join(expected_lines)

        self.assertEqual(result, expected)

    @patch("auto_post.create_metadata.requests.post")
    def test_call_openai_success(self, mock_post):
        """OpenAI API呼び出し成功時のテスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated title"}}]
        }
        mock_post.return_value = mock_response

        result = call_openai("Test prompt")
        self.assertEqual(result, "Generated title")

    @patch("auto_post.create_metadata.requests.post")
    def test_call_openai_failure(self, mock_post):
        """OpenAI API呼び出し失敗時のテスト"""
        # モックの設定
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # 実際のコードでは例外を発生させずに空文字列を返す
        result = call_openai("Test prompt")
        self.assertEqual(result, "")

    @patch("auto_post.create_metadata.OPENAI_API_KEY", None)
    def test_call_openai_no_api_key(self):
        """APIキーが設定されていない場合のテスト"""
        with self.assertRaises(ValueError):
            call_openai("Test prompt")

    @patch("auto_post.create_metadata.call_openai")
    def test_create_metadata_success(self, mock_call_openai):
        """メタデータ生成成功時のテスト"""
        # モックの設定
        mock_call_openai.side_effect = ["Generated Title", "Generated description"]

        # テスト用のトラックJSONファイルを作成
        tracks_json = self.test_data_dir / "tracks.json"
        tracks_data = [{"title": "Track 1", "start_time": 0.0}]
        with open(tracks_json, "w") as f:
            json.dump(tracks_data, f)

        result = create_metadata(
            output_dir=str(self.test_data_dir),
            tracks_json=str(tracks_json),
            lofi_type="sad",
            music_prompt="melancholic piano",
            api_url="",
            temperature=0.7,
        )

        self.assertIsInstance(result, Path)
        self.assertTrue(result.exists())
        mock_call_openai.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch("auto_post.create_metadata.json.load")
    def test_load_tracks_file_exists(self, mock_json_load, mock_file):
        """トラックファイルが存在する場合のテスト"""
        mock_json_load.return_value = [{"title": "Track 1", "start_time": 0.0}]

        with patch("auto_post.create_metadata.TRACKS_JSON") as mock_tracks_json:
            mock_tracks_json.exists.return_value = True
            result = load_tracks()
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["title"], "Track 1")

    @patch("auto_post.create_metadata.TRACKS_JSON")
    def test_load_tracks_file_not_exists(self, mock_tracks_json):
        """トラックファイルが存在しない場合のテスト"""
        mock_tracks_json.exists.return_value = False
        result = load_tracks()
        self.assertEqual(result, [])

    @patch("builtins.open", new_callable=mock_open)
    @patch("auto_post.create_metadata.json.loads")
    def test_load_random_lofi(self, mock_json_loads, mock_file):
        """ランダムLo-Fiデータ読み込みのテスト"""
        mock_data = [
            {"type": "sad", "music_prompt": "melancholic"},
            {"type": "happy", "music_prompt": "upbeat"},
        ]
        mock_file.return_value.__enter__.return_value.readlines.return_value = [
            '{"type": "sad", "music_prompt": "melancholic"}',
            '{"type": "happy", "music_prompt": "upbeat"}',
        ]
        mock_json_loads.side_effect = mock_data

        with patch("auto_post.create_metadata.JSONL_PATH") as mock_jsonl_path:
            mock_jsonl_path.read_text.return_value = "\n".join(
                [
                    '{"type": "sad", "music_prompt": "melancholic"}',
                    '{"type": "happy", "music_prompt": "upbeat"}',
                ]
            )
            with patch("auto_post.create_metadata.random.choice") as mock_choice:
                mock_choice.return_value = mock_data[0]
                result = load_random_lofi()
                self.assertEqual(result["type"], "sad")
                self.assertEqual(result["music_prompt"], "melancholic")


if __name__ == "__main__":
    unittest.main()
