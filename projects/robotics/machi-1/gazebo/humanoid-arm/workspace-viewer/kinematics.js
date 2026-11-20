import {Matrix4, Vector3, Euler, Quaternion} from 'three';

const children = (node, tag) => Array.from(node?.childNodes || []).filter(n => n.nodeType === 1 && (!tag || n.nodeName === tag));
const child = (node, tag) => children(node, tag)[0];
const attr = (node, name, fallback) => node?.hasAttribute(name) ? node.getAttribute(name) : fallback;
function number(raw, label) {
  const value = Number(raw);
  if (raw == null || String(raw).trim() === '' || !Number.isFinite(value)) throw Error(`Invalid ${label}: ${raw}`);
  return value;
}
function vector(raw, length, label) {
  const result = raw.trim().split(/\s+/).map(v => number(v, label));
  if (result.length !== length) throw Error(`${label} needs ${length} numbers`);
  return result;
}
function origin(node) {
  const o = child(node, 'origin');
  const xyz = vector(attr(o, 'xyz', '0 0 0'), 3, 'origin xyz');
  const rpy = vector(attr(o, 'rpy', '0 0 0'), 3, 'origin rpy');
  // URDF fixed-axis roll/pitch/yaw: Rz(yaw) Ry(pitch) Rx(roll).
  return new Matrix4().compose(new Vector3(...xyz),
    new Quaternion().setFromEuler(new Euler(...rpy, 'ZYX')), new Vector3(1, 1, 1));
}
function uniqueName(node, map, kind) {
  const name = attr(node, 'name', '').trim();
  if (!name || map.has(name)) throw Error(`Missing or duplicate ${kind} name: ${name}`);
  return name;
}

export function parseRobot(xml, Parser = globalThis.DOMParser) {
  if (xml.length > 5e6) throw Error('URDF is too large (5 MB limit).');
  if (/<!DOCTYPE|<!ENTITY/i.test(xml)) throw Error('DTD/entity declarations are not supported.');
  const doc = new Parser().parseFromString(xml, 'application/xml');
  if (doc.getElementsByTagName('parsererror').length) throw Error('Invalid XML: check the URDF syntax.');
  if (doc.documentElement.nodeName !== 'robot') throw Error('Expected a <robot> URDF document.');
  // Xacro can leave unevaluated expressions in comments; inspect actual
  // elements and attributes, not comment text in the serialized document.
  for (const element of Array.from(doc.getElementsByTagName('*'))) {
    if (element.nodeName.startsWith('xacro:') || Array.from(element.attributes).some(a => /\$\{|\$\(/.test(a.value))) {
      throw Error('Expand Xacro to URDF first, or use “Load current rig”.');
    }
  }
  const root = doc.documentElement;
  const links = new Map(), joints = new Map(), materials = new Map(), warnings = [];
  for (const m of children(root, 'material')) {
    const color = child(m, 'color');
    if (color) materials.set(attr(m, 'name'), vector(attr(color, 'rgba', ''), 4, 'rgba'));
  }
  for (const l of children(root, 'link')) {
    const name = uniqueName(l, links, 'link');
    const visuals = [];
    for (const v of children(l, 'visual')) {
      const shape = children(child(v, 'geometry'))[0];
      if (!shape) continue;
      const kind = shape.nodeName;
      if (kind === 'mesh') { warnings.push(`${name}: mesh omitted; joint frames and FK still work. Set the tip offset manually.`); continue; }
      if (!['box', 'sphere', 'cylinder'].includes(kind)) throw Error(`Unsupported geometry: ${kind}`);
      const size = kind === 'box' ? vector(attr(shape, 'size', ''), 3, 'box size')
        : kind === 'sphere' ? [number(attr(shape, 'radius'), 'sphere radius')]
        : [number(attr(shape, 'radius'), 'cylinder radius'), number(attr(shape, 'length'), 'cylinder length')];
      if (size.some(v => v <= 0)) throw Error('Geometry dimensions must be positive.');
      const material = child(v, 'material'), color = child(material, 'color');
      const rgba = color ? vector(attr(color, 'rgba', ''), 4, 'rgba') : materials.get(attr(material, 'name')) || [0.38, 0.66, 0.77, 1];
      visuals.push({kind, size, origin: origin(v), rgba});
    }
    links.set(name, {name, visuals});
  }
  const parents = new Map();
  for (const j of children(root, 'joint')) {
    const name = uniqueName(j, joints, 'joint'), type = attr(j, 'type');
    if (!['fixed', 'revolute', 'continuous', 'prismatic'].includes(type)) throw Error(`${name}: unsupported joint type ${type}`);
    if (child(j, 'mimic')) throw Error(`${name}: mimic joints are not supported in this version.`);
    const parent = attr(child(j, 'parent'), 'link'), target = attr(child(j, 'child'), 'link');
    if (!links.has(parent) || !links.has(target)) throw Error(`${name}: unknown parent/child link`);
    if (parents.has(target)) throw Error(`${target} has multiple parent joints`);
    const axis = new Vector3(...vector(attr(child(j, 'axis'), 'xyz', '1 0 0'), 3, 'joint axis'));
    if (type !== 'fixed' && axis.length() < 1e-12) throw Error(`${name}: zero joint axis`);
    axis.normalize();
    const limit = child(j, 'limit');
    let min = 0, max = 0;
    if (type === 'continuous') { min = -Math.PI; max = Math.PI; }
    if (type === 'revolute' || type === 'prismatic') {
      min = number(attr(limit, 'lower'), `${name} lower limit`);
      max = number(attr(limit, 'upper'), `${name} upper limit`);
      if (min > max) throw Error(`${name}: lower limit exceeds upper limit`);
    }
    joints.set(name, {name, type, parent, child: target, axis, origin: origin(j), min, max});
    parents.set(target, name);
  }
  const roots = [...links.keys()].filter(n => !parents.has(n));
  if (roots.length !== 1) throw Error('URDF must have exactly one root link and form a connected tree.');
  const ordered = [], visited = new Set();
  function visit(name) {
    if (visited.has(name)) throw Error('Joint tree contains a cycle');
    visited.add(name);
    for (const j of joints.values()) if (j.parent === name) { ordered.push(j); visit(j.child); }
  }
  visit(roots[0]);
  if (visited.size !== links.size) throw Error('Disconnected or cyclic joint tree');
  return {name: attr(root, 'name', 'Robot'), root: roots[0], links, joints, ordered, parents, warnings};
}

export function forward(robot, positions = {}) {
  const transforms = new Map([[robot.root, new Matrix4()]]);
  for (const joint of robot.ordered) {
    const angle = positions[joint.name] ?? 0;
    const motion = joint.type === 'prismatic'
      ? new Matrix4().makeTranslation(joint.axis.x * angle, joint.axis.y * angle, joint.axis.z * angle)
      : joint.type === 'fixed' ? new Matrix4() : new Matrix4().makeRotationAxis(joint.axis, angle);
    transforms.set(joint.child, transforms.get(joint.parent).clone().multiply(joint.origin).multiply(motion));
  }
  return transforms;
}
export function tipPosition(robot, link, offset, positions = {}) {
  const frame = forward(robot, positions).get(link);
  if (!frame) throw Error(`Unknown tip link: ${link}`);
  return new Vector3(...offset).applyMatrix4(frame);
}
export function chain(robot, link) {
  const result = [];
  while (robot.parents.has(link)) {
    const joint = robot.joints.get(robot.parents.get(link));
    result.unshift(joint); link = joint.parent;
  }
  return result;
}
export function suggestedTip(robot, link) {
  const v = robot.links.get(link).visuals[0];
  if (!v) return [0, 0, 0];
  const z = v.kind === 'box' ? -v.size[2] / 2 : v.kind === 'cylinder' ? -v.size[1] / 2 : -v.size[0];
  return new Vector3(0, 0, z).applyMatrix4(v.origin).toArray();
}

// Keep the sampled configurations so orientation IK can start at a known
// reachable pose for precisely the same (unrounded) workspace point.
export function configurationSampler(robot, link, states, count) {
  const movable = chain(robot, link).filter(j => j.type !== 'fixed' && states[j.name].enabled && states[j.name].max > states[j.name].min);
  const base = Object.fromEntries(Object.entries(states).map(([n, s]) => [n, s.enabled && s.max === s.min ? s.min : s.value]));
  let seed = 123456789;
  const random = () => { seed = (Math.imul(1664525, seed) + 1013904223) >>> 0; return seed / 4294967296; };
  return index => {
    const q = {...base};
    for (const j of movable) {
      const s = states[j.name];
      const t = movable.length === 1 ? index / Math.max(1, count - 1) : random();
      q[j.name] = s.min + t * (s.max - s.min);
    }
    return q;
  };
}

export function sampler(robot, link, offset, states, count) {
  const configurations = configurationSampler(robot, link, states, count);
  return index => tipPosition(robot, link, offset, configurations(index));
}