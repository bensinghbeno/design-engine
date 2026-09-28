import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {estimateTrajectory, parseSensorCsv} from './motion.js';

const $ = id => document.getElementById(id);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x091019);
scene.fog = new THREE.FogExp2(0x091019, 0.12);
const camera = new THREE.PerspectiveCamera(42, 1, 0.001, 100);
camera.up.set(0, 0, 1); camera.position.set(1.2, 1.2, 0.75);
const renderer = new THREE.WebGLRenderer({antialias: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
$('viewport').prepend(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.target.set(0, 0, 0.1);
scene.add(new THREE.HemisphereLight(0xddeeff, 0x18202b, 2.5));
const keyLight = new THREE.DirectionalLight(0xffffff, 4); keyLight.position.set(2, -3, 5); scene.add(keyLight);
const grid = new THREE.GridHelper(4, 40, 0x355069, 0x1a2b3a); grid.rotation.x = Math.PI / 2; scene.add(grid);
const axisLength = 0.22;
scene.add(
  new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(), axisLength, 0xff0000, 0.045, 0.022),
  new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), new THREE.Vector3(), axisLength, 0x00ff00, 0.045, 0.022),
  new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(), axisLength, 0x0000ff, 0.045, 0.022),
);

const gripper = new THREE.Group();
const metal = new THREE.MeshStandardMaterial({color: 0x5ad6b0, roughness: 0.35, metalness: 0.5});
const grip = new THREE.MeshStandardMaterial({color: 0xff685f, roughness: 0.7});
const palm = new THREE.Mesh(new THREE.BoxGeometry(0.025, 0.12, 0.035), metal); palm.position.x = -0.0125; gripper.add(palm);
for (const side of [-1, 1]) {
  const finger = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.022, 0.025), grip);
  finger.position.set(0.05, side * 0.049, 0); gripper.add(finger);
  const tip = new THREE.Mesh(new THREE.BoxGeometry(0.025, 0.032, 0.04), grip);
  tip.position.set(0.091, side * 0.044, 0); gripper.add(tip);
}
gripper.rotation.z = Math.PI / 2;
scene.add(gripper);
let route = null, trail = null;
let recording = null;
const replay = {playing: false, elapsed: 0, startedAt: 0, frame: 0};

const observer = new ResizeObserver(() => {
  const {width, height} = $('viewport').getBoundingClientRect();
  renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
}); observer.observe($('viewport'));

function lineFor(positions, color, opacity) {
  const geometry = new THREE.BufferGeometry().setFromPoints(positions.map(point => new THREE.Vector3(...point)));
  return new THREE.Line(geometry, new THREE.LineBasicMaterial({color, transparent: opacity < 1, opacity}));
}
function disposeLine(line) { if (!line) return; line.geometry.dispose(); line.material.dispose(); line.removeFromParent(); }
function setPosition(point, elapsed) {
  gripper.position.fromArray(point);
  for (const [axis, id] of [['x', 'position-x'], ['y', 'position-y'], ['z', 'position-z']]) {
    $(id).textContent = `${point['xyz'.indexOf(axis)].toFixed(3)} m`;
  }
  $('elapsed').textContent = `${elapsed.toFixed(2)} s`;
  $('progress').style.width = `${100 * elapsed / recording.time.at(-1)}%`;
}
function fit() {
  if (!recording) return;
  const bounds = new THREE.Box3().setFromPoints(recording.position.map(point => new THREE.Vector3(...point)));
  bounds.expandByObject(gripper);
  const center = bounds.getCenter(new THREE.Vector3()), radius = Math.max(0.18, bounds.getSize(new THREE.Vector3()).length() / 2);
  controls.target.copy(center);
  camera.position.copy(center).add(new THREE.Vector3(1.3, 1.5, 0.9).normalize().multiplyScalar(radius * 3.2));
  camera.near = Math.max(0.0001, radius / 100); camera.far = Math.max(20, radius * 30); camera.updateProjectionMatrix(); controls.update();
}
function restart(keepPlaying = false) {
  if (!recording) return;
  replay.elapsed = 0; replay.frame = 0; replay.startedAt = performance.now();
  setPosition(recording.position[0], 0); trail.geometry.setDrawRange(0, 1);
  replay.playing = keepPlaying; $('play').textContent = keepPlaying ? 'Pause' : 'Play';
}
function togglePlay() {
  if (!recording) return;
  if (replay.elapsed >= recording.time.at(-1)) restart(true);
  else if (replay.playing) { replay.playing = false; $('play').textContent = 'Play'; }
  else { replay.playing = true; replay.startedAt = performance.now() - replay.elapsed * 1000 / Number($('speed').value); $('play').textContent = 'Pause'; }
}
function updateReplay(now) {
  if (!recording || !replay.playing) return;
  replay.elapsed = (now - replay.startedAt) / 1000 * Number($('speed').value);
  const duration = recording.time.at(-1);
  if (replay.elapsed >= duration) { replay.elapsed = duration; replay.playing = false; $('play').textContent = 'Replay'; }
  while (replay.frame + 1 < recording.time.length && recording.time[replay.frame + 1] <= replay.elapsed) replay.frame++;
  const next = Math.min(replay.frame + 1, recording.time.length - 1);
  const span = recording.time[next] - recording.time[replay.frame];
  const mix = span ? (replay.elapsed - recording.time[replay.frame]) / span : 0;
  const point = recording.position[replay.frame].map((value, axis) => THREE.MathUtils.lerp(value, recording.position[next][axis], mix));
  setPosition(point, replay.elapsed); trail.geometry.setDrawRange(0, next + 1);
}
function animate(now) { updateReplay(now); controls.update(); renderer.render(scene, camera); }
renderer.setAnimationLoop(animate);

async function loadCsv(text, name) {
  const {time, acceleration} = parseSensorCsv(text);
  const estimate = estimateTrajectory(time, acceleration);
  recording = {time, ...estimate}; replay.playing = false;
  disposeLine(route); disposeLine(trail);
  route = lineFor(recording.position, 0x557086, 0.45); trail = lineFor(recording.position, 0x55f0bc, 1);
  trail.geometry.setDrawRange(0, 1); scene.add(route, trail);
  route.visible = $('show-path').checked;
  $('filename').textContent = name; $('samples').textContent = time.length.toLocaleString();
  $('duration').textContent = `${time.at(-1).toFixed(2)} s`; $('summary-duration').textContent = `${time.at(-1).toFixed(2)} s`;
  $('travel').textContent = `${recording.pathLength.toFixed(3)} m`;
  $('bias').textContent = recording.bias.map(value => value.toFixed(3)).join(' / ');
  $('play').disabled = false; $('restart').disabled = false;
  restart(false); fit(); $('status').textContent = 'Recording ready · press Play to replay the estimated path.';
}
async function loadDefault() {
  $('status').textContent = 'Loading sensors/Accelerometer.csv…';
  const response = await fetch('/api/motion');
  if (!response.ok) throw Error(await response.text());
  await loadCsv(await response.text(), 'sensors/Accelerometer.csv');
}
async function guard(action) { try { await action(); } catch (error) { $('status').textContent = error.message; console.error(error); } }

$('load-default').onclick = () => guard(loadDefault);
$('upload').onchange = () => guard(async () => { const file = $('upload').files[0]; if (!file) return; if (file.size > 10e6) throw Error('CSV exceeds 10 MB.'); await loadCsv(await file.text(), file.name); });
$('play').onclick = togglePlay;
$('restart').onclick = () => restart(false);
$('fit').onclick = fit;
$('show-path').onchange = () => { if (route) route.visible = $('show-path').checked; };
$('speed').onchange = () => { if (replay.playing) replay.startedAt = performance.now() - replay.elapsed * 1000 / Number($('speed').value); };
await guard(loadDefault);