"""
pytest設定ファイル
テスト実行時の共通設定とフィクスチャを定義
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# テスト対象のモジュールパスを追加（プロジェクトルート/src を先頭に）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture(scope="session")
def test_environment():
    """テスト環境の設定"""
    # テスト用の環境変数を設定
    os.environ["TESTING"] = "true"
    os.environ["SLACK_WEBHOOK_URL"] = "https://hooks.slack.com/services/test/test/test"

    # テスト用のディレクトリを作成
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    # クリーンアップ
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_lofi_data():
    """サンプルのLo-Fiデータ"""
    return [
        {
            "type": "sad",
            "music_prompt": "melancholic piano",
            "thumbnail_title": "Sad Lo-Fi",
            "ambient": "rain.mp3",
            "image_prompts": ["melancholic scene"],
        },
        {
            "type": "happy",
            "music_prompt": "upbeat jazz",
            "thumbnail_title": "Happy Lo-Fi",
            "ambient": "cafe.mp3",
            "image_prompts": ["cheerful scene"],
        },
    ]


@pytest.fixture
def sample_tracks_data():
    """サンプルのトラックデータ"""
    return [
        {"title": "Track 1", "start_time": 0.0},
        {"title": "Track 2", "start_time": 120.0},
        {"title": "Track 3", "start_time": 240.0},
    ]


@pytest.fixture
def mock_audio_file():
    """モック音声ファイル"""
    temp_dir = tempfile.mkdtemp()
    audio_file = Path(temp_dir) / "test_audio.mp3"
    audio_file.touch()
    yield audio_file
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_image_file():
    """モック画像ファイル"""
    temp_dir = tempfile.mkdtemp()
    image_file = Path(temp_dir) / "test_image.png"
    image_file.touch()
    yield image_file
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_video_file():
    """モック動画ファイル"""
    temp_dir = tempfile.mkdtemp()
    video_file = Path(temp_dir) / "test_video.mp4"
    video_file.touch()
    yield video_file
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """環境変数のモックフィクスチャ"""
    # テスト用の環境変数を設定
    test_vars = {
        "PIAPI_KEY": "test_piapi_key",
        "OPENAI_API_KEY": "test_openai_key",
        "GOOGLE_REFRESH_TOKEN": "test_refresh_token",
        "GOOGLE_CLIENT_ID": "test_client_id",
        "GOOGLE_CLIENT_SECRET": "test_client_secret",
    }

    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)

    return test_vars
