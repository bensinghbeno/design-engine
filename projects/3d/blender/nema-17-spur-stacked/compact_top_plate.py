import math
from pathlib import Path
import runpy

import bpy
from mathutils import Vector


COLLECTION_NAME = 'Compact Top - Integrated Bearing Plate'


def build():
    if bpy.data.collections.get(COLLECTION_NAME):
        raise RuntimeError('Integrated top plate already exists.')
    scene = bpy.context.scene
    scene.frame_set(1)
    source = bpy.data.objects['Poles | S4 72T output']
    drive = bpy.data.objects['Center hub | S4 transfer pinion 20T']
    centered = bpy.data.objects['Center hub | centered driven gear 20T']
    rotor = bpy.data.objects['Center hub | recessed 34mm flange and shaft']
    top_plate = bpy.data.objects['Poles | top plate']
    assert all(abs(value-1)<1e-6 for value in source.scale)
    origin = source.location-Vector((7, math.sqrt(15), 0))
    right, left = (7, math.sqrt(15)), (-7, math.sqrt(15))
    helpers = runpy.run_path(str(Path(__file__).with_name('build_fresh_100.py')))
    cylinder, cut, assign = helpers['cylinder'], helpers['cut'], helpers['assign']
    collection = bpy.data.collections.new(COLLECTION_NAME)
    scene.collection.children.link(collection)
    cylinder.__globals__.update(collection=collection, origin=origin)
    steel = helpers['surface']('Compact top | steel', (0.35, 0.42, 0.46), 0.85)
    aluminum = helpers['surface']('Compact top | aluminum', (0.65, 0.7, 0.73), 0.7)
    amber = helpers['surface']('Compact top | amber', (0.88, 0.39, 0.08), 0.15)

    def hex_cut(target, center, af, lower, upper):
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=af/math.sqrt(3), depth=upper-lower,
                                          location=origin+Vector((*center, (lower+upper)/2)))
        cutter = assign(bpy.context.object, 'hex cutter', steel)
        cutter.rotation_euler.z = target.rotation_euler.z
        cut(target, cutter)

    replacement = helpers['gear']('integral S4 replacement', 72, 14/45, right, 48, 54, 3.1,
                                  amber, connector=(20, 0.4, 62))
    source.data = replacement.data
    bpy.data.objects.remove(replacement, do_unlink=True)
    source['connector_teeth'] = 20
    source['connector_module_mm'] = 0.4
    source['output_connection'] = 'One-piece 72T/20T compound gear, no intermediate key; center transfer mesh z56..62'
    for curve in centered.animation_data.drivers:
        for variable in curve.driver.variables:
            for target in variable.targets:
                if target.id == drive:
                    target.id = source
    washer = cylinder('Compact top | S4 upper thrust washer', 2.3, 62, 62.8, right, steel)
    cut(washer, cylinder('cutter', 1.6, 61, 64, right, steel))

    shifted = [rotor, bpy.data.objects['Center hub | 4mm AF shaft drive key'],
               bpy.data.objects['Center hub | upper 688 bearing reference']]
    for obj in shifted:
        obj.data = obj.data.copy()
        inverse = obj.matrix_world.inverted()
        for vertex in obj.data.vertices:
            point = obj.matrix_world @ vertex.co
            point.z -= 12
            vertex.co = inverse @ point
        obj.data.update()
    replacement = helpers['gear']('centered gear replacement', 20, 0.4, (0, 0), 56, 62, 3.2,
                                  amber, hub=(3, 63.6))
    centered.data = replacement.data
    bpy.data.objects.remove(replacement, do_unlink=True)
    hex_cut(centered, (0, 0), 4.2, 59.5, 64)
    cut(centered, cylinder('cutter', 2.9, 55, 59.2, (0, 0), steel))
    center_key = bpy.data.objects['Center hub | 4mm AF shaft drive key']
    cut(center_key, cylinder('cutter', 1.6, 58, 70, (0, 0), steel))
    cut(rotor, cylinder('cutter', 1.25, 63, 76.2, (0, 0), steel))
    rotor['axial_retention'] = 'M3x16 bolt from below driven gear into tapped shaft; 2.5mm tap drill, thread not modeled'

    count = 96
    rings = [(56.2, 2.75), (59.2, 2.75), (59.2, 1.2), (75.2, 1.2)]
    vertices = [(radius*math.cos(2*math.pi*index/count), radius*math.sin(2*math.pi*index/count), height)
                for height, radius in rings for index in range(count)]
    faces = [tuple(reversed(range(count))), tuple(range(3*count, 4*count))]
    for layer in range(3):
        faces.extend((layer*count+index, layer*count+(index+1)%count,
                      (layer+1)*count+(index+1)%count, (layer+1)*count+index) for index in range(count))
    mesh = bpy.data.meshes.new('M3 axial retention screw reference')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bolt = bpy.data.objects.new('Compact top | M3x16 axial retention screw', mesh)
    collection.objects.link(bolt)
    bolt.location = origin
    bolt.data.materials.append(steel)
    hex_cut(bolt, (0, 0), 2.5, 55.9, 57.7)
    driver = bolt.driver_add('rotation_euler', 2).driver
    variable = driver.variables.new()
    variable.name = 'hub_angle'
    variable.type = helpers['enum'](bpy.types.DriverVariable, 'type', 'SINGLE_PROP')
    variable.targets[0].id = rotor
    variable.targets[0].data_path = 'rotation_euler[2]'
    driver.expression = 'hub_angle'
    bolt['reference'] = 'M3x16 head envelope and simplified minor-diameter shaft; threads not modeled'

    bpy.ops.mesh.primitive_cube_add(size=1, location=origin+Vector((0, 0, 74.5)))
    plate = assign(bpy.context.object, 'integrated top plate replacement', aluminum)
    plate.dimensions = (42, 42, 23)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cut(plate, cylinder('cutter', 4.3, 62, 87, (0, 0), steel))
    cut(plate, cylinder('cutter', 6.05, 62, 66.8, (0, 0), steel))
    cut(plate, cylinder('cutter', 8.05, 73.8, 79.2, (0, 0), steel))
    cut(plate, cylinder('cutter', 17.2, 79, 87, (0, 0), steel))
    for center in [left, right]:
        cut(plate, cylinder('cutter', 1.525, 62, 65.1, center, steel))
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            center = (horizontal, vertical)
            cut(plate, cylinder('cutter', 1.7, 62, 87, center, steel))
            cut(plate, cylinder('cutter', 3, 83.2, 87, center, steel))
    top_plate.data = plate.data
    top_plate.matrix_world = plate.matrix_world.copy()
    bpy.data.objects.remove(plate, do_unlink=True)
    top_plate['integrated_hub_support'] = '42x42x23mm, z63..86; pole sockets to65.1; centered 34.4mm opening, hub flush at86'
    bearing = cylinder('Compact top | lower 678 bearing reference 8x12x3', 6, 63.8, 66.8, (0, 0), steel)
    cut(bearing, cylinder('cutter', 4, 63, 68, (0, 0), steel))
    bearing['part'] = 'Purchased 678 bearing 8x12x3mm; smaller OD clears both unchanged poles'
    ring = cylinder('Compact top | lower bearing retaining ring', 6, 63, 63.8, (0, 0), steel)
    cut(ring, cylinder('cutter', 4.3, 62, 65, (0, 0), steel))
    ring['retention'] = 'Reference retainer; groove and fastening details not certified'

    obsolete = ['Center hub | S4 transfer pinion 20T', 'Center hub | S4 hollow hex drive',
                'Center hub | right journal bushing', 'Center hub | centered thrust pedestal',
                'Center hub | centered thrust pad', 'Center hub | raised plate with 34.4mm opening',
                'Center hub | lower 688 bearing reference', 'Center hub | lower bearing retaining ring']
    obsolete.extend(obj.name for obj in bpy.data.objects if obj.name.startswith('Center hub | standoff '))
    for name in obsolete:
        obj = bpy.data.objects[name]
        obj.hide_set(True)
        obj.hide_render = True
        obj['status'] = 'Superseded by integral S4 pinion and integrated top plate'
    collection['layout'] = 'S4 integral 20T meshes centered 20T at z56..62, below plate z63..86; poles and corner posts unchanged'
    collection['ratio'] = 'Unchanged 100:1, same direction as motor'
    collection['manufacturing'] = 'Prototype: bearing fits, retainer fastening, shaft thread, hollow key strength and camera-load capacity unverified'
    scene.frame_set(1)
    bpy.context.view_layer.update()
    print('BUILT integral S4 72T/20T, transfer below integrated 23mm plate, unchanged poles, flush centered hub at z86')


def shorten_integral_hub():
    name = 'Short Output - One Piece Center Rotor'
    if bpy.data.collections.get(name):
        raise RuntimeError('Short one-piece rotor already exists.')
    scene = bpy.context.scene
    scene.frame_set(1)
    source = bpy.data.objects['Poles | S4 72T output']
    centered = bpy.data.objects['Center hub | centered driven gear 20T']
    rotor = bpy.data.objects['Center hub | recessed 34mm flange and shaft']
    top_plate = bpy.data.objects['Poles | top plate']
    origin = source.location-Vector((7, math.sqrt(15), 0))
    assert all(abs(value-1)<1e-6 for value in rotor.scale)
    helpers = runpy.run_path(str(Path(__file__).with_name('build_fresh_100.py')))
    cylinder, cut, assign = helpers['cylinder'], helpers['cut'], helpers['assign']
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    cylinder.__globals__.update(collection=collection, origin=origin)
    steel = helpers['surface']('Short hub | steel', (0.35, 0.42, 0.46), 0.85)
    aluminum = helpers['surface']('Short hub | aluminum', (0.65, 0.7, 0.73), 0.7)
    bronze = helpers['surface']('Short hub | guide bushing', (0.49, 0.31, 0.1), 0.6)
    profile = helpers['outline'](20, 0.4)
    angles = [angle for angle, radius in profile]
    radii = [radius for angle, radius in profile]
    count = len(angles)
    sections = [(56, radii), (62, radii), (62, [3]*count), (62.3, [3]*count),
                (62.3, [4.99]*count), (70.3, [4.99]*count), (70.3, [5.5]*count),
                (71.5, [5.5]*count), (71.5, [17]*count), (77.5, [17]*count)]
    vertices = [(radius*math.cos(angle), radius*math.sin(angle), height)
                for height, values in sections for angle, radius in zip(angles, values)]
    bottom, top = len(vertices), len(vertices)+1
    vertices.extend([(0, 0, 56), (0, 0, 77.5)])
    faces = []
    for index in range(count):
        after = (index+1)%count
        for layer in range(len(sections)-1):
            offset = layer*count
            faces.append((offset+index, offset+after, offset+count+after, offset+count+index))
        offset = (len(sections)-1)*count
        faces.extend([(after, index, bottom), (offset+index, offset+after, top)])
    mesh = bpy.data.meshes.new('One-piece centered 20T gear stem and flange')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(aluminum)
    rotor.data = mesh
    rotor.animation_data_clear()
    old_driver = next(curve.driver for curve in centered.animation_data.drivers
                      if curve.data_path == 'rotation_euler' and curve.array_index == 2)
    driver = rotor.driver_add('rotation_euler', 2).driver
    driver.expression = old_driver.expression
    for old_variable in old_driver.variables:
        variable = driver.variables.new()
        variable.name, variable.type = old_variable.name, old_variable.type
        for target, old_target in zip(variable.targets, old_variable.targets):
            target.id, target.data_path = old_target.id, old_target.data_path
    scene.frame_set(1)
    bpy.context.view_layer.update()
    for index in range(4):
        angle = math.pi/4+index*math.pi/2
        world = rotor.matrix_world @ Vector((11.5*math.cos(angle), 11.5*math.sin(angle), 0))
        center = (world.x-origin.x, world.y-origin.y)
        cut(rotor, cylinder('cutter', 2.2, 71.3, 78.5, center, steel))
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=7.2/math.sqrt(3), depth=3.7,
                                          location=(world.x, world.y, origin.z+73.15))
        cutter = assign(bpy.context.object, 'M4 hex nut pocket', steel)
        cutter.rotation_euler.z = angle+rotor.rotation_euler.z+math.pi/6
        cut(rotor, cutter)
    rotor['construction'] = 'Single connected 20T gear, stem and 34mm flange; no center bore, hex coupling or coupling screw'
    rotor['stem_height_mm'] = 9.5
    rotor['journal_diameter_mm'] = 9.98
    rotor['teeth'], rotor['module_mm'] = 20, 0.4
    rotor['axial_retention'] = 'Shoulder seats on bearing inner race; upward retention and preload not finalized'
    rotor['assembly'] = '8.8mm gear and 9.98mm journal pass through 10mm bearing ID and 10.1mm guide bore before shoulder seats'

    bpy.ops.mesh.primitive_cube_add(size=1, location=origin+Vector((0, 0, 70.25)))
    replacement = assign(bpy.context.object, 'short top plate replacement', aluminum)
    replacement.dimensions = (42, 42, 14.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cut(replacement, cylinder('cutter', 6.05, 62, 65.3, (0, 0), steel))
    cut(replacement, cylinder('cutter', 5.3, 62, 78.5, (0, 0), steel))
    cut(replacement, cylinder('cutter', 9.55, 65.3, 70.7, (0, 0), steel))
    cut(replacement, cylinder('cutter', 17.2, 70.5, 78.5, (0, 0), steel))
    for horizontal in [-7, 7]:
        cut(replacement, cylinder('cutter', 1.525, 62, 65.1, (horizontal, math.sqrt(15)), steel))
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            center = (horizontal, vertical)
            cut(replacement, cylinder('cutter', 1.7, 62, 78.5, center, steel))
            cut(replacement, cylinder('cutter', 3, 74.7, 78.5, center, steel))
    top_plate.data = replacement.data
    top_plate.matrix_world = replacement.matrix_world.copy()
    bpy.data.objects.remove(replacement, do_unlink=True)
    top_plate['integrated_hub_support'] = '42x42x14.5mm, z63..77.5; unchanged pole sockets, 34.4mm recess, rotor flush'
    bearing = cylinder('Short hub | 6800 bearing reference 10x19x5', 9.5, 65.3, 70.3, (0, 0), steel)
    cut(bearing, cylinder('cutter', 5, 64, 72, (0, 0), steel))
    bearing['part'] = 'Purchased 6800 bearing, 10x19x5mm; modeled envelope only'
    guide = cylinder('Short hub | lower guide bushing 10.1x12', 6, 63, 65.3, (0, 0), bronze)
    cut(guide, cylinder('cutter', 5.05, 62, 66, (0, 0), steel))
    guide['fit'] = '10.1mm ID, 12mm OD, 2.3mm long; physical running fit and retention unverified'
    for old_name in ['Center hub | centered driven gear 20T', 'Center hub | 4mm AF shaft drive key',
                     'Compact top | M3x16 axial retention screw', 'Compact top | lower 678 bearing reference 8x12x3',
                     'Compact top | lower bearing retaining ring', 'Center hub | upper 688 bearing reference']:
        obj = bpy.data.objects[old_name]
        obj.hide_set(True)
        obj.hide_render = True
        obj['status'] = 'Superseded by short one-piece center rotor'
    collection['dimensions'] = 'Stem 9.5mm vs prior18; plate14.5mm vs prior23; rotor flange top77.5 vs prior86; 8.5mm height reduction'
    collection['ratio'] = '100:1, same direction as motor; integrated 20T directly driven by S4'
    collection['limitations'] = 'Prototype: single bearing plus short guide; reduced tilt stiffness vs two-bearing layout; fits, upward retention, preload and load capacity unverified'
    scene.frame_set(1)
    bpy.context.view_layer.update()
    print('BUILT short one-piece rotor; stem9.5mm, top plate14.5mm; fixed poles unchanged')


def seven_mm_slab():
    scene = bpy.context.scene
    scene.frame_set(1)
    plate = bpy.data.objects['Poles | top plate']
    if plate.get('slab_thickness_mm') == 7:
        raise RuntimeError('Seven millimeter slab already exists.')
    rotor = bpy.data.objects['Center hub | recessed 34mm flange and shaft']
    bearing = bpy.data.objects['Short hub | 6800 bearing reference 10x19x5']
    guide = bpy.data.objects['Short hub | lower guide bushing 10.1x12']
    source = bpy.data.objects['Poles | S4 72T output']
    origin = source.location-Vector((7, math.sqrt(15), 0))
    helpers = runpy.run_path(str(Path(__file__).with_name('build_fresh_100.py')))
    cylinder, cut, assign = helpers['cylinder'], helpers['cut'], helpers['assign']
    collection = bpy.data.collections['Short Output - One Piece Center Rotor']
    cylinder.__globals__.update(collection=collection, origin=origin)
    material = plate.data.materials[0]

    def merge(target, addition):
        bpy.context.view_layer.objects.active = target
        modifier = target.modifiers.new('Integrated support union', 'BOOLEAN')
        modifier.operation = helpers['enum'](bpy.types.BooleanModifier, 'operation', 'UNION')
        modifier.solver = helpers['enum'](bpy.types.BooleanModifier, 'solver', 'EXACT')
        modifier.object = addition
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(addition, do_unlink=True)

    bpy.ops.mesh.primitive_cube_add(size=1, location=origin+Vector((0, 0, 74)))
    replacement = assign(bpy.context.object, 'seven mm slab replacement', material)
    replacement.dimensions = (42, 42, 7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    merge(replacement, cylinder('support web', 20.2, 68.3, 70.6, (0, 0), material))
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            merge(replacement, cylinder('mounting boss', 4, 63, 70.6,
                                        (horizontal, vertical), material))
    for horizontal in [-7, 7]:
        merge(replacement, cylinder('pole socket boss', 2.3, 63, 68.4,
                                    (horizontal, math.sqrt(15)), material))
    cut(replacement, cylinder('cutter', 17.2, 70.1, 78.5, (0, 0), material))
    cut(replacement, cylinder('cutter', 5, 62, 79, (0, 0), material))
    merge(replacement, bearing)
    for horizontal in [-7, 7]:
        cut(replacement, cylinder('cutter', 1.525, 62, 65.1,
                                  (horizontal, math.sqrt(15)), material))
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            center = (horizontal, vertical)
            cut(replacement, cylinder('cutter', 1.7, 62, 79, center, material))
            cut(replacement, cylinder('cutter', 3, 74.7, 79, center, material))
    plate.data = replacement.data
    plate.matrix_world = replacement.matrix_world.copy()
    bpy.data.objects.remove(replacement, do_unlink=True)
    bpy.data.objects.remove(guide, do_unlink=True)
    rotor.data = rotor.data.copy()
    for vertex in rotor.data.vertices:
        if 71.4999 <= vertex.co.z <= 75.0001:
            vertex.co.z -= 1
    rotor.data.update()
    rotor['flange_thickness_mm'] = 7
    rotor['stem_height_mm'] = 8.5
    rotor['assembly'] = '8.8mm gear and 9.98mm journal pass through integrated 10mm support bore'
    rotor['axial_retention'] = 'Shoulder contacts integrated support at z70.3; upward retention and preload not finalized'
    plate['slab_thickness_mm'] = 7
    plate['integrated_hub_support'] = '42x42x7mm slab z70.5..77.5; web z68.3..70.1 under opening; integrated 6800 envelope z65.3..70.3; mounting and pole bosses down to63'
    plate['bearing_status'] = 'Former 6800 reference fused into plate; solid support geometry, not a functioning rolling bearing'
    collection['dimensions'] = '7mm main slab and 7mm flange; flush at77.5; support web and mounting bosses extend below slab to63'
    collection['limitations'] = 'Solid integrated support replaces bearing reference; guide removed; friction, fits, axial retention and load capacity unverified'
    if 'validation' in collection:
        del collection['validation']
    bpy.context.view_layer.update()
    print('BUILT seven mm slab and flange; bearing reference fused, guide deleted')


if __name__ == '__main__':
    build()