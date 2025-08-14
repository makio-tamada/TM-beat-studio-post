#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from diffusers import DiffusionPipeline
import torch
from pathlib import Path
import datetime

# 画像の解像度設定
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024

# .env 読み込み
load_dotenv()

def generate_image(prompt: str, output_dir: str = "src/test/output") -> str:
    """
    プロンプトを入力として画像を生成する関数
    
    Args:
        prompt (str): 画像生成のためのプロンプト
        output_dir (str): 出力ディレクトリのパス
    
    Returns:
        str: 生成された画像のパス
    """
    # 出力ディレクトリの作成
    os.makedirs(output_dir, exist_ok=True)
    
    # デバイス設定
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    print(f"==> Using device: {device}")

    # モデルロード
    print("==> Loading Stable Diffusion 3.5 Large model...")
    pipe = DiffusionPipeline.from_pretrained(
        "stabilityai/stable-diffusion-3.5-large",
        use_auth_token=os.getenv("HUGGINGFACE_TOKEN"),
        torch_dtype=torch.float16 if device != "cpu" else torch.float32
    ).to(device)

    # 画像生成
    print(f"==> Generating image for prompt: \"{prompt}\"")
    image = pipe(
        prompt,
        guidance_scale=7.5,
        height=IMAGE_HEIGHT,
        width=IMAGE_WIDTH
    ).images[0]

    # ファイル名の生成（タイムスタンプ付き）
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"generated_image_{timestamp}.png"
    output_path = os.path.join(output_dir, filename)
    
    # 画像の保存
    image.save(output_path)
    print(f"==> Saved image to {output_path}")
    
    return output_path

def main():
    # テスト用のプロンプト
    test_prompt = "lofi girl anime style, high school girl, study in the room, 35mm film tone, 4k, realistic, high quality, 8k"
    
    # 画像生成
    image_path = generate_image(test_prompt)
    print(f"Generated image saved at: {image_path}")

if __name__ == "__main__":
    main()
