# Blender ke andar chalta hai. Automatic camera presets.
import math

import bpy

# camera offsets: (x, y, z) target se relative
PRESETS = {
    "wide":          (5.0, -9.0, 4.5),
    "medium":        (3.0, -4.5, 2.0),
    "closeup":       (1.0, -1.7, 1.6),
    "follow":        (2.2, -3.4, 1.7),
    "front":         (0.0, -4.2, 1.5),
    "back":          (0.0,  4.2, 1.6),
    "side_tracking": (3.4, -0.4, 1.5),
    "low_angle":     (1.6, -2.8, 0.35),
    "high_angle":    (3.0, -4.0, 6.5),
    "overhead":      (0.1, -0.3, 12.0),
}


def setup_camera(scene, shots, target_obj):
    """Ek camera banao, TRACK_TO target pe, har shot ke liye preset offset keyframes."""
    cam_data = bpy.data.cameras.new("shorts_cam")
    cam_data.lens = 32
    cam = bpy.data.objects.new("shorts_cam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam

    con = cam.constraints.new(type="TRACK_TO")
    con.target = target_obj
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"

    total_frames = scene.frame_end
    start = 1
    for shot in shots:
        stype = (shot.get("type") or "medium").lower()
        dur_frames = max(1, int(round(float(shot.get("duration", 3)) * scene.render.fps)))
        end = min(start + dur_frames, total_frames + 1)
        if end <= start:
            break

        if stype == "orbit":
            scene.frame_set(start)
            base = target_obj.matrix_world.translation
            steps = 8
            for i in range(steps + 1):
                f = start + int((end - 1 - start) * i / steps)
                ang = 2.0 * math.pi * i / steps
                cam.location = (base.x + 4.2 * math.sin(ang),
                                base.y + 4.2 * math.cos(ang),
                                1.9)
                cam.keyframe_insert("location", frame=f)
        elif stype in ("follow", "side_tracking"):
            off = PRESETS[stype]
            for f in range(start, end, 5):
                scene.frame_set(f)
                base = target_obj.matrix_world.translation
                cam.location = (base.x + off[0], base.y + off[1], off[2])
                cam.keyframe_insert("location", frame=f)
            last_f = max(end - 1, start)
            scene.frame_set(last_f)
            base = target_obj.matrix_world.translation
            cam.location = (base.x + off[0], base.y + off[1], off[2])
            cam.keyframe_insert("location", frame=last_f)
        else:
            off = PRESETS.get(stype, PRESETS["medium"])
            scene.frame_set(start)
            base = target_obj.matrix_world.translation
            cam.location = (base.x + off[0], base.y + off[1], off[2])
            cam.keyframe_insert("location", frame=start)

        print("Camera shot: %s (frames %d-%d)" % (stype, start, end - 1))
        start = end

    scene.frame_set(1)
    return cam
