import logging
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

# OAuth 2.0のスコープ設定
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def get_refresh_token():
    """YouTube API用のリフレッシュトークンを取得する"""
    # クライアントシークレットファイルのパス
    from .config import Config

    client_secrets_file = Config.CLIENT_SECRETS_PATH

    if not client_secrets_file.exists():
        logger.error(f"エラー: {client_secrets_file} が見つかりません")
        logger.error(
            "Google Cloud Consoleからclient_secrets.jsonをダウンロードして、このディレクトリに配置してください"
        )
        return

    # OAuth 2.0認証フローの作成
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes=SCOPES)

    # ローカルサーバーで認証を実行
    credentials = flow.run_local_server(port=0)

    # 認証情報を表示
    logger.info("\n=== 認証情報 ===")
    logger.info(f"アクセストークン: {credentials.token}")
    logger.info(f"リフレッシュトークン: {credentials.refresh_token}")
    logger.info(f"トークンの有効期限: {credentials.expiry}")
    logger.info(f"スコープ: {credentials.scopes}")

    # .envファイルに保存
    env_path = Path(__file__).parent / ".env"
    env_content = f"""GOOGLE_REFRESH_TOKEN={credentials.refresh_token}
GOOGLE_CLIENT_ID={credentials.client_id}
GOOGLE_CLIENT_SECRET={credentials.client_secret}
"""

    with open(env_path, "w") as f:
        f.write(env_content)

    logger.info(f"\n認証情報を {env_path} に保存しました")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    get_refresh_token()
