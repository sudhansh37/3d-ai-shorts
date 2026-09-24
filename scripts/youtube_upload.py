#!/usr/bin/env python3
"""
Rendered MP4 ko YouTube Data API v3 se upload karta hai.
Secrets env se aate hain: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, YT_REFRESH_TOKEN.
- AI-generated content ka disclosure (containsSyntheticMedia) automatically ON rehta hai
- Koi secret missing ho to 'SKIP' print karke exit 0 (pipeline rukti nahi).
Usage:
  python scripts/youtube_upload.py --video output/video.mp4 --json generated/scene.json
"""
import argparse
import json
import os
import sys
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def upload_video(youtube, video_path, title, description, tags, privacy, category_id):
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": [str(t)[:100] for t in tags][:15],
            "categoryId": str(category_id),
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            # AI-generated content disclosure (YouTube settings me "Altered content" = Yes)
            "containsSyntheticMedia": True,
        },
    }
    media = MediaFileUpload(video_path, chunksize=8 * 1024 * 1024,
                            resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print("Upload: %d%%" % int(status.progress() * 100))
    return response


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--json", required=True)
    args = ap.parse_args()

    if not os.path.exists(args.video):
        sys.exit("ERROR: video file nahi mili: %s" % args.video)

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("YT_REFRESH_TOKEN", "").strip()

    if not (client_id and client_secret and refresh_token):
        print("SKIP: YouTube secrets missing (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / "
              "YT_REFRESH_TOKEN). Video upload nahi hua - sirf render hua.")
        return 0

    with open(args.json, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(os.path.join(REPO_ROOT, "config", "config.json")) as f:
        cfg = json.load(f)

    title = meta.get("title") or "3D Short"
    description = meta.get("description") or ""
    tags = meta.get("tags") or []
    privacy = cfg.get("youtube_privacy", "private")
    category_id = cfg.get("youtube_category_id", "1")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    last_err = None
    for attempt in range(1, 4):
        try:
            print("Upload try %d/3..." % attempt)
            response = upload_video(youtube, args.video, title, description, tags, privacy, category_id)
            print("UPLOAD_OK: https://www.youtube.com/watch?v=%s" % response["id"])
            print("Title: %s | Privacy: %s | AI disclosure: ON" % (title, privacy))
            return 0
        except HttpError as e:
            last_err = e
            print("WARN: upload fail (%s): %s" % (e.resp.status, str(e)[:300]))
            if e.resp.status in (401, 403):
                print("ERROR: token/permission problem. YT_REFRESH_TOKEN dobara banao "
                      "(YouTube Auth workflow) ya console.developers.google.com me API enabled check karo.")
                return 1
            time.sleep(15 * attempt)
        except Exception as e:
            last_err = e
            print("WARN: upload fail: %s" % e)
            time.sleep(15 * attempt)
    print("ERROR: 3 try me upload nahi hua: %s" % last_err)
    return 1


if __name__ == "__main__":
    sys.exit(main())
