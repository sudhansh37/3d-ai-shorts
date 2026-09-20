Ye folder me apne 3D assets daalo. Jab tak khali hai, system proxy dummy (cube houses, capsule hero) se kaam karega - pipeline test karne ke liye kaafi hai.

Format: .glb sabse behtar hai (Blender + Mixamo se dono se export hota hai), .gltf aur .fbx bhi chalega.

assets/
├── character/
│   └── character.glb        <- properly rigged character (Mixamo se bhi le sakte ho)
├── animations/              <- har file ek animation (Mixamo se download karke rename karo)
│   ├── idle.glb
│   ├── walk.glb
│   ├── run.glb
│   ├── wave.glb
│   └── jump.glb
├── houses/
│   ├── house_1.glb          <- locations.json ke house_1 ke liye
│   ├── house_2.glb
│   └── house_3.glb
└── map/
    └── map.glb              <- poora environment (road, ground, trees) - optional

Important:
1. File ka NAAM hi animation ka naam hai: run.glb -> "run". Gemini isi naam se choose karta hai.
2. Character aur animations Mixamo ke same rig se ho to NLA me perfectly fit honge.
3. character.glb export karte waqt scale 1.0 rakhna (height lagbhag 1.5-2 meter).
4. Agar character sahi direction me face nahi kar raha to config/config.json me
   "character_face_offset_deg" badlo (jaise 90 ya -90).
5. Files 100MB se badi nahi honi chahiye (GitHub limit) - badi files ko decimate/compress karo.

Mixamo se assets lene ka tarika (free):
- mixamo.com pe login -> character choose -> animations tab -> walk/run/wave download
  (format: FBX Binary ya GLTF) -> un files ko naam karke is folder me daal do.
