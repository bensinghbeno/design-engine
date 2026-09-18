import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {existsSync, mkdtempSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {DOMParser} from '@xmldom/xmldom';
import {Vector3} from 'three';
import {parseRobot, forward, tipPosition, suggestedTip} from '../kinematics.js';

const file = fileURLToPath(new URL('../../urdf/rig.urdf.xacro', import.meta.url));
const expand = (...args) => execFileSync('/opt/ros/noetic/bin/xacro', [file, ...args], {
  encoding: 'utf8', timeout: 15000, env: {...process.env,
    PATH: '/opt/ros/noetic/bin:/usr/bin:/bin', PYTHONNOUSERSITE: '1',
    PYTHONPATH: '/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages'},
});
const xml = expand();
const robot = parseRobot(xml, DOMParser);
const near = (a, b) => assert.ok(Math.abs(a-b)<1e-8, `${a} != ${b}`);
const centre = (name, pose={}) => tipPosition(robot, name, [0,0,0], pose);

test('one cube per actuator, gold shafts and correct stator/output hierarchy', () => {
  for (const name of ['yaw_actuator', 'pitch_actuator']) {
    const visuals = robot.links.get(name).visuals;
    assert.equal(visuals.length, 1);
    assert.equal(visuals[0].kind, 'box');
    visuals[0].size.forEach(size => near(size,.12));
  }
  const colours = ['yaw_actuator','pitch_actuator','shoulder_yaw_link'].map(
    name => JSON.stringify(robot.links.get(name).visuals[0].rgba));
  assert.equal(new Set(colours).size,3);
  for (const name of ['shoulder_yaw_link','shoulder_pitch_shaft']) {
    assert.equal(robot.links.get(name).visuals[0].kind,'cylinder');
    near(robot.links.get(name).visuals[0].size[0],.012);
  }
  assert.equal(robot.joints.get('shoulder_yaw_joint').parent,'yaw_actuator');
  assert.equal(robot.joints.get('shoulder_yaw_joint').child,'shoulder_yaw_link');
  assert.equal(robot.joints.get('shoulder_joint').parent,'pitch_actuator');
  assert.equal(robot.joints.get('shoulder_joint').child,'shoulder_pitch_shaft');
  assert.equal(robot.joints.get('yaw_output_to_pitch_actuator').type,'fixed');
  assert.equal(robot.joints.get('pitch_output_to_upper_arm').type,'fixed');
});

test('housing touches bar and both shafts extend through their driven components', () => {
  near(centre('yaw_actuator').y-.06,.5);
  near(centre('pitch_actuator').z-.06-(centre('yaw_actuator').z+.06),.04);
  near(centre('upper_arm').y-.035-(centre('pitch_actuator').y+.06),.04);
  const transforms = forward(robot);
  function ends(name) {
    const v = robot.links.get(name).visuals[0];
    return [-1,1].map(sign => new Vector3(0,0,sign*v.size[1]/2)
      .applyMatrix4(v.origin).applyMatrix4(transforms.get(name)));
  }
  const yawEnds = ends('shoulder_yaw_link').sort((a,b)=>a.z-b.z);
  near(yawEnds[0].z,1.576); // inserted 24 mm into the fixed yaw housing
  near(yawEnds[1].z,centre('pitch_actuator').z+.06+.012);
  const pitchEnds = ends('shoulder_pitch_shaft').sort((a,b)=>a.y-b.y);
  near(pitchEnds[0].y,centre('pitch_actuator').y-.06-.012);
  near(pitchEnds[1].y,centre('upper_arm').y+.035+.012);
});

test('yaw carries pitch housing; pitching moves only the output shaft and arm', () => {
  const yawPose = {shoulder_yaw_joint:Math.PI/2};
  const pitchPose = {...yawPose, shoulder_joint:Math.PI/3};
  const zero = forward(robot), yaw = forward(robot,yawPose), pitched = forward(robot,pitchPose);
  assert.deepEqual(yaw.get('yaw_actuator').elements,zero.get('yaw_actuator').elements);
  assert.notDeepEqual(yaw.get('pitch_actuator').elements,zero.get('pitch_actuator').elements);
  assert.deepEqual(pitched.get('pitch_actuator').elements,yaw.get('pitch_actuator').elements);
  assert.notDeepEqual(pitched.get('shoulder_pitch_shaft').elements,yaw.get('shoulder_pitch_shaft').elements);
  assert.notDeepEqual(pitched.get('upper_arm').elements,yaw.get('upper_arm').elements);
});

test('actuator dimensions follow larger sections and arm_side mirrors the mounting', () => {
  const scaled = parseRobot(expand('stem_width:=0.2','crossbar_depth:=0.16'),DOMParser);
  scaled.links.get('yaw_actuator').visuals[0].size.forEach(size=>near(size,.24));
  const mirrored = parseRobot(expand('arm_side:=-1'),DOMParser);
  for (const name of ['yaw_actuator','pitch_actuator','upper_arm']) {
    const a = centre(name), b = tipPosition(mirrored,name,[0,0,0]);
    near(a.x,b.x); near(a.y,-b.y); near(a.z,b.z);
  }
  const tip = tipPosition(mirrored,'upper_arm',suggestedTip(mirrored,'upper_arm'));
  near(tip.y,-.695); near(tip.z,1.365);
});

test('Gazebo SDF conversion retains two movable joints and all coloured actuator parts', t => {
  if (!existsSync('/usr/bin/gz')) return t.skip('Gazebo Classic is not installed');
  const directory = mkdtempSync(path.join(tmpdir(),'arm-actuator-test-'));
  try {
    const filename = path.join(directory,'rig.urdf');
    writeFileSync(filename,xml);
    const sdf = execFileSync('/usr/bin/gz',['sdf','-p',filename],{encoding:'utf8',timeout:20000});
    const doc = new DOMParser().parseFromString(sdf,'application/xml');
    const joints = Array.from(doc.getElementsByTagName('joint'));
    for (const name of ['shoulder_yaw_joint','shoulder_joint']) {
      assert.ok(joints.some(j=>j.getAttribute('name')===name),`${name} survives conversion`);
    }
    const visuals = Array.from(doc.getElementsByTagName('visual'));
    for (const name of ['yaw_actuator','pitch_actuator','shoulder_yaw_link','shoulder_pitch_shaft']) {
      assert.ok(visuals.some(v=>v.getAttribute('name').includes(name)),`${name} has a visible part`);
    }
    for (const colour of ['Gazebo/Turquoise','Gazebo/Purple','Gazebo/Yellow']) assert.ok(sdf.includes(colour));
  } finally { rmSync(directory,{recursive:true,force:true}); }
});