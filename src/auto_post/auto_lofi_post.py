"""
Lo-Fi音楽の自動生成とYouTube投稿を行うメインモジュール.

このモジュールは以下の機能を提供します：
- Lo-Fi音楽の自動生成
- サムネイル画像の生成
- 動画の作成
- YouTubeへの自動投稿
- Slack通知
"""

import argparse
import json
import os
import random
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from pydub import AudioSegment

from .combine_audio import combine_audio
from .config import Config
from .create_metadata import create_metadata
from .create_video import create_video
from .piapi_music_generation import piapi_music_generation
from .thumbnail_generation import thumbnail_generation
from .upload_to_youtube import upload_video_to_youtube

# .envファイルを読み込み
load_dotenv()


class LofiPostGenerator:
    """Lo-Fi投稿生成を管理するクラス."""

    def __init__(self, args: argparse.Namespace):
        """AutoLoFiPostクラスの初期化.

        Args:
            args: コマンドライン引数
        """
        # 設定の妥当性を検証
        Config.validate_config()

        self.args = args
        self.output_dir = Path(args.output_dir)
        self.success_music_gen = True
        self.selected_prompt: Dict[str, Any] = {}
        self.selected_image_prompt: str = ""  # 選択されたimage_promptを保持
        self.newly_generated_files: List[Path] = (
            []
        )  # 新規生成したファイルのリストを保持

    def setup(self) -> None:
        """初期設定を行う"""
        start_time = time.time()
        print("==> 初期設定を開始します...")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.send_slack_notification(
            f"🚀 Lo-Fi音楽生成処理を開始します\n日付: {self.args.output_dir}"
        )

        elapsed_time = time.time() - start_time
        print(f"==> 初期設定完了 (処理時間: {elapsed_time:.2f}秒)")

    def send_slack_notification(self, message: str, is_error: bool = False) -> None:
        """Slackに通知を送信"""
        # テスト環境ではSlack通知をスキップ
        if os.getenv("TESTING") == "true":
            print(f"[TEST] Slack通知: {message}")
            return

        try:
            payload = {
                "text": message,
                "username": "TM-beat-studio",
                "icon_emoji": ":robot_face:",
            }

            if is_error:
                payload["text"] = f"❌ {message}"

            response = requests.post(Config.SLACK_WEBHOOK_URL, json=payload, timeout=10)
            response.raise_for_status()

        except Exception as e:
            print(f"==> Slack通知の送信に失敗しました: {e}")

    def _extract_type_from_thumbnail(self) -> str:
        """サムネイルファイル名からLo-Fiタイプを抽出"""
        start_time = time.time()
        print("==> サムネイルからLo-Fiタイプを抽出中...")

        thumbnail = self._find_latest_file(Config.THUMBNAIL_PATTERN)
        if not thumbnail:
            error_msg = "サムネイルファイルが見つかりません"
            self.send_slack_notification(error_msg, is_error=True)
            print(f"==> {error_msg}")
            sys.exit(1)

        # ファイル名から最初の_までの部分を取得
        type_name = thumbnail.stem.split("_")[0]
        print(f"==> サムネイルからLo-Fiタイプを抽出: {type_name}")

        elapsed_time = time.time() - start_time
        print(f"==> Lo-Fiタイプ抽出完了 (処理時間: {elapsed_time:.2f}秒)")
        return type_name

    def select_prompt(self) -> None:
        """プロンプトを選択する"""
        start_time = time.time()
        print("==> プロンプト選択を開始します...")

        try:
            if self.args.skip_type_selection:
                print("==> Lo-Fiタイプの選択をスキップします")
                lofi_type = self._extract_type_from_thumbnail()

                # 抽出したタイプに対応するプロンプトを探す（sadが含まれているかで判断）
                jsonl_path = self.args.jsonl_path or Config.JSONL_PATH
                with open(jsonl_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    samples = [json.loads(line) for line in lines if line.strip()]
                    selected = next(
                        (
                            sample
                            for sample in samples
                            if "sad" in sample["type"].lower()
                        ),
                        None,
                    )

                    if not selected:
                        error_msg = f"抽出したタイプ '{lofi_type}' に対応するプロンプトが見つかりません"
                        self.send_slack_notification(error_msg, is_error=True)
                        print(f"==> {error_msg}")
                        sys.exit(1)

                    self.selected_prompt = selected

                    # thumbnail_titleが配列の場合はランダム選択
                    if isinstance(self.selected_prompt["thumbnail_title"], list):
                        self.selected_prompt["thumbnail_title"] = random.choice(
                            self.selected_prompt["thumbnail_title"]
                        )

                    # image_promptsから1つをランダム選択
                    if "image_prompts" in selected and selected["image_prompts"]:
                        self.selected_image_prompt = random.choice(
                            selected["image_prompts"]
                        )
                    else:
                        # 後方互換性のため、image_promptも確認
                        self.selected_image_prompt = selected.get("image_prompt", "")
            elif self.args.lofi_type:
                self._select_specific_prompt()
            else:
                self._select_random_prompt()

            self._print_selected_prompt()
            self.send_slack_notification(
                f"📝 プロンプト選択完了\nタイプ: {self.selected_prompt['type']}\n"
                f"音楽プロンプト: {self.selected_prompt['music_prompt']}"
            )

            elapsed_time = time.time() - start_time
            print(f"==> プロンプト選択完了 (処理時間: {elapsed_time:.2f}秒)")

        except Exception as e:
            error_msg = f"プロンプトの読み込み中にエラーが発生しました: {e}"
            self.send_slack_notification(error_msg, is_error=True)
            print(f"==> {error_msg}")
            sys.exit(1)

    def _select_specific_prompt(self) -> None:
        """指定されたタイプのプロンプトを選択"""
        jsonl_path = self.args.jsonl_path or Config.JSONL_PATH
        with open(jsonl_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            samples = [json.loads(line) for line in lines if line.strip()]
            selected = next(
                (
                    sample
                    for sample in samples
                    if sample["type"].lower() == self.args.lofi_type.lower()
                ),
                None,
            )

            if not selected:
                raise ValueError(
                    f"指定されたタイプ '{self.args.lofi_type}' が見つかりません"
                )

            self.selected_prompt = selected

            # thumbnail_titleが配列の場合はランダム選択
            if isinstance(self.selected_prompt["thumbnail_title"], list):
                self.selected_prompt["thumbnail_title"] = random.choice(
                    self.selected_prompt["thumbnail_title"]
                )

            # image_promptsから1つをランダム選択
            if "image_prompts" in selected and selected["image_prompts"]:
                self.selected_image_prompt = random.choice(selected["image_prompts"])
            else:
                # 後方互換性のため、image_promptも確認
                self.selected_image_prompt = selected.get("image_prompt", "")

    def _select_random_prompt(self) -> None:
        """ランダムにプロンプトを選択"""
        jsonl_path = self.args.jsonl_path or Config.JSONL_PATH
        with open(jsonl_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            samples = [json.loads(line) for line in lines if line.strip()]
            self.selected_prompt = random.choice(samples)

            # thumbnail_titleが配列の場合はランダム選択
            if isinstance(self.selected_prompt["thumbnail_title"], list):
                self.selected_prompt["thumbnail_title"] = random.choice(
                    self.selected_prompt["thumbnail_title"]
                )

            # image_promptsから1つをランダム選択
            if (
                "image_prompts" in self.selected_prompt
                and self.selected_prompt["image_prompts"]
            ):
                self.selected_image_prompt = random.choice(
                    self.selected_prompt["image_prompts"]
                )
            else:
                # 後方互換性のため、image_promptも確認
                self.selected_image_prompt = self.selected_prompt.get(
                    "image_prompt", ""
                )

    def _print_selected_prompt(self) -> None:
        """選択されたプロンプトを表示"""
        print(f"==> Selected type: {self.selected_prompt['type']}")
        print(
            f'==> Generating music for prompt: "{self.selected_prompt["music_prompt"]}"'
        )
        print(
            f"==> Generating thumbnail for prompt: "
            f'"{self.selected_prompt["thumbnail_title"]}"'
        )
        print(f'==> Generating image for prompt: "{self.selected_image_prompt}"')
        print(f'==> Using ambient: "{self.selected_prompt["ambient"]}"')

    def generate_music(self) -> None:
        """音楽を生成する"""
        start_time = time.time()
        print("\n=== 音楽生成 ===")
        if self.args.skip_music_gen:
            print("==> 音楽生成をスキップします")
            elapsed_time = time.time() - start_time
            print(f"==> 音楽生成スキップ完了 (処理時間: {elapsed_time:.2f}秒)")
            return

        # 目標時間の半分を新規生成、残りをストックから取得
        target_duration_new = self.args.target_duration_sec // 2
        target_duration_stock = self.args.target_duration_sec - target_duration_new

        print(f"==> 新規生成目標時間: {target_duration_new}秒")
        print(f"==> ストック使用目標時間: {target_duration_stock}秒")

        # 新規生成を試みる
        try:
            piapi_music_generation(
                today_folder=self.args.output_dir,
                prompt=self.selected_prompt["music_prompt"],
                target_duration_sec=target_duration_new,
            )
            # 新規生成したファイルを記録
            self.newly_generated_files = list(self.output_dir.glob("*.mp3"))
            self.send_slack_notification("🎵 新規音楽生成が完了しました")
        except Exception as e:
            self.success_music_gen = False
            error_msg = f"新規音楽生成中にエラーが発生しました: {e}"
            self.send_slack_notification(error_msg, is_error=True)
            print(f"==> {error_msg}")
            # エラー時は残りの時間分をストックから取得
            target_duration_stock = self.args.target_duration_sec

        # ストックから音楽を取得
        if target_duration_stock > 0:
            print("\n=== ストック音楽の取得 ===")
            print(f"==> 目標時間: {target_duration_stock}秒")
            self._use_stock_music(target_duration_stock)

        elapsed_time = time.time() - start_time
        print(f"==> 音楽生成完了 (処理時間: {elapsed_time:.2f}秒)")

    def _use_stock_music(self, target_duration: int) -> None:
        """ストック音楽を使用"""
        stock_audio_dir = Config.STOCK_AUDIO_BASE_DIR / self.selected_prompt["type"]
        stock_audio_dir.mkdir(parents=True, exist_ok=True)

        self._copy_existing_music_to_stock(stock_audio_dir)
        self._load_music_from_stock(stock_audio_dir, target_duration)

    def _copy_existing_music_to_stock(self, stock_audio_dir: Path) -> None:
        """既存の音楽ファイルをストックにコピー"""
        existing_music_files = list(self.output_dir.glob("*.mp3"))
        if existing_music_files:
            print("==> 既存の音楽ファイルをストックにコピーします")
            for file in existing_music_files:
                self._copy_file_to_stock(file, stock_audio_dir)

    def _copy_file_to_stock(self, file: Path, stock_dir: Path) -> None:
        """ファイルをストックにコピー"""
        base_name = file.stem
        extension = file.suffix
        counter = 1
        new_file_path = stock_dir / f"{base_name}{extension}"

        while new_file_path.exists():
            new_file_path = stock_dir / f"{base_name}_{counter}{extension}"
            counter += 1

        shutil.copy(file, new_file_path)
        print(f"==> ストックにコピーしました: {file.name}")

    def _load_music_from_stock(
        self, stock_audio_dir: Path, target_duration: int
    ) -> None:
        """ストックから音楽を読み込む"""
        print("==> 音楽ストックから音楽を読み込みます")

        stock_files = list(stock_audio_dir.glob("*.mp3"))
        if not stock_files:
            error_msg = f"ストックに音楽ファイルが見つかりません: {stock_audio_dir}"
            self.send_slack_notification(error_msg, is_error=True)
            print(f"==> {error_msg}")
            sys.exit(1)

        selected_files = self._select_music_files(stock_files, target_duration)
        self._copy_selected_files_to_output(selected_files)

    def _select_music_files(
        self, stock_files: List[Path], target_duration: int
    ) -> List[Path]:
        """音楽ファイルを選択（改善版：より正確に目標時間に近づける）"""
        music_files_with_duration = [
            (file, len(AudioSegment.from_mp3(file)) / 1000) for file in stock_files
        ]

        selected_files = []
        total_duration = 0
        max_attempts = len(music_files_with_duration) * 3  # 無限ループ防止
        attempts = 0

        # 目標時間の95%以上を目指す（より厳密に）
        min_target = target_duration * 0.95

        while (
            total_duration < min_target
            and music_files_with_duration
            and attempts < max_attempts
        ):
            attempts += 1

            # 残り時間を計算
            remaining_time = target_duration - total_duration

            # 残り時間に最も適したファイルを選択（より厳密に）
            suitable_files = [
                (file, duration)
                for file, duration in music_files_with_duration
                if duration <= remaining_time * 1.2  # 1.2倍まで許容（より厳密に）
            ]

            if suitable_files:
                # 適したファイルからランダム選択
                file, duration = random.choice(suitable_files)
            else:
                # 適したファイルがない場合は最短のファイルを選択
                file, duration = min(music_files_with_duration, key=lambda x: x[1])

            selected_files.append(file)
            total_duration += duration
            music_files_with_duration.remove((file, duration))

        if not selected_files:
            raise ValueError("適切な長さの曲を組み合わせることができませんでした")

        print(
            f"==> 選択完了: 目標 {target_duration}秒 → "
            f"実際 {total_duration:.1f}秒 ({total_duration/60:.1f}分)"
        )
        print(f"==> 目標達成率: {(total_duration/target_duration)*100:.1f}%")
        return selected_files

    def _copy_selected_files_to_output(self, selected_files: List[Path]) -> None:
        """選択したファイルを出力ディレクトリにコピー"""
        total_duration = 0
        existing_files = set()

        for file in selected_files:
            # 元のファイル名を取得
            original_name = file.stem
            extension = file.suffix

            # 重複を避けるためのファイル名を生成
            counter = 1
            new_name = original_name
            while new_name in existing_files:
                new_name = f"{original_name}_{counter}"
                counter += 1

            # ファイルをコピー
            output_file = self.output_dir / f"{new_name}{extension}"
            shutil.copy(file, output_file)
            existing_files.add(new_name)

            # 再生時間を計算
            audio = AudioSegment.from_mp3(file)
            duration = len(audio) / 1000
            total_duration += duration

            print(
                f"==> ストックから音楽をコピーしました: {new_name} (長さ: {duration:.1f}秒)"
            )

        print(f"==> 合計長さ: {total_duration:.1f}秒")
        self.send_slack_notification(
            f"🎵 ストックから音楽を読み込みました\n合計長さ: {total_duration:.1f}秒"
        )

    def _find_latest_file(self, pattern: str) -> Optional[Path]:
        """指定されたパターンに一致する最新のファイルを探す"""
        print(f"==> ファイル検索パターン: {pattern}")
        print(f"==> 検索ディレクトリ: {self.output_dir}")

        files = list(self.output_dir.glob(pattern))
        print(f"==> 見つかったファイル: {[f.name for f in files]}")

        if not files:
            return None
        return max(files, key=lambda x: x.stat().st_mtime)

    def combine_audio_tracks(self) -> Tuple[str, str]:
        """音声トラックを結合"""
        start_time = time.time()
        print("\n=== 音楽結合 ===")
        if self.args.skip_audio_combine:
            print("==> 音声結合をスキップします")
            # 既存のファイルを探す
            output_mp3 = self._find_latest_file(Config.COMBINED_AUDIO_FILENAME)
            tracks_json = self._find_latest_file(Config.TRACKS_INFO_FILENAME)

            if not output_mp3 or not tracks_json:
                error_msg = (
                    "音声結合をスキップしましたが、必要なファイルが見つかりません"
                )
                self.send_slack_notification(error_msg, is_error=True)
                print(f"==> {error_msg}")
                sys.exit(1)

            print(
                f"==> 既存のファイルを使用します: {output_mp3.name}, {tracks_json.name}"
            )
            elapsed_time = time.time() - start_time
            print(f"==> 音楽結合スキップ完了 (処理時間: {elapsed_time:.2f}秒)")
            return str(output_mp3), str(tracks_json)

        try:
            ambient_dir = self.args.ambient_dir or Config.AMBIENT_DIR
            output_mp3_path, tracks_json_path = combine_audio(
                input_dir=self.output_dir,
                output_dir=self.output_dir,
                fade_ms=3000,
                ambient=os.path.join(ambient_dir, self.selected_prompt["ambient"]),
            )
            self.send_slack_notification("🎧 音楽結合が完了しました")
            elapsed_time = time.time() - start_time
            print(f"==> 音楽結合完了 (処理時間: {elapsed_time:.2f}秒)")
            return output_mp3_path, tracks_json_path
        except Exception as e:
            error_msg = f"音楽結合中にエラーが発生しました: {e}"
            self.send_slack_notification(error_msg, is_error=True)
            print(f"==> {error_msg}")
            sys.exit(1)

    def generate_thumbnail(self) -> Tuple[str, str]:
        """サムネイルを生成"""
        start_time = time.time()
        print("\n=== サムネイル生成 ===")
        if self.args.skip_thumbnail_gen:
            print("==> サムネイル生成をスキップします")
            # 既存のファイルを探す
            print("==> サムネイルファイルを検索中...")
            thumbnail_path = self._find_latest_file(Config.THUMBNAIL_PATTERN)

            if not thumbnail_path:
                error_msg = (
                    "サムネイル生成をスキップしましたが、必要なファイルが見つかりません"
                )
                self.send_slack_notification(error_msg, is_error=True)
                print(f"==> {error_msg}")
                sys.exit(1)

            print(f"==> 既存のファイルを使用します: {thumbnail_path.name}")
            # サムネイルファイルを画像ファイルとしても使用
            elapsed_time = time.time() - start_time
            print(f"==> サムネイル生成スキップ完了 (処理時間: {elapsed_time:.2f}秒)")
            return str(thumbnail_path), str(thumbnail_path)

        try:
            image_path, thumbnail_path = thumbnail_generation(
                output_dir=self.output_dir,
                lofi_type=self.selected_prompt["type"],
                prompt=self.selected_image_prompt,
                thumb_title=self.selected_prompt["thumbnail_title"],
            )
            self.send_slack_notification("🖼️ サムネイル生成が完了しました")
            elapsed_time = time.time() - start_time
            print(f"==> サムネイル生成完了 (処理時間: {elapsed_time:.2f}秒)")
            return image_path, thumbnail_path
        except Exception as e:
            error_msg = f"サムネイル生成中にエラーが発生しました: {e}"
            self.send_slack_notification(error_msg, is_error=True)
            print(f"==> {error_msg}")
            sys.exit(1)

    def generate_metadata(self, tracks_json_path: str) -> str:
        """メタデータを生成"""
        start_time = time.time()
        print("\n=== メタデータ生成 ===")
        if self.args.skip_metadata_gen:
            print("==> メタデータ生成をスキップします")
            # 既存のファイルを探す
            metadata_path = self._find_latest_file(Config.METADATA_FILENAME)

            if not metadata_path:
                error_msg = (
                    "メタデータ生成をスキップしましたが、必要なファイルが見つかりません"
                )
                self.send_slack_notification(error_msg, is_error=True)
                print(f"==> {error_msg}")
                sys.exit(1)

            print(f"==> 既存のファイルを使用します: {metadata_path.name}")
            elapsed_time = time.time() - start_time
            print(f"==> メタデータ生成スキップ完了 (処理時間: {elapsed_time:.2f}秒)")
            return str(metadata_path)

        try:
            metadata_path = create_metadata(
                output_dir=self.output_dir,
                tracks_json=Path(tracks_json_path),
                lofi_type=self.selected_prompt["type"],
                music_prompt=self.selected_prompt["music_prompt"],
                api_url="",  # OpenAI APIを使用するため不要
                temperature=self.args.temperature,
            )
            self.send_slack_notification("📋 メタデータ生成が完了しました")
            elapsed_time = time.time() - start_time
            print(f"==> メタデータ生成完了 (処理時間: {elapsed_time:.2f}秒)")
            return metadata_path
        except Exception as e:
            error_msg = f"メタデータ生成中にエラーが発生しました: {e}"
            self.send_slack_notification(error_msg, is_error=True)
            print(f"==> {error_msg}")
            sys.exit(1)

    def generate_video(self, image_path: str, output_mp3_path: str) -> Optional[str]:
        """動画を生成"""
        start_time = time.time()
        print("\n=== 動画生成 ===")
        if self.args.skip_video_gen:
            print("==> 動画生成をスキップします")
            # 既存のファイルを探す
            video_path = self._find_latest_file(Config.FINAL_VIDEO_FILENAME)

            if not video_path:
                error_msg = (
                    "動画生成をスキップしましたが、必要なファイルが見つかりません"
                )
                self.send_slack_notification(error_msg, is_error=True)
                print(f"==> {error_msg}")
                sys.exit(1)

            print(f"==> 既存のファイルを使用します: {video_path.name}")
            elapsed_time = time.time() - start_time
            print(f"==> 動画生成スキップ完了 (処理時間: {elapsed_time:.2f}秒)")
            return str(video_path)

        try:
            video_path = create_video(
                output_dir=self.output_dir,
                still_path=image_path,
                audio_path=output_mp3_path,
            )
            self.send_slack_notification("🎥 動画生成が完了しました")
            elapsed_time = time.time() - start_time
            print(f"==> 動画生成完了 (処理時間: {elapsed_time:.2f}秒)")
            return video_path
        except Exception as e:
            error_msg = f"動画生成中にエラーが発生しました: {e}"
            self.send_slack_notification(error_msg, is_error=True)
            print(f"==> {error_msg}")
            sys.exit(1)

    def upload_to_youtube(
        self, video_path: str, thumbnail_path: str, metadata_path: str
    ) -> None:
        """YouTubeにアップロード"""
        start_time = time.time()
        print("\n=== YouTubeにアップロード ===")
        if self.args.skip_upload:
            print("==> 動画のアップロードをスキップします")
            elapsed_time = time.time() - start_time
            print(
                f"==> YouTubeアップロードスキップ完了 (処理時間: {elapsed_time:.2f}秒)"
            )
            return

        try:
            upload_video_to_youtube(
                video_path=Path(video_path),
                thumbnail_path=Path(thumbnail_path),
                metadata_path=Path(metadata_path),
                privacy=self.args.privacy,
                tags=self.args.tags,
            )
            self.send_slack_notification("📤 YouTubeへのアップロードが完了しました")
            print("==> YouTubeへのアップロードが完了しました")
            elapsed_time = time.time() - start_time
            print(f"==> YouTubeアップロード完了 (処理時間: {elapsed_time:.2f}秒)")
        except Exception as e:
            error_msg = f"動画のアップロード中にエラーが発生しました: {e}"
            self.send_slack_notification(error_msg, is_error=True)
            print(f"==> {error_msg}")
            sys.exit(1)

    def store_assets(self) -> None:
        """アセットをストックに保存"""
        start_time = time.time()
        print("\n=== 音源データのストック ===")

        if not self.success_music_gen:
            elapsed_time = time.time() - start_time
            print(f"==> アセット保存スキップ完了 (処理時間: {elapsed_time:.2f}秒)")
            return

        stock_audio_dir = Config.STOCK_AUDIO_BASE_DIR / self.selected_prompt["type"]
        stock_image_dir = Config.STOCK_IMAGE_BASE_DIR / self.selected_prompt["type"]

        stock_audio_dir.mkdir(parents=True, exist_ok=True)
        stock_image_dir.mkdir(parents=True, exist_ok=True)

        # 新規生成した音楽ファイルのみをストックに保存
        for file in self.newly_generated_files:
            if not file.stem.startswith("combined_audio"):
                self._copy_file_to_stock(file, stock_audio_dir)
                print(f"==> 新規生成ファイルをストックに保存: {file.name}")

        # 画像ファイルをストック
        for file in self.output_dir.glob("*.png"):
            shutil.copy(file, stock_image_dir / file.name)

        # 出力ディレクトリを削除
        shutil.rmtree(self.output_dir)

        print("\n=== 音源データのストック完了 ===")
        print(f"音源データのストックディレクトリ: {stock_audio_dir.absolute()}")
        print(f"画像データのストックディレクトリ: {stock_image_dir.absolute()}")

        self.send_slack_notification(
            "✅ 処理が正常に完了しました\n"
            + f"出力ディレクトリ: {self.output_dir.absolute()}\n"
            + f"音源データのストックディレクトリ: {stock_audio_dir.absolute()}\n"
            + f"画像データのストックディレクトリ: {stock_image_dir.absolute()}"
        )

        elapsed_time = time.time() - start_time
        print(f"==> アセット保存完了 (処理時間: {elapsed_time:.2f}秒)")

    def run(self) -> None:
        """メイン処理を実行"""
        total_start_time = time.time()
        print(f"=== 実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

        try:
            self.setup()
            self.select_prompt()
            self.generate_music()

            output_mp3_path, tracks_json_path = self.combine_audio_tracks()
            image_path, thumbnail_path = self.generate_thumbnail()
            metadata_path = self.generate_metadata(tracks_json_path)
            video_path = self.generate_video(image_path, output_mp3_path)
            if video_path:
                self.upload_to_youtube(video_path, thumbnail_path, metadata_path)

            print("\n=== 処理完了 ===")
            print(f"出力ディレクトリ: {self.output_dir.absolute()}")

            self.store_assets()

            total_elapsed_time = time.time() - total_start_time
            print(f"\n=== 実行終了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            print(f"=== 総処理時間: {total_elapsed_time:.2f}秒 ===")

        except Exception as e:
            error_msg = f"予期せぬエラーが発生しました: {e}"
            self.send_slack_notification(error_msg, is_error=True)
            print(f"==> {error_msg}")
            sys.exit(1)


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description="自動でyoutubeに音楽を投稿するプログラム"
    )

    # 共通
    common_group = parser.add_argument_group("共通")
    common_group.add_argument(
        "--output_dir",
        type=str,
        default=datetime.now().strftime("%Y%m%d"),
        help="出力ディレクトリ",
    )
    common_group.add_argument(
        "--jsonl_path",
        type=str,
        help="jsonlファイルのパス（未指定時は環境変数JSONL_PATHを使用）",
    )
    common_group.add_argument(
        "--lofi_type", type=str, help="指定するLo-Fiタイプ（指定がない場合はランダム）"
    )
    common_group.add_argument(
        "--skip_type_selection",
        action="store_true",
        help="Lo-Fiタイプの選択をスキップする",
    )

    # 音楽
    music_group = parser.add_argument_group("音楽")
    music_group.add_argument(
        "--target_duration_sec",
        type=int,
        default=60 * 12 * 6,
        help="音楽の長さ（フェード処理による短縮を考慮して余裕を持たせた時間）",
    )
    music_group.add_argument(
        "--ambient_dir",
        type=str,
        help="環境音ファイルのディレクトリ（未指定時は環境変数AMBIENT_DIRを使用）",
    )
    music_group.add_argument(
        "--skip_music_gen", action="store_true", help="音楽生成をスキップする"
    )
    music_group.add_argument(
        "--skip_audio_combine", action="store_true", help="音声結合をスキップする"
    )

    # サムネイル
    thumbnail_group = parser.add_argument_group("サムネイル")
    thumbnail_group.add_argument(
        "--skip_thumbnail_gen", action="store_true", help="サムネイル生成をスキップする"
    )

    # メタデータ
    metadata_group = parser.add_argument_group("メタデータ")
    metadata_group.add_argument(
        "--temperature", type=float, default=0.7, help="生成温度"
    )
    metadata_group.add_argument(
        "--skip_metadata_gen", action="store_true", help="メタデータ生成をスキップする"
    )

    # 動画
    video_group = parser.add_argument_group("動画")
    video_group.add_argument(
        "--skip_video_gen", action="store_true", help="動画生成をスキップする"
    )

    # アップロード
    upload_group = parser.add_argument_group("アップロード")
    upload_group.add_argument(
        "--privacy",
        type=str,
        default="public",
        choices=["private", "public", "unlisted"],
        help="公開設定",
    )
    upload_group.add_argument(
        "--tags",
        nargs="+",
        default=[
            "lofi",
            "music",
            "relax",
            "sleep",
            "study",
            "work",
            "chill",
            "ambient",
            "background",
            "background music",
            "background sound",
            "background noise",
            "background music",
            "background sound",
            "background noise",
        ],
        help="タグ",
    )
    upload_group.add_argument(
        "--skip_upload", action="store_true", help="アップロードをスキップする"
    )

    return parser.parse_args()


def main():
    """メイン関数。Lo-Fi投稿生成の全プロセスを実行する。"""
    args = parse_args()
    generator = LofiPostGenerator(args)
    generator.run()


if __name__ == "__main__":
    main()
