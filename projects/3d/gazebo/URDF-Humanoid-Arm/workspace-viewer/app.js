import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {parseRobot, forward, chain, suggestedTip, sampler} from './kinematics.js';
import {examples} from './examples.js';

const $ = id => document.getElementById(id);
const status = text => { $('status').textContent = text; };
let robot, states = {}, frames = new Map(), cloud, points = [], generation = 0;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.001, 10000);
camera.up.set(0,0,1); camera.position.set(3,3,2);
let renderer;
try { renderer = new THREE.WebGLRenderer({antialias: true, alpha: true}); }
catch (e) { status('WebGL is unavailable. Enable browser hardware acceleration and reload.'); throw e; }
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
$('viewport').prepend(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
const robotGroup = new THREE.Group(); scene.add(robotGroup);
scene.add(new THREE.HemisphereLight(0xdaefff, 0x35404c, 2.5));
const light = new THREE.DirectionalLight(0xffffff, 3); light.position.set(3,-4,6); scene.add(light);
const grid = new THREE.GridHelper(6, 30, 0x46566b, 0x243244); grid.rotation.x = Math.PI/2; scene.add(grid);
scene.add(new THREE.AxesHelper(0.3));
const marker = new THREE.Mesh(new THREE.SphereGeometry(0.015, 12, 8), new THREE.MeshBasicMaterial({color:0xffffff})); scene.add(marker);
const observer = new ResizeObserver(() => {
  const {width, height} = $('viewport').getBoundingClientRect();
  renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
}); observer.observe($('viewport'));
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });

function dispose(object) {
  object.traverse(o => { o.geometry?.dispose(); if (o.material) for (const m of [o.material].flat()) m.dispose(); });
  object.removeFromParent();
}
function clearCloud() {
  generation++;
  if (cloud) { dispose(cloud); cloud = null; }
  points = []; $('export').disabled = true;
  for (const id of ['count','bx','by','bz']) $(id).textContent = '—';
}
function invalidate() { clearCloud(); status('Settings changed. Generate workspace to update the cloud.'); }
function offset() {
  const values = ['tx','ty','tz'].map(id => $(id).value.trim() === '' ? NaN : Number($(id).value));
  if (values.some(v => !Number.isFinite(v))) throw Error('Tip offsets must be finite numbers.');
  return values;
}
function setOffset(values) { ['tx','ty','tz'].forEach((id,i) => { $(id).value = Number(values[i].toFixed(6)); }); }
function guard(fn) { return async (...args) => { try { await fn(...args); } catch (e) { status(e.message); console.error(e); } }; }
function updatePose() {
  if (!robot) return;
  const transforms = forward(robot, Object.fromEntries(Object.entries(states).map(([name,s]) => [name,s.value])));
  for (const [name, frame] of frames) { frame.matrix.copy(transforms.get(name)); frame.matrixWorldNeedsUpdate = true; }
  marker.position.copy(new THREE.Vector3(...offset()).applyMatrix4(transforms.get($('tip').value)));
}
function renderRobot() {
  for (const obj of [...robotGroup.children]) dispose(obj);
  frames = new Map();
  for (const [name, link] of robot.links) {
    const frame = new THREE.Group(); frame.matrixAutoUpdate = false; frames.set(name, frame); robotGroup.add(frame);
    frame.add(new THREE.AxesHelper(0.07));
    for (const v of link.visuals) {
      let geometry;
      if (v.kind === 'box') geometry = new THREE.BoxGeometry(...v.size);
      else if (v.kind === 'sphere') geometry = new THREE.SphereGeometry(v.size[0], 20, 12);
      else { geometry = new THREE.CylinderGeometry(v.size[0], v.size[0], v.size[1], 24); geometry.rotateX(Math.PI/2); }
      const material = new THREE.MeshStandardMaterial({color: new THREE.Color(...v.rgba.slice(0,3)), roughness:0.65, metalness:0.08,
        transparent: v.rgba[3] < 1, opacity:v.rgba[3]});
      const mesh = new THREE.Mesh(geometry, material); mesh.matrixAutoUpdate = false; mesh.matrix.copy(v.origin); frame.add(mesh);
    }
  }
  for (const joint of robot.ordered.filter(j => j.type !== 'fixed')) {
    const color = Math.abs(joint.axis.x) > .99 ? 0xff6969 : Math.abs(joint.axis.y) > .99 ? 0x6ee799 : Math.abs(joint.axis.z) > .99 ? 0x689eff : 0xffdd88;
    frames.get(joint.child).add(new THREE.ArrowHelper(joint.axis, new THREE.Vector3(), .13, color, .03, .02));
  }
}
function fit() {
  scene.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(robotGroup);
  if (cloud) bounds.union(new THREE.Box3().setFromObject(cloud));
  if (bounds.isEmpty()) return;
  const center = bounds.getCenter(new THREE.Vector3());
  const radius = Math.max(.2, bounds.getSize(new THREE.Vector3()).length()/2);
  const distance = radius / Math.sin(THREE.MathUtils.degToRad(camera.fov/2)) * 1.25 / Math.min(camera.aspect, 1);
  controls.target.copy(center);
  camera.position.copy(center).add(new THREE.Vector3(1.5,1.8,1).normalize().multiplyScalar(distance));
  camera.near = Math.max(.0001, distance/10000); camera.far = Math.max(100, distance*100);
  camera.updateProjectionMatrix(); controls.update();
}
function activeCount() {
  if (!robot) return;
  const path = chain(robot, $('tip').value).filter(j => j.type !== 'fixed');
  const active = path.filter(j => states[j.name].enabled && states[j.name].max > states[j.name].min).length;
  $('dof').textContent = `${active} sampled DOF / ${path.length} on tip chain`;
}
function jointControls() {
  $('joints').replaceChildren();
  if (!robot) return;
  const path = chain(robot, $('tip').value).filter(j => j.type !== 'fixed');
  if (!path.length) $('joints').textContent = 'This link has no movable ancestors: its workspace is a point.';
  for (const joint of path) {
    const s = states[joint.name], factor = joint.type === 'prismatic' ? 1 : 180/Math.PI, unit = factor === 1 ? 'm' : '°';
    const panel = document.createElement('div'); panel.className = 'joint';
    const title = document.createElement('div'); title.className = 'joint-title';
    const label = document.createElement('label'), checkbox = document.createElement('input'), readout = document.createElement('output');
    checkbox.type = 'checkbox'; checkbox.checked = s.enabled;
    label.append(checkbox, ` ${joint.name}`); title.append(label, readout); panel.append(title);
    const note = document.createElement('div'); note.className = 'axis-note'; note.textContent = `${joint.type} · local axis ${joint.axis.toArray().join(', ')}`; panel.append(note);
    const slider = document.createElement('input'); slider.type = 'range'; slider.min = joint.min*factor; slider.max = joint.max*factor;
    slider.step = 'any'; slider.value = s.value*factor; slider.setAttribute('aria-label', `${joint.name} preview`); panel.append(slider);
    const updateReadout = () => { readout.textContent = `${(s.value*factor).toFixed(1)}${unit}`; }; updateReadout();
    slider.oninput = guard(() => { s.value = Number(slider.value)/factor; updateReadout(); updatePose(); if (!s.enabled) invalidate(); });
    checkbox.onchange = () => { s.enabled = checkbox.checked; invalidate(); activeCount(); };
    const ranges = document.createElement('div'); ranges.className = 'range-pair';
    for (const [key,text] of [['min','Sample from'],['max','Sample to']]) {
      const label = document.createElement('label'); label.textContent = `${text} (${unit})`;
      const input = document.createElement('input'); input.type = 'number'; input.step = factor === 1 ? '.01' : '1'; input.value = Number((s[key]*factor).toFixed(4));
      input.onchange = () => {
        const v = Number(input.value)/factor;
        if (input.value.trim() === '' || !Number.isFinite(v) || v < joint.min-1e-6 || v > joint.max+1e-6 || (key === 'min' ? v > s.max : v < s.min)) {
          input.value = s[key]*factor; status('Invalid range: stay inside URDF limits and keep lower ≤ upper.'); return;
        }
        s[key] = Math.max(joint.min, Math.min(joint.max, v)); invalidate(); activeCount();
      };
      label.append(input); ranges.append(label);
    }
    panel.append(ranges); $('joints').append(panel);
  }
  activeCount();
}
function load(xml, preferredTip, preferredOffset) {
  const parsed = parseRobot(xml); // Validate before replacing the current model.
  robot = parsed; states = {}; clearCloud();
  for (const j of robot.joints.values()) if (j.type !== 'fixed') states[j.name] = {min:j.min,max:j.max,value:Math.max(j.min,Math.min(j.max,0)),enabled:true};
  $('xml').value = xml; $('robot-name').textContent = robot.name;
  $('warnings').textContent = robot.warnings.join('\n');
  $('tip').replaceChildren(...[...robot.links.keys()].map(name => new Option(name,name)));
  const leaves = [...robot.links.keys()].filter(n => !robot.ordered.some(j => j.parent === n));
  $('tip').value = preferredTip || (robot.links.has('upper_arm') ? 'upper_arm' : leaves.at(-1));
  setOffset(preferredOffset || suggestedTip(robot,$('tip').value));
  renderRobot(); jointControls(); updatePose(); fit();
  status('Robot loaded. White marker = tracked point. Generate a workspace to trace its reach.');
}
async function generate() {
  if (!robot) throw Error('Load a robot first.');
  const localOffset = offset();
  clearCloud(); const token = generation;
  const total = Number($('samples').value), next = sampler(robot,$('tip').value,localOffset,structuredClone(states),total);
  const positions = new Float32Array(total*3), bounds = new THREE.Box3();
  for (let start = 0; start < total; start += 400) {
    if (token !== generation) return;
    for (let i = start; i < Math.min(start+400,total); i++) { const p = next(i); positions.set(p.toArray(), i*3); bounds.expandByPoint(p); }
    status(`Sampling ${Math.min(start+400,total).toLocaleString()} / ${total.toLocaleString()}…`);
    await new Promise(resolve => setTimeout(resolve, 0));
  }
  if (token !== generation) return;
  const colors = new Float32Array(total*3), color = new THREE.Color();
  for (let i = 0; i < total; i++) {
    const t = (positions[i*3+2]-bounds.min.z)/Math.max(bounds.max.z-bounds.min.z,1e-9);
    color.setHSL(.61-.23*t,.8,.6); colors.set(color.toArray(),i*3);
  }
  const geometry = new THREE.BufferGeometry(); geometry.setAttribute('position',new THREE.BufferAttribute(positions,3)); geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));
  cloud = new THREE.Points(geometry,new THREE.PointsMaterial({size:2.5,sizeAttenuation:false,vertexColors:true,transparent:true,opacity:.65,depthWrite:false}));
  scene.add(cloud); cloud.visible = $('show-cloud').checked;
  points = positions; $('export').disabled = false;
  $('count').textContent = total.toLocaleString();
  ['x','y','z'].forEach(axis => { $(`b${axis}`).textContent = `${bounds.min[axis].toFixed(3)} → ${bounds.max[axis].toFixed(3)}`; });
  status('Workspace ready · geometric samples in the robot root frame · collisions not checked.'); fit();
}

for (const [key,e] of Object.entries(examples)) $('example').add(new Option(e.title,key));
$('example').onchange = guard(async () => { const e = examples[$('example').value]; if (e) { load(e.xml,e.tip,e.offset); await generate(); } });
$('upload').onchange = guard(async () => { const file = $('upload').files[0]; if (!file) return; if (file.size > 5e6) throw Error('File exceeds 5 MB.'); load(await file.text()); $('example').value = ''; });
async function loadRig() {
  status('Expanding the current project Xacro…');
  const response = await fetch('/api/rig'); const text = await response.text();
  if (!response.ok) throw Error(text);
  load(text); $('example').value = ''; await generate();
}
$('rig').onclick = guard(loadRig);
$('apply').onclick = guard(() => load($('xml').value));
$('tip').onchange = guard(() => { setOffset(suggestedTip(robot,$('tip').value)); jointControls(); invalidate(); updatePose(); });
$('suggest').onclick = guard(() => { if (!robot) return; setOffset(suggestedTip(robot,$('tip').value)); invalidate(); updatePose(); });
for (const id of ['tx','ty','tz']) $(id).onchange = guard(() => { invalidate(); updatePose(); });
$('samples').onchange = invalidate;
$('generate').onclick = guard(generate);
$('show-robot').onchange = () => { robotGroup.visible = $('show-robot').checked; };
$('show-cloud').onchange = () => { if (cloud) cloud.visible = $('show-cloud').checked; };
$('fit').onclick = fit;
$('export').onclick = () => {
  let csv = 'x_m,y_m,z_m\n';
  for (let i = 0; i < points.length; i += 3) csv += `${points[i]},${points[i+1]},${points[i+2]}\n`;
  const url = URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  const a = document.createElement('a'); a.href = url; a.download = 'workspace.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
};
await guard(loadRig)();