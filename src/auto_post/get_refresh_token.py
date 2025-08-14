import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from pathlib import Path

# OAuth 2.0のスコープ設定
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

def get_refresh_token():
    """YouTube API用のリフレッシュトークンを取得する"""
    # クライアントシークレットファイルのパス
    from .config import Config
    client_secrets_file = Config.CLIENT_SECRETS_PATH
    
    if not client_secrets_file.exists():
        print(f"エラー: {client_secrets_file} が見つかりません")
        print("Google Cloud Consoleからclient_secrets.jsonをダウンロードして、このディレクトリに配置してください")
        return

    # OAuth 2.0認証フローの作成
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file,
        scopes=SCOPES
    )

    # ローカルサーバーで認証を実行
    credentials = flow.run_local_server(port=0)

    # 認証情報を表示
    print("\n=== 認証情報 ===")
    print(f"アクセストークン: {credentials.token}")
    print(f"リフレッシュトークン: {credentials.refresh_token}")
    print(f"トークンの有効期限: {credentials.expiry}")
    print(f"スコープ: {credentials.scopes}")

    # .envファイルに保存
    env_path = Path(__file__).parent / '.env'
    env_content = f"""GOOGLE_REFRESH_TOKEN={credentials.refresh_token}
GOOGLE_CLIENT_ID={credentials.client_id}
GOOGLE_CLIENT_SECRET={credentials.client_secret}
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n認証情報を {env_path} に保存しました")

if __name__ == "__main__":
    get_refresh_token() 