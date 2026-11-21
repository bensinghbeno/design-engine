import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {performance} from 'node:perf_hooks';
import {DOMParser} from '@xmldom/xmldom';
import {Matrix4, Quaternion, Vector3} from 'three';
import {
  parseRobot, forward, chain, tipPosition, sampler, configurationSampler,
} from '../kinematics.js';
import {
  forwardPose, solvePose, orientationTargets, coverageColor, coverageCategory, DEFAULT_IK_OPTIONS,
} from '../orientation.js';
import {analyzeProbe, selectProbes} from '../orientation-analysis.js';

const parse = xml => parseRobot(xml, DOMParser);
const near = (a, b, eps = 1e-9, label = '') =>
  assert.ok(Number.isFinite(a) && Math.abs(a - b) <= eps, `${label}: ${a} != ${b} (±${eps})`);
function vectorNear(a, b, eps = 1e-9) {
  assert.equal(a.length, b.length);
  a.forEach((v, i) => near(v, b[i], eps, `component ${i}`));
}
// Independent THREE quaternion distance, insensitive to the double cover of
// SO(3), and numerically stable at both zero and pi (unlike acos(dot)).
function angleBetween(a, b) {
  const delta = new Quaternion(...a).normalize()
    .multiply(new Quaternion(...b).normalize().conjugate());
  return 2 * Math.atan2(Math.hypot(delta.x, delta.y, delta.z), Math.abs(delta.w));
}
const statesFor = robot => Object.fromEntries([...robot.joints.values()]
  .filter(j => j.type !== 'fixed')
  .map(j => [j.name, {min: j.min, max: j.max, value: 0, enabled: true}]));
function modelFor(robot, tip, offset = [0, 0, 0], states = statesFor(robot)) {
  return {offset: offset.slice(), joints: chain(robot, tip).map(j => ({
    name: j.name, type: j.type, origin: j.origin.toArray(), axis: j.axis.toArray(),
    min: j.min, max: j.max, value: 0, enabled: j.type !== 'fixed', ...states[j.name],
  }))};
}
function threePose(robot, tip, offset, q) {
  // Uses the existing THREE matrix FK, never forwardPose to construct targets.
  const frame = forward(robot, q).get(tip);
  return {
    position: new Vector3(...offset).applyMatrix4(frame).toArray(),
    orientation: new Quaternion().setFromRotationMatrix(frame).normalize().toArray(),
  };
}
function checkResult(model, target, result, options = {}) {
  const settings = {...DEFAULT_IK_OPTIONS, ...options};
  const actual = forwardPose(model, result.positions);
  const positionError = Math.hypot(...actual.position.map((v, i) => v - target.position[i]));
  const orientationError = angleBetween(actual.orientation, target.orientation);
  near(result.positionError, positionError, 1e-9, 'reported position residual');
  near(result.orientationError, orientationError, 1e-9, 'reported angular residual');
  assert.ok(Number.isInteger(result.iterations) && result.iterations >= 0);
  assert.ok(result.iterations <= settings.maxIterations * settings.restarts);
  for (const j of model.joints) {
    const v = result.positions[j.name];
    assert.ok(Number.isFinite(v), j.name);
    if (j.enabled === false || j.type === 'fixed') assert.equal(v, j.value);
    else if (j.min === j.max) assert.equal(v, j.min);
    else assert.ok(v >= j.min && v <= j.max, `${j.name}: ${v} outside [${j.min}, ${j.max}]`);
  }
  assert.equal(result.success,
    positionError <= settings.positionTolerance && orientationError <= settings.orientationTolerance,
    'success must describe the returned FK pose, not a small step or an earlier iterate');
}

// Cartesian positioning is decoupled from an intersecting XYZ wrist. With the
// tool at its origin this is a genuine six-DOF control, not an offset arm that
// can lose positional reach while turning. Removing Z leaves orient rank <= 2.
function cartesianWrist(rotations = 3) {
  const axes = ['1 0 0', '0 1 0', '0 0 1'];
  const specs = [0, 1, 2].map(i => [`slide_${'xyz'[i]}`, 'prismatic', axes[i]])
    .concat(Array.from({length: rotations}, (_, i) => [`wrist_${'xyz'[i]}`, 'continuous', axes[i]]));
  const xml = `<robot name="cartesian_wrist"><link name="base"/>${specs.map(([name, type, axis], i) => `
    <link name="link_${i}"/><joint name="${name}" type="${type}">
      <parent link="${i ? `link_${i - 1}` : 'base'}"/><child link="link_${i}"/>
      <axis xyz="${axis}"/>${type === 'prismatic' ? '<limit lower="-2" upper="2"/>' : ''}
    </joint>`).join('')}</robot>`;
  const robot = parse(xml), tip = `link_${specs.length - 1}`;
  return {robot, tip, model: modelFor(robot, tip)};
}
function singleJoint(overrides = {}) {
  return {offset: [0, 0, 0], joints: [{
    name: 'joint', type: 'continuous', axis: [1, 0, 0],
    origin: new Matrix4().toArray(), min: -Math.PI, max: Math.PI,
    value: 0, enabled: true, ...overrides,
  }]};
}
const strictIK = {positionTolerance: 1e-4, orientationTolerance: 1e-3, maxIterations: 100, restarts: 3};

test('orientationTargets are deterministic, normalized, prefix-stable and spread through SO(3), including roll', () => {
  const all = orientationTargets(96);
  for (const count of [1, 8, 24, 96]) {
    const targets = orientationTargets(count);
    assert.deepEqual(targets, orientationTargets(count));
    assert.deepEqual(targets, all.slice(0, count));
    for (const q of targets) near(Math.hypot(...q), 1, 1e-14);
  }
  // Broad finite-sample moment bounds, not a claim of exact uniformity.
  // Check rotated coordinate axes, which do not depend on quaternion signs.
  for (const count of [24, 96]) {
    const targets = all.slice(0, count);
    for (const axis of [[1, 0, 0], [0, 1, 0], [0, 0, 1]]) {
      const directions = targets.map(q => new Vector3(...axis).applyQuaternion(new Quaternion(...q)).toArray());
      for (let k = 0; k < 3; k++) {
        assert.ok(Math.abs(directions.reduce((s, v) => s + v[k], 0) / count) < .3);
        near(directions.reduce((s, v) => s + v[k] ** 2, 0) / count, 1 / 3, .2);
        assert.ok(Math.min(...directions.map(v => v[k])) < -.7);
        assert.ok(Math.max(...directions.map(v => v[k])) > .7);
      }
    }
  }
  // Quaternion second moments also catch degenerate, fixed-axis-only sets;
  // the nearby-direction frame check below specifically tests roll freedom.
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    near(all.reduce((s, q) => s + q[i] * q[j], 0) / all.length, i === j ? .25 : 0, .07);
  }
  const frames = all.map(q => ({
    x: new Vector3(1, 0, 0).applyQuaternion(new Quaternion(...q)),
    z: new Vector3(0, 0, 1).applyQuaternion(new Quaternion(...q)),
  }));
  assert.ok(frames.some((a, i) => frames.slice(i + 1).some(b =>
    a.z.dot(b.z) > .97 && a.x.dot(b.x) < -.5)),
  'nearly identical pointing directions must also have substantially different roll');
  for (let i = 0; i < all.length; i++) for (let j = i + 1; j < all.length; j++) {
    assert.ok(angleBetween(all[i], all[j]) > 1e-6, 'no sign-equivalent duplicate orientations');
  }
  for (const invalid of [0, -1, 97, 1.5, NaN, Infinity]) assert.throws(() => orientationTargets(invalid));
});

test('forwardPose agrees with independent THREE FK for arbitrary axes, RPY, fixed offsets and prismatic motion', () => {
  const robot = parse(`<robot name="mixed"><link name="base"/><link name="mount"/>
    <link name="arm"/><link name="carriage"/><link name="wrist"/><link name="tool"/>
    <joint name="mounting" type="fixed"><parent link="base"/><child link="mount"/><origin xyz=".2 -.3 .4" rpy=".2 -.5 .8"/></joint>
    <joint name="hinge" type="revolute"><parent link="mount"/><child link="arm"/><origin xyz="-.1 .23 .31" rpy="-.7 .4 -.2"/><axis xyz="2 -3 4"/><limit lower="-2" upper="2"/></joint>
    <joint name="slide" type="prismatic"><parent link="arm"/><child link="carriage"/><origin xyz=".4 .1 -.2" rpy=".3 -.6 .9"/><axis xyz="-3 1 2"/><limit lower="-.8" upper=".9"/></joint>
    <joint name="twist" type="continuous"><parent link="carriage"/><child link="wrist"/><origin xyz="-.12 .25 .08" rpy=".5 .2 -.4"/><axis xyz="1 4 -2"/></joint>
    <joint name="tool_mount" type="fixed"><parent link="wrist"/><child link="tool"/><origin xyz=".13 -.17 .21" rpy="-.2 .4 .1"/></joint>
  </robot>`);
  const offset = [.17, -.11, .29], model = modelFor(robot, 'tool', offset);
  for (const q of [{}, {hinge: .7, slide: -.4, twist: 1.1}, {hinge: -1.2, slide: .65, twist: -2.3}]) {
    const actual = forwardPose(model, q), expected = threePose(robot, 'tool', offset, q);
    vectorNear(actual.position, expected.position);
    near(Math.hypot(...actual.orientation), 1, 1e-14);
    near(angleBetween(actual.orientation, expected.orientation), 0);
  }
  // Exercise all largest-diagonal matrix-to-quaternion branches at pi.
  for (const axis of [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, -2, 3]]) {
    const q = new Quaternion().setFromAxisAngle(new Vector3(...axis).normalize(), Math.PI);
    const frame = new Matrix4().makeRotationFromQuaternion(q).setPosition(.3, -.4, .5);
    const fixed = singleJoint({type: 'fixed', origin: frame.toArray(), min: 0, max: 0});
    fixed.offset = offset;
    const actual = forwardPose(fixed);
    vectorNear(actual.position, new Vector3(...offset).applyMatrix4(frame).toArray());
    near(angleBetween(actual.orientation, q.toArray()), 0);
  }
});

test('IK solves independently known reachable poses with a nonzero local tool offset', () => {
  const {robot, tip} = cartesianWrist();
  const offset = [.23, -.17, .31], model = modelFor(robot, tip, offset);
  for (const angles of [[.4, -.7, 1.1], [-.8, .3, -1.4], [1.2, -.9, .6]]) {
    const q = {slide_x: .3, slide_y: -.45, slide_z: .6,
      wrist_x: angles[0], wrist_y: angles[1], wrist_z: angles[2]};
    const target = threePose(robot, tip, offset, q);
    const seed = Object.fromEntries(Object.entries(q).map(([name, v], i) => [name, v + (i % 2 ? -.18 : .15)]));
    assert.ok(angleBetween(forwardPose(model, seed).orientation, target.orientation) > .05);
    const result = solvePose(model, target, seed, strictIK);
    checkResult(model, target, result, strictIK);
    assert.equal(result.success, true);
    assert.ok(result.iterations > 0, 'must exercise iterative IK, not just validate an exact seed');
    const actual = threePose(robot, tip, offset, result.positions);
    vectorNear(actual.position, target.position, strictIK.positionTolerance);
    assert.ok(angleBetween(actual.orientation, target.orientation) <= strictIK.orientationTolerance);
  }
});

test('IK handles exactly 180 degrees and both quaternion signs without singular angular errors', () => {
  for (const axis of [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, -2, 3]]) {
    const unit = new Vector3(...axis).normalize().toArray();
    const model = singleJoint({axis});
    const results = [1, -1].map(sign => {
      const target = {position: [0, 0, 0], orientation: [...unit, 0].map(v => v * sign)};
      const result = solvePose(model, target, {joint: 0}, strictIK);
      checkResult(model, target, result, strictIK);
      assert.equal(result.success, true);
      near(Math.abs(result.positions.joint), Math.PI, strictIK.orientationTolerance);
      return result;
    });
    near(results[0].positions.joint, results[1].positions.joint);
  }
});

test('impossible positions and bounded rotations never report success; full-turn continuous seeds wrap', () => {
  const {model} = cartesianWrist();
  const unreachable = {position: [8, 0, 0], orientation: [0, 0, 0, 1]};
  const result = solvePose(model, unreachable, {}, strictIK);
  checkResult(model, unreachable, result, strictIK);
  assert.equal(result.success, false);
  assert.ok(result.positionError >= 6 - 1e-9);
  for (const type of ['revolute', 'continuous', 'prismatic']) {
    const limited = singleJoint({type, min: -.2, max: .3});
    const target = type === 'prismatic'
      ? {position: [.9, 0, 0], orientation: [0, 0, 0, 1]}
      : {position: [0, 0, 0], orientation: [Math.SQRT1_2, 0, 0, Math.SQRT1_2]};
    const failed = solvePose(limited, target, {joint: 50}, strictIK);
    checkResult(limited, target, failed, strictIK);
    assert.equal(failed.success, false, `${type} must obey its finite interval`);
  }
  const fullTurn = singleJoint();
  const target = {position: [0, 0, 0], orientation: new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), .5).toArray()};
  const wrapped = solvePose(fullTurn, target, {joint: 4 * Math.PI + .5}, strictIK);
  checkResult(fullTurn, target, wrapped, strictIK);
  assert.equal(wrapped.success, true);
  near(wrapped.positions.joint, .5);
});

test('disabled joints lock to preview values while enabled equal-min/max joints lock to min', () => {
  for (const type of ['prismatic', 'revolute']) for (const enabled of [false, true]) {
    const model = singleJoint({type, enabled, value: -.7, min: .3, max: .3});
    const expected = enabled ? .3 : -.7;
    const target = type === 'prismatic'
      ? {position: [expected, 0, 0], orientation: [0, 0, 0, 1]}
      : {position: [0, 0, 0], orientation: new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), expected).toArray()};
    const result = solvePose(model, target, {joint: 99}, strictIK);
    checkResult(model, target, result, strictIK);
    assert.equal(result.success, true);
    assert.equal(result.positions.joint, expected);
    const impossible = {...target, position: [5, 5, 5]};
    const failed = solvePose(model, impossible, {joint: -99}, strictIK);
    checkResult(model, impossible, failed, strictIK);
    assert.equal(failed.success, false);
    assert.equal(failed.positions.joint, expected);
  }
});

test('six-DOF Cartesian XYZ + intersecting XYZ wrist covers all 24 targets; rank-deficient five-DOF covers less', t => {
  const targets = orientationTargets(24), seed = {slide_x: .35, slide_y: -.45, slide_z: .6};
  const position = [.35, -.45, .6];
  const six = cartesianWrist(), five = cartesianWrist(2);
  assert.equal(six.model.joints.length, 6);
  assert.equal(five.model.joints.length, 5);
  let solved = 0;
  for (const [i, orientation] of targets.entries()) {
    const target = {position, orientation};
    const result = solvePose(six.model, target, seed, {...strictIK, seed: 12345 + i * 104729});
    checkResult(six.model, target, result, strictIK);
    assert.equal(result.success, true, `six-DOF target ${i}`);
    solved += Number(result.success);
  }
  const full = analyzeProbe(six.model, {position, seed}, targets, strictIK);
  const deficient = analyzeProbe(five.model, {position, seed}, targets, strictIK);
  assert.deepEqual(full, {position, solved, tested: 24, fraction: 1});
  assert.equal(deficient.tested, 24);
  near(deficient.fraction, deficient.solved / 24);
  assert.ok(deficient.fraction < .5, 'missing wrist axis must not be mistaken for full SO(3) freedom');
  assert.ok(deficient.solved < full.solved);
  t.diagnostic(`synthetic coverage: 6 DOF ${full.solved}/24; 5 DOF ${deficient.solved}/24`);
});

test('analyzeProbe counts exactly the supplied orientations, not an added reachable baseline', () => {
  const model = {joints: [], offset: [.2, -.3, .4]};
  const probe = {position: model.offset.slice(), seed: {}};
  const targets = orientationTargets(24), snapshot = structuredClone({model, probe, targets});
  const result = analyzeProbe(model, probe, targets);
  assert.deepEqual(result, {position: probe.position, solved: 0, tested: 24, fraction: 0});
  assert.notEqual(result.position, probe.position, 'result position should not alias the sample');
  assert.equal(solvePose(model, forwardPose(model), probe.seed).success, true, 'baseline really is reachable');
  const mixed = [[1, 0, 0, 0], [0, 0, 0, 1], [0, 1, 0, 0], [0, 0, 0, -1]];
  assert.deepEqual(analyzeProbe(model, probe, mixed), {position: probe.position, solved: 2, tested: 4, fraction: .5});
  assert.deepEqual({model, probe, targets}, snapshot, 'analysis must not mutate model, sample or target list');
  assert.throws(() => analyzeProbe(model, {...probe, position: [.3, -.3, .4]}, targets), /known reachable/);
});

test('analyzeProbe validates the known FK seed after applying locks, collapsed ranges and limits', () => {
  const {robot, tip} = cartesianWrist();
  const states = statesFor(robot);
  Object.assign(states.slide_x, {enabled: false, value: .4});
  Object.assign(states.slide_y, {min: -.3, max: -.3, value: .8});
  Object.assign(states.slide_z, {min: -.2, max: .2});
  const model = modelFor(robot, tip, [0, 0, 0], states);
  const seed = {slide_x: -1, slide_y: 1, slide_z: .7};
  const known = threePose(robot, tip, model.offset, {slide_x: .4, slide_y: -.3, slide_z: .2});
  const result = analyzeProbe(model, {position: known.position, seed}, [known.orientation]);
  assert.equal(result.solved, 1);
  const wrong = threePose(robot, tip, model.offset, seed);
  assert.throws(() => analyzeProbe(model, {position: wrong.position, seed}, [known.orientation]), /known reachable/);
  assert.throws(() => analyzeProbe(model, {position: known.position, seed: {...seed, slide_z: -.1}}, [known.orientation]), /known reachable/);
});

test('analyzeProbe and solvePose agree that an omitted enabled flag defaults to enabled', () => {
  const {model} = cartesianWrist();
  delete model.joints[0].enabled;
  const seed = {slide_x: .35, slide_y: -.45, slide_z: .6};
  const known = forwardPose(model, seed);
  assert.equal(solvePose(model, known, seed).success, true);
  const result = analyzeProbe(model, {position: known.position, seed}, [known.orientation]);
  assert.equal(result.solved, 1);
});

test('selectProbes returns distinct deterministic actual samples, caps count and deduplicates positions', () => {
  const candidates = [[0, 0, 0], [4, 0, 0], [0, 3, 0], [0, 0, 2], [4, 0, 0], [1, 1, 1]]
    .map((position, i) => ({position, seed: {joint: i}, id: i}));
  const before = structuredClone(candidates);
  const selected = selectProbes(candidates, 250);
  assert.equal(selected.length, 5, 'stop at distinct actual positions, not requested count');
  assert.equal(new Set(selected.map(p => JSON.stringify(p.position))).size, selected.length);
  assert.deepEqual(selectProbes(candidates, 250), selected);
  for (const probe of selected) assert.ok(candidates.includes(probe), 'must retain the actual sample and its seed');
  assert.deepEqual(selectProbes(candidates, 3), selected.slice(0, 3));
  assert.deepEqual(selectProbes(candidates, 1), [candidates[0]]);
  assert.deepEqual(selectProbes([], 3), []);
  const repeated = Array.from({length: 12}, (_, i) => ({position: [2, 3, 4], seed: {joint: i}}));
  assert.deepEqual(selectProbes(repeated, 12), [repeated[0]]);
  assert.deepEqual(candidates, before);
  for (const count of [0, 251, 1.5]) assert.throws(() => selectProbes(candidates, count));
  assert.throws(() => selectProbes(Array(513).fill(candidates[0]), 1));
});

test('configurationSampler reproduces sampler FK, deterministic sequences and collapsed enabled values', () => {
  const {robot, tip} = cartesianWrist(), states = statesFor(robot), count = 32;
  Object.assign(states.slide_x, {min: .4, max: .4, value: -1});
  Object.assign(states.wrist_x, {enabled: false, value: .37});
  const offset = [.2, -.1, .3], before = structuredClone(states);
  const configurations = configurationSampler(robot, tip, states, count);
  const repeated = configurationSampler(robot, tip, states, count);
  const points = sampler(robot, tip, offset, states, count);
  const model = modelFor(robot, tip, offset, states);
  const samples = Array.from({length: count}, (_, i) => {
    const q = configurations(i);
    assert.deepEqual(q, repeated(i));
    assert.equal(q.slide_x, .4, 'enabled collapsed range uses min, not preview value');
    assert.equal(q.wrist_x, .37, 'disabled range uses preview value');
    for (const [name, s] of Object.entries(states)) if (s.enabled) assert.ok(q[name] >= s.min && q[name] <= s.max);
    const position = tipPosition(robot, tip, offset, q).toArray();
    vectorNear(points(i).toArray(), position, 1e-12);
    vectorNear(forwardPose(model, q).position, position);
    return {position, seed: q};
  });
  assert.notEqual(samples[0].seed, samples[1].seed, 'each sample owns its configuration');
  assert.ok(new Set(samples.map(p => JSON.stringify(p.seed))).size > 20);
  for (const probe of selectProbes(samples, 8)) {
    assert.ok(samples.includes(probe));
    vectorNear(forwardPose(model, probe.seed).position, probe.position);
  }
  assert.deepEqual(states, before);
  // The one-moving-joint path is an endpoint-inclusive sweep, not the RNG path.
  for (const s of Object.values(states)) s.enabled = false;
  Object.assign(states.slide_z, {enabled: true, min: -.8, max: .9});
  const sweep = configurationSampler(robot, tip, states, 3);
  vectorNear([sweep(0).slide_z, sweep(1).slide_z, sweep(2).slide_z], [-.8, .05, .9]);
  assert.equal(configurationSampler(robot, tip, states, 1)(0).slide_z, -.8);
});

test('coverageColor has finite red/yellow/green endpoints and handles clamping', () => {
  for (const [fraction, expected] of [[0, [.95, .16, .2]], [.5, [1, .75, .15]], [1, [.16, .85, .45]]]) {
    const color = coverageColor(fraction);
    vectorNear(color, expected, 1e-14);
    assert.ok(color.every(v => Number.isFinite(v) && v >= 0 && v <= 1));
  }
  assert.deepEqual(coverageColor(-1), coverageColor(0));
  assert.deepEqual(coverageColor(2), coverageColor(1));
  for (const invalid of [NaN, Infinity, -Infinity]) assert.deepEqual(coverageColor(invalid), coverageColor(0));
});

test('coverageCategory partitions fractions into red, yellow, and green', () => {
  assert.equal(coverageCategory(0), 'red');
  assert.equal(coverageCategory(0.2), 'red');
  assert.equal(coverageCategory(0.329), 'red');
  assert.equal(coverageCategory(0.33), 'yellow');
  assert.equal(coverageCategory(0.5), 'yellow');
  assert.equal(coverageCategory(0.66), 'yellow');
  assert.equal(coverageCategory(0.67), 'green');
  assert.equal(coverageCategory(1.0), 'green');
  assert.equal(coverageCategory(-0.5), 'red');
  assert.equal(coverageCategory(1.5), 'green');
  assert.equal(coverageCategory(NaN), 'red');
});

test('current four-joint rig: known sample baseline succeeds but 24-target orientation coverage stays low (benchmark)', t => {
  // Expand the actual current rig rather than duplicating its geometry here.
  // Match the existing rig tests' ROS environment; no server or browser needed.
  const file = fileURLToPath(new URL('../../urdf/rig.urdf.xacro', import.meta.url));
  const xml = execFileSync('/opt/ros/noetic/bin/xacro', [file], {
    encoding: 'utf8', timeout: 15000, env: {...process.env,
      PATH: '/opt/ros/noetic/bin:/usr/bin:/bin', PYTHONNOUSERSITE: '1',
      PYTHONPATH: '/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages'},
  });
  const robot = parse(xml), tip = 'gripper_tool', offset = [0, 0, 0];
  const states = statesFor(robot), model = modelFor(robot, tip, offset, states);
  assert.deepEqual(model.joints.filter(j => j.type !== 'fixed').map(j => j.name), [
    'shoulder_joint', 'shoulder_roll_joint', 'elbow_joint', 'wrist_roll_joint',
  ]);
  const q = configurationSampler(robot, tip, states, 80)(0);
  const known = threePose(robot, tip, offset, q);
  vectorNear(forwardPose(model, q).position, known.position);
  near(angleBetween(forwardPose(model, q).orientation, known.orientation), 0);
  const options = {...DEFAULT_IK_OPTIONS, restarts: 3};
  const baseline = solvePose(model, known, q, options);
  checkResult(model, known, baseline, options);
  assert.equal(baseline.success, true);
  const targets = orientationTargets(24), probe = {position: known.position, seed: q};
  // Only this call is timed: FK/Xacro and assertions are not worker IK work.
  const start = performance.now();
  const result = analyzeProbe(model, probe, targets, options);
  const duration = performance.now() - start;
  t.diagnostic(`real rig: ${result.solved}/${result.tested} (${(100 * result.fraction).toFixed(1)}%) coverage; ` +
    `1 probe × 24 orientations, restarts=3: ${duration.toFixed(1)} ms; ` +
    `80 probes linear estimate: ${(duration * 80 / 1000).toFixed(2)} s (not a measured batch; no worker/UI overhead)`);
  assert.equal(result.tested, 24);
  near(result.fraction, result.solved / 24);
  assert.ok(result.fraction < .5, 'five-axis rig must not look like a full six-DOF pose workspace');
  // Independent enumeration checks identical targets, restart seeds and
  // denominator, without silently adding a successful baseline orientation.
  let solved = 0;
  for (const [i, orientation] of targets.entries()) {
    const target = {position: probe.position, orientation};
    const answer = solvePose(model, target, q, {...options, seed: 12345 + i * 104729});
    checkResult(model, target, answer, options);
    solved += Number(answer.success);
  }
  assert.equal(result.solved, solved);
});