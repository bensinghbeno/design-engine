import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {parseRobot, forward, chain, suggestedTip, configurationSampler, tipPosition} from './kinematics.js';
import {examples} from './examples.js';
import {coverageColor, coverageCategory, DEFAULT_IK_OPTIONS} from './orientation.js';

const $ = id => document.getElementById(id);
const status = text => { $('status').textContent = text; };
let robot, states = {}, frames = new Map(), cloud, points = [], generation = 0;
let workspaceSnapshot = null, orientationWorker = null, coverageCloud = null;
let coverageRecords = [], coverageSettings = null, coverageTotal = 0, coverageComplete = false;
const fingerNames = ['gripper_left_joint','gripper_right_joint'];
function hasParallelGripper() {
  return robot?.name === 'arm_rig' && fingerNames.every(name => robot.joints.get(name)?.type === 'prismatic');
}
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
function setColourMode() {
  const coverage = $('colour-mode').value === 'coverage';
  $('height-key').hidden = coverage;
  $('coverage-key').hidden = !coverage;
  if (cloud) {
    cloud.material.vertexColors = !coverage;
    cloud.material.color.set(coverage ? '#7d8896' : '#ffffff');
    cloud.material.opacity = coverage ? .13 : .65;
    cloud.material.needsUpdate = true;
  }
  if (coverageCloud) coverageCloud.visible = coverage && $('show-cloud').checked;
  $('coverage-summary').hidden = !coverage || !coverageRecords.length;
  if (!coverage) $('probe-detail').hidden = true;
}
function clearCoverage(message = 'Generate a workspace first.') {
  if (orientationWorker) orientationWorker.terminate();
  orientationWorker = null;
  if (coverageCloud) dispose(coverageCloud);
  coverageCloud = null; coverageRecords = []; coverageSettings = null;
  coverageTotal = 0; coverageComplete = false;
  $('cancel-analysis').disabled = true;
  $('analyze').disabled = !workspaceSnapshot;
  $('export-coverage').disabled = true;
  $('coverage-summary').hidden = true; $('coverage-summary').textContent = '';
  $('probe-detail').hidden = true; $('probe-detail').textContent = '';
  $('orientation-progress').textContent = message;
}
function clearCloud() {
  generation++;
  workspaceSnapshot = null; clearCoverage();
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
    // The project gripper is one symmetric aperture, not two unrelated
    // sampled axes. Keep its aperture fixed while sampling arm reach.
    if (hasParallelGripper() && fingerNames.includes(joint.name)) continue;
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
    slider.oninput = guard(() => { s.value = Number(slider.value)/factor; updateReadout(); updatePose(); if (!s.enabled || s.min === s.max) invalidate(); });
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
  if (hasParallelGripper()) {
    const panel = document.createElement('div'); panel.className = 'joint';
    const label = document.createElement('label'); label.textContent = 'Gripper aperture · ';
    const readout = document.createElement('output'); readout.id = 'gripper-aperture-readout';
    const slider = document.createElement('input'); slider.type = 'range'; slider.id = 'gripper-aperture';
    slider.min = 0;
    slider.max = 2000*Math.min(...fingerNames.map(name=>robot.joints.get(name).max));
    slider.step = '.1'; slider.value = 1000*fingerNames.reduce((sum,name)=>sum+states[name].value,0);
    slider.setAttribute('aria-label','Gripper aperture (mm)');
    const update = () => { readout.textContent = `${Number(slider.value).toFixed(1)} mm`; };
    update(); label.append(readout);
    slider.oninput = guard(() => {
      for (const name of fingerNames) states[name].value = Number(slider.value)/2000;
      update(); updatePose();
      if (path.some(j=>fingerNames.includes(j.name))) invalidate();
    });
    const note = document.createElement('div'); note.className = 'axis-note';
    note.textContent = 'Symmetric fingers; aperture held fixed during sampling. Tool point is between the fingertip ends.';
    panel.append(label,slider,note); $('joints').append(panel);
  }
  activeCount();
}
function load(xml, preferredTip, preferredOffset) {
  const parsed = parseRobot(xml); // Validate before replacing the current model.
  robot = parsed; states = {}; clearCloud();
  for (const j of robot.joints.values()) if (j.type !== 'fixed') states[j.name] = {min:j.min,max:j.max,value:Math.max(j.min,Math.min(j.max,0)),enabled:true};
  if (hasParallelGripper()) for (const name of fingerNames) {
    states[name].enabled = false;
    states[name].value = robot.joints.get(name).max; // preview open gripper
  }
  $('xml').value = xml; $('robot-name').textContent = robot.name;
  $('warnings').textContent = robot.warnings.join('\n');
  $('tip').replaceChildren(...[...robot.links.keys()].map(name => new Option(name,name)));
  const leaves = [...robot.links.keys()].filter(n => !robot.ordered.some(j => j.parent === n));
  $('tip').value = preferredTip || (robot.links.has('gripper_tool') ? 'gripper_tool'
    : robot.links.has('upper_arm') ? 'upper_arm' : leaves.at(-1));
  setOffset(preferredOffset || suggestedTip(robot,$('tip').value));
  renderRobot(); jointControls(); updatePose(); fit();
  status('Robot loaded. White marker = tracked point. Generate a workspace to trace its reach.');
}
async function generate() {
  if (!robot) throw Error('Load a robot first.');
  const localOffset = offset();
  clearCloud(); const token = generation;
  const sourceRobot = robot, link = $('tip').value, captured = structuredClone(states);
  const model = {offset:localOffset,joints:chain(sourceRobot,link).map(j=>({
    name:j.name,type:j.type,origin:j.origin.toArray(),axis:j.axis.toArray(),
    min:j.type==='fixed' ? 0 : captured[j.name].min,
    max:j.type==='fixed' ? 0 : captured[j.name].max,
    value:j.type==='fixed' ? 0 : captured[j.name].value,
    enabled:j.type!=='fixed' && captured[j.name].enabled,
  }))};
  const total = Number($('samples').value), next = configurationSampler(sourceRobot,link,captured,total);
  const candidates = [], stride = Math.ceil(total/512);
  const positions = new Float32Array(total*3), bounds = new THREE.Box3();
  for (let start = 0; start < total; start += 400) {
    if (token !== generation) return;
    for (let i = start; i < Math.min(start+400,total); i++) {
      const q = next(i), p = tipPosition(sourceRobot,link,localOffset,q);
      positions.set(p.toArray(),i*3); bounds.expandByPoint(p);
      if (i%stride === 0) candidates.push({position:p.toArray(),seed:q});
    }
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
  workspaceSnapshot = {model,candidates};
  $('analyze').disabled = false;
  $('orientation-progress').textContent = 'Ready to test orientations at selected reachable points.';
  setColourMode();
  $('count').textContent = total.toLocaleString();
  ['x','y','z'].forEach(axis => { $(`b${axis}`).textContent = `${bounds.min[axis].toFixed(3)} → ${bounds.max[axis].toFixed(3)}`; });
  status('Workspace ready · geometric samples in the robot root frame · collisions not checked.'); fit();
}

function coverageOptions() {
  const positionMM = Number($('position-tolerance').value), angleDegrees = Number($('angle-tolerance').value);
  if (!Number.isFinite(positionMM) || positionMM<.1 || positionMM>50) throw Error('Position tolerance must be 0.1–50 mm.');
  if (!Number.isFinite(angleDegrees) || angleDegrees<1 || angleDegrees>30) throw Error('Orientation tolerance must be 1–30°.');
  return {...DEFAULT_IK_OPTIONS,positionTolerance:positionMM/1000,orientationTolerance:angleDegrees*Math.PI/180};
}
function applyCoverageFilter() {
  if (!coverageCloud) return;
  const filter = $('coverage-filter')?.value || 'all';
  const geometry = coverageCloud.geometry;
  const positions = geometry.attributes.position;
  const colors = geometry.attributes.color;
  let visibleCount = 0;
  for (let i = 0; i < coverageRecords.length; i++) {
    const r = coverageRecords[i];
    const cat = coverageCategory(r.fraction);
    if (filter === 'all' || filter === cat) {
      r._visibleIndex = visibleCount;
      positions.setXYZ(visibleCount, ...r.position);
      colors.setXYZ(visibleCount, ...coverageColor(r.fraction));
      visibleCount++;
    } else {
      r._visibleIndex = -1;
    }
  }
  positions.needsUpdate = true;
  colors.needsUpdate = true;
  geometry.setDrawRange(0, visibleCount);
  geometry.computeBoundingSphere();
}

function updateCoverageSummary() {
  if (!coverageRecords.length) return;
  const values = coverageRecords.map(r=>r.fraction), mean = values.reduce((s,v)=>s+v,0)/values.length;
  const filter = $('coverage-filter')?.value || 'all';
  const counts = {green: 0, yellow: 0, red: 0};
  for (const r of coverageRecords) counts[coverageCategory(r.fraction)]++;
  const filterText = filter === 'all' ? '' : ` [showing ${filter}: ${counts[filter]}/${coverageRecords.length}]`;
  $('coverage-summary').textContent = `${coverageComplete ? 'Complete' : 'Partial'} · ${coverageRecords.length}/${coverageTotal} positions tested${filterText} · `
    + `mean orientations found ${(100*mean).toFixed(1)}% · range ${(100*Math.min(...values)).toFixed(0)}–${(100*Math.max(...values)).toFixed(0)}% · `
    + `${coverageRecords[0].tested} orientations/point · ${(coverageSettings.positionTolerance*1000).toFixed(1)} mm / ${(coverageSettings.orientationTolerance*180/Math.PI).toFixed(1)}° tolerances. No solution found ≠ impossible.`;
  $('coverage-summary').hidden = $('colour-mode').value !== 'coverage';
}
function cancelAnalysis() {
  if (!orientationWorker) return;
  orientationWorker.terminate(); orientationWorker = null;
  $('cancel-analysis').disabled = true; $('analyze').disabled = !workspaceSnapshot;
  $('orientation-progress').textContent = `Cancelled · ${coverageRecords.length} completed spots retained (partial).`;
  updateCoverageSummary();
}
function analyzeOrientations() {
  if (!workspaceSnapshot) throw Error('Generate a workspace before analysing orientations.');
  const options = coverageOptions();
  const probeCount = Number($('probe-count').value), orientationCount = Number($('orientation-count').value);
  clearCoverage('Starting orientation IK…');
  coverageSettings = options;
  $('colour-mode').value = 'coverage';
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.BufferAttribute(new Float32Array(probeCount*3),3));
  geometry.setAttribute('color',new THREE.BufferAttribute(new Float32Array(probeCount*3),3));
  geometry.setDrawRange(0,0);
  // Use the transparent queue (at full opacity) so renderOrder really puts
  // probes after the translucent grey cloud, even at coincident samples.
  coverageCloud = new THREE.Points(geometry,new THREE.PointsMaterial({size:9,sizeAttenuation:false,vertexColors:true,
    transparent:true,opacity:1,depthTest:false,depthWrite:false}));
  coverageCloud.frustumCulled = false; coverageCloud.renderOrder = 5;
  scene.add(coverageCloud); setColourMode();
  let worker;
  try { worker = new Worker(new URL('./orientation-worker.js',import.meta.url),{type:'module'}); }
  catch (e) { clearCoverage('Could not start the orientation worker.'); throw e; }
  orientationWorker = worker;
  $('analyze').disabled = true; $('cancel-analysis').disabled = false;
  const fail = message => {
    if (orientationWorker !== worker) return;
    worker.terminate(); orientationWorker = null;
    $('analyze').disabled = !workspaceSnapshot; $('cancel-analysis').disabled = true;
    $('orientation-progress').textContent = `Analysis failed: ${message}. Any retained spots are partial.`;
    updateCoverageSummary();
  };
  worker.onerror = event => { event.preventDefault(); fail(event.message || 'Worker unavailable'); };
  worker.onmessage = event => {
    if (orientationWorker !== worker) return; // Ignore stale results after changes/cancel.
    const data = event.data;
    if (data.type === 'error') { fail(data.message); return; }
    coverageTotal = data.total;
    if (data.type === 'probe') {
      const r = data.result;
      coverageRecords.push(r);
      applyCoverageFilter();
      $('export-coverage').disabled = false;
      updateCoverageSummary();
    }
    if (data.type === 'done') {
      coverageComplete = true; worker.terminate(); orientationWorker = null;
      $('analyze').disabled = false; $('cancel-analysis').disabled = true;
      applyCoverageFilter();
      $('orientation-progress').textContent = `Orientation analysis complete · ${coverageRecords.length} tested spots. Click a coloured spot for details.`;
      updateCoverageSummary();
    } else {
      $('orientation-progress').textContent = `Testing orientations · ${coverageRecords.length}/${coverageTotal} positions · ${orientationCount} orientations each…`;
    }
  };
  worker.postMessage({...workspaceSnapshot,probeCount,orientationCount,options});
}

// Picking is informational only; orbit drags must not select a spot.
const probeRay = new THREE.Raycaster();
let pointerDown = null;
renderer.domElement.addEventListener('pointerdown',event=> { pointerDown=[event.clientX,event.clientY]; });
renderer.domElement.addEventListener('pointerup',event=> {
  if (!pointerDown || event.button!==0 || Math.hypot(event.clientX-pointerDown[0],event.clientY-pointerDown[1])>5) return;
  pointerDown=null;
  if (!coverageCloud?.visible || !coverageRecords.length) return;
  const rect = renderer.domElement.getBoundingClientRect();
  probeRay.params.Points.threshold = camera.position.distanceTo(controls.target)*.008;
  probeRay.setFromCamera(new THREE.Vector2((event.clientX-rect.left)/rect.width*2-1,1-(event.clientY-rect.top)/rect.height*2),camera);
  const maxIndex = coverageCloud.geometry.drawRange.count;
  const hits = probeRay.intersectObject(coverageCloud).filter(hit=>hit.index<maxIndex);
  hits.sort((a,b)=>a.distanceToRay-b.distanceToRay);
  if (!hits.length) return;
  const hitVisibleIndex = hits[0].index;
  const r = coverageRecords.find(rec => rec._visibleIndex === hitVisibleIndex) || coverageRecords[hitVisibleIndex];
  if (!r) return;
  $('probe-detail').hidden = false;
  $('probe-detail').textContent = `Point (${r.position.map(v=>v.toFixed(3)).join(', ')}) m · ${r.solved}/${r.tested} orientations found (${(100*r.fraction).toFixed(1)}%). `
    + 'Position known reachable; missing orientations are unconfirmed, not proven impossible.';
});

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
$('analyze').onclick = guard(analyzeOrientations);
$('cancel-analysis').onclick = cancelAnalysis;
$('colour-mode').onchange = setColourMode;
$('coverage-filter').onchange = () => { applyCoverageFilter(); updateCoverageSummary(); };
for (const id of ['probe-count','orientation-count','position-tolerance','angle-tolerance']) {
  $(id).onchange = () => clearCoverage(workspaceSnapshot ? 'Analysis settings changed. Run orientation analysis again.' : 'Generate a workspace first.');
}
$('show-robot').onchange = () => { robotGroup.visible = $('show-robot').checked; };
$('show-cloud').onchange = () => { if (cloud) cloud.visible = $('show-cloud').checked; setColourMode(); };
$('fit').onclick = fit;
$('export').onclick = () => {
  let csv = 'x_m,y_m,z_m\n';
  for (let i = 0; i < points.length; i += 3) csv += `${points[i]},${points[i+1]},${points[i+2]}\n`;
  const url = URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  const a = document.createElement('a'); a.href = url; a.download = 'workspace.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
};
$('export-coverage').onclick = () => {
  if (!coverageRecords.length) return;
  let csv = 'x_m,y_m,z_m,orientations_found,orientations_tested,found_fraction,position_tolerance_m,orientation_tolerance_deg,ik_starts,max_iterations,analysis_complete,collisions_checked\n';
  for (const r of coverageRecords) csv += [...r.position,r.solved,r.tested,r.fraction,
    coverageSettings.positionTolerance,coverageSettings.orientationTolerance*180/Math.PI,
    coverageSettings.restarts,coverageSettings.maxIterations,coverageComplete,false].join(',')+'\n';
  const url = URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  const a = document.createElement('a'); a.href=url; a.download='orientation-coverage.csv'; a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
};
await guard(loadRig)();
// Explicit opt-in link for opening this view directly; ordinary launches keep
// the fast position-only preview and do not start an expensive analysis.
if (new URLSearchParams(location.search).get('orientation') === '1' && workspaceSnapshot) {
  await guard(analyzeOrientations)();
}