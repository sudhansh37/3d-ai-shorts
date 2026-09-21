#!/usr/bin/env bash
# CC0 assets download (Kenney - kenney.nl, GitHub mirror: shorepine/kenney).
# Ek hi baar download hote hain; pehle se present ho to skip. Commercial use OK.
set -e
BASE="https://raw.githubusercontent.com/shorepine/kenney/main/3d"
mkdir -p assets/character/Textures assets/houses/Textures assets/map/Textures

if [ ! -f assets/character/character.glb ]; then
  echo "Character download ho raha hai (Kenney blocky character, 28 animations)..."
  curl -sfL "$BASE/blocky-characters/character-a.glb" -o assets/character/character.glb
  curl -sfL "$BASE/blocky-characters/Textures/texture-a.png" -o assets/character/Textures/texture-a.png
fi
if [ ! -f assets/houses/house_1.glb ]; then
  echo "Houses download ho rahe hain..."
  curl -sfL "$BASE/city-suburban/building-type-a.glb" -o assets/houses/house_1.glb
  curl -sfL "$BASE/city-suburban/building-type-b.glb" -o assets/houses/house_2.glb
  curl -sfL "$BASE/city-suburban/building-type-c.glb" -o assets/houses/house_3.glb
  curl -sfL "$BASE/city-suburban/Textures/colormap.png" -o assets/houses/Textures/colormap.png
fi
if [ ! -f assets/map/tree.glb ]; then
  echo "Trees download ho rahe hain..."
  curl -sfL "$BASE/city-suburban/tree-large.glb" -o assets/map/tree.glb
  curl -sfL "$BASE/city-suburban/tree-small.glb" -o assets/map/tree_small.glb
  curl -sfL "$BASE/city-suburban/Textures/colormap.png" -o assets/map/Textures/colormap.png
fi
# sanity check
test -s assets/character/character.glb || { echo "ERROR: character download fail"; exit 1; }
echo "ASSETS_READY"
