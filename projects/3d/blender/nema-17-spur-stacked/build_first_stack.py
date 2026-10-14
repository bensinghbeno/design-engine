import bisect
import math

import bpy
from mathutils import Vector


COLLECTION_NAME = 'Gearbox - First Stack'
MODULE = 0.5
INPUT_TEETH = 18
OUTPUT_TEETH = 36
PRESSURE_ANGLE = math.radians(20)
BACKLASH = 0.10
CENTER_DISTANCE = MODULE * (INPUT_TEETH + OUTPUT_TEETH) / 2
AXIS_OFFSET = CENTER_DISTANCE / math.sqrt(2)


def enum_value(rna_type, property_name, identifier):
    return next(item.identifier for item in rna_type.bl_rna.properties[property_name].enum_items
                if item.identifier == identifier)


def material(name, color, metallic=0.0, roughness=0.4):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    shader = next(node for node in result.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    result.diffuse_color = (*color, 1)
    return result


def move_to_collection(obj):
    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def assign(obj, name, surface):
    obj.name = name
    move_to_collection(obj)
    obj.data.materials.clear()
    obj.data.materials.append(surface)
    return obj


def cylinder(name, radius, bottom, top, center, surface):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=radius, depth=top-bottom,
                                      location=(origin.x+center[0], origin.y+center[1], origin.z+(bottom+top)/2))
    return assign(bpy.context.object, name, surface)


def boolean(target, cutter, operation):
    bpy.context.view_layer.objects.active = target
    modifier = target.modifiers.new('Precision cut', enum_value(bpy.types.Modifier, 'type', 'BOOLEAN'))
    modifier.operation = enum_value(bpy.types.BooleanModifier, 'operation', operation)
    modifier.solver = enum_value(bpy.types.BooleanModifier, 'solver', 'EXACT')
    modifier.object = cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def profile(teeth):
    pitch = MODULE * teeth / 2
    base = pitch * math.cos(PRESSURE_ANGLE)
    root = pitch - 1.25 * MODULE
    tip = pitch + MODULE
    half_pitch_angle = math.pi / (2 * teeth) - BACKLASH / (4 * pitch)
    half_base_angle = half_pitch_angle + math.tan(PRESSURE_ANGLE) - PRESSURE_ANGLE

    def involute(radius):
        angle = math.acos(min(1, base / radius))
        return math.tan(angle) - angle

    half_tip_angle = half_base_angle - involute(tip)
    flank_start = max(root, base)
    half_root_angle = half_base_angle - involute(flank_start)
    polar = []
    for tooth in range(teeth):
        middle = tooth * 2 * math.pi / teeth
        if root < base:
            polar.append((root, middle-half_root_angle))
        for step in range(9):
            radius = flank_start + (tip-flank_start) * step / 8
            polar.append((radius, middle-half_base_angle+involute(radius)))
        for step in range(1, 5):
            polar.append((tip, middle-half_tip_angle+2*half_tip_angle*step/4))
        for step in range(1, 9):
            radius = tip - (tip-flank_start) * step / 8
            polar.append((radius, middle+half_base_angle-involute(radius)))
        if root < base:
            polar.append((root, middle+half_root_angle))
        gap = 2 * math.pi / teeth - 2 * half_root_angle
        for step in range(1, 5):
            polar.append((root, middle+half_root_angle+gap*step/5))
    return polar


def gear(name, teeth, bottom, top, center, bore, surface, phase=0, d_flat=None, upper_teeth=None, connector_height=7):
    outline = profile(teeth)
    outer_layers = [(bottom, outline), (top, outline)]
    if upper_teeth is not None:
        upper = profile(upper_teeth)
        lower_start = min(angle for radius, angle in outline)
        normalized = []
        for shape in [outline, upper]:
            normalized.append(sorted(((angle-lower_start) % (2*math.pi)+lower_start, radius)
                                     for radius, angle in shape))
        angles = sorted(set(round(angle, 12) for shape in normalized for angle, radius in shape))
        resampled = []
        for shape in normalized:
            extended = [(shape[-1][0]-2*math.pi, shape[-1][1])] + shape + [(shape[0][0]+2*math.pi, shape[0][1])]
            samples = [angle for angle, radius in extended]
            result = []
            for angle in angles:
                index = max(1, min(len(extended)-1, bisect.bisect_right(samples, angle)))
                start_angle, start_radius = extended[index-1]
                end_angle, end_radius = extended[index]
                fraction = (angle-start_angle)/(end_angle-start_angle)
                result.append((start_radius+(end_radius-start_radius)*fraction, angle))
            resampled.append(result)
        outline, upper = resampled
        outer_layers = [(bottom, outline), (top, outline), (top, upper), (top+connector_height, upper)]
    count = len(outline)
    outer_count = len(outer_layers)
    inner_bottom = outer_count*count
    inner_top = (outer_count+1)*count
    vertices = []
    layers = [(height, shape, False) for height, shape in outer_layers]
    layers.extend([(bottom, outline, True), (outer_layers[-1][0], outline, True)])
    for height, shape, inner in layers:
        for radius, angle in shape:
            if inner:
                radius = bore / 2
                if d_flat is not None and math.cos(angle) < 0:
                    radius = min(radius, d_flat / math.cos(angle))
            vertices.append((radius*math.cos(angle), radius*math.sin(angle), height))
    faces = []
    for index in range(count):
        after = (index+1) % count
        for layer in range(outer_count-1):
            offset = layer*count
            faces.append((offset+index, offset+after, offset+count+after, offset+count+index))
        last = (outer_count-1)*count
        faces.extend([(inner_bottom+after, inner_bottom+index, inner_top+index, inner_top+after),
                      (after, index, inner_bottom+index, inner_bottom+after),
                      (last+index, last+after, inner_top+after, inner_top+index)])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = origin + Vector((center[0], center[1], 0))
    obj.rotation_euler.z = phase
    obj.data.materials.append(surface)
    obj['teeth'] = teeth
    obj['module_mm'] = MODULE
    obj['pressure_angle_degrees'] = 20
    obj['bore_diameter_mm'] = bore
    return obj


def build_first_stack():
    global collection, origin
    if bpy.data.collections.get(COLLECTION_NAME):
        raise RuntimeError('First stack already exists; leave the existing assembly intact.')
    source = bpy.data.objects['NEMA_17']
    assert all(abs(value-1) < 1e-6 for value in source.scale)
    assert all(abs(value) < 1e-6 for value in source.rotation_euler)
    origin = source.matrix_world @ Vector((3, 0, 33))
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    collection['status'] = 'Fit and motion prototype; bearing fits and load capacity not certified'
    collection['ratio'] = '2:1 per stage; compound pinion prepared for next stage'
    collection['module_mm'] = MODULE
    collection['center_distance_mm'] = CENTER_DISTANCE
    collection['mount_hole_spacing_mm'] = 31.0
    collection['source_motor_body_mm'] = 33.0
    collection['source_motor_exposed_shaft_mm'] = 24.0
    collection['design_motor_body_mm'] = 20.0
    collection['design_motor_shaft_mm'] = 20.0
    collection['mount_note'] = '31 mm standard NEMA 17 pitch; verify supplied 43.6 mm bolt circle'

    scene = bpy.context.scene
    scene.unit_settings.system = enum_value(bpy.types.UnitSettings, 'system', 'METRIC')
    scene.unit_settings.scale_length = 0.001
    steel = material('Gearbox | steel', (0.36, 0.42, 0.46), 0.8, 0.27)
    orange = material('Gearbox | drive amber', (0.95, 0.34, 0.055), 0.15, 0.35)
    red = material('Gearbox | compound terracotta', (0.63, 0.15, 0.09), 0.1, 0.4)
    plate_surface = material('Gearbox | satin aluminum', (0.6, 0.66, 0.68), 0.65, 0.35)
    dark = material('Gearbox | motor graphite', (0.07, 0.085, 0.095), 0.35, 0.4)
    bronze = material('Gearbox | plain bushing', (0.51, 0.3, 0.09), 0.7, 0.32)

    bpy.ops.mesh.primitive_cube_add(size=1, location=origin+Vector((0, 0, 3.5)))
    plate = assign(bpy.context.object, 'S1 | 42mm mounting plate', plate_surface)
    plate.dimensions = (42, 42, 7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = plate.modifiers.new('Rounded plate edges', enum_value(bpy.types.Modifier, 'type', 'BEVEL'))
    bevel.width = 1.2
    bevel.segments = 4
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    boolean(plate, cylinder('cutter', 11.2, -1, 2.2, (0, 0), steel), 'DIFFERENCE')
    boolean(plate, cylinder('cutter', 3, 0, 8, (0, 0), steel), 'DIFFERENCE')
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            boolean(plate, cylinder('cutter', 1.7, 0, 8, (horizontal, vertical), steel), 'DIFFERENCE')
            boolean(plate, cylinder('cutter', 3, 4.3, 8, (horizontal, vertical), steel), 'DIFFERENCE')
    plate['mount'] = '4 x 3.4 mm clearance on 31 x 31 mm centers; 6 mm head counterbores'
    plate['pilot_recess'] = '22.4 mm diameter; 2.2 mm deep from underside'
    plate['mounting_screws'] = 'Select length for measured motor thread depth; not included'
    output_center = (AXIS_OFFSET, AXIS_OFFSET)
    boolean(plate, cylinder('cutter', 1.5, 2.8, 8, output_center, steel), 'DIFFERENCE')
    axle = cylinder('S1 | 3mm fixed output axle', 1.5, 3, 22, output_center, steel)
    axle['status'] = 'Steel reference axle; retention and fit must be finalized'

    pinion = gear('S1 | 18T motor pinion', 18, 8, 14, (0, 0), 5.15, orange, d_flat=-1.9)
    pinion['shaft_fit'] = '5.15 mm D bore, flat at -1.9 mm; matches STL flat orientation only'
    pinion['retention'] = 'Prototype slip fit; axial retention to be finalized'
    output_phase = ((1+INPUT_TEETH/OUTPUT_TEETH)*math.pi/4-math.pi/OUTPUT_TEETH) % (2*math.pi/OUTPUT_TEETH)
    compound = gear('S1 | 36T gear + 18T connector', 36, 8, 14, output_center, 5.0, red, output_phase, upper_teeth=18)
    compound['connector_teeth'] = 18
    compound['connector_face_z_mm'] = '15 to 21 (1 mm shoulder above lower mesh)'
    compound['ratio'] = '2:1, reverse rotation relative to motor'
    compound['next_stage'] = 'Add second driven 36T gear at motor axis in upper plane; not built'
    bushing = cylinder('S1 | 3mm ID bronze sleeve', 2.5, 8, 21, output_center, bronze)
    boolean(bushing, cylinder('cutter', 1.6, 7, 22, output_center, steel), 'DIFFERENCE')
    bushing['fit'] = 'Nominal 5mm OD sleeve in 5mm gear bore; fit allowance not finalized'
    for bottom, top, name in [(7, 7.7, 'lower thrust washer'), (21.3, 22, 'upper thrust washer')]:
        washer = cylinder('S1 | '+name, 2.8, bottom, top, output_center, steel)
        boolean(washer, cylinder('cutter', 1.6, bottom-1, top+1, output_center, steel), 'DIFFERENCE')

    source.data.materials.clear()
    source.data.materials.append(dark)
    source.data.materials.append(plate_surface)
    source.data.materials.append(steel)
    for polygon in source.data.polygons:
        height = polygon.center.z
        polygon.material_index = 2 if height > 35 else (1 if height > 25.4 or height < 5 else 0)

    for name in ['Cube', 'Camera', 'Light']:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_set(True)

    pinion.rotation_euler.z = 0
    driver = compound.driver_add('rotation_euler', 2).driver
    variable = driver.variables.new()
    variable.name = 'input_angle'
    variable.type = enum_value(bpy.types.DriverVariable, 'type', 'SINGLE_PROP')
    variable.targets[0].id = pinion
    variable.targets[0].data_path = 'rotation_euler[2]'
    driver.expression = f'{output_phase!r} - input_angle * 0.5'
    for frame, angle in [(1, 0), (241, 4*math.pi)]:
        pinion.rotation_euler.z = angle
        pinion.keyframe_insert(data_path='rotation_euler', index=2, frame=frame)
    if pinion.animation_data and pinion.animation_data.action:
        for layer in pinion.animation_data.action.layers:
            for strip in layer.strips:
                for channelbag in strip.channelbags:
                    for curve in channelbag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation = enum_value(bpy.types.Keyframe, 'interpolation', 'LINEAR')
    scene.frame_start = 1
    scene.frame_end = 240
    scene.frame_set(1)

    bpy.ops.object.select_all(action=next(item.identifier for item in bpy.ops.object.select_all.get_rna_type().properties['action'].enum_items if item.identifier == 'DESELECT'))
    compound.select_set(True)
    bpy.context.view_layer.objects.active = compound
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.shading.type = enum_value(bpy.types.View3DShading, 'type', 'SOLID')
            space.shading.color_type = enum_value(bpy.types.View3DShading, 'color_type', 'MATERIAL')
            space.overlay.show_floor = False
            space.region_3d.view_distance = 100
            space.region_3d.view_location = origin+Vector((0, 0, -1))
            space.region_3d.view_rotation = Vector((0.9, -1.3, 1.6)).to_track_quat('Z', 'Y')

    print('BUILT', len(collection.objects), 'objects; 18:36 = 2:1; module', MODULE)
    print('CENTER DISTANCE', CENTER_DISTANCE, 'mm; diagonal offset', AXIS_OFFSET)
    print('GEAR XY EXTENT FROM MOTOR CENTER', AXIS_OFFSET+MODULE*(OUTPUT_TEETH+2)/2, 'mm, limit 21')
    print('SOURCE MOTOR RETAINED', source.name, tuple(source.location))


def build_second_stack():
    global collection, origin
    name = 'Gearbox - Second Stack'
    if bpy.data.collections.get(name):
        raise RuntimeError('Second stack already exists; leave the existing assembly intact.')
    scene = bpy.context.scene
    scene.frame_set(1)
    first = bpy.data.objects['S1 | 36T gear + 18T connector']
    motor_pinion = bpy.data.objects['S1 | 18T motor pinion']
    assert first['connector_teeth'] == INPUT_TEETH and first['module_mm'] == MODULE
    assert math.isclose((first.location-motor_pinion.location).length, CENTER_DISTANCE, abs_tol=1e-4)
    origin = motor_pinion.location.copy()
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    collection['ratio'] = '2:1 stage reduction; 4:1 cumulative, same direction as motor'
    collection['status'] = 'Fit and motion prototype; independent shaft bearing and axial retention not finalized'
    collection['module_mm'] = MODULE
    collection['footprint_mm'] = 'Inside existing 42 x 42 mm mounting plate'
    collection['gear_planes_mm'] = 'Driven gear 15-21; next connector 21-28 above motor face'
    collection['support_note'] = 'Prototype bronze sleeve runs on motor shaft; D-cut is not a qualified bearing journal'
    steel = bpy.data.materials['Gearbox | steel']
    bronze = bpy.data.materials['Gearbox | plain bushing']
    surface = material('Gearbox | second stack amber', (0.88, 0.43, 0.09), 0.15, 0.35)
    direction = math.atan2(origin.y-first.location.y, origin.x-first.location.x)
    phase = ((1+INPUT_TEETH/OUTPUT_TEETH)*direction-math.pi/OUTPUT_TEETH) % (2*math.pi/OUTPUT_TEETH)
    compound = gear('S2 | 36T gear + 18T connector', 36, 15, 21, (0, 0), 6.5,
                    surface, phase-first.rotation_euler.z*0.5, upper_teeth=18)
    compound['connector_teeth'] = 18
    compound['ratio'] = '4:1 cumulative; rotates independently around motor shaft'
    compound['next_stage'] = 'Upper 18T connector reserved for stack 3; not built'
    compound['minimum_connector_root_wall_mm'] = MODULE*(18/2-1.25)-6.5/2
    sleeve = cylinder('S2 | 5.3mm ID free-running sleeve', 3.25, 15, 21, (0, 0), bronze)
    boolean(sleeve, cylinder('cutter', 2.65, 14, 22, (0, 0), steel), 'DIFFERENCE')
    sleeve['fit'] = '5.3 mm ID / 6.5 mm OD; 6 mm long; nominal gear fit, validate manufacturing tolerances'
    washer = cylinder('S2 | lower thrust washer', 3.6, 14.15, 14.85, (0, 0), steel)
    boolean(washer, cylinder('cutter', 2.65, 14, 15, (0, 0), steel), 'DIFFERENCE')
    driver = compound.driver_add('rotation_euler', 2).driver
    variable = driver.variables.new()
    variable.name = 'first_stack_angle'
    variable.type = enum_value(bpy.types.DriverVariable, 'type', 'SINGLE_PROP')
    variable.targets[0].id = first
    variable.targets[0].data_path = 'rotation_euler[2]'
    driver.expression = f'{phase!r} - first_stack_angle * 0.5'
    first['next_stage'] = compound.name
    scene.frame_set(1)
    bpy.context.view_layer.update()
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    compound.select_set(True)
    bpy.context.view_layer.objects.active = compound
    print('BUILT SECOND STACK', len(collection.objects), 'objects; cumulative ratio 4:1')


def build_upper_stacks():
    global collection, origin
    names = ['Gearbox - Third Stack', 'Gearbox - Fourth Stack']
    if any(bpy.data.collections.get(name) for name in names):
        raise RuntimeError('An upper stack already exists; leave the existing assembly intact.')
    scene = bpy.context.scene
    scene.frame_set(1)
    motor_pinion = bpy.data.objects['S1 | 18T motor pinion']
    first = bpy.data.objects['S1 | 36T gear + 18T connector']
    previous = bpy.data.objects['S2 | 36T gear + 18T connector']
    axle = bpy.data.objects['S1 | 3mm fixed output axle']
    separator = bpy.data.objects['S1 | upper thrust washer']
    assert previous['connector_teeth'] == INPUT_TEETH and previous['module_mm'] == MODULE
    assert math.isclose((first.location-motor_pinion.location).length, CENTER_DISTANCE, abs_tol=1e-4)
    origin = motor_pinion.location.copy()
    steel = bpy.data.materials['Gearbox | steel']
    bronze = bpy.data.materials['Gearbox | plain bushing']
    offset = first.location-origin
    for stage, name in zip([3, 4], names):
        collection = bpy.data.collections.new(name)
        scene.collection.children.link(collection)
        collection['cumulative_ratio'] = float(2**stage)
        collection['status'] = 'Fit and motion prototype; spindle retention, tolerances and load capacity unverified'
        collection['module_mm'] = MODULE
        collection['footprint_mm'] = 'Inside existing 42 x 42 mm mounting plate'
        center = (offset.x, offset.y) if stage == 3 else (0, 0)
        bottom = 8+7*(stage-1)
        top = bottom+6
        target = origin+Vector((*center, 0))
        direction = math.atan2(target.y-previous.location.y, target.x-previous.location.x)
        phase = ((1+INPUT_TEETH/OUTPUT_TEETH)*direction-math.pi/OUTPUT_TEETH) % (2*math.pi/OUTPUT_TEETH)
        color = (0.63, 0.15, 0.09) if stage == 3 else (0.88, 0.43, 0.09)
        surface = material(f'Gearbox | stack {stage}', color, 0.15, 0.35)
        compound = gear(f'S{stage} | 36T gear + 18T connector', 36, bottom, top,
                        center, 5.0, surface, phase-previous.rotation_euler.z*0.5, upper_teeth=18)
        compound['connector_teeth'] = 18
        compound['ratio'] = f'{2**stage}:1 cumulative'
        compound['next_stage'] = 'Not built'
        sleeve = cylinder(f'S{stage} | 3.2mm ID bronze sleeve', 2.5, bottom, top+7, center, bronze)
        boolean(sleeve, cylinder('cutter', 1.6, bottom-1, top+8, center, steel), 'DIFFERENCE')
        sleeve['fit'] = '3.2 mm ID / 5 mm OD; nominal gear fit, verify tolerances'
        washer = cylinder(f'S{stage} | upper thrust washer', 2.8, top+7.3, top+8, center, steel)
        boolean(washer, cylinder('cutter', 1.6, top+7, top+9, center, steel), 'DIFFERENCE')
        driver = compound.driver_add('rotation_euler', 2).driver
        variable = driver.variables.new()
        variable.name = 'previous_stack_angle'
        variable.type = enum_value(bpy.types.DriverVariable, 'type', 'SINGLE_PROP')
        variable.targets[0].id = previous
        variable.targets[0].data_path = 'rotation_euler[2]'
        driver.expression = f'{phase!r} - previous_stack_angle * 0.5'
        previous['next_stage'] = compound.name
        previous = compound
        scene.frame_set(1)
        bpy.context.view_layer.update()

    axle_points = [axle.matrix_world @ vertex.co for vertex in axle.data.vertices]
    old_bottom = min(point.z for point in axle_points)
    old_top = max(point.z for point in axle_points)
    inverse = axle.matrix_world.inverted()
    for vertex, point in zip(axle.data.vertices, axle_points):
        point.z = origin.z+3+(point.z-old_bottom)/(old_top-old_bottom)*34
        vertex.co = inverse @ point
    axle.data.update()
    axle['status'] = 'Extended fixed 3mm reference axle, z=3..37; retention and stiffness unverified'
    separator.location.z -= 0.15
    separator['role'] = 'Interstage thrust washer between stacks 1 and 3; 0.15mm upper clearance'

    spindle = cylinder('S4 | independent 3mm overhead spindle', 1.5, 25, 47, (0, 0), steel)
    spindle['support'] = 'Fixed to overhead bridge; starts 1mm above STL motor shaft tip, no shaft coupling'
    spindle['retention'] = 'Bridge fit and spindle axial retention to be finalized'
    washer = cylinder('S4 | lower thrust washer', 2.8, 28.15, 28.85, (0, 0), steel)
    boolean(washer, cylinder('cutter', 1.6, 28, 29, (0, 0), steel), 'DIFFERENCE')
    washer['retention'] = 'Requires retained thrust support; provisional position'
    surface = bpy.data.materials['Gearbox | satin aluminum']
    outline = [(-19, -19), (19, -19), (19, -12), (4, -12), (4, 4), (-4, 4), (-4, -12), (-19, -12)]
    vertices = [(origin.x+horizontal, origin.y+vertical, origin.z+height)
                for height in [44, 47] for horizontal, vertical in outline]
    count = len(outline)
    faces = [tuple(reversed(range(count))), tuple(range(count, 2*count))]
    faces.extend((index, (index+1) % count, (index+1) % count+count, index+count)
                 for index in range(count))
    mesh = bpy.data.meshes.new('Overhead bridge')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bridge = bpy.data.objects.new('S4 | overhead spindle bridge', mesh)
    collection.objects.link(bridge)
    bridge.data.materials.append(surface)
    boolean(bridge, cylinder('cutter', 1.5, 43, 48, (0, 0), steel), 'DIFFERENCE')
    for horizontal in [-15.5, 15.5]:
        center = (horizontal, -15.5)
        boolean(bridge, cylinder('cutter', 1.7, 43, 48, center, steel), 'DIFFERENCE')
        post = cylinder(f'S4 | bridge standoff {horizontal:+g}', 3.5, 7, 44, center, surface)
        boolean(post, cylinder('cutter', 1.7, 6, 45, center, steel), 'DIFFERENCE')
        post['mount'] = '3.4mm through bore on existing front M3 hole; fastener length and motor thread depth unverified'
    bridge['status'] = 'Support concept; fasteners, spindle retention and bridge stiffness not finalized'
    collection['support_note'] = 'Separate overhead spindle clears motor shaft; no upper gear keyed to motor'
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    previous.select_set(True)
    bpy.context.view_layer.objects.active = previous
    scene.frame_set(1)
    bpy.context.view_layer.update()
    print('BUILT STACKS 3 AND 4; cumulative ratio 16:1')


def build_four_stage_100():
    global collection, origin, MODULE, BACKLASH
    name = 'Gearbox - 100 to 1 - Four Stages'
    if bpy.data.collections.get(name):
        raise RuntimeError('100:1 assembly already exists; leave it intact.')
    scene = bpy.context.scene
    scene.frame_set(1)
    source = bpy.data.objects['NEMA_17']
    assert all(abs(value-1) < 1e-6 for value in source.scale)
    assert all(abs(value) < 1e-6 for value in source.rotation_euler)
    origin = source.matrix_world @ Vector((3, 0, 33))
    old_module, old_backlash = MODULE, BACKLASH
    MODULE, BACKLASH = 0.4, 0.06
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    collection['ratio'] = '2.5 x 4 x 2.5 x 4 = 100:1; four external spur reductions'
    collection['module_mm'] = MODULE
    collection['status'] = 'Prototype; fine teeth, bearing fits, shaft retention, bridge stiffness and load capacity unverified'
    collection['envelope_mm'] = '42 x 42 footprint; 62 mm above motor mounting face'
    collection['motor_fit'] = 'Based on imported 33mm body / 24mm shaft STL, not supplied 20mm short motor shaft'
    steel = bpy.data.materials['Gearbox | steel']
    bronze = bpy.data.materials['Gearbox | plain bushing']
    aluminum = bpy.data.materials['Gearbox | satin aluminum']
    amber = material('R100 | amber', (0.88, 0.43, 0.09), 0.15, 0.35)
    red = material('R100 | terracotta', (0.63, 0.15, 0.09), 0.15, 0.4)
    first = 14/math.sqrt(2)
    second = first-18/math.sqrt(2)
    third = (8, second-math.sqrt(12.6**2-(8-second)**2))
    fourth = (-4, third[1]+math.sqrt(18**2-12**2))
    centers = [(0, 0), (first, first), (second, second), third, fourth]

    bpy.ops.mesh.primitive_cube_add(size=1, location=origin+Vector((0, 0, 3.5)))
    plate = assign(bpy.context.object, 'R100 | 42mm mounting plate', aluminum)
    plate.dimensions = (42, 42, 7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = plate.modifiers.new('Plate edges', enum_value(bpy.types.Modifier, 'type', 'BEVEL'))
    bevel.width = 1.2
    bevel.segments = 4
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    boolean(plate, cylinder('cutter', 11.2, -1, 2.2, (0, 0), steel), 'DIFFERENCE')
    boolean(plate, cylinder('cutter', 3, -1, 8, (0, 0), steel), 'DIFFERENCE')
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            boolean(plate, cylinder('cutter', 1.7, -1, 8, (horizontal, vertical), steel), 'DIFFERENCE')
            boolean(plate, cylinder('cutter', 3, 4.3, 8, (horizontal, vertical), steel), 'DIFFERENCE')
    boolean(plate, cylinder('cutter', 1.5, 2.8, 8, centers[1], steel), 'DIFFERENCE')
    plate['mount'] = '4 x M3 clearance on 31mm square, 22.4mm pilot recess; screw engagement unverified'

    motor_pinion = gear('R100 | input 20T', 20, 18, 24, centers[0], 5.15, amber, d_flat=-1.9)
    motor_pinion['shaft_fit'] = 'D bore for imported shaft; axial retention unverified; too high for full engagement on specified 20mm shaft'
    previous = motor_pinion
    cumulative = 1
    for stage, (driving_teeth, teeth) in enumerate([(20, 50), (18, 72), (18, 45), (18, 72)], 1):
        bottom = 18+9*(stage-1)
        top = bottom+6
        center = centers[stage]
        prior_center = centers[stage-1]
        direction = math.atan2(center[1]-prior_center[1], center[0]-prior_center[0])
        phase = ((1+driving_teeth/teeth)*direction-math.pi/teeth) % (2*math.pi/teeth)
        compound = gear(f'R100 | S{stage} {teeth}T + 18T', teeth, bottom, top, center, 5.0,
                        red if stage % 2 else amber, phase-previous.rotation_euler.z*driving_teeth/teeth,
                        upper_teeth=18, connector_height=9)
        cumulative *= teeth/driving_teeth
        compound['stage'] = stage
        compound['connector_teeth'] = 18
        compound['cumulative_ratio'] = cumulative
        compound['gear_plane_mm'] = f'{bottom} to {top}'
        compound['connector_root_wall_mm'] = 0.6
        driver = compound.driver_add('rotation_euler', 2).driver
        variable = driver.variables.new()
        variable.name = 'upstream_angle'
        variable.type = enum_value(bpy.types.DriverVariable, 'type', 'SINGLE_PROP')
        variable.targets[0].id = previous
        variable.targets[0].data_path = 'rotation_euler[2]'
        driver.expression = f'{phase!r} - upstream_angle * {driving_teeth/teeth!r}'
        previous = compound
        sleeve = cylinder(f'R100 | S{stage} bronze sleeve', 2.5, bottom, top+9, center, bronze)
        boolean(sleeve, cylinder('cutter', 1.6, bottom-1, top+10, center, steel), 'DIFFERENCE')
        for low, high, label in [(bottom-0.4, bottom-0.1, 'lower'), (top+9.3, top+10, 'upper')]:
            washer = cylinder(f'R100 | S{stage} {label} washer', 2.8, low, high, center, steel)
            boolean(washer, cylinder('cutter', 1.6, low-1, high+1, center, steel), 'DIFFERENCE')
        axle_bottom = 3 if stage == 1 else bottom-2.5
        axle = cylinder(f'R100 | S{stage} 3mm fixed spindle', 1.5, axle_bottom, top+11, center, steel)
        axle['status'] = 'Reference fixed spindle; retention, stiffness and thrust support unverified'
        if stage == 1:
            spacer = cylinder('R100 | S1 pedestal', 2.8, 7, bottom-0.5, center, aluminum)
            boolean(spacer, cylinder('cutter', 1.6, 6, bottom, center, steel), 'DIFFERENCE')
        else:
            support_start = (-15.5, 15.5) if stage == 4 else (-15.5, -15.5)
            lower, upper = bottom-2.5, bottom-0.5
            delta = Vector((center[0]-support_start[0], center[1]-support_start[1], 0))
            midpoint = origin+Vector(((center[0]+support_start[0])/2, (center[1]+support_start[1])/2, (lower+upper)/2))
            bpy.ops.mesh.primitive_cube_add(size=1, location=midpoint)
            bridge = assign(bpy.context.object, f'R100 | S{stage} support arm', aluminum)
            bridge.dimensions = (delta.length+5, 5, upper-lower)
            bridge.rotation_euler.z = math.atan2(delta.y, delta.x)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            boolean(bridge, cylinder('cutter', 1.5, lower-1, upper+1, center, steel), 'DIFFERENCE')
            boolean(bridge, cylinder('cutter', 1.7, lower-1, upper+1, support_start, steel), 'DIFFERENCE')
            bridge['status'] = 'Cantilever support concept; fasteners and stiffness unverified'
        scene.frame_set(1)
        bpy.context.view_layer.update()

    for center, spans, label in [((-15.5, -15.5), [(10, 24.5), (26.5, 33.5)], 'front'),
                                  ((-15.5, 15.5), [(10, 42.5)], 'rear')]:
        for index, (lower, upper) in enumerate(spans, 1):
            post = cylinder(f'R100 | {label} spacer {index}', 2.5, lower, upper, center, aluminum)
            boolean(post, cylinder('cutter', 1.7, lower-1, upper+1, center, steel), 'DIFFERENCE')
        foot = cylinder(f'R100 | {label} post foot', 3.5, 7, 10, center, aluminum)
        boolean(foot, cylinder('cutter', 1.7, 6, 11, center, steel), 'DIFFERENCE')
    for frame, angle in [(1, 0), (301, 200*math.pi)]:
        motor_pinion.rotation_euler.z = angle
        motor_pinion.keyframe_insert(data_path='rotation_euler', index=2, frame=frame)
    for layer in motor_pinion.animation_data.action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for curve in channelbag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = enum_value(bpy.types.Keyframe, 'interpolation', 'LINEAR')
    scene.frame_start = 1
    scene.frame_end = 300
    scene.frame_set(1)
    for old_name in ['Gearbox - First Stack', 'Gearbox - Second Stack', 'Gearbox - Third Stack', 'Gearbox - Fourth Stack']:
        old = bpy.data.collections.get(old_name)
        if old:
            old.hide_viewport = True
            old.hide_render = True
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    previous.select_set(True)
    bpy.context.view_layer.objects.active = previous
    MODULE, BACKLASH = old_module, old_backlash
    print('BUILT', len(collection.objects), 'objects; FOUR STAGES, EXACT 100:1')


if __name__ == '__main__':
    build_first_stack()