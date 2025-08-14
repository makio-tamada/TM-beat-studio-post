#!/usr/bin/env python3
"""
TM-beat-studio 単体テスト実行スクリプト
"""

import os
import sys
import unittest
from pathlib import Path

# テスト環境を設定
os.environ['TESTING'] = 'true'

# プロジェクトルートをパスに追加
project_root = Path(__file__).resolve().parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def run_tests():
    """テストを実行"""
    print("=== TM-beat-studio 単体テスト実行 ===")
    
    # テストディレクトリ
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob("test_*.py"))
    
    print(f"発見されたテストファイル数: {len(test_files)}")
    print()
    
    # 各テストファイルを読み込み
    for test_file in test_files:
        module_name = test_file.stem
        print(f"読み込み中: {module_name}")
    
    print()
    
    # テストを実行
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果を表示
    print("\n" + "="*70)
    print("=== テスト実行結果 ===")
    print(f"実行されたテスト数: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print(f"スキップ: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n=== 失敗したテスト ===")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\n=== エラーが発生したテスト ===")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ 全てのテストが成功しました！")
    else:
        print("\n❌ 一部のテストが失敗しました。")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
