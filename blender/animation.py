# Blender ke andar chalta hai. Animation library + movement.
import math
import os

import bpy

SUPPORTED = (".glb", ".gltf", ".fbx")


def collect_animation_library(assets_dir):
    """assets/animations/<name>.glb -> library['<name>'] = action.
    Character ke apne embedded actions bhi name se add hote hain."""
    library = {}
    anim_dir = os.path.join(assets_dir, "animations")
    if os.path.isdir(anim_dir):
        for fn in sorted(os.listdir(anim_dir)):
            if not fn.lower().endswith(SUPPORTED):
                continue
            stem = os.path.splitext(fn)[0].strip().lower()
            path = os.path.join(anim_dir, fn)
            before_actions = set(bpy.data.actions)
            before_objs = set(bpy.context.scene.objects)
            try:
                if fn.lower().endswith((".glb", ".gltf")):
                    bpy.ops.import_scene.gltf(filepath=path)
                else:
                    bpy.ops.import_scene.fbx(filepath=path)
            except Exception as e:
                print("WARN: animation import fail %s: %s" % (fn, e))
                continue
            new_actions = [a for a in bpy.data.actions if a not in before_actions]
            new_objs = [o for o in bpy.context.scene.objects if o not in before_objs]
            # imported dummy objects hata do (actions reh jaate hain)
            for o in new_objs:
                try:
                    bpy.data.objects.remove(o, do_unlink=True)
                except Exception:
                    pass
            if new_actions:
                library[stem] = new_actions[0]
                print("Animation loaded: %s (%s)" % (stem, new_actions[0].name))
            else:
                print("WARN: %s me koi action nahi mila" % fn)

    # character ke embedded actions (import ke baad bpy.data.actions me hote hain)
    for act in bpy.data.actions:
        key = act.name.strip().lower()
        if key and key not in library:
            library[key] = act
    return library


def find_action(library, name):
    name = (name or "").strip().lower()
    if name in library:
        return library[name]
    # partial match
    for key, act in library.items():
        if name and name in key:
            return act
    return None


def add_action_strips(armature, action, start_frame, end_frame):
    """Armature ke NLA me action ko loop karke fit karo."""
    ad = armature.animation_data_create()
    alen = max(1.0, float(action.frame_range[1] - action.frame_range[0]))
    cur = int(start_frame)
    track = ad.nla_tracks.new()
    track.name = action.name
    while cur < end_frame:
        strip = track.strips.new(name="%s.%d" % (action.name, cur), start=cur, action=action)
        cur += int(alen)


def fake_bounce_animation(root, start_frame, end_frame, base_z=0.0):
    """Animation na mile to simple bounce (proxy test ke liye)."""
    root.location.z = base_z
    root.keyframe_insert("location", index=2, frame=int(start_frame))
    for f in range(int(start_frame) + 2, int(end_frame) + 1, 4):
        t = (f - start_frame) * 0.55
        root.location.z = base_z + abs(math.sin(t)) * 0.22
        root.keyframe_insert("location", index=2, frame=f)
    root.location.z = base_z
    root.keyframe_insert("location", index=2, frame=int(end_frame))


def apply_action(character_root, action, start_frame, end_frame, is_proxy):
    if action is not None and character_root.type == "ARMATURE":
        try:
            add_action_strips(character_root, action, int(start_frame), int(end_frame))
            return "nla:%s" % action.name
        except Exception as e:
            print("WARN: NLA fail (%s) - bounce use hoga: %s" % (action.name, e))
    fake_bounce_animation(character_root, start_frame, end_frame)
    return "bounce"


def move_character(root, loc_from, loc_to, start_frame, end_frame, face_offset_deg=0.0):
    """A -> B movement keyframes (x,y) + facing rotation."""
    root.location.x = loc_from[0]
    root.location.y = loc_from[1]
    root.keyframe_insert("location", index=0, frame=int(start_frame))
    root.keyframe_insert("location", index=1, frame=int(start_frame))

    root.location.x = loc_to[0]
    root.location.y = loc_to[1]
    root.keyframe_insert("location", index=0, frame=int(end_frame))
    root.keyframe_insert("location", index=1, frame=int(end_frame))

    dx = loc_to[0] - loc_from[0]
    dy = loc_to[1] - loc_from[1]
    if abs(dx) + abs(dy) > 0.05:
        yaw = math.atan2(dx, dy) + math.radians(face_offset_deg)
        root.rotation_mode = "XYZ"
        root.rotation_euler = (0.0, 0.0, yaw)
        root.keyframe_insert("rotation_euler", frame=int(start_frame))
        root.keyframe_insert("rotation_euler", frame=int(end_frame))


def place_character(root, loc, frame):
    root.location.x = loc[0]
    root.location.y = loc[1]
    root.keyframe_insert("location", index=0, frame=int(frame))
    root.keyframe_insert("location", index=1, frame=int(frame))
