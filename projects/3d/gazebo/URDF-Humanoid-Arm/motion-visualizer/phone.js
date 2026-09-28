const $ = id => document.getElementById(id);
const token = new URLSearchParams(location.search).get('token') || '';
let socket = null, stopSensor = null, wakeLock = null, sent = 0, windowStart = 0, windowCount = 0;

function status(text) { $('status').textContent = text; }

function publish(t, x, y, z) {
  if (![x, y, z].every(Number.isFinite)) return;
  // Drop rather than queue when the network falls behind, keeping latency low.
  if (socket?.readyState === WebSocket.OPEN && socket.bufferedAmount < 16384) {
    socket.send(JSON.stringify({t, a: [x, y, z]}));
    sent++;
  }
  windowCount++;
  const now = performance.now();
  if (now - windowStart >= 1000) {
    $('rate').textContent = `${Math.round(windowCount * 1000 / (now - windowStart))} Hz`;
    $('x').textContent = x.toFixed(3); $('y').textContent = y.toFixed(3); $('z').textContent = z.toFixed(3);
    $('sent').textContent = sent.toLocaleString();
    windowStart = now; windowCount = 0;
  }
}

function startDeviceMotion() {
  const handler = event => {
    const a = event.acceleration;
    if (a) publish(event.timeStamp, a.x, a.y, a.z);
  };
  addEventListener('devicemotion', handler);
  $('source').textContent = 'devicemotion';
  return () => removeEventListener('devicemotion', handler);
}

function startSensor() {
  if (!('LinearAccelerationSensor' in window)) return Promise.resolve(startDeviceMotion());
  return new Promise(resolve => {
    let sensor;
    try { sensor = new LinearAccelerationSensor({frequency: 1000, referenceFrame: 'device'}); }
    catch { return resolve(startDeviceMotion()); }
    sensor.onreading = () => publish(sensor.timestamp, sensor.x, sensor.y, sensor.z);
    sensor.onerror = () => { sensor.stop(); resolve(startDeviceMotion()); };
    sensor.onactivate = () => { $('source').textContent = 'Generic Sensor'; resolve(() => sensor.stop()); };
    sensor.start();
  });
}

async function start() {
  if (!isSecureContext) return status('Open this page over HTTPS; Chrome blocks motion sensors otherwise.');
  socket = new WebSocket(`wss://${location.host}/ws?token=${encodeURIComponent(token)}`);
  socket.onopen = async () => {
    status('Streaming · keep still for the first half second to calibrate.');
    windowStart = performance.now(); windowCount = 0;
    stopSensor = await startSensor();
    try { wakeLock = await navigator.wakeLock?.request('screen'); } catch { /* optional */ }
  };
  socket.onclose = () => { if (socket) stop('Disconnected from server.'); };
  socket.onerror = () => status('Could not connect. Check the token link and that the server is running.');
  $('toggle').textContent = 'Stop streaming'; $('toggle').classList.add('stop');
}

function stop(message = 'Stopped.') {
  const current = socket; socket = null;
  current?.close();
  stopSensor?.(); stopSensor = null;
  wakeLock?.release(); wakeLock = null;
  $('toggle').textContent = 'Start streaming'; $('toggle').classList.remove('stop');
  status(message);
}

$('toggle').onclick = () => (socket ? stop() : start());
if (!token) status('Missing token. Open the phone link shown in the desktop viewer.');
