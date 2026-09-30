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

function quaternionAngles([x, y, z, w]) {
  const roll = Math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y));
  const pitch = Math.asin(Math.max(-1, Math.min(1, 2 * (w * y - z * x))));
  const yaw = Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z));
  return {x: roll * 180 / Math.PI, y: pitch * 180 / Math.PI, z: yaw * 180 / Math.PI};
}

function emitOrientation(t, quaternion) {
  if (!quaternion || quaternion.length !== 4 || !quaternion.every(Number.isFinite)) return;
  publish({t, q: quaternion}, quaternionAngles(quaternion));
}

async function startOrientation() {
  for (const Sensor of [window.AbsoluteOrientationSensor, window.RelativeOrientationSensor]) {
    if (!Sensor) continue;
    let sensor;
    try { sensor = new Sensor({frequency: 60, referenceFrame: 'device'}); }
    catch { continue; }
    const started = await new Promise(resolve => {
      let settled = false;
      const timer = setTimeout(() => finish(false), 2000);
      const finish = ready => { if (settled) return; settled = true; clearTimeout(timer); resolve(ready); };
      sensor.onreading = () => { emitOrientation(sensor.timestamp, [...sensor.quaternion]); finish(true); };
      sensor.onerror = () => finish(false);
      try { sensor.start(); } catch { finish(false); }
    });
    if (started) {
      $('source').textContent = Sensor.name;
      return () => sensor.stop();
    }
    sensor.stop();
  }
  throw Error('This browser did not provide a native orientation quaternion sensor.');
}

function setEnabled(next) {
  if (enabled === next) return;
  enabled = next;
  send({enabled});
  $('enable').classList.toggle('on', enabled);
  $('enable').setAttribute('aria-pressed', String(enabled));
  $('enable').textContent = enabled ? 'ENABLED · RELEASE TO HOLD' : 'PRESS & HOLD TO ENABLE';
  status(enabled ? 'Streaming · the gripper follows the phone.'
    : 'Holding · the gripper keeps its last position.');
}

async function connect() {
  if (!isSecureContext) return status('Open this page over HTTPS; Chrome blocks motion sensors otherwise.');
  socket = new WebSocket(`wss://${location.host}/ws?token=${encodeURIComponent(token)}`);
  socket.onopen = async () => {
    status('Connected · starting tracking…');
    windowStart = performance.now(); windowCount = 0;
    try { stop = await startOrientation(); } catch (error) { return disconnect(error.message); }
    try { wakeLock = await navigator.wakeLock?.request('screen'); } catch { /* optional */ }
    $('enable').disabled = false;
    enabled = false; $('enable').textContent = 'PRESS & HOLD TO ENABLE'; $('enable').classList.remove('on');
    $('enable').setAttribute('aria-pressed', 'false');
    status('Orientation ready · press and hold ENABLE, then tilt the phone.');
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
  $('enable').disabled = true; $('enable').classList.remove('on'); $('enable').textContent = 'PRESS & HOLD TO ENABLE';
  $('enable').setAttribute('aria-pressed', 'false');
  $('toggle').textContent = 'Connect'; $('toggle').classList.remove('stop');
  status(message);
}

$('toggle').onclick = () => (socket ? disconnect() : connect());
$('enable').addEventListener('pointerdown', event => {
  if ($('enable').disabled) return;
  event.preventDefault();
  $('enable').setPointerCapture(event.pointerId);
  setEnabled(true);
});
$('enable').addEventListener('pointerup', () => setEnabled(false));
$('enable').addEventListener('pointercancel', () => setEnabled(false));
$('enable').addEventListener('lostpointercapture', () => setEnabled(false));
$('enable').addEventListener('keydown', event => {
  if ((event.key === ' ' || event.key === 'Enter') && !event.repeat) { event.preventDefault(); setEnabled(true); }
});
$('enable').addEventListener('keyup', event => {
  if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); setEnabled(false); }
});
addEventListener('blur', () => setEnabled(false));
document.addEventListener('visibilitychange', () => { if (document.hidden) setEnabled(false); });
if (!token) status('Missing token. Open the phone link shown in the desktop viewer.');
