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


if __name__ == '__main__':
    build()