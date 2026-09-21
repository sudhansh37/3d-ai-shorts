# Kaggle GPU Rendering

GitHub Actions ka runner GPU nahi deta, isliye rendering ab **Kaggle ke free GPU (T4 x2 / P100)** pe hoti hai - 30 GPU-ghante/week free, matlab 100+ videos/week.

## Kaise kaam karta hai

```
Actions: Gemini se scene JSON banaya
   -> scene JSON kernel script me inject karke `kaggle kernels push` (GPU kernel chala)
   -> Actions status poll karta rehta hai (har 20 sec)
   -> complete hone par `kaggle kernels output` se video.mp4 wapas
   -> YouTube upload + artifact + commit
```
Secrets sirf GitHub pe rehte hain (Kaggle pe kuch nahi jata sirf scene JSON).

## Setup (bas 2 secrets)

1. kaggle.com -> apna profile -> **Settings** -> **API** -> **Create New Token** (kaggle.json download hoga)
2. Us file me `username` aur `key` hoga
3. GitHub repo -> Settings -> Secrets and variables -> Actions -> 2 secrets banao:
   - `KAGGLE_USERNAME` = tumhara Kaggle username
   - `KAGGLE_KEY` = kaggle.json wali key

Bas! Next run se render Kaggle GPU pe hoga (~5-10 min CPU ke 1.5 ghante ke bajaye).

## Notes
- Kaggle quota khatam ho jaye ya key galat ho to system khud **CPU render pe fall back** karti hai - pipeline kabhi nahi rukti (bas dheemi ho jaati hai)
- Render GPU pe chunna ho manually: Run workflow -> `render_backend` = `kaggle` (default) ya `actions`
- Kernel private rehta hai (`kaggle/kernel-metadata.json` me `is_private: true`)
- Kernel ka output sirf `video.mp4` + `scene.json` hota hai (cleanup code me hai)
