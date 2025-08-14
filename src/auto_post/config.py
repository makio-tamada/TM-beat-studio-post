import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

class Config:
    """設定を管理するクラス"""
    # Slack設定
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
    
    # ストックディレクトリ設定
    STOCK_AUDIO_BASE_DIR = Path(os.getenv('STOCK_AUDIO_BASE_DIR', '/tmp/music/lofi'))
    STOCK_IMAGE_BASE_DIR = Path(os.getenv('STOCK_IMAGE_BASE_DIR', '/tmp/image'))
    
    # ファイルパス設定
    JSONL_PATH = Path(os.getenv('JSONL_PATH', 'src/auto_post/lofi_type_with_variations.jsonl'))
    OPENING_VIDEO_PATH = Path(os.getenv('OPENING_VIDEO_PATH', 'src/auto_post/openning.mov'))
    AMBIENT_DIR = Path(os.getenv('AMBIENT_DIR', 'data/ambient'))
    CLIENT_SECRETS_PATH = Path(os.getenv('CLIENT_SECRETS_PATH', 'src/auto_post/client_secrets.json'))
    POST_DETAIL_PATH = Path(os.getenv('POST_DETAIL_PATH', 'src/auto_post/post_detail.txt'))
    
    # 出力ファイル名設定
    COMBINED_AUDIO_FILENAME = os.getenv('COMBINED_AUDIO_FILENAME', 'combined_audio.mp3')
    TRACKS_INFO_FILENAME = os.getenv('TRACKS_INFO_FILENAME', 'tracks_info.json')
    METADATA_FILENAME = os.getenv('METADATA_FILENAME', 'metadata.json')
    FINAL_VIDEO_FILENAME = os.getenv('FINAL_VIDEO_FILENAME', 'final_video.mp4')
    THUMBNAIL_PATTERN = os.getenv('THUMBNAIL_PATTERN', '*thumb.png')
    
    @classmethod
    def validate_config(cls):
        """設定の妥当性を検証"""
        required_vars = ['SLACK_WEBHOOK_URL']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"必要な環境変数が設定されていません: {', '.join(missing_vars)}")
        
        # ディレクトリの存在確認
        if not cls.STOCK_AUDIO_BASE_DIR.exists():
            print(f"警告: 音声ストックディレクトリが存在しません: {cls.STOCK_AUDIO_BASE_DIR}")
        
        if not cls.STOCK_IMAGE_BASE_DIR.exists():
            print(f"警告: 画像ストックディレクトリが存在しません: {cls.STOCK_IMAGE_BASE_DIR}")
        
        # ファイルの存在確認
        if not cls.JSONL_PATH.exists():
            print(f"警告: JSONLファイルが存在しません: {cls.JSONL_PATH}")
        
        if not cls.OPENING_VIDEO_PATH.exists():
            print(f"警告: オープニング動画ファイルが存在しません: {cls.OPENING_VIDEO_PATH}")
        
        if not cls.AMBIENT_DIR.exists():
            print(f"警告: 環境音ディレクトリが存在しません: {cls.AMBIENT_DIR}")
        
        if not cls.CLIENT_SECRETS_PATH.exists():
            print(f"警告: クライアントシークレットファイルが存在しません: {cls.CLIENT_SECRETS_PATH}")
        
        if not cls.POST_DETAIL_PATH.exists():
            print(f"警告: 投稿詳細ファイルが存在しません: {cls.POST_DETAIL_PATH}")
