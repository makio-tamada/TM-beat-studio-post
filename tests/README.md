# TM-beat-studio テスト項目詳細

このドキュメントでは、TM-beat-studioプロジェクトの各テストファイルとテスト項目について詳細に説明します。

## 📁 テストファイル構成

```
tests/
├── README.md                           # このファイル
├── __init__.py                         # テストパッケージ初期化
├── conftest.py                         # pytest設定とフィクスチャ
├── run_tests.py                        # テスト実行スクリプト
├── test_auto_lofi_post.py              # メインクラステスト
├── test_combine_audio.py               # 音声結合機能テスト
├── test_create_metadata.py             # メタデータ生成テスト
├── test_piapi_music_generation.py      # 音楽生成テスト
└── test_upload_to_youtube.py           # YouTubeアップロードテスト
```

## 🔧 テスト環境の特徴

### Slack通知の自動無効化
テスト実行時は、実際のSlack通知が自動的に無効化され、代わりにテスト用メッセージが表示されます：

```
[TEST] Slack通知: 📝 プロンプト選択完了
[TEST] Slack通知: 🎵 新規音楽生成が完了しました
[TEST] Slack通知: 🖼️ サムネイル生成が完了しました
[TEST] Slack通知: 🎧 音楽結合が完了しました
[TEST] Slack通知: 📋 メタデータ生成が完了しました
[TEST] Slack通知: 🎥 動画生成が完了しました
[TEST] Slack通知: 📤 YouTubeへのアップロードが完了しました
```

**実装方法**:
- テスト実行時に`TESTING=true`環境変数が自動設定
- `send_slack_notification`メソッドでテスト環境を検出
- 実際のHTTPリクエストの代わりにテスト用メッセージを出力

**メリット**:
- テスト実行時のSlackスパム防止
- 本番環境での通知は通常通り動作
- テストの独立性と再現性の向上

## 🧪 テスト項目詳細

### 1. test_auto_lofi_post.py - メインクラステスト

**テスト対象**: `LofiPostGenerator`クラス（メインの統合クラス）

#### テスト項目一覧

| テストメソッド | 説明 | テスト内容 |
|---|---|---|
| `test_config_attributes` | Configクラスの属性テスト | 設定値の存在確認 |
| `test_generator_initialization` | 初期化テスト | クラス初期化時の状態確認 |
| `test_send_slack_notification_success` | Slack通知成功テスト | テスト環境での通知無効化確認 |
| `test_send_slack_notification_error` | Slack通知失敗テスト | エラー時の例外処理確認 |
| `test_extract_type_from_thumbnail_success` | サムネイルタイプ抽出成功 | ファイル名からのタイプ抽出 |
| `test_extract_type_from_thumbnail_not_found` | サムネイル未発見テスト | ファイル未発見時のエラー処理 |
| `test_select_prompt_with_skip_type_selection` | スキップ時のプロンプト選択 | タイプ選択スキップ機能 |
| `test_select_prompt_without_skip` | 通常のプロンプト選択 | ランダム選択機能 |
| `test_generate_music_success` | 音楽生成成功テスト | PiAPI呼び出し成功時 |
| `test_generate_music_failure` | 音楽生成失敗テスト | PiAPI呼び出し失敗時 |
| `test_generate_thumbnail_success` | サムネイル生成テスト | 画像生成機能 |
| `test_combine_audio_tracks_success` | 音声結合テスト | ファイル結合機能 |
| `test_generate_metadata_success` | メタデータ生成テスト | タイトル・説明文生成 |
| `test_generate_video_success` | 動画作成テスト | 動画生成機能 |
| `test_upload_to_youtube_success` | YouTubeアップロードテスト | 動画アップロード機能 |
| `test_cleanup_newly_generated_files` | クリーンアップテスト | 一時ファイル削除 |
| `test_run_full_pipeline_success` | 完全パイプラインテスト | 全処理の統合テスト |

#### 重要なテストケース

- **エラーハンドリング**: 各段階での失敗時の処理
- **スキップ機能**: 各処理段階のスキップ機能
- **ファイル管理**: 生成ファイルの追跡とクリーンアップ
- **統合フロー**: 音楽生成→サムネイル→結合→メタデータ→動画→アップロード
- **Slack通知**: テスト環境での自動無効化機能

---

### 2. test_combine_audio.py - 音声結合機能テスト

**テスト対象**: `combine_audio.py`モジュール

#### テスト項目一覧

| テストメソッド | 説明 | テスト内容 |
|---|---|---|
| `test_get_audio_files_empty_directory` | 空ディレクトリテスト | MP3ファイルが存在しない場合 |
| `test_get_audio_files_with_mp3_files` | MP3ファイル取得テスト | 正しいファイルの抽出 |
| `test_human_minutes` | 時間フォーマットテスト | 秒→分:秒形式の変換 |
| `test_load_ambient_short_track` | 環境音読み込みテスト | 短いトラックのループ処理 |
| `test_combine_tracks_empty_list` | 空リスト結合テスト | エラー処理の確認 |
| `test_combine_tracks_single_track` | 単一トラック結合テスト | 1つのファイルの処理 |
| `test_combine_tracks_multiple_tracks` | 複数トラック結合テスト | クロスフェード処理 |

#### 重要なテストケース

- **ファイルフィルタリング**: `combined_audio.mp3`の除外
- **時間計算**: トラック情報の正確な時間計算
- **クロスフェード**: フェードイン・アウトの処理
- **エラーハンドリング**: 空のディレクトリやファイルリスト

---

### 3. test_create_metadata.py - メタデータ生成テスト

**テスト対象**: `create_metadata.py`モジュール

#### テスト項目一覧

| テストメソッド | 説明 | テスト内容 |
|---|---|---|
| `test_format_timestamp` | タイムスタンプフォーマット | 秒→分:秒形式の変換 |
| `test_build_tracklist_empty` | 空トラックリスト | トラック情報なしの場合 |
| `test_build_tracklist_with_tracks` | トラックリスト構築 | 複数トラックの情報 |
| `test_call_openai_success` | OpenAI API成功テスト | 正常なAPI呼び出し |
| `test_call_openai_failure` | OpenAI API失敗テスト | API呼び出し失敗時（空文字列返却） |
| `test_call_openai_no_api_key` | APIキー未設定テスト | 環境変数未設定時 |
| `test_create_metadata_success` | メタデータ生成成功テスト | 完全なメタデータ生成フロー |
| `test_load_tracks_file_exists` | トラックファイル存在テスト | JSONファイル読み込み |
| `test_load_tracks_file_not_exists` | トラックファイル未存在テスト | ファイル未発見時 |
| `test_load_random_lofi` | ランダムLo-Fi読み込みテスト | JSONLファイルからの選択 |

#### 重要なテストケース

- **API呼び出し**: OpenAI APIの成功・失敗パターン
- **ファイル処理**: JSON/JSONLファイルの読み込み
- **文字列処理**: タイムスタンプとトラックリストのフォーマット
- **エラーハンドリング**: ファイル未発見やAPI失敗時の処理

---

### 4. test_piapi_music_generation.py - 音楽生成テスト

**テスト対象**: `piapi_music_generation.py`モジュール

#### テスト項目一覧

| テストメソッド | 説明 | テスト内容 |
|---|---|---|
| `test_get_existing_filenames_empty_directory` | 空ディレクトリテスト | 既存ファイルなし |
| `test_get_existing_filenames_with_mp3_files` | MP3ファイル取得テスト | 既存ファイルの検出 |
| `test_generate_unique_filename_no_duplicate` | 重複なしファイル名生成 | ユニークファイル名 |
| `test_generate_unique_filename_with_duplicate` | 重複ありファイル名生成 | 重複回避機能 |
| `test_generate_unique_filename_special_characters` | 特殊文字ファイル名生成 | 特殊文字の処理 |
| `test_generate_unique_filename_empty_title` | 空タイトルファイル名生成 | デフォルト名の生成 |
| `test_create_music_task_success` | タスク作成成功テスト | PiAPIタスク作成 |
| `test_create_music_task_failure` | タスク作成失敗テスト | API呼び出し失敗時 |
| `test_wait_for_task_completed` | タスク完了監視テスト | ステータス監視 |
| `test_wait_for_task_failed` | タスク失敗監視テスト | 失敗時の処理 |
| `test_download_audio_success` | 音声ダウンロード成功テスト | ファイルダウンロード |
| `test_download_audio_failure` | 音声ダウンロード失敗テスト | ダウンロード失敗時 |
| `test_piapi_music_generation_success` | 全体フロー成功テスト | 完全な音楽生成フロー |

#### 重要なテストケース

- **ファイル名管理**: 重複回避と特殊文字処理
- **API連携**: PiAPIとの通信処理
- **非同期処理**: タスクステータスの監視
- **ファイル操作**: 音声ファイルのダウンロード

---

### 5. test_upload_to_youtube.py - YouTubeアップロードテスト

**テスト対象**: `upload_to_youtube.py`モジュール

#### テスト項目一覧

| テストメソッド | 説明 | テスト内容 |
|---|---|---|
| `test_get_authenticated_service_missing_env_vars` | 環境変数未設定テスト | 認証情報不足時 |
| `test_get_authenticated_service_with_refresh_token` | リフレッシュトークン認証テスト | 既存トークンでの認証 |
| `test_get_authenticated_service_new_auth` | 新規認証テスト | 新規認証フロー |
| `test_upload_video_to_youtube_success` | 動画アップロード成功テスト | 正常なアップロード |
| `test_upload_video_to_youtube_service_failure` | サービス取得失敗テスト | 認証失敗時 |
| `test_upload_video_to_youtube_upload_failure` | アップロード失敗テスト | アップロード失敗時 |
| `test_upload_video_to_youtube_file_not_exists` | ファイル未存在テスト | ファイル未発見時 |

#### 重要なテストケース

- **認証処理**: Google OAuth認証の成功・失敗パターン
- **メタデータ設定**: タイトル、説明、タグ、プライバシー設定
- **ファイル検証**: アップロードファイルの存在確認
- **エラーハンドリング**: 認証失敗やアップロード失敗時の処理

---

## 🎯 テスト実行方法

### 全テスト実行
```bash
# テスト用依存関係のインストール
pip install -r requirements-test.txt

# 全テスト実行（Slack通知自動無効化）
python tests/run_tests.py

# またはpytest使用
pytest tests/ -v
```

### 特定のテスト実行
```bash
# 特定のテストファイル
python tests/run_tests.py auto_lofi_post
python tests/run_tests.py combine_audio
python tests/run_tests.py create_metadata
python tests/run_tests.py piapi_music_generation
python tests/run_tests.py upload_to_youtube

# 特定のテストクラス
pytest tests/test_auto_lofi_post.py::TestLofiPostGenerator -v

# 特定のテストメソッド
pytest tests/test_combine_audio.py::TestCombineAudio::test_combine_tracks_single_track -v
```

### カバレッジ付きテスト実行
```bash
# HTMLレポート付き
pytest tests/ --cov=src/auto_post --cov-report=html

# コンソール出力
pytest tests/ --cov=src/auto_post --cov-report=term
```

---

## 🔧 テスト環境設定

### 自動設定される環境変数
```bash
# テスト実行時に自動設定される
TESTING=true  # Slack通知無効化フラグ
```

### 必要な環境変数（テスト用）
```bash
# テスト用の環境変数（実際の値は不要）
export PIAPI_KEY="test_key"
export OPENAI_API_KEY="test_key"
export GOOGLE_REFRESH_TOKEN="test_token"
export GOOGLE_CLIENT_ID="test_id"
export GOOGLE_CLIENT_SECRET="test_secret"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/test/test/test"

# ファイルパス設定（テスト用）
export JSONL_PATH="data/type/lofi_type_with_variations.jsonl"
export OPENING_VIDEO_PATH="data/openning/openning.mov"
export AMBIENT_DIR="data/ambient"
export CLIENT_SECRETS_PATH="data/json/client_secrets.json"
export POST_DETAIL_PATH="data/post_data/post_detail.txt"
```

### テスト用依存関係
```bash
# requirements-test.txt に含まれるもの
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-asyncio>=0.21.0
coverage>=7.0.0
responses>=0.23.0
httpx>=0.24.0
pydub>=0.25.1
```

---

## 📊 テスト結果の解釈

### 成功パターン
```
=== TM-beat-studio 単体テスト実行 ===
発見されたテストファイル数: 5

読み込み中: test_auto_lofi_post
読み込み中: test_combine_audio
読み込み中: test_create_metadata
読み込み中: test_piapi_music_generation
読み込み中: test_upload_to_youtube

=== テスト実行結果 ===
実行されたテスト数: 54
失敗: 0
エラー: 0
スキップ: 0

✅ 全てのテストが成功しました！
```

### Slack通知のテスト出力例
```
[TEST] Slack通知: 📝 プロンプト選択完了
[TEST] Slack通知: 🎵 新規音楽生成が完了しました
[TEST] Slack通知: 🖼️ サムネイル生成が完了しました
[TEST] Slack通知: 🎧 音楽結合が完了しました
[TEST] Slack通知: 📋 メタデータ生成が完了しました
[TEST] Slack通知: 🎥 動画生成が完了しました
[TEST] Slack通知: 📤 YouTubeへのアップロードが完了しました
```

### 失敗時の対処法

1. **インポートエラー**
   - `PYTHONPATH`の設定確認
   - `src/auto_post/__init__.py`の存在確認
   - 循環インポートの確認（`config.py`の分離により解決済み）

2. **モックエラー**
   - モックパスの確認（`auto_post.module.function`）
   - 依存関係のインストール確認

3. **ファイル操作エラー**
   - 一時ディレクトリの権限確認
   - テストファイルのクリーンアップ確認

4. **Slack通知エラー**
   - `TESTING=true`環境変数の確認
   - テスト環境での通知無効化機能の確認

---

## 🚀 継続的インテグレーション

### GitHub Actions設定例
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      TESTING: true  # Slack通知無効化
      PIAPI_KEY: "test_key"
      OPENAI_API_KEY: "test_key"
      GOOGLE_REFRESH_TOKEN: "test_token"
      GOOGLE_CLIENT_ID: "test_id"
      GOOGLE_CLIENT_SECRET: "test_secret"
      SLACK_WEBHOOK_URL: "https://hooks.slack.com/services/test/test/test"
      JSONL_PATH: "data/type/lofi_type_with_variations.jsonl"
      OPENING_VIDEO_PATH: "data/openning/openning.mov"
      AMBIENT_DIR: "data/ambient"
      CLIENT_SECRETS_PATH: "data/json/client_secrets.json"
      POST_DETAIL_PATH: "data/post_data/post_detail.txt"
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          python tests/run_tests.py
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📈 テスト改善計画

### 短期目標
- [x] テストカバレッジ90%以上達成
- [x] Slack通知の自動無効化機能実装
- [x] 統合テストの追加
- [x] 循環インポート問題の解決（`config.py`の分離）
- [ ] パフォーマンステストの実装

### 中期目標
- [ ] E2Eテストの実装
- [ ] セキュリティテストの追加
- [ ] 自動テスト実行の定期化

### 長期目標
- [ ] テスト自動化パイプラインの構築
- [ ] テスト結果の可視化ダッシュボード
- [ ] テスト駆動開発の導入

---

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. Slack通知がテスト中に送信される
**問題**: テスト実行時に実際のSlackに通知が送信される
**解決**: `TESTING=true`環境変数が正しく設定されているか確認

#### 2. テストが遅い
**問題**: テスト実行に時間がかかる
**解決**: 
- モックの適切な使用確認
- 不要なファイル操作の削減
- 並列テスト実行の検討

#### 3. テストが不安定
**問題**: 時々テストが失敗する
**解決**:
- テストの独立性確認
- 一時ファイルの適切なクリーンアップ
- 非同期処理の適切なモック

#### 4. インポートエラー
**問題**: モジュールが見つからない
**解決**:
- `src/auto_post/__init__.py`の存在確認
- `PYTHONPATH`の設定確認
- 相対インポートの確認
- 循環インポートの確認（`config.py`の分離により解決済み）
