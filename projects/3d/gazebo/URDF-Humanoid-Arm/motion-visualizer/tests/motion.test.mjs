import assert from 'node:assert/strict';
import test from 'node:test';
import {createLiveEstimator, estimateTrajectory, parseSensorCsv} from '../motion.js';

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

test('live estimator holds a +Y push after the phone stops, then slowly relaxes', () => {
  const live = createLiveEstimator();
  let t = 0, point;
  const step = acceleration => { point = live.update(t, acceleration); t += 0.01; };
  while (t < 0.6) step([0.01, 0.02, -0.01]);
  for (let i = 0; i < 20; i++) step([0.01, 2.02, -0.01]);
  for (let i = 0; i < 20; i++) step([0.01, -1.98, -0.01]);
  assert.ok(point[1] > 0.07 && point[1] < 0.085, `at stop ${point[1]}`);
  while (t < 1.8) step([0.01, 0.02, -0.01]);
  assert.ok(point[1] > 0.06, `held ${point[1]}`);
  assert.ok(Math.abs(point[0]) < 1e-9 && Math.abs(point[2]) < 1e-9);
  while (t < 60) step([0.01, 0.02, -0.01]);
  assert.ok(Math.abs(point[1]) < 0.01, `relaxed ${point[1]}`);
});

test('live estimator ignores long sample gaps instead of integrating them', () => {
  const live = createLiveEstimator();
  for (let t = 0; t <= 0.6; t += 0.01) live.update(t, [0, 0, 0]);
  const point = live.update(5, [0, 9, 0]);
  assert.deepEqual(point, [0, 0, 0]);
});