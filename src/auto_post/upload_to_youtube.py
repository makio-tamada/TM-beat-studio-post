import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# .envファイルを読み込む
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# YouTube APIのスコープ
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def get_authenticated_service():
    """認証済みのYouTube APIサービスを取得する"""
    credentials = None

    # 必要な環境変数のチェック
    required_env_vars = [
        "GOOGLE_REFRESH_TOKEN",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
    ]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        raise Exception(
            f"必要な環境変数が設定されていません: {', '.join(missing_vars)}"
        )

    # 環境変数から認証情報を取得
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    try:
        # リフレッシュトークンから認証情報を作成
        credentials = Credentials(
            None,  # access_token
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )

        # トークンを更新
        credentials.refresh(Request())

    except Exception as e:
        print(f"リフレッシュトークンからの認証に失敗しました: {e}")
        print("新規認証を開始します...")

        # client_secrets.jsonのパスを確認
        from .config import Config

        client_secrets_path = Config.CLIENT_SECRETS_PATH
        if not client_secrets_path.exists():
            raise Exception(
                f"client_secrets.jsonが見つかりません: {client_secrets_path}"
            )

        # 新規認証
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secrets_path), SCOPES
        )
        credentials = flow.run_local_server(port=0)

        # 新しいリフレッシュトークンを.envファイルに保存
        with open(env_path, "a") as f:
            f.write(f"\nGOOGLE_REFRESH_TOKEN={credentials.refresh_token}")
            f.write(f"\nGOOGLE_CLIENT_ID={credentials.client_id}")
            f.write(f"\nGOOGLE_CLIENT_SECRET={credentials.client_secret}")

    return build("youtube", "v3", credentials=credentials)


def upload_video(
    video_path,
    title,
    description,
    category_id="10",
    privacy_status="private",
    tags=None,
    made_for_kids=False,
    default_language="en",
    license_type="youtube",
):
    """
    動画をYouTubeにアップロード

    Args:
        video_path (str): アップロードする動画ファイルのパス
        title (str): 動画のタイトル
        description (str): 動画の説明文
        category_id (str): カテゴリID（デフォルトは"10"=Music）
        privacy_status (str): 公開設定（"private", "public", "unlisted"）
        tags (list): タグのリスト
        made_for_kids (bool): 子供向けコンテンツかどうか
        default_language (str): デフォルト言語
        license_type (str): ライセンスタイプ（"youtube", "creativeCommon"）

    Returns:
        str: アップロードされた動画のID、失敗した場合はNone
    """
    try:
        # YouTubeサービスを取得
        youtube = get_authenticated_service()

        # メタデータを設定
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": category_id,
                "defaultLanguage": default_language,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": made_for_kids,
                "license": license_type,
            },
        }

        # タグの追加
        if tags:
            body["snippet"]["tags"] = tags

        # 動画ファイルをアップロード
        media = MediaFileUpload(
            video_path, chunksize=1024 * 1024, resumable=True, mimetype="video/mp4"
        )

        print("動画のアップロードを開始します...")
        request = youtube.videos().insert(
            part=",".join(body.keys()), body=body, media_body=media
        )

        # アップロードの進捗を表示
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"アップロード進捗: {int(status.progress() * 100)}%")

        print("動画のアップロードが完了しました！")
        print(f"動画ID: {response['id']}")
        return response["id"]

    except Exception as e:
        print(f"アップロード中にエラーが発生しました: {e}")
        return None


def upload_thumbnail(video_id, thumbnail_path):
    """
    サムネイル画像をアップロード

    Args:
        video_id (str): サムネイルをアップロードする動画のID
        thumbnail_path (str): サムネイル画像のパス

    Returns:
        bool: アップロードが成功したかどうか
    """
    try:
        # YouTubeサービスを取得
        youtube = get_authenticated_service()

        # サムネイル画像をアップロード
        request = youtube.thumbnails().set(
            videoId=video_id, media_body=MediaFileUpload(thumbnail_path)
        )
        request.execute()

        print("サムネイルのアップロードが完了しました！")
        return True

    except Exception as e:
        print(f"サムネイルのアップロード中にエラーが発生しました: {e}")
        return False


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="YouTubeへの動画アップロード")
    parser.add_argument(
        "--video", type=str, required=True, help="アップロードする動画ファイルのパス"
    )
    parser.add_argument("--title", type=str, required=True, help="動画のタイトル")
    parser.add_argument("--description", type=str, required=True, help="動画の説明文")
    parser.add_argument(
        "--privacy",
        type=str,
        default="private",
        choices=["private", "public", "unlisted"],
        help="公開設定（private/public/unlisted）",
    )
    parser.add_argument("--thumbnail", type=str, help="サムネイル画像のパス")
    parser.add_argument("--tags", type=str, help="カンマ区切りのタグリスト")

    args = parser.parse_args()

    # タグの処理
    tags = None
    if args.tags:
        tags = [tag.strip() for tag in args.tags.split(",")]

    # 動画をアップロード
    video_id = upload_video(
        video_path=args.video,
        title=args.title,
        description=args.description,
        privacy_status=args.privacy,
        tags=tags,
    )

    if video_id:
        print("動画のアップロードが成功しました！")
        print(f"動画URL: https://www.youtube.com/watch?v={video_id}")

        # サムネイルをアップロード
        if args.thumbnail:
            upload_thumbnail(video_id, args.thumbnail)
    else:
        print("動画のアップロードに失敗しました。")


def upload_video_to_youtube(
    video_path: Path,
    thumbnail_path: Path,
    metadata_path: Path,
    privacy: str = "private",
    tags: list = None,
):
    # メタデータを読み込む
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # post_detail.txtを読み込む
    from .config import Config

    post_detail_path = Config.POST_DETAIL_PATH
    post_detail = post_detail_path.read_text(encoding="utf-8")

    # 説明文を組み立てる
    description = (
        f"{metadata['description']}\n\n{metadata['tracklist']}\n\n{post_detail}"
    )

    # 動画をアップロード
    video_id = upload_video(
        video_path=video_path,
        title=metadata["title"],
        description=description,
        privacy_status=privacy,
        tags=tags,
    )

    if not video_id:
        raise Exception("動画のアップロードに失敗しました")

    print("動画のアップロードが成功しました！")
    print(f"動画URL: https://www.youtube.com/watch?v={video_id}")

    # サムネイルをアップロード
    if thumbnail_path:
        if not upload_thumbnail(video_id, thumbnail_path):
            raise Exception("サムネイルのアップロードに失敗しました")

    return video_id


if __name__ == "__main__":
    main()
