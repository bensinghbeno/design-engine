import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {DOMParser} from '@xmldom/xmldom';

const file = fileURLToPath(new URL('../../urdf/base_joint.urdf.xacro', import.meta.url));
const expand = (...args) => new DOMParser().parseFromString(execFileSync('/usr/bin/python3',
  ['/opt/ros/noetic/bin/xacro', file, ...args], {encoding: 'utf8', env: {...process.env,
    PYTHONPATH: '/opt/ros/noetic/lib/python3/dist-packages', PYTHONNOUSERSITE: '1'}}), 'application/xml');
const named = (doc, tag, name) => [...doc.getElementsByTagName(tag)]
  .find(element => element.getAttribute('name') === name);
const vector = text => text.split(/\s+/).map(Number);
const size = (doc, name) => vector(named(doc, 'link', name)
  .getElementsByTagName('box')[0].getAttribute('size'));
const origin = (doc, tag, name) => vector(named(doc, tag, name)
  .getElementsByTagName('origin')[0].getAttribute('xyz'));
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-10,
  `${actual} != ${expected}`);

test('single-servo bracket envelopes match the dimension drawing', () => {
  for (const args of [[], ['shaft_end_setback:=0.012']]) {
    const doc = expand(...args);
    near(size(doc, 'rotating_bracket')[1], 0.0655);
    near(size(doc, 'fixed_bracket')[1], 0.052);
    near(size(doc, 'rotating_bracket')[0], 0.030);
    near(size(doc, 'fixed_bracket')[0], 0.030);
    near(origin(doc, 'joint', 'fixed_bracket_to_servo')[2]
      + origin(doc, 'joint', 'base_joint')[2]
      + origin(doc, 'link', 'rotating_bracket')[2]
      + size(doc, 'rotating_bracket')[2] / 2, 0.0945);
    const hubDepth = Number(named(doc, 'link', 'hub_left')
      .getElementsByTagName('cylinder')[0].getAttribute('length'));
    near(origin(doc, 'joint', 'hub_left_mount')[1]
      - origin(doc, 'joint', 'hub_right_mount')[1] + hubDepth, 0.0614);
    for (const side of ['left', 'right']) {
      const cheekInner = Math.abs(origin(doc, 'link', `bracket_${side}`)[1])
        - size(doc, `bracket_${side}`)[1] / 2;
      const hubOuter = Math.abs(origin(doc, 'joint', `hub_${side}_mount`)[1]) + hubDepth / 2;
      near(cheekInner - hubOuter, 0.00005);
    }
  }
});

test('fixed bracket clears the rotating hubs and upper bracket', () => {
  for (const args of [[], ['shaft_end_setback:=0.018'], ['fixed_bracket_hub_clearance:=0.002']]) {
    const doc = expand(...args);
    const axisHeight = origin(doc, 'joint', 'fixed_bracket_to_servo')[2]
      + origin(doc, 'joint', 'base_joint')[2];
    const expectedGap = args[0]?.startsWith('fixed_bracket_hub_clearance') ? 0.002 : 0.001;
    for (const side of ['left', 'right']) {
      const fixedSize = size(doc, `fixed_bracket_${side}`);
      const fixedOrigin = origin(doc, 'link', `fixed_bracket_${side}`);
      const hubRadius = Number(named(doc, 'link', `hub_${side}`)
        .getElementsByTagName('cylinder')[0].getAttribute('radius'));
      near(axisHeight - hubRadius - fixedOrigin[2] - fixedSize[2] / 2, expectedGap);
      const movingInner = Math.abs(origin(doc, 'link', `bracket_${side}`)[1])
        - size(doc, `bracket_${side}`)[1] / 2;
      const fixedOuter = Math.abs(fixedOrigin[1]) + fixedSize[1] / 2;
      near(movingInner - fixedOuter, 0.00475);
    }
  }
});

test('wood mount and one 270-degree output joint are preserved', () => {
  const doc = expand();
  assert.deepEqual(size(doc, 'wooden_arm'), [0.0254, 0.0254, 0.375]);
  near(origin(doc, 'joint', 'bracket_to_wood')[2],
    origin(doc, 'link', 'rotating_bracket')[2] + size(doc, 'rotating_bracket')[2] / 2);
  const moving = [...doc.getElementsByTagName('joint')]
    .filter(joint => joint.getAttribute('type') !== 'fixed');
  assert.equal(moving.length, 1);
  assert.equal(moving[0].getAttribute('name'), 'base_joint');
  assert.equal(moving[0].getElementsByTagName('axis')[0].getAttribute('xyz'), '0 1 0');
  const limit = moving[0].getElementsByTagName('limit')[0];
  near(Number(limit.getAttribute('upper')) - Number(limit.getAttribute('lower')), 1.5 * Math.PI);
  for (const name of ['fixed_bracket_to_servo', 'fixed_bracket_left_mount', 'fixed_bracket_right_mount']) {
    assert.equal(named(doc, 'joint', name).getAttribute('type'), 'fixed');
  }
});