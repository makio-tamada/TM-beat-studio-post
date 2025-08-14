#!/bin/bash

# UVのPATHを追加
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# ログファイルの設定
LOG_FILE="cron.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# ログの開始（前回のログを上書き）
echo "=== 実行開始: $TIMESTAMP ===" > "$LOG_FILE"

# UV仮想環境をアクティベートしてスクリプトを実行
source .venv/bin/activate
python -m src.auto_post.auto_lofi_post >> "$LOG_FILE" 2>&1

# 実行結果の確認
if [ $? -eq 0 ]; then
    echo "実行成功: $TIMESTAMP" >> "$LOG_FILE"
else
    echo "実行失敗: $TIMESTAMP" >> "$LOG_FILE"
fi

echo "=== 実行終了: $TIMESTAMP ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE" 