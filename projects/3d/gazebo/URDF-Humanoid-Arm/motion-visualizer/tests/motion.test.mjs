import assert from 'node:assert/strict';
import test from 'node:test';
import {createOrientationTracker, parseSensorCsv} from '../motion.js';

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

test('orientation tracker passes the absolute quaternion through without accumulating', () => {
  const tracker = createOrientationTracker();
  const absolute = [0.2, -0.3, 0.4, 0.8];
  const expected = absolute;
  assert.deepEqual(tracker.update(absolute), expected);
  let repeated;
  for (let i = 0; i < 20; i++) repeated = tracker.update(absolute);
  assert.deepEqual(repeated, expected);
});

test('orientation clutch holds raw quaternion and resumes direct input', () => {
  const tracker = createOrientationTracker();
  const q90 = [0, 0, Math.sin(Math.PI / 4), Math.cos(Math.PI / 4)];
  const q180 = [0, 0, 1, 0];
  const held = tracker.update(q90);
  assert.deepEqual(held, q90);
  tracker.hold();
  assert.deepEqual(tracker.update(q180), held);
  tracker.resume();
  assert.deepEqual(tracker.update(q180), q180);
});