"""Run with Blender: blender --background blender/rig-2.blend --python gazebo/rig2/export_rig2.py."""

import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

import bpy
from mathutils import Euler, Matrix


def export():
    folder = Path(__file__).resolve().parent
    scene = bpy.data.scenes['Single Servo Rig']
    bpy.context.window.scene = scene
    bpy.context.view_layer.update()
    tree = ET.parse(folder / 'urdf/rig2.urdf')
    robot = tree.getroot()
    joint_names = {joint.attrib['name'] for joint in robot.findall('joint')}
    for link in robot.findall('link'):
        old_name = link.attrib['name']
        if old_name not in joint_names:
            continue
        new_name = old_name + '_link'
        link.set('name', new_name)
        for joint in robot.findall('joint'):
            for tag in ('parent', 'child'):
                endpoint = joint.find(tag)
                if endpoint.get('link') == old_name:
                    endpoint.set('link', new_name)
        for gazebo in robot.findall('gazebo'):
            if gazebo.get('reference') == old_name:
                gazebo.set('reference', new_name)
    links = {link.attrib['name']: link for link in robot.findall('link')}
    poses = {'world': Matrix.Identity(4)}
    pending = list(robot.findall('joint'))
    while pending:
        progressed = False
        for joint in pending[:]:
            parent = joint.find('parent').attrib['link']
            if parent not in poses:
                continue
            origin = joint.find('origin')
            xyz = [float(value) for value in origin.get('xyz', '0 0 0').split()] if origin is not None else [0, 0, 0]
            rpy = [float(value) for value in origin.get('rpy', '0 0 0').split()] if origin is not None else [0, 0, 0]
            transform = Euler(rpy).to_matrix().to_4x4()
            transform.translation = xyz
            poses[joint.find('child').attrib['link']] = poses[parent] @ transform
            pending.remove(joint)
            progressed = True
        if not progressed:
            raise ValueError('Disconnected or cyclic URDF joints')

    mesh_folder = folder / 'urdf/meshes/rig2'
    mesh_folder.mkdir(parents=True, exist_ok=True)
    graph = bpy.context.evaluated_depsgraph_get()
    report = {'source': str(Path(bpy.data.filepath).resolve()), 'scene': scene.name, 'meshes': []}
    minimum_z = float('inf')
    for obj in scene.objects:
        if obj.type != 'MESH' or obj.hide_render:
            continue
        name = re.sub(r'[^A-Za-z0-9_]', '_', obj.name)
        if name not in links and name + '_link' in links:
            name += '_link'
        if name not in links:
            raise ValueError(f'No URDF link for visible mesh {obj.name}: {name}')
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            if not mesh.loop_triangles:
                raise ValueError(f'Empty mesh: {obj.name}')
            world_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
            minimum_z = min(minimum_z, min(point.z for point in world_points))
            inverse = poses[name].inverted()
            points = [inverse @ point for point in world_points]
            path = mesh_folder / f'{name}.stl'
            with path.open('wb') as output:
                output.write(b'Rig 2 evaluated Blender mesh'.ljust(80, b'\0'))
                output.write(struct.pack('<I', len(mesh.loop_triangles)))
                for triangle in mesh.loop_triangles:
                    vertices = [points[index] for index in triangle.vertices]
                    normal = (vertices[1] - vertices[0]).cross(vertices[2] - vertices[0]).normalized()
                    output.write(struct.pack('<12fH', *normal, *vertices[0], *vertices[1], *vertices[2], 0))
            assert path.stat().st_size == 84 + 50 * len(mesh.loop_triangles)
            link = links[name]
            color_name, rgba = 'Grey', '0.7 0.7 0.7 1'
            if obj.name.startswith('T_'):
                color_name, rgba = 'Blue', '0 0 1 1'
            elif obj.name.startswith('wooden_'):
                color_name, rgba = 'Orange', '1 0.5 0 1'
            elif 'servo_body' in obj.name or 'housing' in obj.name or 'front cover' in obj.name:
                color_name, rgba = 'DarkGrey', '0.2 0.2 0.2 1'
            elif 'adapter' in obj.name.lower() or obj.name == 'Wrist2Gripper':
                color_name, rgba = 'Yellow', '1 1 0 1'
            material = ET.Element('material', name=f'material_{name}')
            ET.SubElement(material, 'color', rgba=rgba)
            gazebo = next((element for element in robot.findall('gazebo')
                           if element.get('reference') == name), None)
            if gazebo is None:
                gazebo = ET.SubElement(robot, 'gazebo', reference=name)
            for previous in list(gazebo.findall('material')):
                gazebo.remove(previous)
            ET.SubElement(gazebo, 'material').text = f'Gazebo/{color_name}'
            for element in list(link):
                if element.tag in ('visual', 'collision'):
                    link.remove(element)
            for kind in ('visual', 'collision'):
                element = ET.SubElement(link, kind)
                geometry = ET.SubElement(element, 'geometry')
                ET.SubElement(geometry, 'mesh', filename=f'package://urdf_humanoid_arm/urdf/meshes/rig2/{name}.stl')
                if kind == 'visual' and material is not None:
                    element.append(material)
            report['meshes'].append({'object': obj.name, 'link': name, 'triangles': len(mesh.loop_triangles)})
        finally:
            evaluated.to_mesh_clear()
    assert report['meshes'], 'No meshes exported'
    report['minimum_source_z'] = minimum_z
    report['spawn_height'] = max(0.0, -minimum_z)
    ET.indent(tree)
    tree.write(folder / 'urdf/rig2.urdf', encoding='utf-8', xml_declaration=True)
    (folder / 'urdf/rig2.export.json').write_text(json.dumps(report, indent=2) + '\n')
    print('EXPORTED', len(report['meshes']), 'evaluated meshes; spawn height:', report['spawn_height'])


export()