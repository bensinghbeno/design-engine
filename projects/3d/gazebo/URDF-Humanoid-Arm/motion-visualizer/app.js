import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {createLiveEstimator, createPoseTracker, estimateTrajectory, parseSensorCsv} from './motion.js';

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
let recording = null, mode = 'csv';
const replay = {playing: false, elapsed: 0, startedAt: 0, frame: 0};
const LIVE_POINTS = 1500;
const live = {socket: null, estimator: createLiveEstimator(), tracker: createPoseTracker(), xr: false, enabled: false,
  phone: null, phones: 0, last: null, start: null,
  points: new Float32Array(LIVE_POINTS * 3), length: 0, latest: null, elapsed: 0, samples: 0, rateStart: 0, rateCount: 0};
const liveGeometry = new THREE.BufferGeometry();
liveGeometry.setAttribute('position', new THREE.BufferAttribute(live.points, 3));
liveGeometry.setDrawRange(0, 0);
const liveTrail = new THREE.Line(liveGeometry, new THREE.LineBasicMaterial({color: 0x55f0bc}));
liveTrail.frustumCulled = false; liveTrail.visible = false; scene.add(liveTrail);

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
  $('progress').style.width = mode === 'csv' && recording ? `${100 * elapsed / recording.time.at(-1)}%` : '0';
}
function fit() {
  const points = mode === 'live'
    ? [new THREE.Vector3(-0.15, -0.15, -0.15), new THREE.Vector3(0.15, 0.15, 0.15),
      ...Array.from({length: live.length}, (_, index) => new THREE.Vector3().fromArray(live.points, index * 3))]
    : recording?.position.map(point => new THREE.Vector3(...point));
  if (!points) return;
  const bounds = new THREE.Box3().setFromPoints(points);
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
function animate(now) { updateReplay(now); updateLive(now); controls.update(); renderer.render(scene, camera); }
renderer.setAnimationLoop(animate);

function liveState(text) { $('live-state').textContent = text; }
function resetLive() {
  live.estimator.reset(); live.tracker.reset();
  live.last = null; live.start = null; live.length = 0; live.latest = [0, 0, 0]; live.elapsed = 0;
  liveGeometry.setDrawRange(0, 0);
}
function onSample({phone, t, a, p, q, xr, on}) {
  const seconds = t / 1000;
  // A different phone or a restarted page resets its clock, so start a fresh estimate.
  if (phone !== live.phone || (live.last !== null && seconds <= live.last)) { resetLive(); live.phone = phone; }
  live.last = seconds;
  if (live.start === null) live.start = seconds;
  live.xr = Boolean(xr);
  if (on !== undefined && on !== live.enabled) setClutch(on);
  const point = xr ? live.tracker.update(p, q) : live.estimator.update(seconds, a, q);
  if (live.length === LIVE_POINTS) { live.points.copyWithin(0, 3); live.length--; }
  live.points.set(point, live.length * 3); live.length++;
  live.latest = point; live.elapsed = seconds - live.start; live.samples++; live.rateCount++;
}
function setClutch(enabled) {
  live.enabled = enabled;
  if (enabled) { live.estimator.resume(); live.tracker.resume(); }
  else { live.estimator.hold(); live.tracker.hold(); }
}
function updateLive(now) {
  if (mode !== 'live' || !live.latest) return;
  setPosition(live.latest, live.elapsed);
  liveGeometry.attributes.position.needsUpdate = true; liveGeometry.setDrawRange(0, live.length);
  if (now - live.rateStart >= 1000) {
    $('live-rate').textContent = live.rateCount ? `${Math.round(live.rateCount * 1000 / (now - live.rateStart))} Hz` : '—';
    $('samples').textContent = live.samples.toLocaleString();
    $('bias').textContent = live.xr ? 'ARCore · measured'
      : live.estimator.bias?.map(value => value.toFixed(3)).join(' / ') ?? 'calibrating…';
    $('travel').textContent = live.xr ? 'ARCore (WebXR)'
      : live.estimator.worldFrame ? 'Accelerometer · levelled' : 'Accelerometer · phone frame';
    live.rateStart = now; live.rateCount = 0;
  }
  if (!live.socket || !live.phones || !live.samples) return;
  if (!live.enabled) return liveState('Connected · holding (phone ENABLE is off)');
  if (live.xr) return liveState('Streaming · ARCore');
  liveState(live.estimator.calibrating ? 'Calibrating · keep phone still'
    : live.estimator.still ? 'Streaming · holding' : 'Streaming · moving');
}
function showSession(session) {
  live.phones = session.phones;
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
  if (route) route.visible = csv && $('show-path').checked;
  if (trail) trail.visible = csv;
  liveTrail.visible = !csv;
  $('travel').textContent = csv && recording ? `${recording.pathLength.toFixed(3)} m` : '—';
  if (csv) {
    disconnect();
    $('travel-label').textContent = 'Estimated travel'; $('bias-label').textContent = 'Startup bias X/Y/Z';
    if (recording) { restart(false); $('duration').textContent = `${recording.time.at(-1).toFixed(2)} s`; $('summary-duration').textContent = `${recording.time.at(-1).toFixed(2)} s`; $('samples').textContent = recording.time.length.toLocaleString(); $('bias').textContent = recording.bias.map(value => value.toFixed(3)).join(' / '); }
    $('status').textContent = 'Recording mode · press Play to replay the estimated path.';
  } else {
    $('travel-label').textContent = 'Tracking'; $('bias-label').textContent = 'Sensor offset X/Y/Z';
    replay.playing = false; $('play').textContent = 'Play';
    resetLive(); live.samples = 0; live.enabled = false; setPosition(live.latest, 0);
    $('duration').textContent = 'LIVE'; $('summary-duration').textContent = 'LIVE'; $('samples').textContent = '0'; $('bias').textContent = '—';
    $('status').textContent = 'Live mode · tap ENABLE on the phone to move the gripper; tap again to hold it in place.';
    if (!live.socket) guard(connect);
    fit();
  }
}

function replayPoses(poses, quaternions, enabled) {
  const tracker = createPoseTracker();
  let held = true;
  const position = poses.map((pose, index) => {
    const on = enabled ? enabled[index] : true;
    if (on !== held) { held = on; on ? tracker.resume() : tracker.hold(); }
    return pose && on ? tracker.update(pose, quaternions?.[index]) : tracker.position;
  });
  const pathLength = position.slice(1).reduce((total, point, index) => total
    + Math.hypot(...point.map((value, axis) => value - position[index][axis])), 0);
  return {position, bias: [0, 0, 0], pathLength};
}

async function loadCsv(text, name) {
  const parsed = parseSensorCsv(text);
  const {time, acceleration} = parsed;
  // ARCore sessions carry measured poses, so replay those instead of integrating acceleration.
  const estimate = parsed.position
    ? replayPoses(parsed.position, parsed.quaternion, parsed.enabled)
    : estimateTrajectory(time, acceleration);
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
async function loadServerCsv(url, name) {
  $('status').textContent = `Loading ${name}…`;
  const response = await fetch(url);
  if (!response.ok) throw Error(await response.text());
  await loadCsv(await response.text(), name);
}
const loadDefault = () => loadServerCsv('/api/motion', 'sensors/Accelerometer.csv');
async function guard(action) { try { await action(); } catch (error) { $('status').textContent = error.message; console.error(error); } }

$('load-default').onclick = () => guard(loadDefault);
$('load-live').onclick = () => guard(() => loadServerCsv('/api/live-latest', 'sensors/live-latest.csv'));
$('upload').onchange = () => guard(async () => { const file = $('upload').files[0]; if (!file) return; if (file.size > 10e6) throw Error('CSV exceeds 10 MB.'); await loadCsv(await file.text(), file.name); });
$('play').onclick = togglePlay;
$('restart').onclick = () => restart(false);
$('fit').onclick = fit;
$('mode-csv').onclick = () => setMode('csv');
$('mode-live').onclick = () => setMode('live');
$('connect').onclick = () => guard(connect);
$('server').value = location.host;
$('server').onkeydown = event => { if (event.key === 'Enter' && !live.socket) guard(connect); };
$('zero').onclick = () => { resetLive(); fit(); };
$('show-path').onchange = () => { if (route) route.visible = $('show-path').checked; };
$('speed').onchange = () => { if (replay.playing) replay.startedAt = performance.now() - replay.elapsed * 1000 / Number($('speed').value); };
await guard(loadDefault);