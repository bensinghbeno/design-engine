import bisect
import math

import bpy
from mathutils import Vector


COLLECTION_NAME = 'Fresh 100 - Two Column Gearbox'
DISTANCE = 14.0
ANGLE = math.radians(20)
BACKLASH = 0.04
MODULE_A = 0.4
MODULE_B = 14 / 45


def enum(rna_type, property_name, identifier):
    return next(item.identifier for item in rna_type.bl_rna.properties[property_name].enum_items
                if item.identifier == identifier)


def surface(name, color, metallic=0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = 0.35
    material.diffuse_color = (*color, 1)
    return material


def assign(obj, name, material):
    obj.name = name
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(material)
    return obj


def cylinder(name, radius, lower, upper, center, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=radius, depth=upper-lower,
                                      location=origin+Vector((*center, (lower+upper)/2)))
    return assign(bpy.context.object, name, material)


def cut(target, cutter):
    bpy.context.view_layer.objects.active = target
    modifier = target.modifiers.new('Bore', enum(bpy.types.Modifier, 'type', 'BOOLEAN'))
    modifier.operation = enum(bpy.types.BooleanModifier, 'operation', 'DIFFERENCE')
    modifier.solver = enum(bpy.types.BooleanModifier, 'solver', 'EXACT')
    modifier.object = cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def outline(teeth, module):
    pitch = module*teeth/2
    base = pitch*math.cos(ANGLE)
    root = pitch-1.25*module
    tip = pitch+module

    def involute(radius):
        pressure = math.acos(min(1, base/radius))
        return math.tan(pressure)-pressure

    half_base = math.pi/(2*teeth)-BACKLASH/(4*pitch)+math.tan(ANGLE)-ANGLE
    start = max(root, base)
    half_root = half_base-involute(start)
    half_tip = half_base-involute(tip)
    points = []
    for tooth in range(teeth):
        middle = tooth*2*math.pi/teeth
        if root < base:
            points.append((middle-half_root, root))
        for sample in range(13):
            radius = start+(tip-start)*sample/12
            points.append((middle-half_base+involute(radius), radius))
        for sample in range(1, 5):
            points.append((middle-half_tip+2*half_tip*sample/4, tip))
        for sample in range(1, 13):
            radius = tip-(tip-start)*sample/12
            points.append((middle+half_base-involute(radius), radius))
        if root < base:
            points.append((middle+half_root, root))
        for sample in range(1, 5):
            points.append((middle+half_root+(2*math.pi/teeth-2*half_root)*sample/5, root))
    return sorted((angle % (2*math.pi), radius) for angle, radius in points)


def sample_shape(shape, angles):
    extended = [(shape[-1][0]-2*math.pi, shape[-1][1])]+shape+[(shape[0][0]+2*math.pi, shape[0][1])]
    samples = [angle for angle, radius in extended]
    radii = []
    for angle in angles:
        index = bisect.bisect_right(samples, angle)
        first_angle, first_radius = extended[index-1]
        last_angle, last_radius = extended[index]
        fraction = (angle-first_angle)/(last_angle-first_angle)
        radii.append(first_radius+(last_radius-first_radius)*fraction)
    return radii


def gear(name, teeth, module, center, bottom, top, bore, material, connector=None, hub=None, flat=None):
    lower = outline(teeth, module)
    upper = outline(connector[0], connector[1]) if connector else lower
    angles = sorted(set(round(angle, 11) for shape in [lower, upper] for angle, radius in shape))
    lower_radii = sample_shape(lower, angles)
    rings = [(bottom, lower_radii), (top, lower_radii)]
    if connector:
        upper_radii = sample_shape(upper, angles)
        rings.extend([(top, upper_radii), (connector[2], upper_radii)])
    elif hub:
        rings.extend([(top, [hub[0]]*len(angles)), (hub[1], [hub[0]]*len(angles))])
    count = len(angles)
    outer_count = len(rings)
    bore_radii = [min(bore/2, flat/math.cos(angle)) if flat is not None and math.cos(angle)<0
                  else bore/2 for angle in angles]
    rings.extend([(bottom, bore_radii), (rings[-1][0], bore_radii)])
    vertices = [(radius*math.cos(angle), radius*math.sin(angle), height)
                for height, radii in rings for angle, radius in zip(angles, radii)]
    faces = []
    inner_bottom, inner_top = outer_count*count, (outer_count+1)*count
    for index in range(count):
        after = (index+1) % count
        for layer in range(outer_count-1):
            offset = layer*count
            faces.append((offset+index, offset+after, offset+count+after, offset+count+index))
        last = (outer_count-1)*count
        faces.extend([(after, index, inner_bottom+index, inner_bottom+after),
                      (last+index, last+after, inner_top+after, inner_top+index),
                      (inner_bottom+after, inner_bottom+index, inner_top+index, inner_top+after)])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = origin+Vector((*center, 0))
    obj.data.materials.append(material)
    obj['teeth'] = teeth
    obj['module_mm'] = module
    obj['pitch_diameter_mm'] = module*teeth
    obj['outside_diameter_mm'] = module*(teeth+2)
    obj['bore_mm'] = bore
    obj['pressure_angle_deg'] = 20
    if connector:
        obj['connector_teeth'], obj['connector_module_mm'] = connector[:2]
    return obj


def build():
    global collection, origin
    if bpy.data.collections.get(COLLECTION_NAME):
        raise RuntimeError('Fresh assembly already exists; do not overwrite it.')
    motor = bpy.data.objects['NEMA_17']
    assert all(abs(value-1)<1e-6 for value in motor.scale)
    assert all(abs(value)<1e-6 for value in motor.rotation_euler)
    origin = motor.matrix_world @ Vector((3, 0, 33))
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    collection['ratio'] = '20:50, 18:72, 20:50, 18:72; exact total 100:1'
    collection['center_distance_mm'] = DISTANCE
    collection['tooth_modules_mm'] = f'{MODULE_A}; {MODULE_B:.12f} (custom 14/45)'
    collection['tooth_backlash_mm'] = BACKLASH
    collection['status'] = 'Dimensioned kinematic prototype, not load-rated or manufacturing-certified'
    collection['manufacturing_cautions'] = 'Fine custom-module teeth; direct 3.1mm bores on 3mm shafts; root fillets, fits, wear, thrust retention and stiffness need validation'
    collection['motor_note'] = 'Imported body 33mm, shaft 24mm. Pinion z8..14 also fits 20mm shaft; verify actual D-flat and screw depth.'
    steel = surface('Fresh | steel', (0.34, 0.4, 0.43), 0.8)
    aluminum = surface('Fresh | aluminum', (0.64, 0.69, 0.7), 0.65)
    red = surface('Fresh | terracotta', (0.62, 0.16, 0.1), 0.12)
    amber = surface('Fresh | amber', (0.92, 0.4, 0.07), 0.12)
    center_a = (0, 0)
    center_b = (DISTANCE/math.sqrt(2), DISTANCE/math.sqrt(2))
    bpy.ops.mesh.primitive_cube_add(size=1, location=origin+Vector((0, 0, 3.5)))
    plate = assign(bpy.context.object, 'Fresh | motor plate 42x42x7', aluminum)
    plate.dimensions = (42, 42, 7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = plate.modifiers.new('Plate edge radius', enum(bpy.types.Modifier, 'type', 'BEVEL'))
    bevel.width = 1
    bevel.segments = 4
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    cut(plate, cylinder('cutter', 11.2, -1, 2.2, center_a, steel))
    cut(plate, cylinder('cutter', 3, -1, 8, center_a, steel))
    cut(plate, cylinder('cutter', 1.5, 2.8, 8, center_b, steel))
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            center = (horizontal, vertical)
            cut(plate, cylinder('cutter', 1.7, -1, 8, center, steel))
            cut(plate, cylinder('cutter', 3, 4.3, 8, center, steel))
    plate['mount'] = '31x31mm hole centers; four 3.4mm clearance bores, 6mm counterbores; 22.4mm pilot recess'
    motor_pinion = gear('Fresh | input 20T', 20, MODULE_A, center_a, 8, 14, 5.15, amber, flat=-2.1)
    cut(motor_pinion, cylinder('cutter', 2.575, 7, 9.3, center_a, steel))
    motor_pinion['bore_fit'] = '5.15mm round relief to z9.3, D flat at x=-2.1 above; measured STL flat x=-2 starts z9'
    stages = [(20, 50, MODULE_A, center_b, 8, 14, (18, MODULE_B, 33)),
              (18, 72, MODULE_B, center_a, 27, 33, (20, MODULE_A, 40)),
              (20, 50, MODULE_A, center_b, 34, 40, (18, MODULE_B, 47)),
              (18, 72, MODULE_B, center_a, 41, 47, None)]
    previous = motor_pinion
    prior_center = center_a
    cumulative = 1
    for stage, (drive, teeth, module, center, bottom, top, connector) in enumerate(stages, 1):
        assert math.isclose(module*(drive+teeth)/2, DISTANCE)
        compound = gear(f'Fresh | S{stage} {teeth}T', teeth, module, center, bottom, top, 3.1,
                        red if stage % 2 else amber, connector=connector, hub=(4.5, 54) if stage==4 else None)
        direction = math.atan2(center[1]-prior_center[1], center[0]-prior_center[0])
        phase = ((1+drive/teeth)*direction-math.pi/teeth) % (2*math.pi/teeth)
        driver = compound.driver_add('rotation_euler', 2).driver
        variable = driver.variables.new()
        variable.name = 'upstream_angle'
        variable.type = enum(bpy.types.DriverVariable, 'type', 'SINGLE_PROP')
        variable.targets[0].id = previous
        variable.targets[0].data_path = 'rotation_euler[2]'
        driver.expression = f'{phase!r} - upstream_angle * {drive/teeth!r}'
        cumulative *= teeth/drive
        compound['cumulative_ratio'] = cumulative
        compound['shaft_fit'] = '3.1mm running bore on independent fixed 3mm shaft; physical fit and wear unverified'
        previous, prior_center = compound, center
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()

    cylinder('Fresh | B fixed shaft 3mm', 1.5, 3, 49, center_b, steel)
    cylinder('Fresh | A overhead fixed shaft 3mm', 1.5, 24.6, 56, center_a, steel)
    for center, lower, upper, label in [(center_b, 7.3, 7.8, 'S1'), (center_a, 26.5, 26.8, 'S2'),
                                        (center_b, 33.3, 33.8, 'S3'), (center_a, 40.3, 40.8, 'S4'),
                                        (center_b, 47.3, 48, 'B upper'), (center_a, 54.3, 55, 'A upper')]:
        washer = cylinder('Fresh | '+label+' thrust washer', 2.3, lower, upper, center, steel)
        cut(washer, cylinder('cutter', 1.6, lower-1, upper+1, center, steel))

    shape = [(-19, -19), (19, -19), (19, -12), (4, -12), (4, 4), (-4, 4), (-4, -12), (-19, -12)]
    vertices = [origin+Vector((horizontal, vertical, height)) for height in [24.6, 26.5] for horizontal, vertical in shape]
    count = len(shape)
    faces = [tuple(reversed(range(count))), tuple(range(count, 2*count))]
    faces.extend((index, (index+1)%count, (index+1)%count+count, index+count) for index in range(count))
    mesh = bpy.data.meshes.new('Fresh overhead bridge')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bridge = bpy.data.objects.new('Fresh | overhead spindle bridge', mesh)
    collection.objects.link(bridge)
    bridge.data.materials.append(aluminum)
    cut(bridge, cylinder('cutter', 1.5, 24, 27, center_a, steel))
    for horizontal in [-15.5, 15.5]:
        center = (horizontal, -15.5)
        cut(bridge, cylinder('cutter', 1.7, 24, 27, center, steel))
        for lower, upper, radius, label in [(7, 10, 3.5, 'foot'), (10, 24.6, 2.5, 'post')]:
            post = cylinder(f'Fresh | {horizontal:+g} {label}', radius, lower, upper, center, aluminum)
            cut(post, cylinder('cutter', 1.7, lower-1, upper+1, center, steel))
    bridge['retention'] = 'Bridge clamping screws, fixed-shaft retention and thrust capture must be finalized'
    for frame, rotation in [(1, 0), (401, 200*math.pi)]:
        motor_pinion.rotation_euler.z = rotation
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
    scene.unit_settings.system = enum(bpy.types.UnitSettings, 'system', 'METRIC')
    scene.unit_settings.scale_length = 0.001
    for old in bpy.data.collections:
        if old != collection and old.name.startswith('Gearbox -'):
            old.hide_viewport = True
            old.hide_render = True
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    previous.select_set(True)
    bpy.context.view_layer.objects.active = previous
    print('BUILT', len(collection.objects), 'parts; exact 100:1; center distance 14mm; modules', MODULE_A, MODULE_B)


if __name__ == '__main__':
    build()