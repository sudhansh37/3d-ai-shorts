# Blender ke andar chalta hai. Render settings (vertical MP4).
import os

import bpy


def setup_render(scene, config, out_dir):
    w, h = config.get("resolution", [720, 1280])
    scene.render.resolution_x = int(w)
    scene.render.resolution_y = int(h)
    scene.render.resolution_percentage = int(config.get("resolution_percent", 100))

    engine = str(config.get("render_engine", "CYCLES")).upper()
    if engine == "CYCLES":
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = int(config.get("cycles_samples", 24))
        scene.cycles.use_denoising = True
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
