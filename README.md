# TM Beat Studio

Lo-Fi音楽の自動生成とYouTube投稿を行うPythonアプリケーション

## 📋 概要

TM Beat Studioは、LoFiヒップホップや勉強用BGMなどの長尺音楽動画を自動生成し、YouTubeにアップロードするためのツールです。

### ✅ 動作確認済み環境
- **OS**: macOS 14.6.0 (Darwin 24.6.0)
- **Python**: 3.10.17
- **パッケージマネージャー**: UV
- **シェル**: zsh (/bin/zsh)
- **アーキテクチャ**: Apple Silicon (ARM64)

### 🎯 主な機能
- **自動音楽生成**: PiAPIを使用したLo-Fi音楽の自動生成
- **サムネイル生成**: Stable Diffusionを使用した画像生成
- **動画作成**: 音楽と画像を組み合わせた動画生成
- **YouTube投稿**: 自動的なYouTubeアップロード
- **Slack通知**: 処理状況のリアルタイム通知

## 🚀 クイックスタート

### 1. 環境構築

#### UVのインストール（推奨）
```bash
# UVのインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# PATHの設定（~/.zshrcに追加）
export PATH="$HOME/.local/bin:$PATH"
```

**注意**: 他のOSやPythonバージョンでの動作は未確認です。問題が発生した場合は、動作確認済み環境での実行を推奨します。

#### 仮想環境の作成と依存関係のインストール
```bash
# 仮想環境の作成
uv venv --python 3.10

# 仮想環境のアクティベート
source .venv/bin/activate

# 依存関係のインストール
uv pip install -r requirements.txt
uv pip install -r requirements-test.txt
```

### 2. 環境変数の設定

```bash
# env.exampleをコピーして.envファイルを作成
cp env.example .env

# .envファイルを編集して実際の値を設定
nano .env
```

#### 必須環境変数
```bash
# Slack設定
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR_WORKSPACE/YOUR_CHANNEL/YOUR_TOKEN

# API設定
PIAPI_KEY=your_piapi_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Google OAuth設定
GOOGLE_REFRESH_TOKEN=your_google_refresh_token_here
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# ストックディレクトリ設定
STOCK_AUDIO_BASE_DIR=/path/to/your/music/lofi
STOCK_IMAGE_BASE_DIR=/path/to/your/image
```

#### オプション環境変数
```bash
# ファイルパス設定（デフォルト値で動作）
JSONL_PATH=data/type/lofi_type_with_variations.jsonl
OPENING_VIDEO_PATH=data/openning/openning.mov
AMBIENT_DIR=data/ambient
CLIENT_SECRETS_PATH=data/json/client_secrets.json
POST_DETAIL_PATH=data/post_data/post_detail.txt

# 出力ファイル名設定
COMBINED_AUDIO_FILENAME=combined_audio.mp3
TRACKS_INFO_FILENAME=tracks_info.json
METADATA_FILENAME=metadata.json
FINAL_VIDEO_FILENAME=final_video.mp4
THUMBNAIL_PATTERN=*thumb.png

# サムネイル設定
THUMB_WIDTH=1280
THUMB_HEIGHT=720
LOBSTER_FONT_URL=https://github.com/google/fonts/raw/main/ofl/lobster/Lobster-Regular.ttf
FONT_DIR=data/fonts
LOBSTER_FONT_PATH=data/fonts/Lobster-Regular.ttf
```

### 3. 必要なファイルとディレクトリの準備

#### 環境音ファイルの準備
`data/ambient/` ディレクトリに以下の環境音ファイルを配置してください：

```bash
# 環境音ディレクトリの作成
mkdir -p data/ambient

# 必要な環境音ファイル（MP3形式）
# - rain.mp3      # 雨音
# - cafe.mp3      # カフェの音
# - night.mp3     # 夜の音
# - wave.mp3      # 波の音
# - fire.mp3      # 焚き火の音
# - vinyl.mp3     # レコードの音
# - study.mp3     # 勉強用の音
# - nature.mp3    # 自然の音
# - space.mp3     # 宇宙の音
```

#### オープニング動画の準備
```bash
# オープニング動画ディレクトリの作成
mkdir -p data/openning

# オープニング動画ファイル（MOV形式）
# - data/openning/openning.mov  # 動画の冒頭に使用される3秒間の動画
```

#### 設定ファイルの準備
```bash
# 各種設定ファイルディレクトリの作成
mkdir -p data/type
mkdir -p data/json
mkdir -p data/post_data
mkdir -p data/fonts

# 必要な設定ファイル
# - data/type/lofi_type_with_variations.jsonl  # Lo-Fiタイプ定義
# - data/json/client_secrets.json              # Google OAuth設定
# - data/post_data/post_detail.txt             # 投稿詳細テンプレート
# - data/fonts/Lobster-Regular.ttf             # サムネイル用フォント
```

#### ストックディレクトリの作成
```bash
# ストックディレクトリを作成
mkdir -p "$(grep STOCK_AUDIO_BASE_DIR .env | cut -d'=' -f2)"
mkdir -p "$(grep STOCK_IMAGE_BASE_DIR .env | cut -d'=' -f2)"
```

## 📝 使用方法

### 自動実行（推奨）

```bash
# メインスクリプトの実行
./run_lo_fi.sh
```

このスクリプトは以下を自動実行します：
- 仮想環境のアクティベート
- ログ記録
- 音楽生成からYouTube投稿までの全処理

### 手動実行

```bash
# 仮想環境のアクティベート
source .venv/bin/activate

# メインスクリプトの実行
python -m src.auto_post.auto_lofi_post --output_dir ./output
```

### 定期実行の設定

```bash
# cronに登録（例：2日おきに実行）
crontab -e

# 以下を追加
0 0 */2 * * /path/to/your/TM-beat-studio/run_lo_fi.sh
```

### テスト環境での実行

開発・テスト時は以下の環境変数を設定することでSlack通知をスキップできます：

```bash
export TESTING=true
python -m src.auto_post.auto_lofi_post --output_dir ./test_output
```

## 🧪 テスト実行

```bash
# UV環境でのテスト実行（推奨）
./run_tests_uv.sh

# または直接実行
python tests/run_tests.py

# pytestでの実行
pytest tests/ -v
```

詳細は [tests/README.md](tests/README.md) を参照してください。

## 🔧 個別機能の使用方法

### 音楽生成のみ
```bash
python -m src.auto_post.piapi_music_generation --prompt "melancholic piano" --output_dir ./output
```

### 音声ファイルの結合のみ
```bash
python -m src.auto_post.combine_audio --input_dir ./input --output_dir ./output --ambient ./ambient.mp3
```

### サムネイル作成のみ
```bash
python -m src.auto_post.thumbnail_generation --output_dir ./output --lofi_type "sad" --prompt "melancholic mood"
```

### メタデータ生成のみ
```bash
python -m src.auto_post.create_metadata --output_dir ./output --tracks_json ./tracks_info.json
```

### 動画作成のみ
```bash
python -m src.auto_post.create_video --image ./thumbnail.png --audio ./combined_audio.mp3 --output ./output
```

### YouTubeアップロードのみ
```bash
python -m src.auto_post.upload_to_youtube --video ./final_video.mp4 --title "勉強用BGM" --description "集中できる音楽" --thumbnail ./thumbnail.png
```

## 📁 ディレクトリ構造

```
TM-beat-studio/
├── src/auto_post/                    # メインソースコード
│   ├── auto_lofi_post.py             # メインクラス
│   ├── config.py                     # 設定管理
│   ├── piapi_music_generation.py     # 音楽生成
│   ├── thumbnail_generation.py       # サムネイル生成
│   ├── combine_audio.py              # 音声結合
│   ├── create_metadata.py            # メタデータ生成
│   ├── create_video.py               # 動画作成
│   ├── upload_to_youtube.py          # YouTubeアップロード
│   ├── get_refresh_token.py          # Google OAuth認証
│   └── test_thumbnail_selection.py   # サムネイル選択テスト
├── data/                             # データファイル
│   ├── ambient/                      # 環境音ファイル（要準備）
│   │   ├── rain.mp3                  # 雨音
│   │   ├── cafe.mp3                  # カフェの音
│   │   ├── night.mp3                 # 夜の音
│   │   ├── wave.mp3                  # 波の音
│   │   ├── fire.mp3                  # 焚き火の音
│   │   ├── vinyl.mp3                 # レコードの音
│   │   ├── study.mp3                 # 勉強用の音
│   │   ├── nature.mp3                # 自然の音
│   │   └── space.mp3                 # 宇宙の音
│   ├── openning/                     # オープニング動画（要準備）
│   │   └── openning.mov              # 動画の冒頭用（3秒間）
│   ├── type/                         # Lo-Fiタイプ定義
│   │   ├── lofi_type.jsonl           # 基本タイプ定義
│   │   └── lofi_type_with_variations.jsonl  # バリエーション付き定義
│   ├── json/                         # 設定ファイル
│   │   └── client_secrets.json       # Google OAuth設定
│   ├── post_data/                    # 投稿データ
│   │   └── post_detail.txt           # 投稿詳細テンプレート
│   └── fonts/                        # フォントファイル
│       └── Lobster-Regular.ttf       # サムネイル用フォント
├── tests/                            # テストファイル
│   ├── test_auto_lofi_post.py        # メインクラステスト
│   ├── test_combine_audio.py         # 音声結合テスト
│   ├── test_create_metadata.py       # メタデータ生成テスト
│   ├── test_piapi_music_generation.py # 音楽生成テスト
│   ├── test_upload_to_youtube.py     # YouTubeアップロードテスト
│   └── README.md                     # テストガイド
├── memo/                             # メモファイル
│   └── post_detail.txt               # 投稿詳細（重複）
├── .env                              # 環境変数（要作成）
├── env.example                       # 環境変数テンプレート
├── requirements.txt                  # 依存関係
├── requirements-test.txt             # テスト用依存関係
├── run_lo_fi.sh                     # 自動実行スクリプト
├── run_tests_uv.sh                  # テスト実行スクリプト
└── uv_commands.md                   # UVコマンド集
```

## 🔒 セキュリティ

- `.env`ファイルはGitにコミットされません
- 機密情報は環境変数として管理されます
- 本番環境では適切なシークレット管理を使用してください

## 🚨 トラブルシューティング

### よくあるエラー

#### ModuleNotFoundError: No module named 'src/auto_post/auto_lofi_post'
```bash
# 間違い
python src/auto_post/auto_lofi_post.py

# 正しい
python -m src.auto_post.auto_lofi_post
```

#### ValueError: 必要な環境変数が設定されていません
```bash
# 1. .envファイルを作成
cp env.example .env

# 2. テスト環境で実行（Slack通知をスキップ）
export TESTING=true
python -m src.auto_post.auto_lofi_post

# 3. または.envファイルに必要な設定を追加
```

#### その他のトラブルシューティング
- エラーや不具合が発生した場合は `cron.log` を確認してください
- YouTube API認証時は初回のみブラウザ認証が必要です
- FFmpegやPythonパッケージのインストール状況もご確認ください
- 動作確認済み環境と異なる環境で問題が発生した場合は、環境の違いを確認してください

## 📚 参考資料

- [UV コマンド集](uv_commands.md) - UVの詳細な使い方
- [テストガイド](tests/README.md) - テストの実行方法と詳細

## 🤝 貢献

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesページでお知らせください。 