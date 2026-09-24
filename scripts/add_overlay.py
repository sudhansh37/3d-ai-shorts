#!/usr/bin/env python3
"""
Video me styled captions (narration) + watermark ('zynr2') burn karta hai.
ASS subtitle format + ffmpeg ke ass filter se:
- Captions: neeche-center, bold white text, kaala outline (Hindi Devanagari support)
  narration ke sentences video duration me barabar baante jaate hain
- Watermark: bottom-right corner me hamesha dikhta rehta hai
Usage:
  python scripts/add_overlay.py --video output/video.mp4 --json generated/scene.json --out output/final.mp4
"""
import argparse
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASS_HEADER = (
    "[Script Info]\n"
    "ScriptType: v4.00+\n"
    "PlayResX: 720\n"
    "PlayResY: 1280\n"
    "WrapStyle: 0\n"
    "ScaledBorderAndShadow: yes\n"
    "\n"
    "[V4+ Styles]\n"
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
    "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
    "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
    "MarginL, MarginR, MarginV, Encoding\n"
    # Captions: bold white + black outline, bottom-center
    "Style: Cap,Noto Sans Devanagari,46,&H00FFFFFF,&H000000FF,&H00101010,&H96000000,"
    "-1,0,0,0,100,100,0,0,1,3,1,2,46,46,150,1\n"
    # Watermark: semi-transparent white italic, bottom-right corner
    "Style: Brand,DejaVu Sans,32,&H5AFFFFFF,&H000000FF,&H00000000,&H96000000,"
    "-1,-1,0,0,100,100,2,0,1,2,0,3,40,40,48,1\n"
    "\n"
    "[Events]\n"
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
)


def video_duration(path):
    """ffprobe se, nahi to ffmpeg se duration nikalo."""
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path]).decode().strip()
        return float(out)
    except Exception:
        pass
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", path],
                       capture_output=True, text=True)
    for line in (p.stderr or "").splitlines():
        if "Duration:" in line:
            t = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 10.0


def ass_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


def split_caption_lines(narration, max_chars=52):
    """Narration ko sentence/chhote chunks me todo (Hindi danda + . ! ?)."""
    parts = [p.strip() for p in re.split(r"[\u0964.!?\n]", narration) if p.strip()]
    final = []
    for p in parts:
        if len(p) > max_chars:
            words = p.split()
            cur = ""
            for w in words:
                if len(cur) + len(w) + 1 > max_chars and cur:
                    final.append(cur)
                    cur = w
                else:
                    cur = (cur + " " + w).strip()
            if cur:
                final.append(cur)
        else:
            final.append(p)
    return final or [narration.strip()]


def build_ass(narration, duration, brand):
    events = []
    if narration:
        lines = split_caption_lines(narration)
        n = max(1, len(lines))
        for i, text in enumerate(lines):
            start = duration * i / n
            end = duration * (i + 1) / n
            safe = text.replace("{", "(").replace("}", ")")
            events.append("Dialogue: 0,%s,%s,Cap,,0,0,0,,%s"
                          % (ass_time(start), ass_time(end), safe))
    if brand:
        safe_brand = brand.replace("{", "(").replace("}", ")")
        events.append("Dialogue: 0,%s,%s,Brand,,0,0,0,,%s"
                      % (ass_time(0), ass_time(duration + 1), safe_brand))
    return ASS_HEADER + "\n".join(events) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(os.path.join(REPO_ROOT, "config", "config.json")) as f:
        cfg = json.load(f)
    brand = (cfg.get("watermark") or "").strip()
    narration = ""
    if os.path.isfile(args.json):
        with open(args.json, encoding="utf-8") as f:
            narration = (json.load(f).get("narration") or "").strip()

    if not narration and not brand:
        print("OVERLAY_SKIP: narration bhi nahi, watermark bhi nahi")
        return 0

    duration = video_duration(args.video)
    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    ass_path = os.path.join(out_dir, "overlay.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(build_ass(narration, duration, brand))
    print("Overlay: %d caption(s) + watermark '%s' (%.1fs video)"
          % (len(split_caption_lines(narration)) if narration else 0, brand or "-", duration))

    # ass filter ke liye path escape (colon wala issue se bachne ko)
    esc = ass_path.replace("\\", "/").replace(":", "\\:")
    cmd = ["ffmpeg", "-y", "-i", args.video,
           "-vf", "ass=%s" % esc,
           "-c:v", "libx264", "-crf", "19", "-preset", "medium",
           "-c:a", "copy", args.out]
    subprocess.run(cmd, check=True)
    print("OVERLAY_OK: %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
