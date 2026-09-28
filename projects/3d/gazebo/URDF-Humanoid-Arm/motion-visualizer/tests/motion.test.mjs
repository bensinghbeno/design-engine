import assert from 'node:assert/strict';
import test from 'node:test';
import {createLiveEstimator, createPoseTracker, estimateTrajectory, headingAngle, parseSensorCsv, rotateVector} from '../motion.js';

const close = (actual, expected, tolerance, label) =>
  assert.ok(Math.abs(actual - expected) <= tolerance, `${label}: ${actual} vs ${expected}`);

test('parses Sensor Logger columns by name', () => {
  const csv = 'time,seconds_elapsed,z,y,x\n1,10,3,2,1\n2,10.5,6,5,4\n3,11,9,8,7\n';
  assert.deepEqual(parseSensorCsv(csv), {time:[0,0.5,1],acceleration:[[1,2,3],[4,5,6],[7,8,9]]});
});

test('constant sensor bias produces no motion', () => {
  const time = [0,0.5,1,1.5], acceleration = time.map(() => [0.2,-0.1,0.3]);
  const result = estimateTrajectory(time, acceleration);
  assert.deepEqual(result.position, time.map(() => [0,0,0]));
  assert.equal(result.pathLength, 0);
});

test('rejects non-increasing timestamps', () => {
  const csv = 'seconds_elapsed,x,y,z\n0,0,0,0\n1,0,0,0\n1,0,0,0\n';
  assert.throws(() => parseSensorCsv(csv), /timestamps must increase/);
});

test('live estimator removes calibration bias and stays still', () => {
  const live = createLiveEstimator();
  let point;
  for (let t = 0; t <= 2; t += 0.01) point = live.update(t, [0.2, -0.1, 0.3]);
  assert.equal(live.calibrating, false);
  assert.ok(point.every(value => Math.abs(value) < 1e-9));
});

test('live estimator holds a push while a hand-held phone jitters, despite leftover speed error', () => {
  const live = createLiveEstimator();
  const round = value => Math.round(value * 10) / 10;
  const jitter = (i, phase) => round(0.2 * Math.sin(i * 1.7 + phase));
  let t = 0, i = 0, point;
  const step = acceleration => { point = live.update(t, acceleration.map(round)); t += 0.02; i++; };
  while (t < 0.6) step([0, 0, 0]);
  for (let k = 0; k < 15; k++) step([0, 0, 2]);
  // Slow-down reads 5% strong, like the recorded session, leaving a downward speed error.
  for (let k = 0; k < 15; k++) step([0, 0, -2.1]);
  const atStop = point[2];
  assert.ok(atStop > 0.16 && atStop < 0.19, `at stop ${atStop}`);
  while (t < 1.8) step([jitter(i, 0), jitter(i, 2), jitter(i, 4)]);
  const settled = point[2];
  while (t < 8) step([jitter(i, 0), jitter(i, 2), jitter(i, 4)]);
  assert.ok(live.still);
  assert.ok(Math.abs(point[2] - settled) < 0.005, `drifted ${point[2] - settled} m while held`);
  assert.ok(settled > 0.15, `held ${settled}`);
});

test('live estimator re-learns a small sensor offset while still', () => {
  const live = createLiveEstimator();
  let point;
  for (let t = 0; t <= 0.6; t += 0.02) live.update(t, [0, 0, 0]);
  for (let t = 0.62; t <= 12; t += 0.02) point = live.update(t, [0, 0, 0.1]);
  assert.ok(Math.abs(live.bias[2] - 0.1) < 0.01, `bias ${live.bias[2]}`);
  assert.ok(Math.abs(point[2]) < 0.005, `moved ${point[2]}`);
});

test('live estimator ignores long sample gaps instead of integrating them', () => {
  const live = createLiveEstimator();
  for (let t = 0; t <= 0.6; t += 0.01) live.update(t, [0, 0, 0]);
  const point = live.update(5, [0, 9, 0]);
  assert.deepEqual(point, [0, 0, 0]);
});

// A phone tilted 10 deg about its X axis: device +Z no longer points up.
const tilted = [Math.sin(5 * Math.PI / 180), 0, 0, Math.cos(5 * Math.PI / 180)];

test('orientation levels the frame so tilt does not leak into Z', () => {
  const [, y, z] = rotateVector([0, 0, 1], tilted);
  close(Math.hypot(y, z), 1, 1e-9, 'unit length');
  close(headingAngle([0, 0, 0, 1]), 0, 1e-9, 'heading of identity');

  const tiltedFrame = createLiveEstimator(), levelled = createLiveEstimator();
  // Device-frame reading of a purely horizontal push while the phone is tilted.
  const push = rotateVector([0, 2, 0], [-tilted[0], 0, 0, tilted[3]]);
  let t = 0;
  for (; t < 0.6; t += 0.02) { tiltedFrame.update(t, [0, 0, 0]); levelled.update(t, [0, 0, 0], tilted); }
  let a = null, b = null;
  for (let i = 0; i < 20; i++, t += 0.02) { a = tiltedFrame.update(t, push); b = levelled.update(t, push, tilted); }
  assert.ok(Math.abs(a[2]) > 0.002, `tilted frame leaks into Z: ${a[2]}`);
  close(b[2], 0, 1e-6, 'levelled Z stays flat');
  assert.ok(b[1] > 0.02, `levelled Y follows the push: ${b[1]}`);
});

test('clutch freezes the estimated position and resumes without jumping', () => {
  const live = createLiveEstimator();
  let t = 0, point;
  const step = a => { point = live.update(t, a); t += 0.02; };
  for (; t < 0.6;) step([0, 0, 0]);
  for (let i = 0; i < 15; i++) step([0, 2, 0]);
  for (let i = 0; i < 15; i++) step([0, -2, 0]);
  const held = point[1];
  live.hold();
  for (let i = 0; i < 100; i++) step([0, 3, 0]);
  close(point[1], held, 1e-9, 'position frozen while held');
  live.resume();
  for (let i = 0; i < 10; i++) step([0, 0, 0]);
  close(point[1], held, 1e-3, 'no jump on resume');
});

test('pose tracker follows measured positions and re-anchors after a clutch', () => {
  const tracker = createPoseTracker();
  assert.deepEqual(tracker.update([1, 1, 1], [0, 0, 0, 1]), [0, 0, 0]);
  assert.deepEqual(tracker.update([1, 1.5, 1.25], [0, 0, 0, 1]), [0, 0.5, 0.25]);
  tracker.hold();
  assert.deepEqual(tracker.update([5, 5, 5], [0, 0, 0, 1]), [0, 0.5, 0.25]);
  tracker.resume();
  assert.deepEqual(tracker.update([5, 5, 5], [0, 0, 0, 1]), [0, 0.5, 0.25]);
  assert.deepEqual(tracker.update([5, 6, 5], [0, 0, 0, 1]), [0, 1.5, 0.25]);
});

test('pose tracker aligns +Y with the phone top at anchor time', () => {
  const quarterTurn = [0, 0, Math.sin(Math.PI / 4), Math.cos(Math.PI / 4)];
  close(headingAngle(quarterTurn), -Math.PI / 2, 1e-9, 'heading after quarter turn');
  const tracker = createPoseTracker();
  tracker.update([0, 0, 0], quarterTurn);
  const [x, y] = tracker.update([-1, 0, 0], quarterTurn);
  close(x, 0, 1e-9, 'no sideways component');
  close(y, 1, 1e-9, 'motion along phone top maps to +Y');
});

test('parses orientation and pose columns when present', () => {
  const csv = 'seconds_elapsed,x,y,z,qx,qy,qz,qw,px,py,pz\n'
    + '0,0,0,0,0,0,0,1,0,0,0\n1,0,0,0,0,0,0,1,0.1,0,0\n2,0,0,0,0,0,0,1,0.2,0,0\n';
  const parsed = parseSensorCsv(csv);
  assert.deepEqual(parsed.quaternion[0], [0, 0, 0, 1]);
  assert.deepEqual(parsed.position.at(-1), [0.2, 0, 0]);
});