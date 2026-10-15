import math
from pathlib import Path
import runpy

import bpy
from mathutils import Vector


COLLECTION_NAME = 'Output Hub - 28mm M4 Flange'


def build():
    if bpy.data.collections.get(COLLECTION_NAME):
        raise RuntimeError('Output hub already exists; do not overwrite it.')
    scene = bpy.context.scene
    scene.frame_set(1)
    gear = bpy.data.objects['Poles | S4 72T output']
    top_plate = bpy.data.objects['Poles | top plate']
    pole = bpy.data.objects['Poles | right fixed 3mm pole']
    assert all(abs(value-1)<1e-6 for value in gear.scale)
    assert all(abs(value)<1e-6 for value in gear.rotation_euler[:2])
    origin = gear.location-Vector((7, math.sqrt(15), 0))
    center = (7, math.sqrt(15))
    pole_points = [pole.matrix_world @ vertex.co-origin for vertex in pole.data.vertices]
    assert abs(max(point.z for point in pole_points)-65)<1e-3
    helpers = runpy.run_path(str(Path(__file__).with_name('build_fresh_100.py')))
    cylinder, cut, assign = helpers['cylinder'], helpers['cut'], helpers['assign']
    collection = bpy.data.collections.new(COLLECTION_NAME)
    scene.collection.children.link(collection)
    cylinder.__globals__.update(collection=collection, origin=origin)
    steel = helpers['surface']('Hub | bearing steel', (0.36, 0.42, 0.46), 0.85)
    aluminum = helpers['surface']('Hub | aluminum', (0.66, 0.71, 0.73), 0.7)
    collection['interface'] = '28mm OD, four M4 clearance holes on 18.5mm PCD, captive underside hex nuts'
    collection['ratio'] = 'S4 drives removable shaft through hollow hex insert, no additional reduction; 100:1 opposite motor'
    collection['bearing'] = '6800 reference: 10mm ID x 19mm OD x 5mm width; housing 19.1mm, shaft journal 9.98mm, fits provisional'
    collection['pole'] = 'Original fixed pole unmodified; rotor blind bore ends z65.2, 0.2mm above pole tip'
    collection['status'] = 'Geometric prototype; bearing retention, axial preload, tolerances, fasteners and load capacity require physical validation'

    lower = []
    for vertex in gear.data.vertices:
        radius = math.hypot(vertex.co.x, vertex.co.y)
        if abs(vertex.co.z-48)<1e-4 and radius>2:
            lower.append((math.atan2(vertex.co.y, vertex.co.x) % (2*math.pi), radius))
    lower.sort()
    assert len(lower)>500
    angles = [angle for angle, radius in lower]
    radii = [radius for angle, radius in lower]
    count = len(angles)
    rings = [(48, radii), (54, radii), (54, [4.5]*count), (61, [4.5]*count),
             (62, [4.99]*count), (72.8, [4.99]*count), (72.8, [5.5]*count),
             (74, [5.5]*count), (74, [14]*count), (79, [14]*count),
             (48, [1.55]*count), (65.2, [1.55]*count)]
    vertices = [(radius*math.cos(angle), radius*math.sin(angle), height)
                for height, values in rings for angle, radius in zip(angles, values)]
    bore_cap = len(vertices)
    vertices.append((0, 0, 65.2))
    top_cap = len(vertices)
    vertices.append((0, 0, 79))
    faces = []
    for index in range(count):
        after = (index+1) % count
        for layer in range(9):
            offset = layer*count
            faces.append((offset+index, offset+after, offset+count+after, offset+count+index))
        faces.extend([(after, index, 10*count+index, 10*count+after),
                      (10*count+after, 10*count+index, 11*count+index, 11*count+after),
                      (11*count+after, 11*count+index, bore_cap),
                      (9*count+index, 9*count+after, top_cap)])
    mesh = bpy.data.meshes.new('S4 integral output shaft and M4 flange')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for material in gear.data.materials:
        mesh.materials.append(material)
    mesh.materials.append(aluminum)
    for polygon in mesh.polygons:
        if polygon.center.z>61:
            polygon.material_index = len(mesh.materials)-1
    gear.data = mesh
    gear['output_flange_diameter_mm'] = 28.0
    gear['output_flange_thickness_mm'] = 5.0
    gear['output_bolt_circle_mm'] = 18.5
    gear['output_mount'] = 'Four 4.4mm through holes; underside hex pockets 7.2mm AF x 3.5mm deep; M4 nuts nominal 7mm AF x 3.2mm'
    gear['shaft_support'] = '9.98mm journal in 6800 bearing; 11mm shoulder contacts inner race at z72.8'

    bpy.context.view_layer.update()
    for index in range(4):
        angle = math.pi/4+index*math.pi/2
        local = Vector((9.25*math.cos(angle), 9.25*math.sin(angle), 0))
        world = gear.matrix_world @ local
        hole_center = (world.x-origin.x, world.y-origin.y)
        cut(gear, cylinder('cutter', 2.2, 73.8, 80, hole_center, steel))
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=7.2/math.sqrt(3), depth=3.7,
                                          location=(world.x, world.y, origin.z+75.65))
        cutter = assign(bpy.context.object, 'nut pocket cutter', steel)
        cutter.rotation_euler.z = angle+gear.rotation_euler.z+math.pi/6
        cut(gear, cutter)

    rotor = gear.copy()
    rotor.data = gear.data.copy()
    rotor.name = 'Hub | removable shaft and 28mm M4 flange'
    collection.objects.link(rotor)
    cut(rotor, cylinder('cutter', 40, 0, 61, center, steel))
    cut(gear, cylinder('cutter', 40, 61, 85, center, steel))
    for target, bottom, top in [(gear, 55.8, 62), (rotor, 60, 65.1)]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=6.2/math.sqrt(3), depth=top-bottom,
                                          location=origin+Vector((*center, (bottom+top)/2)))
        cutter = assign(bpy.context.object, 'hex socket cutter', steel)
        cutter.rotation_euler.z = gear.rotation_euler.z
        cut(target, cutter)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=6/math.sqrt(3), depth=9,
                                      location=origin+Vector((*center, 60.5)))
    key = assign(bpy.context.object, 'Hub | hollow 6mm AF hex drive insert', steel)
    key.rotation_euler.z = gear.rotation_euler.z
    cut(key, cylinder('cutter', 1.6, 55, 66, center, steel))
    for obj in [rotor, key]:
        obj.animation_data_clear()
        driver = obj.driver_add('rotation_euler', 2).driver
        variable = driver.variables.new()
        variable.name = 'output_angle'
        variable.type = helpers['enum'](bpy.types.DriverVariable, 'type', 'SINGLE_PROP')
        variable.targets[0].id = gear
        variable.targets[0].data_path = 'rotation_euler[2]'
        driver.expression = 'output_angle'
    gear['shaft_support'] = 'Removable flange shaft, 6mm AF hollow drive insert in 6.2mm AF sockets; coupling fit/backlash unverified'
    collection['assembly'] = 'Install S4 and hex insert, original top plate, added bearing plate and bearing, then lower removable flange shaft into bearing and hex socket'
    cut(top_plate, cylinder('cutter', 5.3, 62, 67, center, steel))
    pole['support'] = 'Length/location unchanged; upper radial support through rotating shaft and bearing; 0.2mm pole-tip clearance to rotor blind bore'
    for name in ['Poles | right upper washer', 'Poles | right retaining spacer']:
        obj = bpy.data.objects[name]
        obj.hide_set(True)
        obj.hide_render = True
        obj['status'] = 'Replaced by bearing-supported integral output shaft'

    bpy.ops.mesh.primitive_cube_add(size=1, location=origin+Vector((0, 0, 69.5)))
    upper_plate = assign(bpy.context.object, 'Hub | added bearing plate 42x42x7', aluminum)
    upper_plate.dimensions = (42, 42, 7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cut(upper_plate, cylinder('cutter', 5.3, 65, 74, center, steel))
    cut(upper_plate, cylinder('cutter', 9.55, 67.8, 74, center, steel))
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            bolt_center = (horizontal, vertical)
            cut(upper_plate, cylinder('cutter', 1.7, 65, 74, bolt_center, steel))
            cut(upper_plate, cylinder('cutter', 3, 70.2, 74, bolt_center, steel))
    upper_plate['attachment'] = 'Uses four existing 31mm-square frame bolt positions; select longer M3 fasteners with verified motor engagement'
    upper_plate['bearing_seat'] = '19.1mm pocket, shoulder at z67.8; bearing retention/preload requires final fit design'
    bearing = cylinder('Hub | 6800 bearing reference 10x19x5', 9.5, 67.8, 72.8, center, steel)
    cut(bearing, cylinder('cutter', 5.0, 67, 74, center, steel))
    bearing['type'] = 'Purchased 6800 bearing reference envelope, not a printable bearing'
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    rotor.select_set(True)
    bpy.context.view_layer.objects.active = rotor
    bpy.context.view_layer.update()
    print('BUILT removable 28mm output flange, hollow hex drive, four M4 captive-nut holes, added bearing plate; pole length unchanged')


if __name__ == '__main__':
    build()