import assert from 'node:assert/strict';
import test from 'node:test';
import {createOrientationTracker, parseSensorCsv, relativeQuaternion} from '../motion.js';

const close = (actual, expected, tolerance, label) =>
  assert.ok(Math.abs(actual - expected) <= tolerance, `${label}: ${actual} vs ${expected}`);

test('parses orientation-only CSV without acceleration columns', () => {
  const csv = 'time,seconds_elapsed,qx,qy,qz,qw,enabled\n'
    + '1,0,0,0,0,1,0\n2,0.1,0,0,0.1,0.995,1\n3,0.2,0,0,0.2,0.98,0\n';
  const parsed = parseSensorCsv(csv);
  assert.deepEqual(parsed.time, [0, 0.1, 0.2]);
  assert.deepEqual(parsed.quaternion[0], [0, 0, 0, 1]);
  assert.deepEqual(parsed.enabled, [false, true, false]);
  assert.equal('acceleration' in parsed, false);
});

test('rejects recordings without orientation columns', () => {
  const csv = 'time,seconds_elapsed,x,y,z\n1,0,0,0,0\n2,0.1,0,0,0\n3,0.2,0,0,0\n';
  assert.throws(() => parseSensorCsv(csv), /missing the qx column/);
});

test('relative quaternion reports rotation on all three axes', () => {
  const identity = [0, 0, 0, 1];
  for (let axis = 0; axis < 3; axis++) {
    const rotation = [0, 0, 0, Math.cos(Math.PI / 4)];
    rotation[axis] = Math.sin(Math.PI / 4);
    const relative = relativeQuaternion(identity, rotation);
    close(relative[axis], rotation[axis], 1e-9, `axis ${axis}`);
  }
});

test('orientation clutch holds and resumes from the held rotation', () => {
  const tracker = createOrientationTracker();
  const q0 = [0, 0, 0, 1];
  const q90 = [0, 0, Math.sin(Math.PI / 4), Math.cos(Math.PI / 4)];
  const q180 = [0, 0, 1, 0];
  tracker.update(q0);
  const held = tracker.update(q90);
  close(held[2], q90[2], 1e-9, 'gripper mirrors enabled rotation');
  let repeated;
  for (let i = 0; i < 20; i++) repeated = tracker.update(q90);
  close(repeated[2], held[2], 1e-9, 'same absolute angle does not accumulate');
  tracker.hold();
  assert.deepEqual(tracker.update(q180), held);
  tracker.resume();
  assert.deepEqual(tracker.update(q180), held);
  const continued = tracker.update([0, 0, Math.sin(3 * Math.PI / 4), Math.cos(3 * Math.PI / 4)]);
  close(continued[2], 1, 1e-9, 'motion continues from held rotation');
});