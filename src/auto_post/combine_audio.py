"""
combine_audio.py
----------------
指定ディレクトリ内の .mp3 ファイルを順番に結合し、フェードアウト／フェードインを入れて
1 本の長尺トラックを生成するスクリプト。

・フェード長はオプション (--fade) で指定可能（デフォ 3000 ms）。
・曲の開始位置一覧を JSON でも保存し、実行時に見やすいフォーマットで表示。
・環境音 (BGM) を重ねる機能もあり (--ambient)。

Usage
-----
python combine_audio.py --input-dir ./audio --output-dir ./out --fade 4000 --ambient rain.mp3
"""

import argparse
import json
import random
from pathlib import Path
from typing import List, Tuple

from pydub import AudioSegment


# -------------------------------------------------------------------
# ヘルパー関数
# -------------------------------------------------------------------
def get_audio_files(directory: Path) -> List[Path]:
    """ディレクトリ内のmp3ファイルリストを返す（自然順）"""
    files = sorted(directory.glob("*.mp3"))
    return [file for file in files if not file.stem.startswith("combined_audio")]


def human_minutes(seconds: float) -> str:
    """秒をM:SS形式に変換する"""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def load_ambient(path: Path, target_length_ms: int) -> AudioSegment:
    """環境音トラックを読み込み、ループして目標の長さに合わせる"""
    ambient = AudioSegment.from_file(str(path), format="mp3") - 10  # 音量を下げる
    if len(ambient) < target_length_ms:
        loops = target_length_ms // len(ambient) + 1
        ambient = ambient * loops
    return ambient[:target_length_ms]


def combine_tracks(
    tracks: List[Path],
    fade_ms: int = 3000,
) -> Tuple[AudioSegment, list]:
    """
    トラックをクロスフェードで結合し、(結合された音声, トラック情報)を返す
    
    Args:
        tracks (List[Path]): 結合するmp3ファイルのパスリスト
        fade_ms (int): フェード長（ミリ秒）
        
    Returns:
        Tuple[AudioSegment, list]: (結合された音声, トラック情報のリスト)
        トラック情報は title, original_title, start_time, end_time（秒単位）を含む辞書のリスト
    """
    if not tracks:
        raise ValueError("トラックが提供されていません")

    # バラエティのためにシャッフル
    random.shuffle(tracks)

    first = AudioSegment.from_file(str(tracks[0]), format="mp3")
    combined = first
    info = [
        dict(
            title=tracks[0].stem,
            original_title=tracks[0].stem,  # 元のファイル名を保持
            start_time=0.0,
            end_time=len(first) / 1000
        )
    ]

    for i, path in enumerate(tracks[1:]):
        clip = AudioSegment.from_file(str(path), format="mp3")
        
        # 現在の結合音声の長さを記録（時間計算用）
        current_length = len(combined)
        
        # クロスフェードを適用
        if current_length > fade_ms:
            # クロスフェード用の重複部分を作成
            overlap_part = combined[-fade_ms:].fade_out(fade_ms)
            combined = combined[:-fade_ms]  # 重複部分を削除
            
            if len(clip) > fade_ms:
                clip_start = clip[:fade_ms].fade_in(fade_ms)
                clip_rest = clip[fade_ms:]
                
                # 重複部分を重ね合わせてクロスフェード
                crossfaded = overlap_part.overlay(clip_start)
                combined = combined + crossfaded + clip_rest
            else:
                # クリップが短い場合は通常の処理
                clip = clip.fade_in(fade_ms)
                combined = combined + clip
        else:
            # 最初の曲または短い曲の場合
            if len(clip) > fade_ms:
                clip = clip.fade_in(fade_ms)
            combined += clip
        
        # 実際の音声長さに基づく時間計算
        start_sec = current_length / 1000
        end_sec = len(combined) / 1000
        
        info.append(dict(
            title=path.stem,
            original_title=path.stem,  # 元のファイル名を保持
            start_time=start_sec,
            end_time=end_sec
        ))

    # 最後のトラックにフェードアウトを適用
    if len(combined) > fade_ms:
        combined = combined.fade_out(fade_ms)

    return combined, info


# -------------------------------------------------------------------
# メインエントリー
# -------------------------------------------------------------------
def main() -> None:
    """コマンドライン実行用のメイン関数"""
    parser = argparse.ArgumentParser(description="ディレクトリ内の mp3 を結合")
    parser.add_argument(
        "--input-dir", type=str, required=True, help="音楽ファイル (*.mp3) 置き場"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output_audio",
        help="書き出しディレクトリ (デフォ: ./output_audio)",
    )
    parser.add_argument(
        "--fade", type=int, default=3000, help="フェード長 (ms)。デフォ 3000"
    )
    parser.add_argument(
        "--ambient",
        type=str,
        help="環境音 mp3 ファイル。--input-dir と同階層、または絶対パス可",
    )
    args = parser.parse_args()

    try:
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_mp3 = output_dir / "combined_audio.mp3"
        output_json = output_dir / "tracks_info.json"

        tracks = get_audio_files(input_dir)
        if not tracks:
            print(f"==> {input_dir}内にmp3ファイルが見つかりません")
            return

        print(f"==> {len(tracks)}個のトラックを見つけました。結合を開始します...")

        combined, info = combine_tracks(tracks, fade_ms=args.fade)

        # 環境音を重ねる
        if args.ambient:
            ambient_path = Path(args.ambient)
            if not ambient_path.is_absolute():
                ambient_path = input_dir / args.ambient
            if ambient_path.exists():
                print(f"==> 環境音を重ねています: {ambient_path.name}")
                ambient = load_ambient(ambient_path, len(combined))
                combined = combined.overlay(ambient)
            else:
                print(f"==> 環境音ファイルが見つかりません: {ambient_path}")

        # mp3書き出し
        combined.export(output_mp3, format="mp3")
        print(f"==> 結合トラックを保存しました: {output_mp3}")

        # JSONを保存
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        # プレイリスト表示
        print("\n=== プレイリスト ===")
        for entry in info:
            mark = human_minutes(entry["start_time"])
            print(f"{mark}  {entry['title']}")

        total_min = human_minutes(info[-1]["end_time"])
        print(f"\n==> 合計時間: {total_min}")

        print(f"==> トラックリストを保存しました: {output_json}")
        
        print("\n=== 処理完了 ===")
        print(f"出力ファイル: {output_mp3}")
        
    except Exception as e:
        print(f"\n=== エラーが発生しました ===")
        print(f"エラー内容: {e}")

def combine_audio(input_dir: Path, output_dir: Path, fade_ms: int = 3000, ambient: str = None) -> Tuple[Path, Path]:
    """
    ディレクトリ内の音声ファイルを結合する
    
    Args:
        input_dir (Path): 入力ディレクトリ
        output_dir (Path): 出力ディレクトリ
        fade_ms (int): フェード長（ミリ秒）
        ambient (str): 環境音ファイルのパス
        
    Returns:
        Tuple[Path, Path]: (結合された音声ファイルのパス, トラック情報のJSONファイルのパス)
    """
    try:
        output_mp3 = output_dir / "combined_audio.mp3"
        output_json = output_dir / "tracks_info.json"

        tracks = get_audio_files(input_dir)
        if not tracks:
            print(f"==> {input_dir}内にmp3ファイルが見つかりません")
            return None, None

        print(f"==> {len(tracks)}個のトラックを見つけました。結合を開始します...")

        combined, info = combine_tracks(tracks, fade_ms=fade_ms)

        # 環境音を重ねる
        if ambient:
            current_path = Path.cwd()
            ambient_path = current_path / ambient
            if not ambient_path.is_absolute():
                # input_dirに対して相対パスを解決する
                ambient_path = input_dir / ambient
            if ambient_path.exists():
                print(f"==> 環境音を重ねています: {ambient_path.name}")
                ambient = load_ambient(ambient_path, len(combined))
                combined = combined.overlay(ambient)
            else:
                print(f"==> 環境音ファイルが見つかりません: {ambient_path}")

        # mp3書き出し
        combined.export(output_mp3, format="mp3")
        print(f"==> 結合トラックを保存しました: {output_mp3}")

        # JSONを保存
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        # プレイリスト表示
        print("\n=== プレイリスト ===")
        for entry in info:
            mark = human_minutes(entry["start_time"])
            print(f"{mark}  {entry['title']}")

        total_min = human_minutes(info[-1]["end_time"])

        print(f"\n==> 合計時間: {total_min}")
        print(f"==> トラックリストを保存しました: {output_json}")

        return output_mp3, output_json
        
    except Exception as e:
        print(f"==> 音声結合中にエラーが発生しました: {e}")
        return None, None


if __name__ == "__main__":
    main()