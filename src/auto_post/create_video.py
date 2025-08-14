"""
create_video.py
---------------
画像 1 枚と音源 mp3 を指定して YouTube 用の 1920×1080 (16:9) 動画を生成する。

構成
1. 冒頭に opening.mov（スクリプトと同じディレクトリに置く）を 3 秒間再生
2. メイン部は静止画＋カラーバック＋おしゃれな波形アニメーション
3. オーディオは mp3 まるごと
4. エンコード設定は libx264 / aac / 24 fps / faststart

使い方
python create_video.py --image ./thumbs/my_thumb.png --audio ./mix/combined_audio.mp3 --output ./out
# mp3 または wav に対応

依存
- moviepy >= 2.0
- pydub, numpy
"""

import argparse
import random
import numpy as np
from pathlib import Path
import os

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)
from moviepy.video.fx import Resize
from pydub import AudioSegment
from moviepy.video.VideoClip import VideoClip


# --------------------------------------------------------------
# 波形アニメーション生成
# --------------------------------------------------------------
class WaveformClip(VideoClip):
    def __init__(self, audio_clip, width, height, fps=24):
        super().__init__(duration=audio_clip.duration)
        self.audio_clip = audio_clip
        self.width = width
        self.height = height
        self.size = (width, height)
        self.samples = audio_clip.to_soundarray(fps=44100)
        if self.samples.ndim > 1:
            self.samples = self.samples.mean(axis=1)
        self.samples = self.samples / np.max(np.abs(self.samples))
        self.total = len(self.samples)
        self.bars = 30  # バーの数を減らしてシンプルに
        self.section = self.total // self.bars
        self.bar_heights = [
            np.mean(np.abs(self.samples[i * self.section : (i + 1) * self.section]))
            for i in range(self.bars)
        ]
        self.bar_w = int(width / (self.bars * 1.2))  # バーの幅を調整
        self.spacing = int((width - self.bars * self.bar_w) / self.bars)
        self.center_y = height // 2
        self.main_color = np.array([240, 214, 105], dtype=np.uint8)
        self.fps = fps
        self.frame_function = self.make_frame

    def make_frame(self, t):
        # 4チャンネル（RGBA）の配列を作成
        img = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        pos = int(t * self.total / self.duration)
        win = self.samples[max(0, pos - 2205) : pos]
        if len(win):
            volume = np.mean(np.abs(win))
        else:
            volume = 0
        scale = 1 + volume * 2  # スケールを小さくして控えめに
        for i, base_h in enumerate(self.bar_heights):
            h = int(base_h * self.height * scale)
            h = min(h, self.height // 2 - 2)  # 最大高さを制限
            x = i * (self.bar_w + self.spacing)
            y_start = max(0, self.center_y - h)
            y_end = min(self.height, self.center_y + h)
            if y_end > y_start and self.bar_w > 0:
                # RGBチャンネルに色を設定
                img[y_start:y_end, x:x + self.bar_w, :3] = self.main_color
                # アルファチャンネルを255（不透明）に設定
                img[y_start:y_end, x:x + self.bar_w, 3] = 255
        return img

def create_waveform_clip(audio_clip, width: int, height: int, fps: int = 24):
    return WaveformClip(audio_clip, width, height, fps).with_fps(fps)


# --------------------------------------------------------------
# メイン動画ビルダー
# --------------------------------------------------------------
def build_video(still_path: Path, audio_path: Path, output_dir: Path):
    """
    静止画と音声ファイルから動画を生成する

    Args:
        still_path (Path): 静止画のパス
        audio_path (Path): 音声ファイルのパス
        output_dir (Path): 出力ディレクトリのパス

    Returns:
        Path: 生成された動画ファイルのパス
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        from .config import Config
        output_file = output_dir / Config.FINAL_VIDEO_FILENAME

        # 定数
        W, H = 1920, 1080
        BG_COLOR = (18, 18, 18)

        # 音声読み込み
        print("==> 音声ファイルを読み込み中...")
        if not audio_path.exists():
            raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_path}")
            
        # 一時的なWAVファイルを作成
        temp_wav = output_dir / "temp_audio.wav"
        audio_segment = AudioSegment.from_file(str(audio_path))
        audio_segment.export(str(temp_wav), format="wav")
        
        audio = AudioFileClip(str(temp_wav))
        duration = audio.duration
        print(f"==> 音声の長さ: {duration:.2f}秒")

        # オープニング
        from .config import Config
        opening_path = Config.OPENING_VIDEO_PATH
        if opening_path.exists():
            opening_clip = VideoFileClip(str(opening_path)).with_effects([Resize((W, H))])
            print(f"==> オープニング動画読み込み完了 (長さ: {opening_clip.duration:.1f}秒)")
        else:
            print("==> オープニング動画が見つかりません。黒い画面を使用します")
            opening_clip = ColorClip((W, H), color=(0, 0, 0), duration=3)

        # 静止画の準備
        print("==> 静止画を準備中...")
        img_clip = (
            ImageClip(str(still_path))
            .with_effects([Resize((W, H))])  # 画面いっぱいに表示
            .with_position("center")
            .with_duration(duration)
        )

        # 背景と波形
        waveform_height = 80  # 波形の高さを小さく
        waveform_width = int(W * 0.5)  # 画面幅の50%
        print("==> 波形アニメーションを生成中...")
        try:
            wf_clip = create_waveform_clip(audio, width=waveform_width, height=waveform_height).with_position(
                ("center", H - waveform_height - 20)  # 下中央に配置
            )
            print(f"wf_clip type: {type(wf_clip)}")
        except Exception as e:
            print(f"wf_clip生成時エラー: {e}")
            raise

        # 構成
        main_clip = CompositeVideoClip([img_clip, wf_clip], size=(W, H)).with_duration(
            duration
        )

        final = concatenate_videoclips([opening_clip, main_clip], method="compose")

        # 音声の付加（短い/長い場合は調整）
        if final.duration < audio.duration:
            audio = audio.subclip(0, final.duration)
        final = final.with_audio(audio)

        # 書き出し
        print("==> 動画をエンコード中...")
        final.write_videofile(
            str(output_file),
            codec="libx264",
            audio_codec="aac",
            fps=24,
            threads=8,
            preset="medium",
            bitrate="6000k",
            audio_bitrate="192k",
            temp_audiofile=str(output_dir / "temp_aac.m4a"),
            remove_temp=True
        )
        
        # 一時ファイルの削除
        if temp_wav.exists():
            os.remove(str(temp_wav))
            
        print(f"==> 動画を保存しました: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"==> 動画生成中にエラーが発生しました: {e}")
        # 一時ファイルの削除
        if 'temp_wav' in locals() and temp_wav.exists():
            os.remove(str(temp_wav))
        return None


# --------------------------------------------------------------
# コマンドラインインターフェース
# --------------------------------------------------------------
def main():
    """コマンドライン実行用のメイン関数"""
    parser = argparse.ArgumentParser(description="画像 + 音声 → 動画")
    parser.add_argument("--image", required=True, help="静止画ファイル")
    parser.add_argument("--audio", required=True, help="音声ファイル (mp3 または wav)")
    parser.add_argument("--output", default="output_video", help="出力ディレクトリ")
    args = parser.parse_args()

    try:
        output_file = build_video(
            still_path=Path(args.image).expanduser(),
            audio_path=Path(args.audio).expanduser(),
            output_dir=Path(args.output).expanduser(),
        )
        if output_file:
            print(f"\n=== 処理完了 ===")
            print(f"出力ファイル: {output_file.absolute()}")
        else:
            print("\n=== 処理失敗 ===")
    except Exception as e:
        print(f"\n=== エラーが発生しました ===")
        print(f"エラー内容: {e}")

def create_video(output_dir: Path, still_path: Path, audio_path: Path):
    """
    静止画と音声ファイルから動画を生成する（外部アプリケーション用インターフェース）

    Args:
        output_dir (Path): 出力ディレクトリのパス
        still_path (Path): 静止画のパス
        audio_path (Path): 音声ファイルのパス

    Returns:
        str: 生成された動画ファイルのパス。失敗した場合はNone
    """
    print("==> 動画生成を開始します")
    output_file = build_video(
        still_path=Path(still_path),
        audio_path=Path(audio_path),
        output_dir=Path(output_dir),
    )
    if output_file:
        print(f"==> 動画生成が完了しました: {output_file}")
        return str(output_file)
    else:
        print("==> 動画生成に失敗しました")
        return None


if __name__ == "__main__":
    main()