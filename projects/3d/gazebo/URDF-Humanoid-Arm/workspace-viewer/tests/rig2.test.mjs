import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {DOMParser} from '@xmldom/xmldom';
import {Vector3} from 'three';
import {parseRobot, forward, tipPosition} from '../kinematics.js';

const robot = parseRobot(readFileSync(new URL('../../urdf/rig2.urdf', import.meta.url), 'utf8'), DOMParser);
const reference = JSON.parse(readFileSync(new URL('../../urdf/rig2.reference.json', import.meta.url), 'utf8'));
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-6, `${actual} != ${expected}`);

test('Rig 2 neutral frames and endpoint match the Blender export', () => {
  const frames = forward(robot);
  for (const [name, expected] of Object.entries(reference.links)) {
    const position = new Vector3().setFromMatrixPosition(frames.get(name));
    position.toArray().forEach((value, index) => near(value, expected.position[index]));
  }
  tipPosition(robot, 'wrist_to_gripper_tip', [0,0,0], {}).toArray()
    .forEach((value, index) => near(value, reference.tip_world[index]));
  assert.equal(robot.warnings.length, 0);
});

test('Rig 2 preserves the Y X Z X chain and all four joints affect the connector', () => {
  const frames = forward(robot);
  const moving = robot.ordered.filter(joint => joint.type !== 'fixed');
  assert.deepEqual(moving.map(joint => joint.name),
    ['shoulder_joint', 'shoulder_roll_joint', 'elbow_joint', 'wrist_roll_joint']);
  const rest = tipPosition(robot, 'wrist_to_gripper_tip', [0,0,0], {});
  for (const joint of moving) {
    near(joint.max - joint.min, 1.5 * Math.PI);
    joint.axis.clone().transformDirection(frames.get(joint.child)).toArray()
      .forEach((value, index) => near(value, reference.axes[joint.name][index]));
    const moved = tipPosition(robot, 'wrist_to_gripper_tip', [0,0,0], {[joint.name]: 0.4});
    assert.ok(moved.distanceTo(rest) > 0.00001, `${joint.name} moves the connector`);
    const posed = forward(robot, {[joint.name]: 0.4});
    assert.notDeepEqual(posed.get('wrist_to_gripper_tip').elements, frames.get('wrist_to_gripper_tip').elements);
  }
});

test('Rig 2 retains the edited wood and wrist connector dimensions', () => {
  for (const name of ['wooden_arm', 'wooden_forearm', 'Wrist2Gripper']) {
    robot.links.get(name).visuals[0].size.forEach((value, index) => near(value, reference.links[name].dimensions[index]));
  }
  assert.equal(robot.joints.get('wrist_connector_to_tip').parent, 'Wrist2Gripper');
});