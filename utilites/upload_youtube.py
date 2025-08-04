# upload_youtube.py

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"
YOUTUBE_API_KEY = os.getenv("youtube_api_key")

def get_authenticated_service():
    # Try OAuth first if credentials.json exists
    if os.path.exists(CLIENT_SECRETS_FILE):
        credentials = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                credentials = pickle.load(token)
        if not credentials:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_console()
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(credentials, token)
        return build("youtube", "v3", credentials=credentials)
    
    # Fallback to API key from environment
    elif YOUTUBE_API_KEY:
        return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    else:
        raise ValueError("No YouTube credentials found. Need either credentials.json or youtube_api_key in .env")

def upload_video(file_path, meta_json_path, privacy="public"):
    with open(meta_json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    youtube = get_authenticated_service()

    request_body = {
        "snippet": {
            "title": meta["video_title"].replace("**", ""),
            "description": meta["video_description"],
            "tags": meta.get("video_hashtags", "").split(),
            "categoryId": "22"  # "People & Blogs"
        },
        "status": {
            "privacyStatus": privacy
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)

    print(f"🚀 Uploading: {file_path}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
    print(f"✅ Video uploaded! ID: {response['id']}")
    return response['id']
