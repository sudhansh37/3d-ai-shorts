#!/usr/bin/env python3
"""
Gemini TTS se scene ka Hindi narration banata hai (free tier).
Output: WAV - ffmpeg se video me judta hai.
Key/narration na ho ya API fail ho to koi file nahi banata (exit 0) -
video chup-chap silent chalega, pipeline nahi rukti.
"""
import argparse
import base64
import json
import os
import sys
import wave

import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTS_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "{model}:generateContent")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="generated/scene.json")
    ap.add_argument("--out", required=True, help="output narration.wav")
    args = ap.parse_args()

    with open(os.path.join(REPO_ROOT, "config", "config.json")) as f:
        config = json.load(f)
    if not config.get("enable_tts", True):
        print("TTS_SKIP: config me enable_tts false hai")
        return 0

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("TTS_SKIP: GEMINI_API_KEY set nahi hai - video silent banegi")
        return 0

    with open(args.json, encoding="utf-8") as f:
        scene = json.load(f)
    narration = (scene.get("narration") or "").strip()
    if not narration:
        print("TTS_SKIP: scene JSON me narration nahi hai")
        return 0

    model = config.get("tts_model", "gemini-2.5-flash-preview-tts")
    voice = config.get("tts_voice", "Kore")
    text = ("Bhaut hi expressive, warm aur dramatic storytelling tone me Hindi me "
            "ye narration bolo - saaf, thoda dheere, achhi energy ke saath:\n\n"
            + narration)
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {
                "prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    try:
        r = requests.post(TTS_URL.format(model=model),
                          headers={"x-goog-api-key": api_key},
                          json=payload, timeout=180)
    except requests.RequestException as e:
        print("WARN: TTS network fail: %s" % e)
        return 0
    if r.status_code == 404:
        print("WARN: TTS model '%s' nahi mila (404) - config/config.json me tts_model check karo" % model)
        return 0
    if r.status_code == 429:
        print("WARN: TTS rate limit (429) - is run me skip")
        return 0
    if r.status_code != 200:
        print("WARN: TTS API error %s: %s" % (r.status_code, r.text[:300]))
        return 0
    try:
        part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
    except (KeyError, IndexError, TypeError):
        print("WARN: TTS response me audio nahi tha")
        return 0

    # Gemini TTS raw PCM (16-bit mono) deta hai - WAV container me daalo
    pcm = base64.b64decode(part["data"])
    rate = 24000
    mime = part.get("mimeType") or ""
    if "rate=" in mime:
        try:
            rate = int(mime.split("rate=")[1].split(";")[0])
        except ValueError:
            pass
    with wave.open(args.out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    print("TTS_OK: %s (%.1f sec, voice=%s)" % (args.out, len(pcm) / 2.0 / rate, voice))
    return 0


if __name__ == "__main__":
    sys.exit(main())
