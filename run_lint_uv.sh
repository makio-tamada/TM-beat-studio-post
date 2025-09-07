#!/bin/bash

# uvを使ったLint実行スクリプト
# 使用方法: ./run_lint_uv.sh [check|fix]

set -e

# 色付きの出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔍 uvでLintチェックを開始します...${NC}"

# プロジェクトのルートディレクトリに移動
cd "$(dirname "$0")"

# ソースコードのディレクトリ
SRC_DIR="src"
TESTS_DIR="tests"

# チェックモードか修正モードかを判定
MODE=${1:-check}

if [ "$MODE" = "fix" ]; then
    echo -e "${YELLOW}🔧 コードを自動修正します...${NC}"
    
    # Blackでコードフォーマット
    echo "📝 Blackでコードフォーマット中..."
    uv run black "$SRC_DIR" "$TESTS_DIR"
    
    # isortでimport文を整理
    echo "📦 import文を整理中..."
    uv run isort "$SRC_DIR" "$TESTS_DIR"
    
    echo -e "${GREEN}✅ 自動修正が完了しました！${NC}"
else
    echo -e "${YELLOW}🔍 コードチェックを実行します...${NC}"
    
    # Blackでフォーマットチェック
    echo "📝 Blackでフォーマットチェック中..."
    if ! uv run black --check "$SRC_DIR" "$TESTS_DIR"; then
        echo -e "${RED}❌ Black: フォーマットエラーが見つかりました${NC}"
        echo -e "${YELLOW}💡 修正するには: ./run_lint_uv.sh fix${NC}"
        exit 1
    fi
    
    # isortでimport文チェック
    echo "📦 import文をチェック中..."
    if ! uv run isort --check-only "$SRC_DIR" "$TESTS_DIR"; then
        echo -e "${RED}❌ isort: import文の順序エラーが見つかりました${NC}"
        echo -e "${YELLOW}💡 修正するには: ./run_lint_uv.sh fix${NC}"
        exit 1
    fi
    
    # flake8でコードスタイルチェック
    echo "🔍 flake8でコードスタイルチェック中..."
    if ! uv run flake8 "$SRC_DIR" "$TESTS_DIR"; then
        echo -e "${RED}❌ flake8: コードスタイルエラーが見つかりました${NC}"
        exit 1
    fi
    
    # mypyで型チェック（オプション）
    echo "🔬 mypyで型チェック中..."
    if ! uv run mypy "$SRC_DIR"; then
        echo -e "${RED}❌ mypy: 型エラーが見つかりました${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ すべてのLintチェックが完了しました！${NC}"
fi

echo -e "${GREEN}🎉 Lint処理が完了しました！${NC}"
