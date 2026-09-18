import test from 'node:test';
import assert from 'node:assert/strict';
import {DOMParser} from '@xmldom/xmldom';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {parseRobot, tipPosition, suggestedTip, sampler, chain} from '../kinematics.js';
import {examples} from '../examples.js';

const parse = xml => parseRobot(xml, DOMParser);
const near = (a,b,eps=1e-8) => assert.ok(Math.abs(a-b)<eps, `${a} != ${b}`);
const state = r => Object.fromEntries([...r.joints.values()].filter(j => j.type !== 'fixed').map(j => [j.name,{min:j.min,max:j.max,value:0,enabled:true}]));
function samples(key, count=2500) {
  const e = examples[key], r = parse(e.xml), next = sampler(r,e.tip,e.offset,state(r),count);
  return Array.from({length:count},(_,i) => next(i));
}

test('one Y hinge traces a circle; positive Y rotates downward tip toward -X', () => {
  const e = examples.circle, r = parse(e.xml);
  const p = tipPosition(r,e.tip,e.offset,{pitch:Math.PI/2}); near(p.x,-.8); near(p.y,0); near(p.z,0);
  for (const p of samples('circle')) { near(p.length(),.8); near(p.y,0); }
});
test('two-axis shoulder spans sphere surface at constant radius', () => {
  const points = samples('sphere');
  for (const p of points) near(p.length(),.8);
  for (const key of ['x','y','z']) {
    assert.ok(Math.min(...points.map(p=>p[key])) < -.75);
    assert.ok(Math.max(...points.map(p=>p[key])) > .75);
  }
});
test('two parallel hinges span a planar annulus, not a sphere', () => {
  const points = samples('planar');
  for (const p of points) { near(p.y,0); assert.ok(p.length()>=.1-1e-9 && p.length()<=1+1e-9); }
  assert.ok(points.some(p=>p.length()<.12)); assert.ok(points.some(p=>p.length()>.98));
});
test('three-joint shoulder/elbow gives spatial reach with varying radius', () => {
  const points = samples('volume');
  for (const p of points) assert.ok(p.length()>=.1-1e-9 && p.length()<=1+1e-9);
  assert.ok(points.some(p=>p.length()<.15)); assert.ok(points.some(p=>p.length()>.95));
  assert.ok(points.some(p=>p.y>.4)); assert.ok(points.some(p=>p.y<-.4));
});
test('locked joints remain at their preview angle', () => {
  const e = examples.sphere, r = parse(e.xml), s = state(r);
  s.roll.enabled = false; s.roll.value = .4;
  const next = sampler(r,e.tip,e.offset,s,100);
  for (let i=0;i<100;i++) near(next(i).y,.8*Math.sin(.4));
});
test('URDF RPY and local prismatic axes are composed in the right order', () => {
  const r = parse(`<robot name="test"><link name="base"/><link name="end"/><joint name="slide" type="prismatic"><parent link="base"/><child link="end"/><origin xyz="1 2 3" rpy="0 0 ${Math.PI/2}"/><axis xyz="1 0 0"/><limit lower="0" upper="2"/></joint></robot>`);
  const p = tipPosition(r,'end',[0,0,0],{slide:1}); near(p.x,1); near(p.y,3); near(p.z,3);
});
test('fixed transforms and arbitrary rotation axes work', () => {
  const r = parse(`<robot name="test"><link name="base"/><link name="fixed"/><link name="end"/>
    <joint name="offset" type="fixed"><parent link="base"/><child link="fixed"/><origin xyz="1 2 3" rpy="0.2 0.3 0.4"/></joint>
    <joint name="rotate" type="continuous"><parent link="fixed"/><child link="end"/><axis xyz="1 1 1"/></joint></robot>`);
  const p = tipPosition(r,'end',[1,2,3],{rotate:.9}); near(p.distanceTo(tipPosition(r,'end',[0,0,0])),Math.sqrt(14));
});
test('limits, XML, Xacro, graph and unsupported joints fail explicitly', () => {
  assert.throws(()=>parse('<robot name="bad"><link name="a"/><link name="b"/></robot>'),/root/);
  assert.throws(()=>parse(examples.circle.xml.replace('axis xyz="0 1 0"','axis xyz="0 0 0"')),/zero/);
  assert.throws(()=>parse(examples.circle.xml.replace('type="revolute"','type="floating"')),/unsupported/);
  assert.throws(()=>parse(examples.circle.xml.replace('<axis', '<mimic joint="other"/><axis')),/mimic/);
  assert.throws(()=>parse(examples.circle.xml.replace('size="0.045','size="-0.045')),/positive/);
  assert.throws(()=>parse('<robot><link name="${name}"/></robot>'),/Xacro/);
  assert.throws(()=>parse('<!DOCTYPE robot><robot/>'),/DTD/);
  assert.throws(()=>parse('<robot><link></robot>'));
});
test('G1-style pitch and roll aim the arm while yaw twists its centreline', () => {
  const file = fileURLToPath(new URL('../../urdf/rig.urdf.xacro', import.meta.url));
  const xml = execFileSync('/opt/ros/noetic/bin/xacro',[file],{encoding:'utf8',env:{...process.env,
    PATH:'/opt/ros/noetic/bin:/usr/bin:/bin',PYTHONNOUSERSITE:'1',
    PYTHONPATH:'/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages'}});
  const r = parse(xml), offset = suggestedTip(r,'upper_arm');
  assert.equal(chain(r,'upper_arm').filter(j=>j.type!=='fixed').length,3);
  assert.deepEqual(chain(r,'upper_arm').filter(j=>j.type!=='fixed').map(j=>j.name),
    ['shoulder_joint','shoulder_roll_joint','shoulder_yaw_joint']);
  assert.deepEqual(r.joints.get('shoulder_joint').axis.toArray(),[0,1,0]);
  assert.deepEqual(r.joints.get('shoulder_roll_joint').axis.toArray(),[1,0,0]);
  assert.deepEqual(r.joints.get('shoulder_yaw_joint').axis.toArray(),[0,0,1]);
  near(offset[0],0); near(offset[1],0); near(offset[2],-.375);
  const p = tipPosition(r,'upper_arm',offset); near(p.x,.16); near(p.y,.72); near(p.z,.985);
  const next = sampler(r,'upper_arm',offset,state(r),2000);
  const points = Array.from({length:2000},(_,i)=>next(i));
  // Offset shoulder axes do not describe the previous constant-radius band.
  const radii = points.map(p=>Math.hypot(p.x,p.y-.62,p.z-1.54));
  assert.ok(Math.max(...radii)-Math.min(...radii)>.18);
  for (const axis of ['x','y','z']) {
    const values = points.map(p=>p[axis]);
    assert.ok(Math.max(...values)-Math.min(...values)>.95, `${axis} must span spatial reach`);
  }
  // Positive Y pitch takes the downward arm toward -X.
  const horizontal = tipPosition(r,'upper_arm',offset,{shoulder_joint:Math.PI/2});
  near(horizontal.x,-.555); near(horizontal.y,.72); near(horizontal.z,1.38);
  const sideways = tipPosition(r,'upper_arm',offset,{shoulder_roll_joint:Math.PI/2});
  near(sideways.x,.16); near(sideways.y,1.235); near(sideways.z,1.50);
  const combined = tipPosition(r,'upper_arm',offset,{shoulder_joint:Math.PI/2,shoulder_roll_joint:Math.PI/2});
  near(combined.x,-.04); near(combined.y,1.235); near(combined.z,1.38);
  // Yaw changes orientation, never the centreline tip, at arbitrary shoulder poses.
  for (const pitch of [-1.2,0,.7]) for (const roll of [-.6,0,1.1]) {
    const q = {shoulder_joint:pitch,shoulder_roll_joint:roll};
    const before = tipPosition(r,'upper_arm',offset,q);
    for (const yaw of [-Math.PI,-.8,Math.PI/2]) {
      near(before.distanceTo(tipPosition(r,'upper_arm',offset,{...q,shoulder_yaw_joint:yaw})),0);
    }
  }
  const doc = new DOMParser().parseFromString(xml,'application/xml');
  for (const l of Array.from(doc.getElementsByTagName('link'))) {
    if (l.getAttribute('name') === 'world') continue;
    assert.ok(Number(l.getElementsByTagName('mass')[0].getAttribute('value'))>0);
    const inertia = l.getElementsByTagName('inertia')[0];
    for (const axis of ['ixx','iyy','izz']) assert.ok(Number(inertia.getAttribute(axis))>0);
  }
});