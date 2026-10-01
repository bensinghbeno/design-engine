import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {existsSync, mkdtempSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {DOMParser} from '@xmldom/xmldom';
import {Vector3} from 'three';
import {parseRobot, forward, tipPosition} from '../kinematics.js';

const file = fileURLToPath(new URL('../../urdf/rig.urdf.xacro', import.meta.url));
const expand = (...args) => execFileSync('/opt/ros/noetic/bin/xacro', [file, ...args], {
  encoding: 'utf8', timeout: 15000, env: {...process.env,
    PATH: '/opt/ros/noetic/bin:/usr/bin:/bin', PYTHONNOUSERSITE: '1',
    PYTHONPATH: '/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages'},
});
const xml = expand();
const robot = parseRobot(xml, DOMParser);
const near = (a, b) => assert.ok(Math.abs(a-b)<1e-8, `${a} != ${b}`);
const centre = (rig, name, pose={}) => tipPosition(rig, name, [0,0,0], pose);

test('shoulder has pitch and roll only; roll shaft is fixed directly to upper arm', () => {
  assert.equal(robot.joints.has('shoulder_yaw_joint'), false);
  assert.equal(robot.links.has('yaw_actuator'), false);
  assert.equal(robot.links.has('shoulder_yaw_link'), false);
  assert.equal(robot.joints.get('shoulder_joint').parent, 'pitch_actuator');
  assert.equal(robot.joints.get('shoulder_joint').child, 'shoulder_pitch_shaft');
  assert.equal(robot.joints.get('shoulder_roll_joint').parent, 'roll_actuator');
  assert.equal(robot.joints.get('shoulder_roll_joint').child, 'shoulder_roll_shaft');
  const mount = robot.joints.get('roll_output_to_upper_arm');
  assert.equal(mount.type, 'fixed');
  assert.equal(mount.parent, 'shoulder_roll_shaft');
  assert.equal(mount.child, 'upper_arm');
  assert.deepEqual(robot.joints.get('shoulder_joint').axis.toArray(), [0,1,0]);
  assert.deepEqual(robot.joints.get('shoulder_roll_joint').axis.toArray(), [1,0,0]);
  const frames = forward(robot);
  const shaftFrame = frames.get('shoulder_roll_shaft').clone().multiply(mount.origin);
  assert.deepEqual(frames.get('upper_arm').elements, shaftFrame.elements);
});

test('direct roll-shaft mount follows pitch and roll with no extra yaw stage', () => {
  const fixed = forward(robot);
  for (const pitch of [0, 0.7, -1.2]) for (const roll of [0, 0.5, -0.9]) {
    const frames = forward(robot, {shoulder_joint:pitch, shoulder_roll_joint:roll});
    const mount = robot.joints.get('roll_output_to_upper_arm');
    const expectedArm = frames.get('shoulder_roll_shaft').clone().multiply(mount.origin);
    assert.deepEqual(frames.get('upper_arm').elements, expectedArm.elements);
    const shaftOriginInArm = new Vector3().applyMatrix4(frames.get('shoulder_roll_shaft'))
      .applyMatrix4(frames.get('upper_arm').clone().invert());
    near(shaftOriginInArm.z, -robot.links.get('upper_arm').visuals[0].size[0]/2);
    if (pitch || roll) assert.notDeepEqual(frames.get('upper_arm').elements, fixed.get('upper_arm').elements);
  }
});

test('four arm joints remain movable and upper arm mirrors with arm_side', () => {
  const movable = [...robot.joints.values()].filter(joint => joint.type !== 'fixed').map(joint => joint.name);
  assert.deepEqual(movable, ['shoulder_joint','shoulder_roll_joint','elbow_joint','wrist_roll_joint',
    'gripper_left_joint','gripper_right_joint']);
  const mirrored = parseRobot(expand('arm_side:=-1'), DOMParser);
  for (const name of ['pitch_actuator','roll_actuator','shoulder_roll_shaft','upper_arm']) {
    const normal = centre(robot, name), reverse = centre(mirrored, name);
    near(normal.x, reverse.x); near(normal.y, -reverse.y); near(normal.z, reverse.z);
  }
});

test('actuator dimensions scale and removed yaw hardware is absent', () => {
  const scaled = parseRobot(expand('stem_width:=0.2','crossbar_depth:=0.16'), DOMParser);
  for (const name of ['pitch_actuator','roll_actuator','elbow_actuator','wrist_roll_actuator']) {
    scaled.links.get(name).visuals[0].size.forEach(size => near(size, .24));
  }
  assert.equal(scaled.links.has('yaw_actuator'), false);
  assert.equal(scaled.links.has('shoulder_yaw_link'), false);
});

test('Gazebo conversion retains four arm joints and the direct arm connection', t => {
  if (!existsSync('/usr/bin/gz')) return t.skip('Gazebo Classic is not installed');
  const directory = mkdtempSync(path.join(tmpdir(), 'arm-actuator-test-'));
  try {
    const filename = path.join(directory, 'rig.urdf');
    writeFileSync(filename, xml);
    const sdf = execFileSync('/usr/bin/gz', ['sdf', '-p', filename], {encoding:'utf8', timeout:20000});
    const doc = new DOMParser().parseFromString(sdf, 'application/xml');
    const joints = [...doc.getElementsByTagName('joint')];
    for (const name of ['shoulder_joint','shoulder_roll_joint','elbow_joint','wrist_roll_joint']) {
      assert.ok(joints.some(joint => joint.getAttribute('name') === name), `${name} survives conversion`);
    }
    assert.ok(!joints.some(joint => joint.getAttribute('name') === 'shoulder_yaw_joint'));
  } finally { rmSync(directory, {recursive:true, force:true}); }
});