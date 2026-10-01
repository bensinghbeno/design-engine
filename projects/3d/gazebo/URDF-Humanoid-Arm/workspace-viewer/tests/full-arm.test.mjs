import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {existsSync, mkdtempSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {DOMParser} from '@xmldom/xmldom';
import {Vector3} from 'three';
import {parseRobot, forward, tipPosition, chain} from '../kinematics.js';

const file = fileURLToPath(new URL('../../urdf/rig.urdf.xacro', import.meta.url));
const expand = (...args) => execFileSync('/opt/ros/noetic/bin/xacro', [file, ...args], {
  encoding: 'utf8', timeout: 15000, env: {...process.env,
    PATH: '/opt/ros/noetic/bin:/usr/bin:/bin', PYTHONNOUSERSITE: '1',
    PYTHONPATH: '/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages'},
});
const elements = (node, tag) => Array.from(node.getElementsByTagName(tag));
const parse = xml => parseRobot(xml, DOMParser);
const document = xml => new DOMParser().parseFromString(xml, 'application/xml');
const xml = expand();
const robot = parse(xml);
const stages = [
  ['shoulder_joint', 'pitch_actuator', 'shoulder_pitch_shaft', 'roll_actuator', [0,1,0], 'Gazebo/Purple', [.60,.16,.82,1]],
  ['shoulder_roll_joint', 'roll_actuator', 'shoulder_roll_shaft', 'upper_arm', [1,0,0], 'Gazebo/Green', [.18,.80,.28,1]],
  ['elbow_joint', 'elbow_actuator', 'elbow_shaft', 'forearm', [0,0,1], 'Gazebo/Orange', [1,.38,.08,1]],
  ['wrist_roll_joint', 'wrist_roll_actuator', 'wrist_roll_shaft', 'gripper_base', [1,0,0], 'Gazebo/Blue', [.12,.32,.90,1]],
].map(([joint, housing, shaft, receiver, axis, colour, rgba]) => ({joint, housing, shaft, receiver, axis, colour, rgba}));
const armJoints = stages.map(s => s.joint);
const fingerJoints = ['gripper_left_joint', 'gripper_right_joint'];
const pose = Object.fromEntries(armJoints.map((name, i) => [name, [.43,-.57,.71,-.83][i]]));
const scaleArgs = ['stem_height:=3', 'stem_width:=0.2', 'stem_depth:=0.2',
  'crossbar_length:=2', 'crossbar_thickness:=0.16', 'crossbar_depth:=0.16',
  'upper_arm_width:=0.14', 'upper_arm_depth:=0.14',
  'density:=750', 'actuator_density:=1800', 'shaft_density:=8000'];
// Cache real Xacro expansions, not hand-written substitutes for the model.
const variants = [
  {name: 'default', xml, side: 1, size: .12, densities: [500,1200,7800]},
  {name: 'mirrored', xml: expand('arm_side:=-1'), side: -1, size: .12, densities: [500,1200,7800]},
  {name: 'scaled', xml: expand(...scaleArgs), side: 1, size: .24, densities: [750,1800,8000]},
  {name: 'scaled mirrored', xml: expand(...scaleArgs, 'arm_side:=-1'), side: -1, size: .24, densities: [750,1800,8000]},
].map(v => ({...v, rig: parse(v.xml)}));
const near = (actual, expected, label = '', eps = 1e-8) =>
  assert.ok(Number.isFinite(actual) && Math.abs(actual - expected) < eps, `${label}: ${actual} != ${expected}`);
function vectorNear(actual, expected, label, eps = 1e-8) {
  actual.toArray().forEach((value, i) => near(value, expected[i], `${label}[${i}]`, eps));
}
function matrixNear(actual, expected, label) {
  actual.elements.forEach((value, i) => near(value, expected.elements[i], `${label}[${i}]`));
}
function matrixChanged(actual, expected, label) {
  assert.ok(actual.elements.some((value, i) => Math.abs(value - expected.elements[i]) > 1e-5), label);
}
const point = (frames, name, xyz = [0,0,0]) => new Vector3(...xyz).applyMatrix4(frames.get(name));
const tool = (rig, q = {}) => tipPosition(rig, 'gripper_tool', [0,0,0], q);
function visualFrame(rig, frames, name) {
  return frames.get(name).clone().multiply(rig.links.get(name).visuals[0].origin);
}
function shaftEnds(rig, frames, name) {
  const visual = rig.links.get(name).visuals[0];
  const frame = visualFrame(rig, frames, name);
  return [-1,1].map(sign => new Vector3(0,0,sign * visual.size[1]/2).applyMatrix4(frame));
}
// Slab intersection in box coordinates: require positive penetration, not
// merely proximity of link origins or contact with an infinite shaft line.
function boxPenetration(rig, frames, name, ends) {
  const inverse = visualFrame(rig, frames, name).invert();
  const [a,b] = ends.map(p => p.clone().applyMatrix4(inverse));
  const delta = b.clone().sub(a);
  const half = rig.links.get(name).visuals[0].size.map(v => v/2);
  let lo = 0, hi = 1;
  for (const [i, axis] of ['x','y','z'].entries()) {
    if (Math.abs(delta[axis]) < 1e-12) {
      if (Math.abs(a[axis]) >= half[i]) return 0;
    } else {
      const limits = [(-half[i]-a[axis])/delta[axis], (half[i]-a[axis])/delta[axis]].sort((x,y) => x-y);
      lo = Math.max(lo, limits[0]); hi = Math.min(hi, limits[1]);
    }
  }
  return Math.max(0, hi-lo) * delta.length();
}

test('full arm: exactly four continuous Y X Z X joints lead to the tool, plus two independent sliders', () => {
  const movable = [...robot.joints.values()].filter(j => j.type !== 'fixed');
  assert.deepEqual(movable.map(j => j.name).sort(), [...armJoints,...fingerJoints].sort());
  assert.deepEqual(chain(robot, 'gripper_tool').filter(j => j.type !== 'fixed').map(j => j.name), armJoints);
  for (const {joint,housing,shaft,receiver,axis} of stages) {
    const j = robot.joints.get(joint);
    assert.equal(j.type, 'continuous', joint);
    assert.equal(j.parent, housing, joint);
    assert.equal(j.child, shaft, joint);
    assert.deepEqual(j.axis.toArray(), axis, joint);
    const receivingJoint = robot.joints.get(robot.parents.get(receiver));
    assert.equal(receivingJoint.type, 'fixed', receiver);
    assert.equal(receivingJoint.parent, shaft, receiver);
  }
  for (const [i,name] of fingerJoints.entries()) {
    const j = robot.joints.get(name);
    assert.equal(j.type, 'prismatic');
    assert.equal(j.parent, 'gripper_base');
    assert.equal(j.child, i === 0 ? 'gripper_left_finger' : 'gripper_right_finger');
    assert.deepEqual(j.axis.toArray(), [0,i === 0 ? 1 : -1,0]);
    near(j.min, 0, name); near(j.max, .04, name);
    assert.deepEqual(chain(robot, j.child).filter(j => j.type !== 'fixed').map(j => j.name), [...armJoints,name]);
  }
  assert.equal(elements(document(xml), 'mimic').length, 0, 'Gazebo sliders must not rely on mimic coupling');
  assert.equal(robot.joints.get('gripper_to_tool').type, 'fixed');
  assert.equal(robot.joints.get('gripper_to_tool').parent, 'gripper_base');
  assert.equal(robot.links.get('gripper_tool').visuals.length, 0);
  assert.deepEqual(robot.warnings, []);
  for (const prefix of ['wrist_pitch','wrist_yaw']) {
    assert.ok(![...robot.links.keys(),...robot.joints.keys()].some(name=>name.startsWith(prefix)), `${prefix} hardware removed`);
  }
  const mounting = robot.joints.get('wrist_roll_to_gripper');
  assert.equal(mounting.type,'fixed');
  assert.equal(mounting.parent,'wrist_roll_shaft');
  assert.equal(mounting.child,'gripper_base');
});

test('full arm: each of four actuators is one correctly coloured cube and each output is gold', () => {
  assert.deepEqual([...robot.links.keys()].filter(name => name.endsWith('_actuator')).sort(), stages.map(s => s.housing).sort());
  for (const {name,rig,size} of variants) for (const stage of stages) {
    const visuals = rig.links.get(stage.housing).visuals;
    assert.equal(visuals.length, 1, `${name} ${stage.housing}`);
    assert.equal(visuals[0].kind, 'box');
    visuals[0].size.forEach(v => near(v, size, `${name} ${stage.housing} cube`));
    vectorNear(new Vector3().applyMatrix4(visuals[0].origin), [0,0,0], 'housing centered on its frame');
    assert.deepEqual(visuals[0].rgba, stage.rgba, stage.housing);
    const shafts = rig.links.get(stage.shaft).visuals;
    assert.equal(shafts.length, 1, stage.shaft);
    assert.equal(shafts[0].kind, 'cylinder');
    near(shafts[0].size[0], size/10, `${name} shaft radius`);
    assert.deepEqual(shafts[0].rgba, [1,.72,.08,1], stage.shaft);
  }
});

for (const stage of stages) test(`full arm geometry: ${stage.shaft} is centered on its parent and physically enters ${stage.receiver}`, () => {
  for (const {name,rig} of variants) for (const q of [{},pose]) {
    const label = `${name} ${stage.shaft} ${JSON.stringify(q)}`;
    const frames = forward(rig, q), ends = shaftEnds(rig, frames, stage.shaft);
    const direction = ends[1].clone().sub(ends[0]).normalize();
    const housingCenter = point(frames, stage.housing);
    near(housingCenter.clone().sub(ends[0]).cross(direction).length(), 0, `${label} axis through parent center`);
    const joint = rig.joints.get(stage.joint);
    const jointFrame = frames.get(stage.housing).clone().multiply(joint.origin);
    const jointAxis = joint.axis.clone().transformDirection(jointFrame);
    near(Math.abs(direction.dot(jointAxis)), 1, `${label} cylinder coaxial with revolute joint`);
    // Shafts insert 20% of a cube into their stator, rather than extending
    // all the way to its center. The axis and crossed face must be centered.
    const face = new Vector3().applyMatrix4(jointFrame);
    const along = face.clone().sub(ends[0]).dot(direction);
    near(face.clone().sub(ends[0]).cross(direction).length(), 0, `${label} parent face center`);
    assert.ok(along > 1e-8 && along < ends[0].distanceTo(ends[1])-1e-8, `${label} actually crosses parent face`);
    const size = rig.links.get(stage.housing).visuals[0].size[0];
    near(face.distanceTo(housingCenter), size/2, `${label} exits face center`);
    near(boxPenetration(rig, frames, stage.housing, ends), size/5, `${label} stator insertion`);
    if (stage.receiver === 'upper_arm') {
      const mount = rig.joints.get('roll_output_to_upper_arm');
      matrixNear(frames.get('upper_arm'), frames.get('shoulder_roll_shaft').clone().multiply(mount.origin), `${label} direct mount`);
      const armFrame = frames.get('upper_arm').clone().invert();
      for (const end of ends) {
        near(end.clone().applyMatrix4(armFrame).z, -rig.links.get('upper_arm').visuals[0].size[0]/2,
          `${label} roll shaft centerline is half the arm depth below its top`);
      }
    } else assert.ok(boxPenetration(rig, frames, stage.receiver, ends) > size/10, `${label} must penetrate receiving solid`);
    if (stage.receiver.endsWith('_actuator')) {
      const receivingCenter = point(frames, stage.receiver);
      near(receivingCenter.clone().sub(ends[0]).cross(direction).length(), 0, `${label} receiver centerline`);
      const projection = receivingCenter.clone().sub(ends[0]).dot(direction);
      assert.ok(projection > 0 && projection < ends[0].distanceTo(ends[1]), `${label} spans receiving center`);
      near(boxPenetration(rig, frames, stage.receiver, ends), size, `${label} through receiving cube`);
    }
  }
});

test('full arm: neutral forearm extends along local +X, with coaxial wrist roll and a touching wrist housing', () => {
  for (const {name,rig} of variants) {
    const visual = rig.links.get('forearm').visuals[0];
    vectorNear(new Vector3().applyMatrix4(visual.origin), [visual.size[0]/2,0,0], `${name} forearm center`);
    const frames = forward(rig);
    const elbowInverse = frames.get('elbow_actuator').clone().invert();
    const start = point(frames, 'forearm').applyMatrix4(elbowInverse);
    const end = point(frames, 'forearm', [visual.size[0],0,0]).applyMatrix4(elbowInverse);
    vectorNear(end.clone().sub(start), [visual.size[0],0,0], `${name} neutral forearm direction`);
    const wrist = rig.joints.get('wrist_roll_joint');
    const axis = wrist.axis.clone().transformDirection(frames.get(wrist.parent).clone().multiply(wrist.origin));
    const forearmAxis = new Vector3(1,0,0).transformDirection(frames.get('forearm'));
    near(axis.dot(forearmAxis), 1, `${name} wrist roll follows forearm`);
    const wristInForearm = point(frames, wrist.parent).applyMatrix4(frames.get('forearm').clone().invert());
    const size = rig.links.get(wrist.parent).visuals[0].size[0];
    vectorNear(wristInForearm, [visual.size[0]+size/2,0,0], `${name} wrist touches distal forearm`);
    const moved = forward(rig, {elbow_joint: Math.PI/2});
    const bentDirection = point(moved, 'forearm', [visual.size[0],0,0]).sub(point(moved, 'forearm'));
    vectorNear(bentDirection, [0,visual.size[0],0], `${name} positive elbow yaw turns +X toward +Y`);
  }
});

for (const {joint,housing,shaft} of stages) test(`full arm motion: ${joint} carries every descendant, not its own housing or upstream links`, () => {
  for (const {name,rig} of variants.slice(0,2)) {
    const before = forward(rig, pose), after = forward(rig, {...pose, [joint]: pose[joint]+.53});
    matrixNear(after.get(housing), before.get(housing), `${name} stationary ${housing}`);
    matrixChanged(after.get(shaft), before.get(shaft), `${name} rotating ${shaft}`);
    for (const link of rig.links.keys()) {
      const downstream = chain(rig, link).some(j => j.name === joint);
      if (downstream) matrixChanged(after.get(link), before.get(link), `${name} ${joint} must carry ${link}`);
      else matrixNear(after.get(link), before.get(link), `${name} ${joint} must not move ${link}`);
    }
    const toolDisplacement = tool(rig, pose).distanceTo(tool(rig, {...pose, [joint]: pose[joint]+.53}));
    if (joint === 'wrist_roll_joint') {
      near(toolDisplacement,0,`${name} coaxial wrist roll keeps fingertip midpoint fixed`);
      assert.ok(point(after,'gripper_left_finger').distanceTo(point(before,'gripper_left_finger'))>.001,
        `${name} wrist roll still rotates the jaws`);
    } else assert.ok(toolDisplacement > .001, `${name} ${joint} changes tool position`);
    const bodyToTool = before.get('gripper_base').clone().invert().multiply(before.get('gripper_tool'));
    const movedBodyToTool = after.get('gripper_base').clone().invert().multiply(after.get('gripper_tool'));
    matrixNear(movedBodyToTool, bodyToTool, `${name} body/tool rigid relationship`);
  }
});

test('full arm: arm_side mirrors every stage, fingertip and tool, including reflected nonzero poses', () => {
  for (const [normal,mirror] of [[variants[0].rig,variants[1].rig], [variants[2].rig,variants[3].rig]]) {
    for (const q of [{}, {...pose, gripper_left_joint: .04, gripper_right_joint: .04}]) {
      // Under Y reflection, axial vectors X/Z reverse, whereas Y does not.
      const reflected = {...q};
      for (const {joint,axis} of stages) reflected[joint] = (q[joint] ?? 0) * (axis[1] ? 1 : -1);
      const a = forward(normal, q), b = forward(mirror, reflected);
      for (const link of normal.links.keys()) {
        const other = link === 'gripper_left_finger' ? 'gripper_right_finger'
          : link === 'gripper_right_finger' ? 'gripper_left_finger' : link;
        const p = point(a, link);
        vectorNear(point(b, other), [p.x,-p.y,p.z], `${link} mirrored frame origin`);
        const visual = normal.links.get(link).visuals[0];
        if (visual) {
          const center = new Vector3().applyMatrix4(visualFrame(normal, a, link));
          vectorNear(new Vector3().applyMatrix4(visualFrame(mirror, b, other)), [center.x,-center.y,center.z], `${link} mirrored visual center`);
        }
      }
    }
  }
});

test('full arm: all solid masses and inertias follow dimensions/densities and remain positive definite on both sides and scales', () => {
  const housingNames = new Set(stages.map(s => s.housing));
  for (const {name,xml: source,densities} of variants) {
    for (const link of elements(document(source), 'link')) {
      const linkName = link.getAttribute('name');
      if (linkName === 'world') continue;
      const label = `${name} ${linkName}`;
      assert.equal(elements(link, 'inertial').length, 1, `${label} has exactly one inertia`);
      const mass = Number(elements(link, 'mass')[0].getAttribute('value'));
      assert.ok(Number.isFinite(mass) && mass > 0, `${label} positive mass`);
      const inertia = elements(link, 'inertia')[0];
      const [xx,yy,zz,xy,xz,yz] = ['ixx','iyy','izz','ixy','ixz','iyz'].map(key => Number(inertia.getAttribute(key)));
      assert.ok([xx,yy,zz,xy,xz,yz].every(Number.isFinite), `${label} finite inertia`);
      assert.ok(xx > 0 && xx*yy-xy*xy > 0 && xx*yy*zz+2*xy*xz*yz-xx*yz*yz-yy*xz*xz-zz*xy*xy > 0,
        `${label} positive-definite inertia tensor (Sylvester minors)`);
      for (const [a,b,c] of [[xx,yy,zz],[yy,zz,xx],[zz,xx,yy]]) assert.ok(a+b >= c-1e-12, `${label} physical inertia triangle inequality`);
      if (linkName === 'gripper_tool') continue; // Deliberate tiny virtual-point inertia.
      const visual = elements(link, 'visual')[0], collision = elements(link, 'collision')[0];
      assert.ok(visual && collision, `${label} has both visual and collision`);
      assert.equal(elements(link, 'collision').length, 1, label);
      const geometry = elements(visual, 'geometry')[0];
      assert.equal(geometry.toString(), elements(collision, 'geometry')[0].toString(), `${label} collision shape matches visual`);
      for (const tag of ['collision','inertial']) for (const attr of ['xyz','rpy']) {
        const origin = node => elements(node, 'origin')[0]?.getAttribute(attr) || '0 0 0';
        assert.deepEqual(origin(elements(link, tag)[0]).trim().split(/\s+/).map(Number), origin(visual).trim().split(/\s+/).map(Number), `${label} ${tag} ${attr}`);
      }
      const box = elements(visual, 'box')[0];
      let expectedMass, expectedInertia;
      if (box) {
        const [x,y,z] = box.getAttribute('size').trim().split(/\s+/).map(Number);
        assert.ok([x,y,z].every(v => v > 0 && Number.isFinite(v)), label);
        const density = housingNames.has(linkName) || linkName.startsWith('gripper_') ? densities[1] : densities[0];
        expectedMass = density*x*y*z;
        expectedInertia = [y*y+z*z,x*x+z*z,x*x+y*y].map(v => expectedMass*v/12);
      } else {
        const cylinder = elements(visual, 'cylinder')[0];
        assert.ok(cylinder, `${label} known solid primitive`);
        const r = Number(cylinder.getAttribute('radius')), length = Number(cylinder.getAttribute('length'));
        assert.ok(r > 0 && length > 0, label);
        expectedMass = densities[2]*Math.PI*r*r*length;
        const transverse = expectedMass*(3*r*r+length*length)/12;
        expectedInertia = [transverse,transverse,expectedMass*r*r/2];
      }
      near(mass, expectedMass, `${label} density times volume`);
      [xx,yy,zz].forEach((value, i) => near(value, expectedInertia[i], `${label} solid inertia ${i}`));
      [xy,xz,yz].forEach(value => near(value, 0, `${label} principal frame`));
    }
  }
});

test('full arm gripper: closed-to-open inner gap is 0..80 mm and the TCP is the midpoint of the finger ends', () => {
  for (const {name,rig} of variants) for (const armPose of [{},pose]) {
    const closed = forward(rig, armPose);
    for (const aperture of [0,.02,.04,.08]) {
      // Command both sliders explicitly; neither FK nor Gazebo supplies mimic.
      const q = {...armPose, gripper_left_joint: aperture/2, gripper_right_joint: aperture/2};
      const frames = forward(rig, q), inverse = frames.get('gripper_base').clone().invert();
      const innerEnds = ['gripper_left_finger','gripper_right_finger'].map((link, i) => {
        const v = rig.links.get(link).visuals[0];
        return new Vector3(v.size[0]/2, (i === 0 ? -1 : 1)*v.size[1]/2, 0)
          .applyMatrix4(visualFrame(rig, frames, link)).applyMatrix4(inverse);
      });
      const [left,right] = innerEnds;
      near(left.y-right.y, aperture, `${name} actual inner gap`);
      near(left.x, right.x, `${name} fingertip x alignment`);
      near(left.z, right.z, `${name} fingertip z alignment`);
      const tcp = point(frames, 'gripper_tool').applyMatrix4(inverse);
      vectorNear(tcp, left.clone().add(right).multiplyScalar(.5).toArray(), `${name} TCP at fingertip midpoint`);
      const baseLength = rig.links.get('gripper_base').visuals[0].size[0];
      const fingerLength = rig.links.get('gripper_left_finger').visuals[0].size[0];
      near(tcp.x, baseLength/2+fingerLength, `${name} tool at finger ends, not their centers`);
      for (const link of rig.links.keys()) if (!link.endsWith('_finger')) {
        matrixNear(frames.get(link), closed.get(link), `${name} aperture does not move ${link}`);
      }
      if (aperture > 0) for (const link of ['gripper_left_finger','gripper_right_finger']) {
        matrixChanged(frames.get(link), closed.get(link), `${name} aperture moves ${link}`);
      }
    }
  }
});

test('full arm gripper: individual sliders are independent and cannot move the body/tool or opposite finger', () => {
  const closed = forward(robot, pose);
  for (const jointName of fingerJoints) {
    const joint = robot.joints.get(jointName), frames = forward(robot, {...pose, [jointName]: .04});
    for (const link of robot.links.keys()) {
      if (link === joint.child) {
        near(point(frames, link).distanceTo(point(closed, link)), .04, `${jointName} stroke`);
      } else matrixNear(frames.get(link), closed.get(link), `${jointName} does not move ${link}`);
    }
  }
});

test('full arm reach: shoulder plus elbow has local positional rank three, not merely a rotated surface', t => {
  // A broad XYZ bounding box is insufficient: a sphere surface also has one.
  // Test a central-difference positional Jacobian with two shoulder columns
  // and the elbow column. Wrist angles stay fixed throughout differentiation.
  const candidates = [pose,
    Object.fromEntries(armJoints.map((name, i) => [name, [-.8,.4,1.1,-.3][i]])),
    Object.fromEntries(armJoints.map((name, i) => [name, [.9,.7,-1.2,.6][i]]))];
  const names = ['shoulder_joint','shoulder_roll_joint','elbow_joint'];
  function derivatives(rig, q, h) {
    return names.map(name => tool(rig, {...q, [name]: q[name]+h})
      .sub(tool(rig, {...q, [name]: q[name]-h})).multiplyScalar(1/(2*h)));
  }
  for (const {name,rig} of variants) {
    const scores = candidates.map(q => {
      const columns = derivatives(rig, q, 1e-5);
      const determinant = Math.abs(columns[0].dot(columns[1].clone().cross(columns[2])));
      return {q,columns,determinant,quality: determinant/columns.reduce((p,v) => p*v.length(), 1)};
    }).sort((a,b) => b.quality-a.quality);
    const best = scores[0];
    assert.ok(best.columns.every(v => v.length() > .01), `${name} all positional derivatives are nonzero`);
    assert.ok(best.quality > .05 && best.determinant > 1e-4,
      `${name} independent positional derivatives required: ${JSON.stringify(scores.map(({quality,determinant}) => ({quality,determinant})))}`);
    const refined = derivatives(rig, best.q, 5e-6);
    refined.forEach((v, i) => vectorNear(v, best.columns[i].toArray(), `${name} stable central difference`, 1e-7));
    t.diagnostic(`${name}: normalized Jacobian determinant ${best.quality.toFixed(6)}, |det| ${best.determinant.toFixed(6)} m^3/rad^3`);
  }
});

test('full arm reach: elbow yaw sweeps the tool around its local Z axis', () => {
  for (const {name,rig} of variants) {
    const frames = forward(rig, pose);
    const elbow = rig.joints.get('elbow_joint');
    const jointFrame = frames.get(elbow.parent).clone().multiply(elbow.origin);
    const pivot = new Vector3().applyMatrix4(jointFrame);
    const axis = elbow.axis.clone().transformDirection(jointFrame);
    const radialDistance = angle => {
      const offset = tool(rig, {...pose, elbow_joint: angle}).sub(pivot);
      return offset.addScaledVector(axis, -offset.dot(axis)).length();
    };
    const radii = [-Math.PI/2,-.7,0,.7,Math.PI/2].map(radialDistance);
    assert.ok(Math.max(...radii)-Math.min(...radii) < 1e-8, `${name} yaw preserves distance to its axis, got ${radii}`);
    assert.ok(tool(rig, {...pose, elbow_joint: Math.PI/2}).distanceTo(tool(rig, {...pose, elbow_joint: 0})) > .01,
      `${name} elbow yaw must sweep the tool`);
  }
});

test('full arm Gazebo: SDF retains all four arm joints, both independent finger joints, and each part colour', t => {
  if (!existsSync('/usr/bin/gz')) return t.skip('Gazebo Classic is not installed');
  const directory = mkdtempSync(path.join(tmpdir(), 'full-arm-test-'));
  try {
    const filename = path.join(directory, 'rig.urdf');
    writeFileSync(filename, xml);
    const sdf = execFileSync('/usr/bin/gz', ['sdf','-p',filename], {encoding: 'utf8', timeout: 20000});
    const doc = document(sdf);
    assert.equal(doc.documentElement.nodeName, 'sdf');
    const joints = elements(doc, 'joint');
    assert.deepEqual(joints.filter(j => j.getAttribute('type') !== 'fixed').map(j => j.getAttribute('name')).sort(), [...armJoints,...fingerJoints].sort(),
      'fixed-joint lumping must not discard any of the six movable joints');
    for (const name of [...armJoints,...fingerJoints]) {
      const matches = joints.filter(j => j.getAttribute('name') === name);
      assert.equal(matches.length, 1, `${name} survives exactly once`);
      const joint = matches[0], finger = fingerJoints.includes(name);
      assert.equal(joint.getAttribute('type'), finger ? 'prismatic' : 'revolute', `${name} SDF type`);
      const xyz = elements(elements(joint, 'axis')[0], 'xyz')[0].textContent.trim().split(/\s+/).map(Number);
      vectorNear(new Vector3(...xyz), robot.joints.get(name).axis.toArray(), `${name} SDF axis`);
      if (finger) {
        near(Number(elements(joint, 'lower')[0].textContent), 0, `${name} SDF lower`);
        near(Number(elements(joint, 'upper')[0].textContent), .04, `${name} SDF upper`);
      }
    }
    assert.equal(elements(doc, 'mimic').length, 0);
    const visuals = elements(doc, 'visual');
    const parts = [...stages.map(s => [s.housing,s.colour]), ...stages.map(s => [s.shaft,'Gazebo/Yellow']),
      ['upper_arm','Gazebo/Orange'], ['forearm','Gazebo/Orange'], ['gripper_base','Gazebo/DarkGrey'],
      ['gripper_left_finger','Gazebo/White'], ['gripper_right_finger','Gazebo/White']];
    for (const [name,colour] of parts) {
      // Fixed children are lumped into upstream links; inspect visual names
      // and their own material scripts rather than requiring original links.
      // Match the whole part name so roll_actuator cannot match wrist_roll_actuator.
      const pattern = new RegExp(`(?:^|__)${name}_visual(?:_\\d+)?$`);
      const matches = visuals.filter(v => pattern.test(v.getAttribute('name')));
      assert.equal(matches.length, 1, `${name} retains one visible part after lumping: ${visuals.map(v => v.getAttribute('name')).join(', ')}`);
      const scripts = elements(matches[0], 'script');
      assert.ok(scripts.some(s => elements(s, 'name').some(n => n.textContent.trim() === colour)), `${name} keeps ${colour}`);
    }
  } finally { rmSync(directory, {recursive: true, force: true}); }
});