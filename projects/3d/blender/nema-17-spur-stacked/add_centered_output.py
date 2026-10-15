import math
from pathlib import Path
import runpy

import bpy
from mathutils import Vector


COLLECTION_NAME = 'Centered Output - Recessed M4 Hub'


def build():
    if bpy.data.collections.get(COLLECTION_NAME):
        raise RuntimeError('Centered output already exists.')
    scene = bpy.context.scene
    scene.frame_set(1)
    source = bpy.data.objects['Poles | S4 72T output']
    old_key = bpy.data.objects['Hub | hollow 6mm AF hex drive insert']
    plate = bpy.data.objects['Poles | top plate']
    origin = source.location-Vector((7, math.sqrt(15), 0))
    right = (7, math.sqrt(15))
    assert abs(plate.location.x-origin.x)<1e-4 and abs(plate.location.y-origin.y)<1e-4
    helpers = runpy.run_path(str(Path(__file__).with_name('build_fresh_100.py')))
    cylinder, cut, assign = helpers['cylinder'], helpers['cut'], helpers['assign']
    collection = bpy.data.collections.new(COLLECTION_NAME)
    scene.collection.children.link(collection)
    cylinder.__globals__.update(collection=collection, origin=origin)
    steel = helpers['surface']('Center hub | steel', (0.35, 0.42, 0.46), 0.85)
    aluminum = helpers['surface']('Center hub | aluminum', (0.65, 0.7, 0.73), 0.7)
    amber = helpers['surface']('Center hub | amber', (0.88, 0.39, 0.08), 0.15)
    bronze = helpers['surface']('Center hub | bronze', (0.49, 0.31, 0.1), 0.6)
    collection['ratio'] = 'S4 to center via 20:20 spur pair; total 100:1, same direction as motor'
    collection['flange'] = '34mm OD x 6mm thick, recessed in 34.4mm opening; flush at z98; 0.2mm radial and 1mm underside clearance'
    collection['mount'] = 'Four 4.4mm holes on 23mm PCD; underside hex pockets 7.2mm AF x 3.5mm deep for M4 nuts'
    collection['bearings'] = 'Two purchased 688 bearings 8x16x5mm; 7.98mm journal, 16.1mm seats; fits provisional'
    collection['status'] = 'Geometric prototype; retention, running fits, thrust preload, fasteners and load capacity not certified'

    def body(name, center, sections, material):
        profile = helpers['outline'](20, 0.4)
        angles = [angle for angle, radius in profile]
        tooth_radii = [radius for angle, radius in profile]
        count = len(angles)
        vertices = []
        for height, radius in sections:
            radii = tooth_radii if radius is None else [radius]*count
            vertices.extend((size*math.cos(angle), size*math.sin(angle), height)
                            for angle, size in zip(angles, radii))
        bottom_cap, top_cap = len(vertices), len(vertices)+1
        vertices.extend([(0, 0, sections[0][0]), (0, 0, sections[-1][0])])
        faces = []
        for index in range(count):
            after = (index+1)%count
            for layer in range(len(sections)-1):
                offset = layer*count
                faces.append((offset+index, offset+after, offset+count+after, offset+count+index))
            last = (len(sections)-1)*count
            faces.extend([(after, index, bottom_cap), (last+index, last+after, top_cap)])
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.location = origin+Vector((*center, 0))
        obj.data.materials.append(material)
        return obj

    def follow(obj, target, expression):
        driver = obj.driver_add('rotation_euler', 2).driver
        variable = driver.variables.new()
        variable.name = 'upstream_angle'
        variable.type = helpers['enum'](bpy.types.DriverVariable, 'type', 'SINGLE_PROP')
        variable.targets[0].id = target
        variable.targets[0].data_path = 'rotation_euler[2]'
        driver.expression = expression
        scene.frame_set(1)
        bpy.context.view_layer.update()

    def hex_cut(target, center, af, lower, upper):
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=af/math.sqrt(3), depth=upper-lower,
                                          location=origin+Vector((*center, (lower+upper)/2)))
        cutter = assign(bpy.context.object, 'hex cutter', steel)
        cutter.rotation_euler.z = target.rotation_euler.z
        cut(target, cutter)

    drive = body('Center hub | S4 transfer pinion 20T', right,
                 [(61, 4.5), (67, 4.5), (68, None), (74, None)], amber)
    follow(drive, source, 'upstream_angle')
    cut(drive, cylinder('cutter', 1.55, 60, 65.2, right, steel))
    hex_cut(drive, right, 6.2, 60, 65.1)
    drive['teeth'], drive['module_mm'] = 20, 0.4
    drive['connection'] = 'Existing S4 hollow 6mm AF insert; original right pole unchanged'
    key = old_key.copy()
    key.data = old_key.data.copy()
    key.name = 'Center hub | S4 hollow hex drive'
    collection.objects.link(key)
    key.hide_set(False)
    key.hide_render = False

    gear = body('Center hub | centered driven gear 20T', (0, 0),
                [(68, None), (74, None), (74, 3), (75.6, 3)], amber)
    direction = math.atan2(-right[1], -right[0])
    phase = (2*direction-math.pi/20) % (2*math.pi/20)
    follow(gear, drive, f'{phase!r} - upstream_angle')
    hex_cut(gear, (0, 0), 4.2, 71.5, 76)
    gear['teeth'], gear['module_mm'] = 20, 0.4
    gear['ratio'] = '1:1 transfer from S4 axis to plate center, center distance 8mm'

    rotor = body('Center hub | recessed 34mm flange and shaft', (0, 0),
                 [(75.6, 3.99), (90.8, 3.99), (90.8, 5.5), (92, 5.5), (92, 17), (98, 17)], aluminum)
    follow(rotor, gear, 'upstream_angle')
    hex_cut(rotor, (0, 0), 4.2, 75.5, 79.9)
    rotor['mount'] = 'Four top-entry M4 screws into underside captive M4 hex nuts; 23mm PCD'
    rotor['shaft'] = '7.98mm bearing journal; removable 4mm AF hex coupling for assembly'
    for index in range(4):
        angle = math.pi/4+index*math.pi/2
        local = Vector((11.5*math.cos(angle), 11.5*math.sin(angle), 0))
        world = rotor.matrix_world @ local
        center = (world.x-origin.x, world.y-origin.y)
        cut(rotor, cylinder('cutter', 2.2, 91.8, 99, center, steel))
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=7.2/math.sqrt(3), depth=3.7,
                                          location=(world.x, world.y, origin.z+93.65))
        cutter = assign(bpy.context.object, 'M4 nut pocket cutter', steel)
        cutter.rotation_euler.z = angle+rotor.rotation_euler.z+math.pi/6
        cut(rotor, cutter)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=4/math.sqrt(3), depth=8,
                                      location=origin+Vector((0, 0, 75.7)))
    center_key = assign(bpy.context.object, 'Center hub | 4mm AF shaft drive key', steel)
    follow(center_key, gear, 'upstream_angle')

    bushing = body('Center hub | right journal bushing', right,
                   [(63, 5.275), (66, 5.275), (66, 6), (66.5, 6)], bronze)
    cut(bushing, cylinder('cutter', 4.55, 62, 67, right, steel))
    bushing['fit'] = '9.1mm ID / 10.55mm OD reference bushing; flange rests on existing top plate'
    cylinder('Center hub | centered thrust pedestal', 1.8, 66, 67.5, (0, 0), steel)
    cylinder('Center hub | centered thrust pad', 2.5, 67.5, 68, (0, 0), bronze)
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            center = (horizontal, vertical)
            post = cylinder(f'Center hub | standoff {horizontal:+g} {vertical:+g}', 2.5, 66, 74.8, center, aluminum)
            cut(post, cylinder('cutter', 1.7, 65, 76, center, steel))
    bpy.ops.mesh.primitive_cube_add(size=1, location=origin+Vector((0, 0, 86.4)))
    housing = assign(bpy.context.object, 'Center hub | raised plate with 34.4mm opening', aluminum)
    housing.dimensions = (42, 42, 23.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cut(housing, cylinder('cutter', 4.3, 74, 99, (0, 0), steel))
    cut(housing, cylinder('cutter', 8.05, 74, 80.8, (0, 0), steel))
    cut(housing, cylinder('cutter', 8.05, 85.8, 91.2, (0, 0), steel))
    cut(housing, cylinder('cutter', 17.2, 91, 99, (0, 0), steel))
    for horizontal in [-15.5, 15.5]:
        for vertical in [-15.5, 15.5]:
            center = (horizontal, vertical)
            cut(housing, cylinder('cutter', 1.7, 74, 99, center, steel))
            cut(housing, cylinder('cutter', 3, 95.2, 99, center, steel))
    housing['opening'] = '34.4mm diameter x 7mm deep circular recess, 34mm rotor flush with top; 3.8mm minimum exterior rim'
    housing['attachment'] = 'Four 31mm-square M3 frame holes; longer fasteners and bearing retention need final design'
    for lower, label in [(75.8, 'lower'), (85.8, 'upper')]:
        bearing = cylinder('Center hub | '+label+' 688 bearing reference', 8, lower, lower+5, (0, 0), steel)
        cut(bearing, cylinder('cutter', 4, lower-1, lower+6, (0, 0), steel))
        bearing['part'] = 'Purchased 688 bearing 8x16x5mm; envelope only, not printable'
    retainer = cylinder('Center hub | lower bearing retaining ring', 8, 74.8, 75.8, (0, 0), steel)
    cut(retainer, cylinder('cutter', 4.3, 74, 77, (0, 0), steel))
    retainer['retention'] = 'Reference retaining ring; fastening method requires detailed manufacturing design'
    old = bpy.data.collections['Output Hub - 28mm M4 Flange']
    old.hide_viewport, old.hide_render = True, True
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    rotor.select_set(True)
    bpy.context.view_layer.objects.active = rotor
    scene.frame_set(1)
    bpy.context.view_layer.update()
    print('BUILT centered recessed 34mm hub, 34.4mm plate opening, 20:20 transfer, fixed poles unchanged')


if __name__ == '__main__':
    build()