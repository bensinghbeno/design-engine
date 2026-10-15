import math
from pathlib import Path
import runpy

import bpy
from mathutils import Vector


COLLECTION_NAME = 'Supported Gearbox - Two Fixed Poles'


def build():
    if bpy.data.collections.get(COLLECTION_NAME):
        raise RuntimeError('Supported assembly already exists.')
    helpers = runpy.run_path(str(Path(__file__).with_name('build_fresh_100.py')))
    gear = helpers['gear']
    cylinder = helpers['cylinder']
    cut = helpers['cut']
    assign = helpers['assign']
    enum = helpers['enum']
    motor = bpy.data.objects['NEMA_17']
    assert all(abs(value-1)<1e-6 for value in motor.scale)
    assert all(abs(value)<1e-6 for value in motor.rotation_euler)
    origin = motor.matrix_world @ Vector((3, 0, 33))
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    gear.__globals__.update(collection=collection, origin=origin)
    steel = helpers['surface']('Poles | steel', (0.34, 0.4, 0.43), 0.8)
    aluminum = helpers['surface']('Poles | aluminum', (0.64, 0.69, 0.7), 0.65)
    red = helpers['surface']('Poles | terracotta', (0.62, 0.16, 0.1), 0.12)
    amber = helpers['surface']('Poles | amber', (0.92, 0.4, 0.07), 0.12)
    left, right = (-7, math.sqrt(15)), (7, math.sqrt(15))
    module_a, module_b = 0.4, 14/45
    collection['ratio'] = '1:1 input transfer, then 2.5 x 4 x 2.5 x 4 = 100:1'
    collection['support'] = 'Two independent 3mm fixed poles on 14mm centers, round 3.1mm running bores'
    collection['envelope_mm'] = '42 x 42 x 66 above motor face'
    collection['status'] = 'Geometric prototype; tooth manufacturing, wear, stiffness, fits, fasteners and camera output interface unverified'

    def ring(name, radius, bottom, top, center, material):
        obj = cylinder(name, radius, bottom, top, center, material)
        cut(obj, cylinder('cutter', 1.6, bottom-1, top+1, center, steel))
        return obj

    for name, bottom, top in [('base', 0, 7), ('top', 63, 66)]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=origin+Vector((0, 0, (bottom+top)/2)))
        plate = assign(bpy.context.object, f'Poles | {name} plate', aluminum)
        plate.dimensions = (42, 42, top-bottom)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bevel = plate.modifiers.new('Edges', enum(bpy.types.Modifier, 'type', 'BEVEL'))
        bevel.width, bevel.segments = 0.8, 3
        bpy.ops.object.modifier_apply(modifier=bevel.name)
        for horizontal in [-15.5, 15.5]:
            for vertical in [-15.5, 15.5]:
                center = (horizontal, vertical)
                cut(plate, cylinder('cutter', 1.7, bottom-1, top+1, center, steel))
                if name == 'base':
                    cut(plate, cylinder('cutter', 3, 4.3, 8, center, steel))
        if name == 'base':
            cut(plate, cylinder('cutter', 11.2, -1, 2.2, (0, 0), steel))
            cut(plate, cylinder('cutter', 3, -1, 8, (0, 0), steel))
        for center in [left, right]:
            low, high = (2.8, 8) if name == 'base' else (62, 65.1)
            cut(plate, cylinder('cutter', 1.525, low, high, center, steel))
        plate['fasteners'] = 'Four 3.4mm bores on 31mm square; M3 fastener lengths and motor thread depth must be checked'

    for label, center in [('left', left), ('right', right)]:
        pole = cylinder(f'Poles | {label} fixed 3mm pole', 1.5, 2.8, 65, center, steel)
        pole['support'] = 'Seated in blind base socket, laterally located by blind top socket; top plate fasteners required'
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            center = (horizontal, vertical)
            for low, high, radius, label in [(7, 10, 3.5, 'foot'), (10, 63, 2.5, 'post')]:
                obj = cylinder(f'Poles | {horizontal:+g} {vertical:+g} {label}', radius, low, high, center, aluminum)
                cut(obj, cylinder('cutter', 1.7, low-1, high+1, center, steel))

    motor_pinion = gear('Poles | motor pinion 20T D bore', 20, module_a, (0, 0), 8, 14, 5.15, amber, flat=-2.1)
    cut(motor_pinion, cylinder('cutter', 2.575, 7, 9.3, (0, 0), steel))
    previous = motor_pinion
    prior_center = (0, 0)
    specs = [('R100 | input 20T.001', 20, 20, module_a, right, 8, 33, None),
             ('Poles | S1 50T', 20, 50, module_a, left, 27, 33, (18, module_b, 40)),
             ('Poles | S2 72T', 18, 72, module_b, right, 34, 40, (20, module_a, 47)),
             ('Poles | S3 50T', 20, 50, module_a, left, 41, 47, (18, module_b, 54)),
             ('Poles | S4 72T output', 18, 72, module_b, right, 48, 54, None)]
    old_named = bpy.data.objects.get('R100 | input 20T.001')
    if old_named:
        old_named.name = 'Reference | R100 input 20T.001'
    cumulative = 1
    for name, drive, teeth, module, center, bottom, top, connector in specs:
        assert math.isclose(math.dist(center, prior_center), module*(drive+teeth)/2, abs_tol=1e-6)
        obj = gear(name, teeth, module, center, bottom, top, 3.1,
                   amber if center == right else red, connector=connector,
                   hub=(4.5, 61) if 'output' in name else None)
        obj['support_pole'] = 'right' if center == right else 'left'
        obj['fit'] = 'Round 3.1mm bore / 3mm fixed pole; direct running fit requires physical wear and tolerance validation'
        cumulative *= teeth/drive
        obj['cumulative_ratio'] = cumulative
        direction = math.atan2(center[1]-prior_center[1], center[0]-prior_center[0])
        phase = ((1+drive/teeth)*direction-math.pi/teeth) % (2*math.pi/teeth)
        driver = obj.driver_add('rotation_euler', 2).driver
        variable = driver.variables.new()
        variable.name = 'upstream_angle'
        variable.type = enum(bpy.types.DriverVariable, 'type', 'SINGLE_PROP')
        variable.targets[0].id = previous
        variable.targets[0].data_path = 'rotation_euler[2]'
        driver.expression = f'{phase!r} - upstream_angle * {drive/teeth!r}'
        previous, prior_center = obj, center
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()

    for name, center, low, high in [('left base spacer', left, 7, 26.5),
                                    ('left lower washer', left, 26.5, 27),
                                    ('left interstage washer', left, 40, 41),
                                    ('left upper washer', left, 54, 54.5),
                                    ('left retaining spacer', left, 54.5, 62.8),
                                    ('right lower spacer', right, 7, 7.5),
                                    ('right lower washer', right, 7.5, 8),
                                    ('right first interstage washer', right, 33, 34),
                                    ('right second interstage washer', right, 47, 48),
                                    ('right upper washer', right, 61, 61.5),
                                    ('right retaining spacer', right, 61.5, 62.8)]:
        obj = ring('Poles | '+name, 2.3, low, high, center, steel)
        obj['support_note'] = 'Nominal seated thrust stack; 0.2mm endplay below top plate; adjust with physical shims'

    for frame, angle in [(1, 0), (401, 200*math.pi)]:
        motor_pinion.rotation_euler.z = angle
        motor_pinion.keyframe_insert(data_path='rotation_euler', index=2, frame=frame)
    for layer in motor_pinion.animation_data.action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for curve in channelbag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = enum(bpy.types.Keyframe, 'interpolation', 'LINEAR')
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 400
    scene.frame_set(1)
    for old in bpy.data.collections:
        if old != collection and (old.name.startswith('Gearbox -') or old.name.startswith('Fresh 100')):
            old.hide_viewport, old.hide_render = True, True
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    bpy.data.objects['R100 | input 20T.001'].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['R100 | input 20T.001']
    print('BUILT', len(collection.objects), 'parts; two seated shafts, round bores, 1:1 transfer + 100:1 train')


if __name__ == '__main__':
    build()