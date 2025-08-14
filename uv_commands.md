# UV コマンド集

## 基本的な使い方

### 仮想環境の管理
```bash
# 新しい仮想環境を作成
uv venv --python 3.10

# 仮想環境をアクティベート
source .venv/bin/activate

# 仮想環境を非アクティベート
deactivate
```

### パッケージのインストール
```bash
# requirements.txtからインストール
uv pip install -r requirements.txt

# requirements-test.txtからインストール
uv pip install -r requirements-test.txt

# 個別のパッケージをインストール
uv pip install package_name

# 開発用パッケージをインストール
uv pip install --dev package_name
```

### パッケージの管理
```bash
# インストール済みパッケージの一覧表示
uv pip list

# パッケージの更新
uv pip install --upgrade package_name

# パッケージの削除
uv pip uninstall package_name
```

## プロジェクト固有のコマンド

### テストの実行
```bash
# テストスクリプトを使用
./run_tests_uv.sh

# 直接実行
python tests/run_tests.py

# pytestで実行
pytest tests/
```

### メインスクリプトの実行
```bash
# Lo-Fi生成スクリプト
./run_lo_fi.sh

# 直接実行
python src/auto_post/auto_lofi_post.py
```

## 便利な設定

### PATHの設定（~/.zshrcに追加）
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### エイリアスの設定（~/.zshrcに追加）
```bash
alias uv-activate="source .venv/bin/activate"
alias uv-test="./run_tests_uv.sh"
alias uv-run="./run_lo_fi.sh"
```

## トラブルシューティング

### UVが見つからない場合
```bash
# PATHを確認
echo $PATH

# UVを再インストール
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 仮想環境の問題
```bash
# 仮想環境を削除して再作成
rm -rf .venv
uv venv --python 3.10
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -r requirements-test.txt
```

## パフォーマンス比較

### インストール速度（参考）
- **pip**: 約60秒（torch等の重いパッケージ含む）
- **uv**: 約8秒（同じパッケージセット）

### メモリ使用量
- **pip**: 高（キャッシュを多用）
- **uv**: 低（効率的なキャッシュ管理）
