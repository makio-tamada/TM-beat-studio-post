#!/usr/bin/env python3

import json
import random
from pathlib import Path

def test_thumbnail_selection():
    """thumbnail_titleのランダム選択機能をテストする"""
    
    jsonl_path = "src/auto_post/lofi_type_with_variations.jsonl"
    
    print("=== thumbnail_title ランダム選択テスト ===")
    
    # JSONLファイルを読み込み
    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        samples = [json.loads(line) for line in lines if line.strip()]
    
    print(f"総タイプ数: {len(samples)}")
    print()
    
    # 各タイプでテスト
    for i, sample in enumerate(samples, 1):
        print(f"{i}. タイプ: {sample['type']}")
        
        # thumbnail_titleの処理
        thumbnail_title = sample["thumbnail_title"]
        if isinstance(thumbnail_title, list):
            print(f"   thumbnail_title (配列): {len(thumbnail_title)}個の選択肢")
            print(f"   選択肢:")
            for j, title in enumerate(thumbnail_title, 1):
                print(f"     {j}. {title}")
            
            # ランダム選択を5回テスト
            print(f"   ランダム選択テスト (5回):")
            for k in range(5):
                selected = random.choice(thumbnail_title)
                print(f"     {k+1}. {selected}")
        else:
            print(f"   thumbnail_title (文字列): {thumbnail_title}")
        
        # image_promptsの処理
        if "image_prompts" in sample:
            image_prompts = sample["image_prompts"]
            print(f"   image_prompts (配列): {len(image_prompts)}個の選択肢")
            print(f"   選択肢:")
            for j, prompt in enumerate(image_prompts, 1):
                print(f"     {j}. {prompt[:80]}...")
        elif "image_prompt" in sample:
            print(f"   image_prompt (文字列): {sample['image_prompt'][:80]}...")
        
        print()

if __name__ == "__main__":
    test_thumbnail_selection()
