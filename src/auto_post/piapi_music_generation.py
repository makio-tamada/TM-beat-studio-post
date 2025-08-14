"""
Generate and download instrumental lo‑fi music via PiAPI Song API (music‑u model).

How it works
------------
1. Create a task (POST https://api.piapi.ai/api/v1/task) with:
   - model: "music-u"
   - task_type: "generate_music"
   - input:  gpt_description_prompt, lyrics_type="instrumental"
2. Poll the task endpoint (GET https://api.piapi.ai/api/v1/task/{task_id})
   until status == "Completed".
3. Download the first audio file in output and save locally.

Environment
-----------
- Requires `requests` (pip install requests)
- Set the environment variable PIAPI_KEY *or* edit API_KEY below.
"""

import os
import time
import requests
from typing import Optional
import json
import random
from datetime import datetime
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
API_KEY = os.getenv("PIAPI_KEY", "51584de2f56859948cdcf6a6f950534d00399c47d60cd45c1d69b049cc9d13cb")  # ← ここにAPIキーを設定するか環境変数で渡す

BASE_URL = "https://api.piapi.ai/api/v1"
CREATE_ENDPOINT = f"{BASE_URL}/task"
GET_ENDPOINT = f"{BASE_URL}/task/{{task_id}}"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json",
}

POLL_INTERVAL = 8          # seconds between polls
POLL_TIMEOUT = 600         # allow up to 10 minutes for long queues

# New config
TARGET_DURATION_SEC = 600             # total length to generate (e.g. 10 min)
from .config import Config
LOFI_TYPES_JSONL = Config.JSONL_PATH

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-3.5-turbo"  # You can change to "gpt-4" if needed

# ------------------------------------------------------------------
# Filename and prompt helpers
# ------------------------------------------------------------------
def get_existing_filenames(directory: str) -> set:
    """
    指定されたディレクトリ内の既存のファイル名を取得する
    
    Args:
        directory (str): ディレクトリのパス
        
    Returns:
        set: 既存のファイル名（拡張子なし）のセット
    """
    existing_files = set()
    for file in os.listdir(directory):
        if file.endswith('.mp3'):
            # 拡張子を除いたファイル名を追加
            existing_files.add(os.path.splitext(file)[0])
    return existing_files

def generate_unique_filename(title: str, directory: str, prompt: str, max_attempts: int = 3) -> str:
    """
    重複しないファイル名を生成する
    
    Args:
        title (str): 元の曲名
        directory (str): 保存先ディレクトリ
        prompt (str): 音楽のプロンプト
        max_attempts (int): 最大再生成回数
        
    Returns:
        str: 重複しないファイル名
    """
    # 基本のファイル名を生成
    base_name = re.sub(r'[^0-9A-Za-z_\- ]+', '', title).strip().replace(" ", "_")
    if not base_name:
        base_name = 'track'
    
    # 既存のファイル名を取得
    existing_files = get_existing_filenames(directory)
    
    # 重複がない場合はそのまま返す
    if base_name not in existing_files:
        return f"{base_name}.mp3"
    
    # 重複がある場合は再生成を試みる
    for attempt in range(max_attempts):
        print(f"Warning: Title '{base_name}' already exists. Attempt {attempt + 1}/{max_attempts}")
        # 新しい曲名を生成（既存のファイル名を考慮）
        new_title = fetch_track_title(prompt, directory)
        new_base_name = re.sub(r'[^0-9A-Za-z_\- ]+', '', new_title).strip().replace(" ", "_")
        if not new_base_name:
            new_base_name = 'track'
        
        if new_base_name not in existing_files:
            return f"{new_base_name}.mp3"
    
    # 最大試行回数を超えた場合、番号を付与
    counter = 1
    while f"{base_name}_{counter}" in existing_files:
        counter += 1
    
    return f"{base_name}_{counter}.mp3"

def choose_random_prompt() -> dict:
    """Load lofi_type.jsonl and return a random record."""
    with open(LOFI_TYPES_JSONL, "r", encoding="utf‑8") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    return random.choice(lines)

def fetch_track_title(prompt: str, directory: str = None) -> str:
    """
    Ask OpenAI API for a catchy track title.
    Falls back to 'Untitled' on any error.
    
    Args:
        prompt (str): 音楽のプロンプト
        directory (str, optional): 既存のファイル名を取得するディレクトリ
    """
    try:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # 既存のファイル名を取得
        existing_titles = set()
        if directory:
            existing_titles = get_existing_filenames(directory)
        
        # 既存のタイトルをプロンプトに含める
        existing_titles_text = ""
        if existing_titles:
            existing_titles_text = "\n- Avoid these existing titles:\n  * " + "\n  * ".join(sorted(existing_titles)[:10])  # 最大10個まで表示
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a creative assistant that writes unique and memorable lo‑fi hip‑hop track titles.\n"
                        "Focus on creating diverse titles that reflect the mood and atmosphere of the track.\n"
                        "Avoid repetitive patterns and common phrases.\n"
                        "Return ONLY the title, nothing else."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Create a unique, memorable title (2-4 words) for a lo‑fi hip‑hop track.\n"
                        f"Track description: '{prompt}'\n"
                        "Requirements:\n"
                        "- Return ONLY the title\n"
                        "- 2-4 words maximum\n"
                        "- No special characters or symbols\n"
                        "- No explanatory text\n"
                        "- Make it creative and unique\n"
                        "- Avoid common phrases like 'lofi', 'beats', 'study', 'relax'\n"
                        "- Focus on the mood and atmosphere\n"
                        "- Examples for rainy style:\n"
                        "  * 'Window Reflections'\n"
                        "  * 'Drizzle Dreams'\n"
                        "  * 'Stormy Night'\n"
                        "  * 'Raindrop Melody'\n"
                        "  * 'Misty Window'\n"
                        "  * 'Cloudy Afternoon'\n"
                        "- Examples for cozy style:\n"
                        "  * 'Coffee Shop'\n"
                        "  * 'Warm Blanket'\n"
                        "  * 'Cozy Corner'\n"
                        "  * 'Tea Time'\n"
                        "  * 'Reading Nook'\n"
                        "  * 'Fireplace'\n"
                        f"{existing_titles_text}\n"
                        "Title:"
                    )
                }
            ],
            "max_tokens": 16,
            "temperature": 0.9
        }
        
        resp = requests.post(OPENAI_API_URL, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        
        data = resp.json()
        if "choices" in data and data["choices"]:
            title = data["choices"][0]["message"]["content"].strip()
        else:
            raise ValueError("Unexpected response format from OpenAI API")
        
        # タイトルのクリーンアップ
        title = title.replace("Title:", "").strip()
        title = title.strip('"\'')
        # 特殊文字を削除
        title = ''.join(c for c in title if c.isalnum() or c.isspace() or c == '-')
        # 複数のスペースを1つに
        title = re.sub(r'\s+', ' ', title)
        return title.strip() or "Untitled"
    except Exception as e:
        print(f"⚠️  OpenAI title generation failed: {e}")
        return "Untitled"


# ------------------------------------------------------------------
# API helpers
# ------------------------------------------------------------------
def create_music_task(prompt: str) -> str:
    """Submit a generate_music task and return task_id."""
    body = {
        "model": "music-u",
        "task_type": "generate_music",
        "input": {
            "gpt_description_prompt": prompt,
            "lyrics_type": "instrumental",
            "negative_tags": "",
            "seed": -1,
        },
        "config": {
            "service_mode": "public"
        },
    }
    resp = requests.post(CREATE_ENDPOINT, headers=HEADERS, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json().get("data") or resp.json()  # unified schema wraps inside "data"
    task_id = data.get("task_id")
    if not task_id:
        raise RuntimeError(f"task_id not found in response: {resp.text}")
    return task_id


def wait_for_task(task_id: str, timeout: int = POLL_TIMEOUT) -> dict:
    """Poll the task until completion and return the full task data."""
    url = GET_ENDPOINT.format(task_id=task_id)
    start = time.time()

    while True:
        resp = requests.get(url, headers={"x-api-key": API_KEY}, timeout=60)
        resp.raise_for_status()
        task_data = resp.json().get("data") or resp.json()

        status = (task_data.get("status") or "").lower()
        if status == "completed":
            return task_data
        if status in ("failed", "error"):
            raise RuntimeError(f"Task failed: {task_data.get('error')}")
        if time.time() - start > timeout:
            raise TimeoutError(f"Task did not complete within {timeout} minutes")

        print("⏳ Generating… waiting", flush=True)
        time.sleep(POLL_INTERVAL)


def extract_audio_url(task_data: dict) -> Optional[str]:
    """Attempt to locate the audio URL inside task output."""
    output = task_data.get("output", {})
    # Common field names observed
    if isinstance(output, dict):
        if "audio_url" in output:
            return output["audio_url"]
        if "audio_urls" in output and output["audio_urls"]:
            return output["audio_urls"][0]
        if "files" in output:  # sometimes a list of file objects
            files = output["files"]
            if files and isinstance(files, list):
                # pick first file with .wav or .mp3 extension
                for f in files:
                    url = f.get("url") or f
                    if isinstance(url, str) and url.startswith("http"):
                        return url
        # PiAPI Song API returns a list under "songs"
        if "songs" in output and output["songs"]:
            first_song = output["songs"][0]
            if isinstance(first_song, dict) and first_song.get("song_path"):
                return first_song["song_path"]
    return None


def download_audio(url: str, save_path: str) -> None:
    """Download the audio file."""
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main() -> None:
    if API_KEY == "YOUR_API_KEY_HERE":
        raise SystemExit("Please set API_KEY or PIAPI_KEY env var.")

    # Prepare dated folder
    today_folder = datetime.now().strftime("%Y%m%d")
    os.makedirs(today_folder, exist_ok=True)

    total_duration = 0.0
    iteration = 1
    record = choose_random_prompt()
    prompt = record["music_prompt"]

    while total_duration < TARGET_DURATION_SEC:
        print(f"\n=== Iteration {iteration} | Accumulated {total_duration:.1f}s ===")
        print(f"🎼 Creating task with prompt: {prompt!r}")

        task_id = create_music_task(prompt)
        print(f"🆔 Task ID: {task_id}")

        print("🚀 Waiting for completion…")
        task_data = wait_for_task(task_id)
        print("✅ Task completed!")

        audio_url = extract_audio_url(task_data)
        duration = task_data.get("output", {}).get("songs", [{}])[0].get("duration", 0)
        if not audio_url:
            print("❌ Audio URL not found, skipping.")
            continue

        # Get title via OpenAI
        title = fetch_track_title(prompt, today_folder)
        filename = generate_unique_filename(title, today_folder, prompt)
        save_path = os.path.join(today_folder, filename)

        print(f"🎧 {os.path.splitext(filename)[0]} ({duration:.1f}s)  ⬇️ {audio_url}")
        download_audio(audio_url, save_path)
        print(f"📁 Saved to {save_path}")

        total_duration += float(duration or 0)
        iteration += 1

    print(f"\n🎉 Generation finished. Total length: {total_duration/60:.1f} minutes")

def piapi_music_generation(today_folder: str, prompt: str, target_duration_sec: int) -> None:
    if API_KEY == "YOUR_API_KEY_HERE":
        raise SystemExit("Please set API_KEY or PIAPI_KEY env var.")

    # 出力ディレクトリの作成
    os.makedirs(today_folder, exist_ok=True)

    total_duration = 0.0
    iteration = 1

    while total_duration < target_duration_sec:
        print(f"\n=== Iteration {iteration} | Accumulated {total_duration:.1f}s ===")
        print(f"🎼 Creating task with prompt: {prompt!r}")

        max_retries = 3
        retry_count = 0
        success = False

        while not success and retry_count < max_retries:
            try:
                task_id = create_music_task(prompt)
                print(f"🆔 Task ID: {task_id}")

                print("🚀 Waiting for completion…")
                task_data = wait_for_task(task_id)
                print("✅ Task completed!")

                audio_url = extract_audio_url(task_data)
                duration = task_data.get("output", {}).get("songs", [{}])[0].get("duration", 0)
                if not audio_url:
                    raise ValueError("Audio URL not found")

                # Get title via OpenAI
                title = fetch_track_title(prompt, today_folder)
                filename = generate_unique_filename(title, today_folder, prompt)
                save_path = os.path.join(today_folder, filename)

                print(f"🎧 {os.path.splitext(filename)[0]} ({duration:.1f}s)  ⬇️ {audio_url}")
                download_audio(audio_url, save_path)
                print(f"📁 Saved to {save_path}")

                total_duration += float(duration or 0)
                success = True

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"❌ Error occurred: {str(e)}")
                    print(f"🔄 Retrying in 3 minutes... (Attempt {retry_count + 1}/{max_retries})")
                    time.sleep(180)  # 3分待機
                else:
                    print(f"❌ Failed after {max_retries} attempts. Moving to next iteration.")
                    break

        if not success:
            continue

        iteration += 1

    print(f"\n🎉 Generation finished. Total length: {total_duration/60:.1f} minutes")

if __name__ == "__main__":
    main()