#!/usr/bin/env python3

import json
import os
import random
import re
from pathlib import Path

import requests
import torch
from diffusers import DiffusionPipeline
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from .config import Config

# Thumbnail resolution for YouTube (16:9, 1280×720)
THUMB_WIDTH = int(os.getenv("THUMB_WIDTH", "1280"))
THUMB_HEIGHT = int(os.getenv("THUMB_HEIGHT", "720"))

# Google Fonts – Lobster Static TTF direct link
LOBSTER_FONT_URL = os.getenv(
    "LOBSTER_FONT_URL",
    "https://github.com/google/fonts/raw/main/ofl/lobster/Lobster-Regular.ttf",
)
FONT_DIR = Path(os.getenv("FONT_DIR", "src/auto_post/fonts"))
FONT_DIR.mkdir(parents=True, exist_ok=True)
LOBSTER_FONT_PATH = Path(
    os.getenv("LOBSTER_FONT_PATH", str(FONT_DIR / "Lobster-Regular.ttf"))
)

# .env 読み込み
load_dotenv()

# 出力ディレクトリ設定
output_dir = "src/auto_post"
os.makedirs(output_dir, exist_ok=True)

# jsonlファイルパス

jsonl_path = Config.JSONL_PATH


def load_random_prompt(jsonl_file):
    with open(jsonl_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        samples = [json.loads(line) for line in lines if line.strip()]
    chosen = random.choice(samples)

    # thumbnail_titleが配列の場合はランダム選択、文字列の場合はそのまま使用
    thumbnail_title = chosen["thumbnail_title"]
    if isinstance(thumbnail_title, list):
        thumbnail_title = random.choice(thumbnail_title)

    return chosen["type"], chosen["image_prompt"], thumbnail_title


def ensure_font() -> str:
    """Lobsterフォントを確保してパスを返す。"""
    if Path(LOBSTER_FONT_PATH).exists():
        return str(LOBSTER_FONT_PATH)

    resp = requests.get(LOBSTER_FONT_URL, timeout=30)
    resp.raise_for_status()
    f = open(str(LOBSTER_FONT_PATH), "wb")
    try:
        f.write(resp.content)
    finally:
        try:
            f.close()
        except Exception:
            pass
    return str(LOBSTER_FONT_PATH)


def create_thumbnail(
    bg_image_path: str,
    title: str,
    output_path: str,
    font_path: str,
    font_size: int = 180,
):
    """
    Overlay `title` onto `bg_image_path` and save to `output_path`.
    """
    img = Image.open(bg_image_path).convert("RGB")
    # slight darken for readability
    img = ImageEnhance.Brightness(img).enhance(0.85)
    img = img.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size)

    # allow "\n" in the string to create new lines
    lines = title.split("\\n")
    # vintage yellow (soft, slightly muted) and grey shadow
    text_color = (240, 214, 105)
    shadow_color = (70, 70, 70)

    line_spacing = int(font_size * 1.1)
    total_h = len(lines) * line_spacing
    y_start = (THUMB_HEIGHT - total_h) // 2
    x_pad = 40

    for i, line in enumerate(lines):
        y = y_start + i * line_spacing
        # shadow (offset 3px)
        draw.text((x_pad + 3, y + 3), line, font=font, fill=shadow_color)
        # main text
        draw.text((x_pad, y), line, font=font, fill=text_color)

    img.save(output_path)
    print(f"==> Saved thumbnail to {output_path}")


def main():
    # デバイス設定
    device = (
        "mps"
        if torch.backends.mps.is_available()
        else "cuda" if torch.cuda.is_available() else "cpu"
    )
    print(f"==> Using device: {device}")

    # ランダムプロンプト選択
    lofi_type, prompt, thumb_title = load_random_prompt(jsonl_path)
    print(f"==> Selected type: {lofi_type}")
    print(f"==> Generating image for prompt: “{prompt}”")

    # モデルロード
    print("==> Loading Stable Diffusion 3.5 Large model...")
    pipe = DiffusionPipeline.from_pretrained(
        "stabilityai/stable-diffusion-3.5-large",
        use_auth_token=os.getenv("HUGGINGFACE_TOKEN"),
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
    ).to(device)

    # 画像生成
    # Generate at YouTube thumbnail resolution
    image = pipe(
        prompt, guidance_scale=7.5, height=THUMB_HEIGHT, width=THUMB_WIDTH
    ).images[0]

    # 保存 ― 余分な文字 ( / \ : * ? " < > | ) などを安全な '_' に置換
    safe_type = re.sub(r"[^0-9A-Za-z_\-]+", "_", lofi_type.lower())
    filename = f"{safe_type}_{THUMB_WIDTH}x{THUMB_HEIGHT}.png"
    out_path = os.path.join(output_dir, filename)
    image.save(out_path)
    print(f"==> Saved image to {out_path}")

    # Create thumbnail with title text
    font_path = ensure_font()
    thumb_name = filename.replace(".png", "_thumb.png")
    thumb_out = os.path.join(output_dir, thumb_name)
    create_thumbnail(
        bg_image_path=out_path,
        title=thumb_title,
        output_path=thumb_out,
        font_path=font_path,
        font_size=180,
    )


def thumbnail_generation(
    output_dir: str, lofi_type: str, prompt: str, thumb_title: str
) -> tuple[str, str]:
    # デバイス設定
    device = (
        "mps"
        if torch.backends.mps.is_available()
        else "cuda" if torch.cuda.is_available() else "cpu"
    )
    print(f"==> Using device: {device}")

    # モデルロード
    print("==> Loading Stable Diffusion 3.5 Large model...")
    pipe = DiffusionPipeline.from_pretrained(
        "stabilityai/stable-diffusion-3.5-large",
        use_auth_token=os.getenv("HUGGINGFACE_TOKEN"),
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
    ).to(device)

    # 画像生成
    # Generate at YouTube thumbnail resolution
    image = pipe(
        prompt, guidance_scale=7.5, height=THUMB_HEIGHT, width=THUMB_WIDTH
    ).images[0]

    import datetime

    # 保存 ― 余分な文字 ( / \ : * ? " < > | ) などを安全な '_' に置換
    safe_type = re.sub(r"[^0-9A-Za-z_\-]+", "_", lofi_type.lower())
    filename = (
        f"{safe_type}_{THUMB_WIDTH}x{THUMB_HEIGHT}_"
        f"{datetime.datetime.now().strftime('%Y%m%d')}.png"
    )
    out_path = os.path.join(output_dir, filename)
    image.save(out_path)
    print(f"==> Saved image to {out_path}")

    # Create thumbnail with title text
    font_path = ensure_font()
    thumb_name = filename.replace(
        ".png", f"_{datetime.datetime.now().strftime('%Y%m%d')}_thumb.png"
    )
    thumb_out = os.path.join(output_dir, thumb_name)
    create_thumbnail(
        bg_image_path=out_path,
        title=thumb_title,
        output_path=thumb_out,
        font_path=font_path,
        font_size=180,
    )

    image_path = os.path.join(output_dir, filename)
    thumbnail_path = os.path.join(output_dir, thumb_name)

    return image_path, thumbnail_path


if __name__ == "__main__":
    main()
