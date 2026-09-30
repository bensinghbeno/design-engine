import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {createOrientationTracker, parseSensorCsv} from './motion.js';

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
scene.add(gripper);
let recording = null, mode = 'csv';
let swapXY = true, invertY = true;
const replay = {playing: false, elapsed: 0, startedAt: 0, frame: 0};
const live = {socket: null, tracker: createOrientationTracker(), enabled: false,
  phone: null, phones: 0, last: null, start: null, latest: [0, 0, 0, 1], elapsed: 0, samples: 0, rateStart: 0, rateCount: 0};

const observer = new ResizeObserver(() => {
  const {width, height} = $('viewport').getBoundingClientRect();
  renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
}); observer.observe($('viewport'));

function setRotation(quaternion, elapsed) {
  gripper.position.set(0, 0, 0);
  const orientation = new THREE.Quaternion(...quaternion);
  const angles = new THREE.Euler().setFromQuaternion(orientation, 'YXZ');
  if (swapXY) [angles.x, angles.y] = [angles.y, angles.x];
  if (invertY) angles.y = -angles.y;
  const displayedOrientation = new THREE.Quaternion().setFromEuler(angles);
  gripper.quaternion.copy(displayedOrientation);
  for (const [axis, id] of [['x', 'rotation-x'], ['y', 'rotation-y'], ['z', 'rotation-z']]) {
    $(id).textContent = `${THREE.MathUtils.radToDeg(angles[axis]).toFixed(1)}°`;
  }
  $('elapsed').textContent = `${elapsed.toFixed(2)} s`;
  $('progress').style.width = mode === 'csv' && recording?.time.at(-1) ? `${100 * elapsed / recording.time.at(-1)}%` : '0';
}
function fit() {
  scene.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(gripper);
  const radius = Math.max(0.18, bounds.getSize(new THREE.Vector3()).length() / 2);
  const center = new THREE.Vector3();
  controls.target.copy(center);
  camera.position.copy(center).add(new THREE.Vector3(1.3, 1.5, 0.9).normalize().multiplyScalar(radius * 3.2));
  camera.near = Math.max(0.0001, radius / 100); camera.far = Math.max(20, radius * 30); camera.updateProjectionMatrix(); controls.update();
}
function restart(keepPlaying = false) {
  if (!recording) return;
  replay.elapsed = 0; replay.frame = 0; replay.startedAt = performance.now();
  setRotation(recording.rotation[0], 0);
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
  setRotation(recording.rotation[replay.frame], replay.elapsed);
}
function animate(now) { updateReplay(now); updateLive(now); controls.update(); renderer.render(scene, camera); }
renderer.setAnimationLoop(animate);

function liveState(text) { $('live-state').textContent = text; }
function resetLive() {
  live.tracker.reset();
  live.last = null; live.start = null; live.latest = [0, 0, 0, 1]; live.elapsed = 0;
}
function onSample({phone, t, q, on}) {
  const seconds = t / 1000;
  if (phone !== live.phone || (live.last !== null && seconds <= live.last)) {
    live.last = null; live.start = null; live.phone = phone;
    if (live.enabled) live.tracker.resume(); else live.tracker.hold();
  }
  live.last = seconds;
  if (live.start === null) live.start = seconds;
  const enabled = on === true;
  if (enabled !== live.enabled) setClutch(enabled);
  if (enabled) live.latest = live.tracker.update(q);
  live.elapsed = seconds - live.start; live.samples++; live.rateCount++;
}
function setClutch(enabled) {
  live.enabled = enabled;
  if (enabled) live.tracker.resume();
  else live.tracker.hold();
}
function updateLive(now) {
  if (mode !== 'live' || !live.latest) return;
  setRotation(live.latest, live.elapsed);
  if (now - live.rateStart >= 1000) {
    $('live-rate').textContent = live.rateCount ? `${Math.round(live.rateCount * 1000 / (now - live.rateStart))} Hz` : '—';
    $('samples').textContent = live.samples.toLocaleString();
    $('travel').textContent = 'Orientation sensor';
    live.rateStart = now; live.rateCount = 0;
  }
  if (!live.socket || !live.phones || !live.samples) return;
  if (!live.enabled) return liveState('Connected · holding (phone ENABLE is off)');
  liveState('Streaming · rotation only');
}
function showSession(session) {
  live.phones = session.phones;
  if (!live.phones) setClutch(false);
  $('phone-link').textContent = session.error ? `Phone stream unavailable: ${session.error}` : session.phoneUrl;
  $('live-phones').textContent = String(session.phones);
  if (!session.phones) liveState('Connected · waiting for phone');
}
function disconnect() {
  const socket = live.socket; live.socket = null;
  socket?.close();
  $('connect').textContent = 'Connect'; liveState('Disconnected');
}
function connect() {
  if (live.socket) return disconnect();
  const address = $('server').value.trim();
  if (!/^([\w.-]+|\[[0-9a-f:]+\]):\d{1,5}$/i.test(address)) throw Error('Enter the server as IP:port, for example 127.0.0.1:8766.');
  const socket = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${address}/ws`);
  live.socket = socket; $('connect').textContent = 'Disconnect'; liveState('Connecting…');
  socket.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.type === 'sample') onSample(message);
    else if (message.type === 'clutch') setClutch(message.enabled);
    else if (message.type === 'session') showSession(message);
    else if (message.type === 'saved') $('status').textContent = `Saved sensors/${message.file} · ${message.samples.toLocaleString()} samples, ${message.seconds.toFixed(1)} s · replay it: From CSV → Load last live session.`;
    else if (message.type === 'save-error') $('status').textContent = `Could not save live session: ${message.message}`;
  };
  socket.onclose = () => { if (live.socket === socket) { live.socket = null; $('connect').textContent = 'Connect'; liveState('Disconnected · check the server address'); } };
}
function setMode(next) {
  mode = next;
  for (const [id, value] of [['mode-csv', 'csv'], ['mode-live', 'live']]) {
    $(id).classList.toggle('active', next === value); $(id).setAttribute('aria-pressed', String(next === value));
  }
  const csv = next === 'csv';
  $('csv-panel').hidden = !csv; $('live-panel').hidden = csv; $('replay-panel').hidden = !csv;
  $('travel').textContent = csv ? 'Orientation recording' : 'Orientation sensor';
  if (csv) {
    disconnect();
    if (recording) { restart(false); $('duration').textContent = `${recording.time.at(-1).toFixed(2)} s`; $('summary-duration').textContent = `${recording.time.at(-1).toFixed(2)} s`; $('samples').textContent = recording.time.length.toLocaleString(); }
    $('status').textContent = 'Recording mode · press Play to replay gripper rotation.';
  } else {
    replay.playing = false; $('play').textContent = 'Play';
    resetLive(); live.samples = 0; live.enabled = false; setRotation(live.latest, 0);
    $('duration').textContent = 'LIVE'; $('summary-duration').textContent = 'LIVE'; $('samples').textContent = '0';
    $('status').textContent = 'Live mode · hold ENABLE on the phone and rotate it; release to freeze.';
    if (!live.socket) guard(connect);
    fit();
  }
}

function replayOrientations(quaternions, enabled) {
  const tracker = createOrientationTracker();
  let active = false;
  return quaternions.map((quaternion, index) => {
    const on = enabled ? enabled[index] : true;
    if (on !== active) { active = on; active ? tracker.resume() : tracker.hold(); }
    return quaternion && active ? tracker.update(quaternion) : tracker.quaternion;
  });
}

async function loadCsv(text, name) {
  const parsed = parseSensorCsv(text);
  if (!parsed.quaternion) throw Error('This viewer now replays orientation-only CSVs with qx, qy, qz and qw columns.');
  recording = {time: parsed.time, rotation: replayOrientations(parsed.quaternion, parsed.enabled)};
  replay.playing = false;
  $('filename').textContent = name; $('samples').textContent = recording.time.length.toLocaleString();
  $('duration').textContent = `${recording.time.at(-1).toFixed(2)} s`; $('summary-duration').textContent = `${recording.time.at(-1).toFixed(2)} s`;
  $('travel').textContent = 'Orientation recording';
  $('play').disabled = false; $('restart').disabled = false;
  restart(false); fit(); $('status').textContent = 'Orientation recording ready · press Play to replay rotation.';
}
async function loadServerCsv(url, name) {
  $('status').textContent = `Loading ${name}…`;
  const response = await fetch(url);
  if (!response.ok) throw Error(await response.text());
  await loadCsv(await response.text(), name);
}
async function guard(action) { try { await action(); } catch (error) { $('status').textContent = error.message; console.error(error); } }

$('load-live').onclick = () => guard(() => loadServerCsv('/api/live-latest', 'sensors/live-latest.csv'));
$('upload').onchange = () => guard(async () => { const file = $('upload').files[0]; if (!file) return; if (file.size > 10e6) throw Error('CSV exceeds 10 MB.'); await loadCsv(await file.text(), file.name); });
$('play').onclick = togglePlay;
$('restart').onclick = () => restart(false);
$('fit').onclick = fit;
$('mode-csv').onclick = () => setMode('csv');
$('mode-live').onclick = () => setMode('live');
$('connect').onclick = () => guard(connect);
$('swap-xy').onclick = () => {
  swapXY = !swapXY;
  $('swap-xy').setAttribute('aria-pressed', String(swapXY));
  $('swap-xy').textContent = `Swap X/Y: ${swapXY ? 'On' : 'Off'}`;
  if (mode === 'live') setRotation(live.latest, live.elapsed);
  else if (recording) setRotation(recording.rotation[replay.frame], replay.elapsed);
};
$('invert-y').onclick = () => {
  invertY = !invertY;
  $('invert-y').setAttribute('aria-pressed', String(invertY));
  $('invert-y').textContent = `Invert Y: ${invertY ? 'On' : 'Off'}`;
  if (mode === 'live') setRotation(live.latest, live.elapsed);
  else if (recording) setRotation(recording.rotation[replay.frame], replay.elapsed);
};
$('server').value = location.host;
$('server').onkeydown = event => { if (event.key === 'Enter' && !live.socket) guard(connect); };
$('zero').onclick = () => { resetLive(); live.latest = [0, 0, 0, 1]; setRotation(live.latest, live.elapsed); };
$('speed').onchange = () => { if (replay.playing) replay.startedAt = performance.now() - replay.elapsed * 1000 / Number($('speed').value); };
setRotation(live.latest, 0);