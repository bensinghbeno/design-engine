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
  for (const name of ['pitch_actuator', 'roll_actuator', 'yaw_actuator']) {
    const visuals = robot.links.get(name).visuals;
    assert.equal(visuals.length, 1);
    assert.equal(visuals[0].kind, 'box');
    visuals[0].size.forEach(size => near(size,.12));
  }
  const colours = ['yaw_actuator','pitch_actuator','roll_actuator','shoulder_yaw_link'].map(
    name => JSON.stringify(robot.links.get(name).visuals[0].rgba));
  assert.equal(new Set(colours).size,4);
  for (const name of ['shoulder_yaw_link','shoulder_pitch_shaft','shoulder_roll_shaft']) {
    assert.equal(robot.links.get(name).visuals[0].kind,'cylinder');
    near(robot.links.get(name).visuals[0].size[0],.012);
  }
  assert.equal(robot.joints.get('shoulder_yaw_joint').parent,'yaw_actuator');
  assert.equal(robot.joints.get('shoulder_yaw_joint').child,'shoulder_yaw_link');
  assert.equal(robot.joints.get('shoulder_joint').parent,'pitch_actuator');
  assert.equal(robot.joints.get('shoulder_joint').child,'shoulder_pitch_shaft');
  assert.equal(robot.joints.get('shoulder_roll_joint').parent,'roll_actuator');
  assert.equal(robot.joints.get('shoulder_roll_joint').child,'shoulder_roll_shaft');
  for (const name of ['pitch_output_to_roll_actuator','roll_output_to_yaw_actuator','yaw_output_to_upper_arm']) {
    assert.equal(robot.joints.get(name).type,'fixed');
  }
});

test('pitch housing touches bar; gold shafts connect all stages with exposed gaps', () => {
  near(centre('pitch_actuator').y-.06,.5);
  near(centre('roll_actuator').y-.06-(centre('pitch_actuator').y+.06),.04);
  near(centre('yaw_actuator').x-.06-(centre('roll_actuator').x+.06),.04);
  near(centre('yaw_actuator').z-.06-centre('upper_arm').z,.04);
  const transforms = forward(robot);
  function ends(name) {
    const v = robot.links.get(name).visuals[0];
    return [-1,1].map(sign => new Vector3(0,0,sign*v.size[1]/2)
      .applyMatrix4(v.origin).applyMatrix4(transforms.get(name)));
  }
  const yawEnds = ends('shoulder_yaw_link').sort((a,b)=>a.z-b.z);
  near(yawEnds[0].z,centre('upper_arm').z-.04); // 40 mm into the arm
  near(yawEnds[1].z,centre('yaw_actuator').z-.06+.024); // 24 mm into its own housing
  const pitchEnds = ends('shoulder_pitch_shaft').sort((a,b)=>a.y-b.y);
  near(pitchEnds[0].y,centre('pitch_actuator').y+.06-.024);
  near(pitchEnds[1].y,centre('roll_actuator').y+.06+.012);
  const rollEnds = ends('shoulder_roll_shaft').sort((a,b)=>a.x-b.x);
  near(rollEnds[0].x,centre('roll_actuator').x+.06-.024);
  near(rollEnds[1].x,centre('yaw_actuator').x+.06+.012);
  near(rollEnds[0].z,centre('roll_actuator').z-.04);
  near(rollEnds[1].z,centre('yaw_actuator').z+.04);
  // The pitch and roll bores in the green cube have 16 mm surface clearance.
  near(pitchEnds[0].z-rollEnds[0].z-2*.012,.016);
});

test('each output carries only downstream stages, never its own actuator housing', () => {
  const zero = forward(robot);
  const stages = [
    {joint:'shoulder_joint', fixed:['pitch_actuator'], moved:['shoulder_pitch_shaft','roll_actuator','shoulder_roll_shaft','yaw_actuator','shoulder_yaw_link','upper_arm']},
    {joint:'shoulder_roll_joint', fixed:['pitch_actuator','shoulder_pitch_shaft','roll_actuator'], moved:['shoulder_roll_shaft','yaw_actuator','shoulder_yaw_link','upper_arm']},
    {joint:'shoulder_yaw_joint', fixed:['pitch_actuator','shoulder_pitch_shaft','roll_actuator','shoulder_roll_shaft','yaw_actuator'], moved:['shoulder_yaw_link','upper_arm']},
  ];
  for (const {joint,fixed,moved} of stages) {
    const pose = forward(robot,{[joint]:.7});
    for (const name of fixed) assert.deepEqual(pose.get(name).elements,zero.get(name).elements,`${joint} must not move ${name}`);
    for (const name of moved) assert.notDeepEqual(pose.get(name).elements,zero.get(name).elements,`${joint} must carry ${name}`);
  }
});

test('yaw axis follows pitch and roll and changes arm orientation rather than tip position', () => {
  const q = {shoulder_joint:Math.PI/2,shoulder_roll_joint:.4};
  const frames = forward(robot,q);
  const axis = new Vector3(0,0,1).transformDirection(frames.get('yaw_actuator'));
  near(axis.x,Math.cos(.4)); near(axis.y,-Math.sin(.4)); near(axis.z,0);
  const twist = {...q,shoulder_yaw_joint:Math.PI/4};
  const tip = suggestedTip(robot,'upper_arm');
  near(tipPosition(robot,'upper_arm',tip,q).distanceTo(tipPosition(robot,'upper_arm',tip,twist)),0);
  assert.ok(tipPosition(robot,'upper_arm',[.035,0,-.375],q)
    .distanceTo(tipPosition(robot,'upper_arm',[.035,0,-.375],twist))>.02);
});

test('actuator dimensions follow larger sections and arm_side mirrors the mounting', () => {
  const scaled = parseRobot(expand('stem_width:=0.2','crossbar_depth:=0.16'),DOMParser);
  scaled.links.get('yaw_actuator').visuals[0].size.forEach(size=>near(size,.24));
  const mirrored = parseRobot(expand('arm_side:=-1'),DOMParser);
  for (const name of ['yaw_actuator','pitch_actuator','roll_actuator','upper_arm']) {
    const a = centre(name), b = tipPosition(mirrored,name,[0,0,0]);
    near(a.x,b.x); near(a.y,-b.y); near(a.z,b.z);
  }
  const tip = tipPosition(mirrored,'upper_arm',suggestedTip(mirrored,'upper_arm'));
  near(tip.x,.16); near(tip.y,-.72); near(tip.z,.985);
  const transforms = forward(mirrored);
  const v = mirrored.links.get('shoulder_pitch_shaft').visuals[0];
  const ends = [-1,1].map(sign => new Vector3(0,0,sign*v.size[1]/2)
    .applyMatrix4(v.origin).applyMatrix4(transforms.get('shoulder_pitch_shaft'))).sort((a,b)=>a.y-b.y);
  near(ends[0].y,-.792); near(ends[1].y,-.596);
});

test('Gazebo SDF conversion retains three movable joints and all coloured actuator parts', t => {
  if (!existsSync('/usr/bin/gz')) return t.skip('Gazebo Classic is not installed');
  const directory = mkdtempSync(path.join(tmpdir(),'arm-actuator-test-'));
  try {
    const filename = path.join(directory,'rig.urdf');
    writeFileSync(filename,xml);
    const sdf = execFileSync('/usr/bin/gz',['sdf','-p',filename],{encoding:'utf8',timeout:20000});
    const doc = new DOMParser().parseFromString(sdf,'application/xml');
    const joints = Array.from(doc.getElementsByTagName('joint'));
    for (const name of ['shoulder_joint','shoulder_roll_joint','shoulder_yaw_joint']) {
      assert.ok(joints.some(j=>j.getAttribute('name')===name),`${name} survives conversion`);
    }
    const visuals = Array.from(doc.getElementsByTagName('visual'));
    for (const name of ['yaw_actuator','pitch_actuator','roll_actuator','shoulder_yaw_link','shoulder_pitch_shaft','shoulder_roll_shaft']) {
      assert.ok(visuals.some(v=>v.getAttribute('name').includes(name)),`${name} has a visible part`);
    }
    for (const colour of ['Gazebo/Turquoise','Gazebo/Purple','Gazebo/Green','Gazebo/Yellow']) assert.ok(sdf.includes(colour));
  } finally { rmSync(directory,{recursive:true,force:true}); }
});