#!/usr/bin/env python3
"""
YouTube OAuth - one-time setup (mobile se, PC ke bina).
Do steps:
  1) python youtube_auth.py start     -> auth URL print karta hai (phone me kholo)
  2) login ke baad browser localhost pe fail hoga - address bar ka POORA URL copy karo,
     GitHub Actions 'YouTube Auth' workflow ko mode=exchange me us URL ke saath chalao
     -> refresh token print hoga -> usko YT_REFRESH_TOKEN secret banao.
NOTE: refresh token ko logs se kisi ko mat dikhana. Repo private rakho jab tak ye step na ho jaye.
"""
import argparse
import sys
import urllib.parse

import requests

SCOPES = "https://www.googleapis.com/auth/youtube.upload"
REDIRECT_URI = "http://localhost:8080"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def cmd_start(client_id):
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print("=" * 60)
    print("STEP 1: Ye URL phone ke browser me kholo aur apne Google")
    print("account (jiske YouTube channel se video upload karna hai) se Allow karo:")
    print()
    print(url)
    print()
    print("STEP 2: Login ke baad page 'localhost' pe khulne ki koshish karega aur")
    print("fail ho jayega - YE NORMAL HAI. Address bar me URL aisa dikhega:")
    print("http://localhost:8080/?code=4/0Axxx...&scope=...")
    print("Us POORE URL ko copy karo (code= ke saath shuru se ant tak).")
    print()
    print("STEP 3: GitHub -> Actions -> 'YouTube Auth' -> Run workflow:")
    print("  mode = exchange")
    print("  redirect_url = wahi poora localhost URL")
    print("=" * 60)


def cmd_exchange(client_id, client_secret, redirect_url):
    if not redirect_url or "code=" not in redirect_url:
        sys.exit("ERROR: redirect_url me 'code=' nahi mila. Login ke baad ka poora localhost URL paste karo.")
    q = urllib.parse.urlparse(redirect_url.strip())
    code = urllib.parse.parse_qs(q.query).get("code", [None])[0]
    if not code:
        sys.exit("ERROR: URL me code parse nahi hua: " + redirect_url[:200])
    r = requests.post(TOKEN_URL, data={
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }, timeout=30)
    if r.status_code != 200:
        sys.exit("ERROR: token exchange fail (%s): %s" % (r.status_code, r.text[:300]))
    refresh_token = r.json().get("refresh_token")
    if not refresh_token:
        sys.exit("ERROR: refresh_token nahi mila. 'start' step me URL me access_type=offline hona chahiye tha. "
                 "Dobara start -> login -> exchange karo.")
    print("=" * 60)
    print("SUCCESS! Ye tumhara REFRESH TOKEN hai (sirf ek baar dikhega):")
    print()
    print(refresh_token)
    print()
    print("Ab turant GitHub -> Settings -> Secrets and variables -> Actions ->")
    print("New repository secret -> Name: YT_REFRESH_TOKEN -> Value: upar wala token.")
    print("Iske baad ye workflow run delete kar dena (Actions me run pe ... menu -> Delete workflow run).")
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["start", "exchange"])
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret", required=True)
    ap.add_argument("--redirect-url", default="")
    args = ap.parse_args()
    if not args.client_id or not args.client_secret:
        sys.exit("ERROR: GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET secrets set karo pehle.")
    if args.mode == "start":
        cmd_start(args.client_id)
    else:
        cmd_exchange(args.client_id, args.client_secret, args.redirect_url)


if __name__ == "__main__":
    main()
