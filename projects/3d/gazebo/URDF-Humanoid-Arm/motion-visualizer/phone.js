const $ = id => document.getElementById(id);
const token = new URLSearchParams(location.search).get('token') || '';
let socket = null, stop = null, wakeLock = null, enabled = false;
let sent = 0, windowStart = 0, windowCount = 0;

const status = text => { $('status').textContent = text; };

function send(message) {
  // Drop rather than queue when the network falls behind, keeping latency low.
  if (socket?.readyState === WebSocket.OPEN && socket.bufferedAmount < 16384) socket.send(JSON.stringify(message));
}

function publish(message, display) {
  send({...message, on: enabled});
  sent++; windowCount++;
  const now = performance.now();
  if (now - windowStart >= 500) {
    $('rate').textContent = `${Math.round(windowCount * 1000 / (now - windowStart))} Hz`;
    for (const [id, value] of Object.entries(display)) $(id).textContent = value.toFixed(3);
    $('sent').textContent = sent.toLocaleString();
    windowStart = now; windowCount = 0;
  }
}

function startOrientation() {
  if ('AbsoluteOrientationSensor' in window) {
    try {
      let quaternion = null;
      const sensor = new AbsoluteOrientationSensor({frequency: 60, referenceFrame: 'device'});
      sensor.onreading = () => { quaternion = [...sensor.quaternion]; };
      sensor.onerror = () => { quaternion = null; };
      sensor.start();
      return {get: () => quaternion, stop: () => sensor.stop()};
    } catch { /* orientation stays unavailable */ }
  }
  return {get: () => null, stop: () => {}};
}

function startAccelerometer() {
  const orientation = startOrientation();
  const emit = (t, x, y, z) => {
    if (![x, y, z].every(Number.isFinite)) return;
    const q = orientation.get();
    publish(q ? {t, a: [x, y, z], q} : {t, a: [x, y, z]}, {x, y, z});
  };
  if ('LinearAccelerationSensor' in window) {
    try {
      const sensor = new LinearAccelerationSensor({frequency: 1000, referenceFrame: 'device'});
      sensor.onreading = () => emit(sensor.timestamp, sensor.x, sensor.y, sensor.z);
      sensor.start();
      $('source').textContent = 'Accelerometer';
      return () => { sensor.stop(); orientation.stop(); };
    } catch { /* fall back to devicemotion */ }
  }
  const handler = event => { const a = event.acceleration; if (a) emit(event.timeStamp, a.x, a.y, a.z); };
  addEventListener('devicemotion', handler);
  $('source').textContent = 'devicemotion';
  return () => { removeEventListener('devicemotion', handler); orientation.stop(); };
}

async function startArCore() {
  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl', {xrCompatible: true});
  const session = await navigator.xr.requestSession('immersive-ar', {
    requiredFeatures: ['local'],
    optionalFeatures: ['dom-overlay'],
    domOverlay: {root: document.body},
  });
  document.body.classList.add('xr');
  session.updateRenderState({baseLayer: new XRWebGLLayer(session, gl)});
  const space = await session.requestReferenceSpace('local');
  const onFrame = (time, frame) => {
    session.requestAnimationFrame(onFrame);
    const pose = frame.getViewerPose(space);
    if (!pose) { status('ARCore is still locating · move the phone slowly'); return; }
    const {x, y, z} = pose.transform.position, q = pose.transform.orientation;
    // WebXR local space is Y-up with -Z forward; map it to X right, Y forward, Z up.
    publish({t: time, p: [x, -z, y], q: [q.x, q.y, q.z, q.w], xr: true}, {x, y: -z, z: y});
  };
  session.requestAnimationFrame(onFrame);
  session.addEventListener('end', () => { document.body.classList.remove('xr'); disconnect('ARCore session ended.'); });
  $('source').textContent = 'ARCore (WebXR)';
  return () => session.end().catch(() => {});
}

async function startTracking() {
  const mode = $('mode').value;
  const supported = Boolean(navigator.xr) && await navigator.xr.isSessionSupported('immersive-ar').catch(() => false);
  if (mode === 'xr' && !supported) throw Error('ARCore is unavailable here. Install Google Play Services for AR, or choose Accelerometer.');
  if (mode === 'xr' || (mode === 'auto' && supported)) return startArCore();
  return startAccelerometer();
}

function setEnabled(next) {
  enabled = next;
  send({enabled});
  $('enable').classList.toggle('on', enabled);
  $('enable').textContent = enabled ? 'ENABLED · TAP TO HOLD' : 'ENABLE';
  status(enabled ? 'Streaming · the gripper follows the phone.'
    : 'Holding · the gripper keeps its last position. Tap ENABLE to continue.');
}

async function connect() {
  if (!isSecureContext) return status('Open this page over HTTPS; Chrome blocks motion sensors otherwise.');
  socket = new WebSocket(`wss://${location.host}/ws?token=${encodeURIComponent(token)}`);
  socket.onopen = async () => {
    status('Connected · starting tracking…');
    windowStart = performance.now(); windowCount = 0;
    try { stop = await startTracking(); } catch (error) { return disconnect(error.message); }
    try { wakeLock = await navigator.wakeLock?.request('screen'); } catch { /* optional */ }
    $('enable').disabled = false;
    enabled = false; $('enable').textContent = 'ENABLE'; $('enable').classList.remove('on');
    status('Tracking · hold the phone still, then tap ENABLE.');
  };
  socket.onclose = () => { if (socket) disconnect('Disconnected from server.'); };
  socket.onerror = () => status('Could not connect. Check the link and that the server is running.');
  $('toggle').textContent = 'Disconnect'; $('toggle').classList.add('stop');
}

function disconnect(message = 'Disconnected.') {
  const current = socket; socket = null;
  enabled = false;
  current?.close();
  stop?.(); stop = null;
  wakeLock?.release(); wakeLock = null;
  $('enable').disabled = true; $('enable').classList.remove('on'); $('enable').textContent = 'ENABLE';
  $('toggle').textContent = 'Connect'; $('toggle').classList.remove('stop');
  status(message);
}

$('toggle').onclick = () => (socket ? disconnect() : connect());
$('enable').onclick = () => setEnabled(!enabled);
if (!token) status('Missing token. Open the phone link shown in the desktop viewer.');
