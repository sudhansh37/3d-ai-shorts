# Blender ke andar chalta hai (headless). Environment + character setup.
import math
import os

import bpy
import mathutils

SUPPORTED = (".glb", ".gltf", ".fbx")


def _first_file(folder):
    if not os.path.isdir(folder):
        return None
    for fn in sorted(os.listdir(folder)):
        if fn.lower().endswith(SUPPORTED):
            return os.path.join(folder, fn)
    return None


def _files(folder):
    if not os.path.isdir(folder):
        return []
    return sorted(os.path.join(folder, f) for f in os.listdir(folder)
                  if f.lower().endswith(SUPPORTED))


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
    """Ground, road, sun, sky, asli houses + trees (assets se), warna proxy."""
    scene = bpy.context.scene

    world = bpy.data.worlds["shorts_world"] if "shorts_world" in bpy.data.worlds \
        else bpy.data.worlds.new("shorts_world")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.55, 0.75, 0.95, 1.0)

    sun_data = bpy.data.lights.new("shorts_sun", "SUN")
    sun = bpy.data.objects.new("shorts_sun", sun_data)
    scene.collection.objects.link(sun)
    sun_data.energy = 3.0
    sun.rotation_euler = (math.radians(40), 0, math.radians(25))

    bpy.ops.mesh.primitive_plane_add(size=140, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "ground"
    ground.data.materials.append(_mat("ground_mat", (0.18, 0.42, 0.12, 1.0)))

    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.02))
    road = bpy.context.active_object
    road.name = "road"
    road.scale = (28.0, 1.6, 1.0)
    road.data.materials.append(_mat("road_mat", (0.22, 0.22, 0.22, 1.0)))

    # houses: asli assets (house_1.glb, house_2.glb...) ya proxy cube
    houses_dir = os.path.join(assets_dir, "houses")
    house_files = _files(houses_dir)
    house_slots = sorted(n for n in locations if n.startswith("house"))
    for i, name in enumerate(house_slots):
        x, y, z = locations[name]
        if i < len(house_files):
            print("House import: %s -> %s" % (os.path.basename(house_files[i]), name))
            for o in _import_file(house_files[i]):
                o.location = (x, y + 6, z)
        else:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y - 7, 1.7))
            h = bpy.context.active_object
            h.name = name
            h.scale = (2.5, 2.2, 1.8)
            h.data.materials.append(_mat(name + "_mat", (0.75, 0.55, 0.35, 1.0)))
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.6, radius2=0,
                                            depth=1.6, location=(x, y - 7, 4.2))
            roof = bpy.context.active_object
            roof.name = name + "_roof"
            roof.rotation_euler[2] = math.radians(45)
            roof.data.materials.append(_mat(name + "_roof", (0.6, 0.2, 0.15, 1.0)))

    # trees: map/ folder ke tree files use karo, warna proxy
    map_files = _files(os.path.join(assets_dir, "map"))
    big_trees = [f for f in map_files
                 if os.path.basename(f).lower().startswith("tree") and "small" not in f.lower()]
    small_trees = [f for f in map_files if "small" in os.path.basename(f).lower()]
    tree_big = big_trees[0] if big_trees else None
    tree_small = small_trees[0] if small_trees else tree_big
    tree_names = sorted(n for n in locations if n.startswith("tree"))
    for i, name in enumerate(tree_names):
        x, y, z = locations[name]
        f = tree_big if i % 2 == 0 else (tree_small or tree_big)
        if f:
            for o in _import_file(f):
                o.location = (x, y, z)
        else:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=2.2, location=(x, y, 1.1))
            trunk = bpy.context.active_object
            trunk.name = name
            trunk.data.materials.append(_mat(name + "_trunk", (0.4, 0.25, 0.12, 1.0)))
            bpy.ops.mesh.primitive_ico_sphere_add(radius=1.1, location=(x, y, 2.9))
            crown = bpy.context.active_object
            crown.name = name + "_crown"
            crown.data.materials.append(_mat(name + "_crown", (0.1, 0.45, 0.15, 1.0)))


def get_character(assets_dir, start_location):
    """Character import (.glb/.fbx) ya proxy. Movement-root object return karta hai.
    glTF ke embedded animations ke active actions hata deta hai taaki NLA chalaye."""
    scene = bpy.context.scene
    char_file = _first_file(os.path.join(assets_dir, "character"))
    if char_file:
        print("Character import: %s" % char_file)
        objs = _import_file(char_file)
        arm = next((o for o in objs if o.type == "ARMATURE"), None)
        if arm is not None:
            root = arm
        else:
            tops = [o for o in objs if o.parent is None]
            root = tops[0] if tops else objs[0]
        if root is None:
            raise RuntimeError("ERROR: character file khali hai: %s" % char_file)
        root.name = "hero"

        # height normalize (0.8m-4m ke bahar ho to ~1.8m kar do)
        try:
            bpy.context.view_layer.update()
        except Exception:
            pass
        zs = []
        for o in objs:
            if o.type == "MESH":
                for c in o.bound_box:
                    zs.append((o.matrix_world @ mathutils.Vector(c)).z)
        if zs:
            h = max(zs) - min(zs)
            if 0.05 < h and (h < 0.8 or h > 4.0):
                root.scale = (root.scale[0] * (1.8 / h),
                              root.scale[1] * (1.8 / h),
                              root.scale[2] * (1.8 / h))
                print("Character scale: %.2fm -> 1.8m" % h)

        root.location = (start_location[0], start_location[1], 0)

        # glTF import har object pe 'static' action assign karta hai -
        # NLA ke liye active action hatao
        for o in objs:
            if o.animation_data and o.animation_data.action is not None:
                o.animation_data.action = None
        return root

    # proxy character (assets na mile to test dummy)
    print("WARN: assets/character/ me koi .glb/.fbx nahi - proxy dummy use ho raha hai")
    root = bpy.data.objects.new("hero", None)
    root.empty_display_size = 0.3
    scene.collection.objects.link(root)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=0.95, location=(0, 0, 1.0))
    body = bpy.context.active_object
    body.name = "hero_body"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, 1.72))
    head = bpy.context.active_object
    head.name = "hero_head"
    hero_mat = _mat("hero_mat", (0.9, 0.6, 0.1, 1.0))
    body.data.materials.append(hero_mat)
    head.data.materials.append(hero_mat)
    for o in (body, head):
        o.parent = root
    root.location = (start_location[0], start_location[1], 0)
    return root
