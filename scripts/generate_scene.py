#!/usr/bin/env python3
"""
Gemini se natural-language prompt ka structured scene JSON banata hai.
- prompts/prompts.txt se roz agli line uthata hai (ya --prompt se custom)
- Gemini ko allowed locations/animations/cameras ki list dekar JSON banwata hai
- narration field: Hindi (Devanagari) storytelling lines - Gemini TTS bolti hai
- Fail hone par fallback scene use karta hai (config me on hai)
Usage:
  python scripts/generate_scene.py [--prompt "..."] [--out generated/scene.json] [--no-consume]
"""
import argparse
import json
import os
import sys

import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

CAMERA_TYPES = [
    "wide", "medium", "closeup", "follow", "side_tracking",
    "front", "back", "low_angle", "high_angle", "overhead", "orbit",
]

SCHEMA_HINT = (
    '{"title": "short title (max 70 chars)", '
    '"description": "1-2 line description with 3 hashtags", '
    '"tags": ["tag1", "tag2", "tag3"], '
    '"narration": "Hindi narration in Devanagari script - 2-4 short dramatic lines telling the story", '
    '"scene": {"duration": 15, "characters": [{"id": "hero", "actions": ['
    '{"animation": "walk", "from": "house_1", "to": "road_center", "duration": 4}, '
    '{"animation": "wave", "location": "road_center", "duration": 3}]}]}, '
    '"camera": [{"type": "follow", "target": "hero", "duration": 5}]}'
)

FALLBACK_SCENE = {
    "title": "Hero Ka Chhota Adventure",
    "description": "3D animated short - hero ghar se nikal kar road par daudta hai aur haath hilata hai! #shorts #3d #animation",
    "tags": ["shorts", "3danimation", "blender"],
    "narration": "हीरो अपने घर से बाहर निकलता है। फिर वह सड़क पर तेज़ी से दौड़ता है। और आखिर में, अपने दोस्त को खुशी से हाथ हिलाता है!",
    "scene": {
        "duration": 11,
        "characters": [
            {
                "id": "hero",
                "actions": [
                    {"animation": "walk", "from": "house_1", "to": "road_center", "duration": 4},
                    {"animation": "run", "from": "road_center", "to": "house_2", "duration": 4},
                    {"animation": "wave", "location": "house_2", "duration": 3},
                ],
            }
        ],
    },
    "camera": [
        {"type": "wide", "target": "hero", "duration": 3},
        {"type": "follow", "target": "hero", "duration": 5},
        {"type": "closeup", "target": "hero", "duration": 3},
    ],
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_animations():
    """Pehle assets/manifest.json (Kenney embedded animations), phir
    assets/animations/ files, warna default list."""
    manifest = os.path.join(REPO_ROOT, "assets", "manifest.json")
    if os.path.isfile(manifest):
        try:
            names = load_json(manifest).get("animations") or []
            if names:
                return names
        except Exception:
            pass
    d = os.path.join(REPO_ROOT, "assets", "animations")
    names = []
    if os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            stem = os.path.splitext(fn)[0].strip().lower()
            if stem and stem not in names:
                names.append(stem)
    if not names:
        names = ["idle", "walk", "run", "jump", "sit", "stand", "wave", "talk", "fall", "attack"]
    return names


def build_system_prompt(locations, animations):
    return (
        "You are a 3D scene planner for a vertical (9:16) YouTube Shorts pipeline.\n"
        "Return ONLY a single valid JSON object, no markdown fences, no commentary.\n"
        "Exact schema:\n" + SCHEMA_HINT + "\n\n"
        "Rules:\n"
        "1. 'from', 'to', 'location' MUST be one of: " + json.dumps(sorted(locations)) + "\n"
        "2. 'animation' MUST be one of: " + json.dumps(animations) + "\n"
        "3. camera 'type' MUST be one of: " + json.dumps(CAMERA_TYPES) + "\n"
        "4. camera 'target' is a character id (e.g. hero).\n"
        "5. Each action starts where the previous action ended (to == next from).\n"
        "6. Total action durations between 10 and 20 seconds.\n"
        "7. Camera durations must sum to the scene duration. 2-4 camera shots.\n"
        "8. Title and description in simple Hinglish/Hindi romanized style.\n"
        "9. 'narration' MUST be in Hindi using Devanagari script, 2-4 short dramatic "
        "storytelling lines (like a narrator voicing a kids story). It must narrate "
        "exactly the events of the actions. Speaking time should be 8-16 seconds.\n"
    )


def call_gemini(api_key, model, prompt, system):
    url = GEMINI_URL.format(model=model)
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9},
    }
    r = requests.post(url, headers={"x-goog-api-key": api_key}, json=payload, timeout=90)
    if r.status_code == 404:
        raise RuntimeError(
            "Gemini model '%s' nahi mila (404). config/config.json me 'gemini_model' "
            "badal kar apne key ka sahi model name dalo (e.g. gemini-2.5-flash-lite)." % model
        )
    if r.status_code == 429:
        raise RuntimeError("Gemini rate limit (429). Thodi der baad retry karo.")
    if r.status_code != 200:
        raise RuntimeError("Gemini API error %s: %s" % (r.status_code, r.text[:300]))
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("Gemini ka response ajeeb tha: " + json.dumps(data)[:300])


def parse_json_text(text):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Gemini response me JSON nahi tha: " + text[:200])
        return json.loads(text[start:end + 1])


def validate_scene(data, locations, animations, max_duration):
    """Clear errors ke saath scene JSON validate karo."""
    for key in ("title", "scene", "camera"):
        if key not in data:
            raise ValueError("scene JSON me '%s' missing hai" % key)
    chars = data["scene"].get("characters") or []
    if not chars:
        raise ValueError("scene.characters khali hai")
    total = 0.0
    for char in chars:
        for act in char.get("actions", []):
            anim = str(act.get("animation", "")).lower()
            if anim not in animations:
                raise ValueError("ERROR: animation '%s' allowed list me nahi hai. Allowed: %s"
                                 % (anim, animations))
            for loc_key in ("from", "to", "location"):
                if loc_key in act and act[loc_key] not in locations:
                    raise ValueError("ERROR: location '%s' config/locations.json me nahi hai. Valid: %s"
                                     % (act[loc_key], sorted(locations)))
            total += float(act.get("duration", 3))
    if total > max_duration:
        raise ValueError("scene %ds ka hai, max %ds allowed" % (total, max_duration))
    for shot in data["camera"]:
        if shot.get("type") not in CAMERA_TYPES:
            raise ValueError("ERROR: camera type '%s' valid nahi. Valid: %s"
                             % (shot.get("type"), CAMERA_TYPES))
    return data


def consume_prompt(used_prompt):
    """prompts.txt se use hui line hatao, used.txt me log karo."""
    prompts_path = os.path.join(REPO_ROOT, "prompts", "prompts.txt")
    used_path = os.path.join(REPO_ROOT, "prompts", "used.txt")
    if not os.path.isfile(prompts_path):
        return
    with open(prompts_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    remaining = []
    removed = False
    for line in lines:
        if not removed and line.strip() and not line.strip().startswith("#"):
            removed = True  # ye wali line use hui
            continue
        remaining.append(line)
    with open(prompts_path, "w", encoding="utf-8") as f:
        f.writelines(remaining)
    with open(used_path, "a", encoding="utf-8") as f:
        f.write(used_prompt.rstrip() + "\n")


def next_prompt_from_file():
    prompts_path = os.path.join(REPO_ROOT, "prompts", "prompts.txt")
    if os.path.isfile(prompts_path):
        with open(prompts_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default="")
    ap.add_argument("--out", default=os.path.join(REPO_ROOT, "generated", "scene.json"))
    ap.add_argument("--no-consume", action="store_true")
    args = ap.parse_args()

    config = load_json(os.path.join(REPO_ROOT, "config", "config.json"))
    locations = load_json(os.path.join(REPO_ROOT, "config", "locations.json"))
    animations = list_animations()

    prompt = args.prompt.strip() or next_prompt_from_file() or config["default_prompt"]
    print("PROMPT: " + prompt)

    scene_data = None
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            print("Gemini call ho raha hai (model: %s)..." % config["gemini_model"])
            raw = call_gemini(api_key, config["gemini_model"], prompt,
                              build_system_prompt(locations, animations))
            scene_data = parse_json_text(raw)
            scene_data = validate_scene(scene_data, locations, animations,
                                        config.get("max_duration_sec", 20))
            print("Gemini scene OK")
        except (RuntimeError, ValueError, json.JSONDecodeError) as e:
            print("WARN: Gemini se scene nahi bana: %s" % e)
            scene_data = None
    else:
        print("WARN: GEMINI_API_KEY set nahi hai - fallback scene use hoga")

    if scene_data is None:
        if not config.get("use_fallback_scene", True):
            print("ERROR: scene generate nahi hua aur fallback disabled hai")
            return 1
        print("Fallback scene use ho raha hai (basic test scene)")
        scene_data = json.loads(json.dumps(FALLBACK_SCENE))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(scene_data, f, indent=2, ensure_ascii=False)
    print("SCENE_OK: %s" % args.out)

    if not args.no_consume:
        consume_prompt(prompt)
        print("Prompt queue update ho gayi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
