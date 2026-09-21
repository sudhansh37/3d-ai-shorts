# 3D AI Shorts - Fully Automated YouTube Pipeline

Mobile-only, zero-budget, fully-automated 3D YouTube Shorts generator:

```
Gemini (story + Hindi narration script)
   -> scene JSON (locations, actions, camera shots)
   -> Blender render on Kaggle free GPU (Actions pe CPU fallback)
   -> Gemini TTS narration (free tier) + ffmpeg me audio merge
   -> YouTube auto-upload + video artifact
```

Sab kuch GitHub Actions pe roz raat **21:00 IST** apne aap chalta hai. Aapko kuch nahi karna.

## Abhi system me kya hai

- **Asli 3D character + animations**: Kenney CC0 blocky character (28 embedded animations - walk, run/sprint, idle, sit, wave, attack, die, pick-up...), Kenney houses, trees. Assets pehle hi download ho jaate hain (`scripts/fetch_assets.sh`). Commercial use bilkul OK - CC0 license.
- **Gemini TTS narration**: har video me Hindi storytelling voiceover (voice: Kore). Bina awaaz wala fallback bhi safe hai.
- **Kaggle GPU rendering**: ~5-10 min me render (CPU pe 2-3 ghante lagte the). Kaggle ka free quota: 30 GPU-ghante/week (~100+ videos).
- **Automation**: roz 21:00 IST khud chalti hai; prompts ki line se agli story uthati hai.

## Setup (ek baar)

### Required secrets (Settings -> Secrets and variables -> Actions)

| Secret | Kahan se milega |
|---|---|
| `GEMINI_API_KEY` | aistudio.google.com -> Get API key (free) |
| `GOOGLE_CLIENT_ID` | Google Cloud Console -> OAuth client (TV/Limited Input type) |
| `GOOGLE_CLIENT_SECRET` | wahi client ka secret |
| `YT_REFRESH_TOKEN` | Actions tab -> "YouTube Auth" workflow run karo - token khud print hoga |
| `KAGGLE_USERNAME` (optional) | kaggle.com -> Settings -> API (GPU render ke liye) |
| `KAGGLE_KEY` (optional) | wahi kaggle.json wali key |

Kaggle secrets na ho to CPU pe render hota hai (dheema par kaam karta hai).

### Prompt queue

`prompts/prompts.txt` me har line ek video idea hai - roz upar wali line use hoti hai. Jaise-jaise khatam hongi, nayi add karte raho (phone se GitHub website par file edit karke).

## Manual run karna ho to

Actions -> **Generate Video** -> Run workflow. Options:
- `prompt`: ek hi baar ke liye custom story
- `skip_upload`: video banega par YouTube pe nahi jayegi
- `render_backend`: `kaggle` (default, GPU) ya `actions` (CPU)

Video Actions run ke artifacts me download ho jaati hai (14 din tak rehti hai).

## Files

```
scripts/generate_scene.py   Gemini -> scene JSON (+narration script)
scripts/generate_tts.py     Gemini TTS -> narration.wav
scripts/fetch_assets.sh     CC0 assets download (Kenney)
scripts/youtube_upload.py   YouTube pe upload
blender/                    headless render pipeline (scene/animation/camera/render)
kaggle/kernel.py            Kaggle GPU render kernel
config/config.json          resolution, samples, TTS voice, models
config/locations.json       map ke points (house_1, road_center, tree_1...)
assets/manifest.json         available animations + aliases (run->sprint, wave->emote-yes...)
prompts/prompts.txt         story ideas queue
```

## Troubleshooting

- **Video me character nahi / pink**: assets download fail hua hoga - "CC0 assets download" step ka log dekho.
- **Awaaz nahi**: "Narration banao" step me TTS_OK ya TTS_SKIP ka reason dikhega (key/limit/narration missing).
- **Render bahut dheema**: Kaggle secrets check karo; ya config.json me cycles_samples kam karo.
- **Gemini 404**: config.json me `gemini_model` apne key ke hisaab se badlo.
- **60-din inactive repo wala schedule issue**: pipeline khud commit karti hai, isliye repo active rehta hai.

## Aage badhne ke ideas

- Aur characters/environments: `scripts/fetch_assets.sh` me nayi Kenney/Quaternius files ke URLs add karo (sab CC0).
- Character badalna: `assets/character/character.glb` replace karo (koi bhi .glb jisme animations ho).
- TTS voice: config.json me `tts_voice` badlo (Kore, Puck, Charon, Fenrir, Leda...).
