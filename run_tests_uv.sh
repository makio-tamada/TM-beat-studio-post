#!/bin/bash

# UVでテストを実行するスクリプト
export PATH="$HOME/.local/bin:$PATH"

echo "=== UVでテストを実行 ==="
echo "仮想環境をアクティベート中..."
source .venv/bin/activate

echo "テストを実行中..."
python tests/run_tests.py

echo "=== テスト完了 ==="
