# Kaggle GPU render kernel.
# GitHub Actions ye script push karta hai - scene JSON niche embedded hota hai.
# Output: /kaggle/working/video.mp4 (Actions ise pull kar leta hai).
import glob
import os
import re
import shutil
import subprocess
import sys

REPO = "sudhansh37/3d-ai-shorts"
BRANCH = "main"
BLENDER_MAJOR = "4.5"
WORK = "/kaggle/working"

# GitHub Actions is file me scene.json inject karke push karta hai
SCENE_JSON = r"""
{{SCENE_JSON}}
"""


def run(cmd, **kw):
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True, **kw)


def main():
    os.chdir(WORK)

    # 1) repo ka code (public repo hai, auth nahi chahiye)
    if not glob.glob("3d-ai-shorts-*/blender/automation.py"):
        run(["curl", "-sL", "https://codeload.github.com/%s/zip/refs/heads/%s" % (REPO, BRANCH), "-o", "repo.zip"])
        run(["unzip", "-oq", "repo.zip"])
    src = sorted(glob.glob("3d-ai-shorts-*/"))[0]
    print("REPO_DIR:", src, flush=True)

    # 2) CC0 assets (Kenney character/houses/trees) - ek baar download
    run(["bash", os.path.join(src, "scripts", "fetch_assets.sh")], cwd=src)

    # 3) Blender download
    blender = os.path.join(WORK, "blender_bin", "blender")
    if not os.path.exists(blender):
        listing = subprocess.check_output(
            ["curl", "-s", "https://download.blender.org/release/Blender%s/" % BLENDER_MAJOR]).decode()
        ver = sorted(set(re.findall(r"blender-%s\.[0-9]+-linux-x64\.tar\.xz" % BLENDER_MAJOR, listing)))[-1]
        print("Blender:", ver, flush=True)
        run(["bash", "-c", "curl -sL 'https://download.blender.org/release/Blender%s/%s' | tar -xJ -C ." % (BLENDER_MAJOR, ver)])
        folder = glob.glob("blender-%s.*-linux-x64" % BLENDER_MAJOR)[0]
        shutil.move(folder, "blender_bin")
    run([blender, "--version"])

    # 4) scene.json likho (Actions ne inject kiya)
    with open("scene.json", "w") as f:
        f.write(SCENE_JSON)

    # 5) render (render.py me AUTO GPU mode hai: OptiX -> CUDA -> CPU)
    cmd = [blender, "-b", "-P", os.path.join(src, "blender", "automation.py"), "--",
           "--scene", os.path.join(WORK, "scene.json"),
           "--config", os.path.join(src, "config", "config.json"),
           "--locations", os.path.join(src, "config", "locations.json"),
           "--assets", os.path.join(src, "assets"),
           "--out", WORK]
    print("RENDER_CMD: " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print("ERROR: blender render fail hua (exit %d)" % r.returncode)
        sys.exit(1)

    # 6) verify
    if not os.path.exists(os.path.join(WORK, "video.mp4")):
        print("ERROR: video.mp4 nahi bana")
        sys.exit(1)
    print("KAGGLE_RENDER_OK", flush=True)

    # 7) cleanup - kernel output me sirf video + scene hona chahiye
    #    (warna 300MB+ blender bhi download hota output me)
    for junk in ("repo.zip",):
        if os.path.exists(junk):
            os.remove(junk)
    for d in ("blender_bin", src.rstrip("/")):
        if os.path.isdir(d):
            shutil.rmtree(d)
    print("Cleanup done. Output files:", os.listdir(WORK))


main()
