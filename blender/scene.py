# Blender ke andar chalta hai (headless). Environment + character setup.
import math
import os

import bpy

SUPPORTED = (".glb", ".gltf", ".fbx")


def _first_file(folder):
    if not os.path.isdir(folder):
        return None
    for fn in sorted(os.listdir(folder)):
        if fn.lower().endswith(SUPPORTED):
            return os.path.join(folder, fn)
    return None


def _import_file(path):
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def _mat(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
    return m


def build_environment(locations, assets_dir):
    """Ground, road, sun, sky, houses, trees. Assets hone par unse, warna proxy."""
    scene = bpy.context.scene

    # sky
    world = bpy.data.worlds.new("shorts_world") if "shorts_world" not in bpy.data.worlds \
        else bpy.data.worlds["shorts_world"]
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.55, 0.75, 0.95, 1.0)

    # sun
    sun_data = bpy.data.lights.new("shorts_sun", "SUN")
    sun = bpy.data.objects.new("shorts_sun", sun_data)
    scene.collection.objects.link(sun)
    sun_data.energy = 3.0
    sun.rotation_euler = (math.radians(40), 0, math.radians(25))

    # ground
    bpy.ops.mesh.primitive_plane_add(size=140, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "ground"
    ground.data.materials.append(_mat("ground_mat", (0.18, 0.42, 0.12, 1.0)))

    # road
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.02))
    road = bpy.context.active_object
    road.name = "road"
    road.scale = (1.6, 28.0, 1.0)
    road.data.materials.append(_mat("road_mat", (0.22, 0.22, 0.22, 1.0)))

    # map (agar user ne diya hai)
    map_file = _first_file(os.path.join(assets_dir, "map"))
    if map_file:
        print("Map import: %s" % map_file)
        _import_file(map_file)

    # houses: asli assets ya proxy
    houses_dir = os.path.join(assets_dir, "houses")
    house_files = []
    if os.path.isdir(houses_dir):
        house_files = sorted(f for f in os.listdir(houses_dir) if f.lower().endswith(SUPPORTED))
    house_slots = sorted(n for n in locations if n.startswith("house"))
    for i, name in enumerate(house_slots):
        x, y, z = locations[name]
        if i < len(house_files):
            print("House import: %s -> %s" % (house_files[i], name))
            for o in _import_file(os.path.join(houses_dir, house_files[i])):
                o.location = (x, y - 6, z)
        else:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y - 6, 1.7))
            h = bpy.context.active_object
            h.name = name
            h.scale = (2.5, 2.2, 1.8)
            h.data.materials.append(_mat(name + "_mat", (0.75, 0.55, 0.35, 1.0)))
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.6, radius2=0,
                                            depth=1.6, location=(x, y - 6, 4.2))
            roof = bpy.context.active_object
            roof.name = name + "_roof"
            roof.rotation_euler[2] = math.radians(45)
            roof.data.materials.append(_mat(name + "_roof", (0.6, 0.2, 0.15, 1.0)))

    # trees proxy
    for name in sorted(locations):
        if not name.startswith("tree"):
            continue
        x, y, z = locations[name]
        bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=2.2, location=(x, y, 1.1))
        trunk = bpy.context.active_object
        trunk.name = name
        trunk.data.materials.append(_mat(name + "_trunk", (0.4, 0.25, 0.12, 1.0)))
        bpy.ops.mesh.primitive_ico_sphere_add(radius=1.1, location=(x, y, 2.9))
        crown = bpy.context.active_object
        crown.name = name + "_crown"
        crown.data.materials.append(_mat(name + "_crown", (0.1, 0.45, 0.15, 1.0)))


def get_character(assets_dir, start_location):
    """Character import (.glb/.fbx) ya proxy capsule. Return: mover object."""
    scene = bpy.context.scene
    char_file = _first_file(os.path.join(assets_dir, "character"))
    if char_file:
        print("Character import: %s" % char_file)
        objs = _import_file(char_file)
        arm = None
        for o in objs:
            if o.type == "ARMATURE":
                arm = o
                break
        root = arm if arm is not None else (objs[0] if objs else None)
        if root is None:
            raise RuntimeError("ERROR: character file khali hai: %s" % char_file)
        root.name = "hero"
        root.location = (start_location[0], start_location[1], 0)
        return root

    # proxy character (assets aane tak ka test dummy)
    print("WARN: assets/character/ me koi .glb/.fbx nahi - proxy dummy use ho raha hai")
    root = bpy.data.objects.new("hero", None)
    root.empty_display_size = 0.3
    scene.collection.objects.link(root)
    bpy.ops.mesh.primitive_capsule_add(radius=0.3, depth=0.9, location=(0, 0, 1.05))
    body = bpy.context.active_object
    body.name = "hero_body"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, 1.75))
    head = bpy.context.active_object
    head.name = "hero_head"
    hero_mat = _mat("hero_mat", (0.9, 0.6, 0.1, 1.0))
    body.data.materials.append(hero_mat)
    head.data.materials.append(hero_mat)
    for o in (body, head):
        o.parent = root
    root.location = (start_location[0], start_location[1], 0)
    return root
