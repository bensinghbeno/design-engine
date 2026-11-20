const $ = id => document.getElementById(id);
const token = new URLSearchParams(location.search).get('token') || '';
let socket = null, motionHandler = null, orientationHandler = null, wakeLock = null;
let latestMotion = null, latestOrientation = null, absoluteQuaternion = null;
let samples = 0, rateSamples = 0, rateStart = 0;
const clean = values => values?.map(value => Number.isFinite(value) ? value : null) ?? [null, null, null];
const text = values => values?.map(value => value === null ? '—' : value.toFixed(2)).join(' / ') ?? '—';

function orientationQuaternion(alpha, beta, gamma) {
  if (![alpha, beta, gamma].every(Number.isFinite)) return null;
  const a = alpha * Math.PI / 360, b = beta * Math.PI / 360, g = -gamma * Math.PI / 360;
  const c1 = Math.cos(b), c2 = Math.cos(a), c3 = Math.cos(g);
  const s1 = Math.sin(b), s2 = Math.sin(a), s3 = Math.sin(g);
  return [
    s1 * c2 * c3 + c1 * s2 * s3,
    c1 * s2 * c3 - s1 * c2 * s3,
    c1 * c2 * s3 - s1 * s2 * c3,
    c1 * c2 * c3 + s1 * s2 * s3,
  ];
}

function sendSample(time) {
  const orientation = latestOrientation || [null, null, null];
  const quaternion = absoluteQuaternion || orientationQuaternion(...orientation) || [null, null, null, null];
  const packet = {
    t: time,
    acceleration: clean(latestMotion?.acceleration),
    accelerationIncludingGravity: clean(latestMotion?.accelerationIncludingGravity),
    rotationRate: clean(latestMotion?.rotationRate),
    orientation: clean(orientation),
    quaternion,
  };
  if (socket?.readyState === WebSocket.OPEN && socket.bufferedAmount < 32768) {
    socket.send(JSON.stringify(packet)); samples++; rateSamples++;
  }
  $('accel').textContent = text(packet.acceleration);
  $('gravity').textContent = text(packet.accelerationIncludingGravity);
  $('rotation').textContent = text(packet.rotationRate);
  $('orientation').textContent = text(packet.orientation);
  $('quaternion').textContent = text(packet.quaternion);
  const now = performance.now();
  if (now - rateStart >= 1000) {
    $('rate').textContent = `${Math.round(rateSamples * 1000 / (now - rateStart))} Hz`;
    $('sent').textContent = samples.toLocaleString();
    rateSamples = 0; rateStart = now;
  }
}

async function requestPermissions() {
  for (const SensorEvent of [window.DeviceMotionEvent, window.DeviceOrientationEvent]) {
    if (typeof SensorEvent?.requestPermission === 'function') {
      const permission = await SensorEvent.requestPermission();
      if (permission !== 'granted') throw Error('Sensor permission was not granted.');
    }
  }
}

function startOrientationQuaternion() {
  if (!window.AbsoluteOrientationSensor) return;
  try {
    const sensor = new AbsoluteOrientationSensor({frequency: 60, referenceFrame: 'device'});
    sensor.onreading = () => { absoluteQuaternion = [...sensor.quaternion]; };
    sensor.onerror = () => { absoluteQuaternion = null; };
    sensor.start();
    return () => sensor.stop();
  } catch { absoluteQuaternion = null; }
}

async function start() {
  if (!isSecureContext) throw Error('Open this page over HTTPS; Chrome blocks sensor access otherwise.');
  await requestPermissions();
  latestMotion = null; latestOrientation = null; absoluteQuaternion = null;
  socket = new WebSocket(`wss://${location.host}/phone?token=${encodeURIComponent(token)}`);
  socket.onopen = async () => {
    $('connection').textContent = 'Online'; $('status').textContent = 'Streaming phone sensor events.';
    rateStart = performance.now(); samples = 0; rateSamples = 0;
    const stopQuaternion = startOrientationQuaternion();
    motionHandler = event => {
      latestMotion = {
        acceleration: clean([event.acceleration?.x, event.acceleration?.y, event.acceleration?.z]),
        accelerationIncludingGravity: clean([event.accelerationIncludingGravity?.x, event.accelerationIncludingGravity?.y, event.accelerationIncludingGravity?.z]),
        rotationRate: clean([event.rotationRate?.alpha, event.rotationRate?.beta, event.rotationRate?.gamma]),
      };
      sendSample(event.timeStamp);
    };
    orientationHandler = event => {
      latestOrientation = [event.alpha, event.beta, event.gamma].map(value => Number.isFinite(value) ? value : null);
      sendSample(event.timeStamp);
    };
    addEventListener('devicemotion', motionHandler);
    addEventListener('deviceorientation', orientationHandler);
    try { wakeLock = await navigator.wakeLock?.request('screen'); } catch { /* optional */ }
    stopQuaternionSensor = stopQuaternion;
  };
  socket.onclose = () => { if (socket) stop('Connection closed.'); };
  socket.onerror = () => { $('status').textContent = 'Could not connect. Check the link and server.'; };
  $('toggle').textContent = 'Stop streaming'; $('toggle').classList.add('stop');
}

let stopQuaternionSensor = null;
function stop(message = 'Stopped streaming.') {
  const current = socket; socket = null; current?.close();
  if (motionHandler) removeEventListener('devicemotion', motionHandler);
  if (orientationHandler) removeEventListener('deviceorientation', orientationHandler);
  motionHandler = null; orientationHandler = null;
  stopQuaternionSensor?.(); stopQuaternionSensor = null;
  wakeLock?.release(); wakeLock = null;
  $('connection').textContent = 'Offline'; $('toggle').textContent = 'Start streaming'; $('toggle').classList.remove('stop');
  $('status').textContent = message;
}

$('toggle').onclick = () => socket ? stop() : start().catch(error => { $('status').textContent = error.message; });
addEventListener('blur', () => { if (socket) stop('Stopped because the phone page lost focus.'); });
document.addEventListener('visibilitychange', () => { if (document.hidden && socket) stop('Stopped because the phone page went to the background.'); });
if (!token) $('status').textContent = 'Missing access token. Open this page from the dashboard link.';
