# 3D AI Shorts - Fully Automated Pipeline

Gemini se story -> Blender se 3D render -> YouTube pe auto upload. Sab kuch GitHub Actions pe
chalta hai - PC/GPU ki zaroorat nahi, mobile se hi sab control hota hai.

```
GitHub Actions (roz 21:00 IST, khud chalti hai)
   -> Gemini API se prompt ka scene JSON
   -> Blender headless render (vertical 9:16 MP4)
   -> YouTube Data API v3 se auto upload
   -> results wapas repo me commit (repo active rehta hai)
```

Abhi assets daale bina bhi chalega - dummy cube houses + capsule hero se poora pipeline test
ho jaata hai. Baad me `assets/` me apne files daal do.

---

## SETUP (ek baar karna hai, ~15 minute)

Repo abhi **private** hai - pehle YouTube token bana lo, PHIR public karna (step 5).

### Step 1: Secrets daalo (4 cheezein)

GitHub repo -> **Settings -> Secrets and variables -> Actions -> New repository secret**:

| Secret ka naam | Value kya hai |
|---|---|
| `GEMINI_API_KEY` | Tumhara Gemini API key (aistudio.google.com se) |
| `GOOGLE_CLIENT_ID` | Google Cloud Console -> OAuth client ka Client ID |
| `GOOGLE_CLIENT_SECRET` | Usi OAuth client ka Client Secret |
| `YT_REFRESH_TOKEN` | Step 2 me banega (abhi chhod do) |

(Kaggle key abhi nahi chahiye - GPU upgrade baad me. Chaho to `KAGGLE_USERNAME` aur
`KAGGLE_KEY` bhi add kar sakte ho, future ke liye.)

### Step 2: YouTube refresh token banao (one-time)

Pehle Google Cloud Console me check karo: APIs & Services -> "YouTube Data API v3" **enabled**
ho + OAuth consent screen banao (External, test users me apna email add karo).

Phir:

1. Repo -> **Actions** tab -> **YouTube Auth** workflow -> **Run workflow**
   - mode = `start` -> logs me ek lambi URL milegi
2. Wahi URL phone ke browser me kholo -> apne Google account se **Allow** karo
   - page `localhost` pe fail hoga - **YE NORMAL HAI**
3. Address bar se **poora URL** copy karo (`http://localhost:8080/?code=...` wala)
4. **YouTube Auth** workflow dobara **Run workflow** karo:
   - mode = `exchange`
   - redirect_url = wahi poora URL
5. Logs me **refresh token** milega -> usko secret banao: `YT_REFRESH_TOKEN`
6. Us workflow run ko **delete kar do** (run pe click -> ... menu -> Delete workflow run)
   - kyunki token logs me dikh raha hai

### Step 3: Test run karo

Actions -> **Generate Video** -> Run workflow -> `skip_upload = true` (pehli baar).
5-30 minute me run green ho jaye to:
- run ke page pe **Artifacts** section se `video-xxxx` download karke dekho

### Step 4: Pehli asli upload

- `config/config.json` me `youtube_privacy` check karo (`private` = sirf tum dikhao,
  `unlisted` = link wale, `public` = sabko)
- Generate Video -> Run workflow (skip_upload = false)
- NOTE: Google ka **audit** hone tak API se upload videos private-lock hoti hain -
  console.developers.google.com pe "Verification" apply karo, uske baad public hongi

### Step 5: Repo PUBLIC karo (important - free unlimited runs ke liye)

Settings -> General -> sabse neeche Danger Zone -> **Change visibility -> Public**.
Public repo me Actions ke standard runners free aur unlimited hain. Secrets encrypted
rehte hain, code dikhna koi problem nahi. (Private me sirf 2000 min/month milte hain.)

Daily schedule pehle se laga hai: **roz 21:00 IST**. Har run apna result repo me commit
karta hai - isse repo "active" rehta hai aur GitHub ka 60-din auto-disable rule lagta hi nahi.

---

## Roz ka use

- **Prompts ki queue**: `prompts/prompts.txt` me ek line = ek video. Roz upar se ek line
  use hoti hai aur `prompts/used.txt` me chali jaati hai. Kabhi bhi nayi lines add kar do.
  File khali ho to `config.json` ka `default_prompt` use hota hai.
- **Manual run**: Actions -> Generate Video -> Run workflow -> prompt bhi de sakte ho.
- **Schedule badalna**: `.github/workflows/generate-video.yml` me `cron:` line badlo (UTC time).

## Config (`config/config.json`)

| Key | Matlab |
|---|---|
| `resolution` | `[720, 1280]` test ke liye; final `[1080, 1920]` (render slow hoga) |
| `cycles_samples` | Quality - kam = fast (12-48) |
| `gemini_model` | Agar 404 aaye to apne key ka model name dalo |
| `youtube_privacy` | `private` / `unlisted` / `public` |
| `character_face_offset_deg` | Character ulta side dekh raha ho to 90 / -90 karo |
| `use_fallback_scene` | Gemini fail ho to test scene se render (true = pipeline kabhi nahi rukti) |

## Locations (`config/locations.json`)

Named spots jahan character ja sakta hai: `house_1`, `road_center`, `tree_1`, etc.
Yahan coordinates badlo to character wahan jayega. Naya naam add karoge to Gemini use
karne lagega (system prompt automatically uthata hai).

## Assets

`assets/README.md` padho - character, animations (walk/run/wave...), houses, map kaise
daalna hai. **File ka naam hi animation ka naam hai** (`run.glb` = "run").

## Trouble ho to

- **Gemini 404**: `gemini_model` galat hai - config me sahi name dalo.
- **Video me sirf dummy scene**: normal hai jab tak assets nahi dale.
- **Upload 401/403**: refresh token expire/invalid - Step 2 dobara karo.
- **Render bahut slow**: `cycles_samples` ghatao ya `resolution` 540x960 karo.
- **Actions tab me schedule nahi dikh raha**: repo 60 din se inactive thi - koi bhi commit
  push karo, phir Enable workflow.

## Aage (Kaggle GPU)

GitHub runner pe GPU nahi hota (CPU render). 1080p ya heavy scenes ke liye Kaggle ka
free GPU (30 ghante/week) jodna planned hai - architecture ready hai, `KAGGLE_USERNAME` /
`KAGGLE_KEY` secrets already rakh sakte ho.
