import assert from 'node:assert/strict';
import test from 'node:test';
import {estimateTrajectory, parseSensorCsv} from '../motion.js';

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