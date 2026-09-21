# Blender ke andar chalta hai. Animation library + movement.
import math
import os

import bpy

SUPPORTED = (".glb", ".gltf", ".fbx")


def collect_animation_library(assets_dir):
    """assets/animations/<name>.glb files + character ke embedded actions.
    Return: {name_lower: action}"""
    library = {}
    anim_dir = os.path.join(assets_dir, "animations")
    if os.path.isdir(anim_dir):
        for fn in sorted(os.listdir(anim_dir)):
            if not fn.lower().endswith(SUPPORTED):
                continue
            stem = os.path.splitext(fn)[0].strip().lower()
            path = os.path.join(anim_dir, fn)
            before_actions = set(a.name for a in bpy.data.actions)
            before_objs = set(bpy.context.scene.objects)
            try:
                if fn.lower().endswith((".glb", ".gltf")):
                    bpy.ops.import_scene.gltf(filepath=path)
                else:
                    bpy.ops.import_scene.fbx(filepath=path)
            except Exception as e:
                print("WARN: animation import fail %s: %s" % (fn, e))
                continue
            new_actions = [a for a in bpy.data.actions if a.name not in before_actions]
            new_objs = [o for o in bpy.context.scene.objects if o not in before_objs]
            for o in new_objs:
                try:
                    bpy.data.objects.remove(o, do_unlink=True)
                except Exception:
                    pass
            if new_actions:
                library[stem] = new_actions[0]
                print("Animation loaded: %s" % stem)

    # character ke embedded actions (Kenney style - ek hi .glb me saare)
    for act in bpy.data.actions:
        key = act.name.strip().lower()
        if key and key not in library:
            library[key] = act
    print("Animation library: %d actions" % len(library))
    return library


def find_action(library, name, aliases=None):
    name = (name or "").strip().lower()
    if aliases:
        mapped = aliases.get(name)
        if mapped:
            name = mapped.strip().lower()
    if name in library:
        return library[name]
    for key, act in library.items():
        if name and name in key:
            return act
    return None


def add_action_strips(action, start_frame, end_frame):
    """Action ko uske slot-objects pe NLA strips se loop karke fit karo.
    (Kenney style: ek action multiple objects ko animate karta hai - Blender 4.4+
    strip banate waqt khud sahi slot chun leta hai.)"""
    slot_names = set()
    try:
        for s in action.slots:
            slot_names.add(s.name_display)
    except Exception:
        pass
    targets = [o for o in bpy.context.scene.objects if o.name in slot_names]
    if not targets:
        targets = [o for o in bpy.context.scene.objects if o.animation_data]
    if not targets:
        return 0
    alen = max(1.0, float(action.frame_range[1] - action.frame_range[0]))
    for obj in targets:
        ad = obj.animation_data_create()
        if ad.action == action:
            ad.action = None
        track = ad.nla_tracks.new()
        track.name = action.name
        cur = int(start_frame)
        n = 0
        while cur < end_frame:
            try:
                track.strips.new(name="%s.%d" % (action.name, n),
                                 start=cur, action=action)
            except Exception as e:
                print("WARN: strip fail on %s: %s" % (obj.name, e))
                break
            cur += int(alen)
            n += 1
    return len(targets)


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


def apply_action(character_root, action, start_frame, end_frame):
    if action is not None:
        try:
            n = add_action_strips(action, int(start_frame), int(end_frame))
            if n > 0:
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
