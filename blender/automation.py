# Main Blender entry point (headless):
#   blender -b -P blender/automation.py -- --scene generated/scene.json --out output
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402  (blender ke andar hi chalta hai)

import animation  # noqa: E402
import camera  # noqa: E402
import render  # noqa: E402
import scene as scene_mod  # noqa: E402


def fail(msg):
    print("ERROR: %s" % msg)
    sys.exit(2)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    repo_root = os.path.dirname(HERE)
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default=os.path.join(repo_root, "generated", "scene.json"))
    ap.add_argument("--config", default=os.path.join(repo_root, "config", "config.json"))
    ap.add_argument("--locations", default=os.path.join(repo_root, "config", "locations.json"))
    ap.add_argument("--assets", default=os.path.join(repo_root, "assets"))
    ap.add_argument("--out", default=os.path.join(repo_root, "output"))
    args = ap.parse_args(argv)

    with open(args.scene) as f:
        data = json.load(f)
    with open(args.config) as f:
        config = json.load(f)
    with open(args.locations) as f:
        locations = json.load(f)

    # animation aliases (assets/manifest.json me ho to)
    aliases = {}
    manifest_path = os.path.join(args.assets, "manifest.json")
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path) as f:
                aliases = json.load(f).get("aliases") or {}
        except Exception as e:
            print("WARN: manifest.json padh nahi paye: %s" % e)

    fps = int(config.get("fps", 24))
    scene = bpy.context.scene
    scene.render.fps = fps

    # default scene saaf karo
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    characters = data.get("scene", {}).get("characters", [])
    if not characters:
        fail("scene JSON me characters khali hai")
    hero = characters[0]
    actions = hero.get("actions", [])
    if not actions:
        fail("hero ke actions khale hain")

    first = actions[0]
    start_loc = first.get("from") or first.get("location")
    if start_loc not in locations:
        fail("location '%s' config/locations.json me nahi hai (valid: %s)"
             % (start_loc, sorted(locations)))

    # 1) environment
    scene_mod.build_environment(locations, args.assets)

    # 2) character
    root = scene_mod.get_character(args.assets, locations[start_loc])

    # 3) animation library
    library = animation.collect_animation_library(args.assets)
    if not library:
        print("WARN: koi animation library nahi mili - bounce chalega")

    # 4) actions -> movement + animation
    face_offset = float(config.get("character_face_offset_deg", 0))
    cur_time = 0.0
    current_loc = start_loc
    for act in actions:
        anim_name = (act.get("animation") or "idle").lower()
        dur = float(act.get("duration", 3))
        if dur <= 0:
            fail("action duration invalid: %s" % act)
        start_f = int(cur_time * fps) + 1
        end_f = int((cur_time + dur) * fps)
        to_loc = act.get("to") or act.get("location") or current_loc
        if to_loc not in locations:
            fail("location '%s' config/locations.json me nahi hai (valid: %s)"
                 % (to_loc, sorted(locations)))
        if to_loc != current_loc:
            animation.move_character(root, locations[current_loc], locations[to_loc],
                                     start_f, end_f, face_offset)
        else:
            animation.place_character(root, locations[to_loc], start_f)
        action = animation.find_action(library, anim_name, aliases)
        if action is None:
            print("WARN: animation '%s' library me nahi - bounce chalega" % anim_name)
        mode = animation.apply_action(root, action, start_f, end_f)
        print("Action: %s %s->%s [%s]" % (anim_name, current_loc, to_loc, mode))
        current_loc = to_loc
        cur_time += dur

    scene_duration = float(data.get("scene", {}).get("duration") or cur_time)
    scene.frame_start = 1
    scene.frame_end = max(int(scene_duration * fps), 2)
    print("Scene duration: %.1fs (%d frames)" % (scene_duration, scene.frame_end))

    # 5) camera
    shots = data.get("camera") or [
        {"type": "wide", "target": "hero", "duration": scene_duration / 3},
        {"type": "follow", "target": "hero", "duration": scene_duration / 3},
        {"type": "closeup", "target": "hero", "duration": scene_duration / 3},
    ]
    camera.setup_camera(scene, shots, root)

    # 6) render
    out_path = render.setup_render(scene, config, args.out)
    print("Render start (engine=%s, samples=%s, %sx%s)..."
          % (config.get("render_engine"), config.get("cycles_samples"),
             config.get("resolution", [720, 1280])[0], config.get("resolution", [720, 1280])[1]))
    bpy.ops.render.render(animation=True)

    # Blender ffmpeg output me frame-range suffix lagata hai - rename karo
    mp4s = sorted(glob.glob(os.path.join(args.out, "*.mp4")))
    if mp4s:
        if os.path.exists(out_path):
            os.remove(out_path)
        os.replace(mp4s[0], out_path)
        print("RENDER_OK: %s" % out_path)
    else:
        fail("render hua par output/ me mp4 nahi mila")


main()
