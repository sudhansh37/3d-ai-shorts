# Blender ke andar chalta hai. Render settings (vertical MP4).
import os

import bpy


def _configure_cycles_device(scene):
    """GPU setup: OptiX -> CUDA -> CPU fallback. (Kaggle T4/P100 pe GPU milta hai)"""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dev_type in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = dev_type
            prefs.get_devices()
            devices = [d for d in prefs.devices if d.type == dev_type]
            if not devices:
                continue
            for d in devices:
                d.use = True
            scene.cycles.device = "GPU"
            print("GPU device: %s x%d" % (dev_type, len(devices)))
            return "%s x%d" % (dev_type, len(devices))
        except Exception as e:
            print("WARN: %s setup fail: %s" % (dev_type, e))
    scene.cycles.device = "CPU"
    return "CPU"


def setup_render(scene, config, out_dir):
    w, h = config.get("resolution", [720, 1280])
    scene.render.resolution_x = int(w)
    scene.render.resolution_y = int(h)
    scene.render.resolution_percentage = int(config.get("resolution_percent", 100))

    engine = str(config.get("render_engine", "CYCLES")).upper()
    if engine == "CYCLES":
        scene.render.engine = "CYCLES"
        scene.cycles.samples = int(config.get("cycles_samples", 24))
        scene.cycles.use_denoising = True
        pref = str(config.get("cycles_device", "AUTO")).upper()
        if pref == "CPU":
            scene.cycles.device = "CPU"
            dev = "CPU"
        else:
            dev = _configure_cycles_device(scene)
        print("CYCLES_DEVICE: %s" % dev)
    else:
        scene.render.engine = "BLENDER_EEVEE"

    scene.render.fps = int(config.get("fps", 24))

    # MP4 H.264 direct output
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "AAC"

    os.makedirs(out_dir, exist_ok=True)
    scene.render.filepath = os.path.join(out_dir, "video")
    return os.path.join(out_dir, "video.mp4")
