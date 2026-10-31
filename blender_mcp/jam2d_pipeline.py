"""Non-destructive Blender -> jam2d export. Run only explicitly with Blender --background."""
import argparse
import json
import math
from pathlib import Path
import sys

STATES = {'spider': ['idle', 'walk', 'turn_left', 'turn_right', 'jump', 'web'],
          'human': ['idle', 'walk', 'run', 'attack', 'collision', 'fall']}
LOOP = {'idle', 'walk', 'run', 'turn_left', 'turn_right'}


def arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--output', type=Path, required=True, help='New, empty export directory')
    p.add_argument('--actor', choices=['all', 'human', 'spider'], default='all')
    p.add_argument('--spider-source', type=Path, default=Path('model/spider_with_animation_1k_texture.glb'))
    p.add_argument('--human-source', type=Path, default=Path('model/persona/Remy.fbx'))
    p.add_argument('--yaw', type=float, default=0, help='Camera azimuth offset in degrees')
    p.add_argument('--samples', type=int, default=32)
    p.add_argument('--action-map', type=Path, help='JSON actor -> state -> exact action name')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    return p.parse_args(argv)


def main():
    args = arguments()
    import bpy
    from mathutils import Vector
    root = args.root.resolve()
    out = args.output.resolve()
    # Never write into the source model tree, even when output is empty.
    models = (root / 'model').resolve()
    if out == models or models in out.parents:
        raise ValueError('Output must be outside model/')
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output directory must be empty; existing exports are not overwritten')
    out.mkdir(parents=True, exist_ok=True)
    mappings = json.loads(args.action_map.read_text(encoding='utf-8')) if args.action_map else {}
    manifest = {'version': 1, 'frameWidth': 512, 'frameHeight': 512, 'frames': 8,
                'fps': 24, 'actors': {}, 'provenance': {}}

    def load(path):
        before = set(bpy.data.objects)
        suffix = path.suffix.lower()
        if suffix == '.fbx':
            bpy.ops.import_scene.fbx(filepath=str(path))
        elif suffix in ('.glb', '.gltf'):
            bpy.ops.import_scene.gltf(filepath=str(path))
        elif suffix == '.blend':
            with bpy.data.libraries.load(str(path), link=False) as (source, dest):
                dest.objects = source.objects
            for obj in dest.objects:
                if obj: bpy.context.scene.collection.objects.link(obj)
        else:
            raise ValueError(f'Unsupported source: {path}')
        return list(set(bpy.data.objects) - before)

    actors = STATES if args.actor == 'all' else [args.actor]
    for actor in actors:
        scene = bpy.data.scenes.new(f'Jam2D_{actor}')
        bpy.context.window.scene = scene
        source = (root / (args.human_source if actor == 'human' else args.spider_source)).resolve()
        if not source.is_file(): raise FileNotFoundError(source)
        objects = load(source)
        meshes = [o for o in objects if o.type == 'MESH']
        rigs = [o for o in objects if o.type == 'ARMATURE']
        if not meshes: raise ValueError(f'No mesh in {source}')
        rig = rigs[0] if rigs else None
        initial_action = rig.animation_data.action if rig and rig.animation_data else None
        sources = [str(source.relative_to(root)) if source.is_relative_to(root) else str(source)]
        action_by_state = {}
        if actor == 'human':
            pack = root / 'model/persona/Action Adventure Pack'
            for state, name in {'idle': 'idle.fbx', 'walk': 'walking.fbx', 'run': 'running.fbx',
                                'collision': 'hard landing.fbx', 'fall': 'falling idle.fbx'}.items():
                path = pack / name
                if not path.exists(): continue
                imported = load(path)
                cliprig = next((o for o in imported if o.type == 'ARMATURE'), None)
                if rig and cliprig and cliprig.animation_data and cliprig.animation_data.action:
                    if set(rig.pose.bones.keys()) != set(cliprig.pose.bones.keys()):
                        raise ValueError(f'Incompatible skeleton: {path}; retarget explicitly')
                    action_by_state[state] = cliprig.animation_data.action
                    action_by_state[state].use_fake_user = True
                    sources.append(str(path.relative_to(root)))
                for obj in imported: bpy.data.objects.remove(obj, do_unlink=True)
        for state, name in mappings.get(actor, {}).items():
            action = bpy.data.actions.get(name)
            if action is None: raise ValueError(f'Action not found: {name}')
            action_by_state[state] = action
        if initial_action and actor == 'spider':
            action_by_state.setdefault('walk', initial_action)
        # Discard source lights/cameras and NLA influences; imported files are never saved.
        for obj in objects:
            if obj.type in ('LIGHT', 'CAMERA'): obj.hide_render = True
        if rig:
            rig.animation_data_create()
            for track in rig.animation_data.nla_tracks: track.mute = True
        pivot = bpy.data.objects.new('JamVisualRoot', None)
        scene.collection.objects.link(pivot)
        for obj in objects:
            if obj.parent is None:
                matrix = obj.matrix_world.copy(); obj.parent = pivot; obj.matrix_world = matrix
        material = bpy.data.materials.new('JamNoir'); material.diffuse_color = (.035, .065, .085, 1)
        material.use_nodes = True
        bsdf = material.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (.035, .065, .085, 1)
        bsdf.inputs['Roughness'].default_value = .65
        for obj in meshes:
            obj.data.materials.clear(); obj.data.materials.append(material)
        scene.render.engine = 'CYCLES'; scene.cycles.samples = max(1, args.samples)
        scene.render.resolution_x = scene.render.resolution_y = 512
        scene.render.resolution_percentage = 100; scene.render.film_transparent = True
        scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
        scene.render.image_settings.color_depth = '8'; scene.render.fps = 24
        scene.world = bpy.data.worlds.new('JamWorld'); scene.world.color = (.05, .05, .05)
        scene.view_settings.view_transform = 'Standard'
        camera_data = bpy.data.cameras.new('JamOrthographic'); camera_data.type = 'ORTHO'
        camera = bpy.data.objects.new('JamCamera', camera_data); scene.collection.objects.link(camera); scene.camera = camera
        # +X camera is strict side view for Mixamo's Y-facing FBX; yaw adapts other source axes.
        yaw = math.radians(args.yaw)
        direction = Vector((math.cos(yaw), math.sin(yaw), 0))
        for name, offset, energy, color in [('Rim', (3, 2, 4), 900, (.55, .75, 1)), ('Fill', (-2, -3, 2), 450, (1, .4, .3))]:
            data = bpy.data.lights.new(name, 'AREA'); data.energy = energy; data.color = color; data.shape = 'DISK'; data.size = 4
            obj = bpy.data.objects.new(name, data); scene.collection.objects.link(obj); obj.location = offset
            obj.rotation_euler = (-obj.location).to_track_quat('-Z', 'Y').to_euler()
        state_meta = {}
        # Evaluate source clips, then in-place stylization for missing clips. No gameplay root motion.
        def pose(state, frame):
            p = frame / 7; phase = frame / 8 * math.tau
            pivot.location = (0, 0, 0); pivot.rotation_euler = (0, 0, 0); pivot.scale = (1, 1, 1)
            action = action_by_state.get(state)
            if rig:
                rig.animation_data.action = action
                for bone in rig.pose.bones:
                    bone.location = (0, 0, 0); bone.rotation_mode = 'QUATERNION'
                    bone.rotation_quaternion = (1, 0, 0, 0); bone.scale = (1, 1, 1)
                if action:
                    start, end = action.frame_range
                    scene.frame_set(int(start + (end - start) * (frame / 8 if state in LOOP else p)))
                    # Remove translation from skeleton root/hips, retain actual limb animation.
                    for bone in rig.pose.bones:
                        if bone.parent is None or bone.name.lower().endswith('hips'):
                            bone.location.x = bone.location.y = 0
                elif actor == 'human':
                    for bone in rig.pose.bones:
                        if bone.name.endswith('Arm'):
                            bone.rotation_mode = 'XYZ'; bone.rotation_euler.z = (-1 if 'Left' in bone.name else 1) * 1.2
                            if state == 'attack' and 'Right' in bone.name: bone.rotation_euler.x = math.sin(p * math.pi) * 2.4
                        if bone.name.endswith('Head'): bone.rotation_mode = 'XYZ'; bone.rotation_euler.y = math.sin(phase) * .12
            if actor == 'spider' and not action:
                if state.startswith('turn'): pivot.rotation_euler.z = math.sin(phase) * (.22 if state == 'turn_left' else -.22)
                if state == 'jump': pivot.scale.z = 1 - .3 * math.sin(p * math.pi); pivot.location.z = .15 * math.sin(p * math.pi)
                if state == 'web': pivot.scale.y = 1 + .12 * math.sin(p * math.pi)
            if state == 'fall': pivot.rotation_euler.x = p * 1.35
            if state == 'collision': pivot.rotation_euler.x = -.2 * math.sin(p * math.pi)
            bpy.context.view_layer.update()
        # One camera fit over EVERY state/frame: no framing pulsation or cropped fall.
        bounds = []
        for state in STATES[actor]:
            for frame in range(8):
                pose(state, frame)
                deps = bpy.context.evaluated_depsgraph_get()
                for obj in meshes:
                    evaluated = obj.evaluated_get(deps)
                    bounds.extend(evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box)
        low = Vector(tuple(min(v[i] for v in bounds) for i in range(3)))
        high = Vector(tuple(max(v[i] for v in bounds) for i in range(3)))
        center = (low + high) / 2; span = max((high - low).length, .1)
        camera.location = center + direction * span * 3
        camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
        camera_data.ortho_scale = span * 1.12
        camera_data.clip_end = span * 20
        for state in STATES[actor]:
            folder = out / actor; folder.mkdir(exist_ok=True)
            frames = folder / f'{state}-frames'; frames.mkdir()
            pixels = [0.0] * (4096 * 512 * 4)
            for frame in range(8):
                pose(state, frame)
                file = frames / f'{frame:02d}.png'; scene.render.filepath = str(file)
                bpy.ops.render.render(write_still=True)
                image = bpy.data.images.load(str(file), check_existing=False)
                data = list(image.pixels[:])
                for y in range(512):
                    start = (y * 4096 + frame * 512) * 4
                    pixels[start:start + 2048] = data[y * 2048:(y + 1) * 2048]
                bpy.data.images.remove(image)
            sheet = bpy.data.images.new(f'{actor}-{state}', width=4096, height=512, alpha=True)
            sheet.alpha_mode = 'STRAIGHT'; sheet.pixels.foreach_set(pixels)
            sheet.filepath_raw = str(folder / f'{state}.png'); sheet.file_format = 'PNG'; sheet.save()
            bpy.data.images.remove(sheet)
            state_meta[state] = {'file': f'{actor}/{state}.png', 'loop': state in LOOP}
        manifest['actors'][actor] = state_meta
        manifest['provenance'][actor] = {'sources': sources, 'license': 'not-established',
            'sourceActions': {s: a.name for s, a in action_by_state.items()},
            'stylizedFallbackStates': [s for s in STATES[actor] if s not in action_by_state]}
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Export complete: {out / "manifest.json"}')


if __name__ == '__main__':
    main()
