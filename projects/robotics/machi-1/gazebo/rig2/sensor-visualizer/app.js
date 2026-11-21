const $ = id => document.getElementById(id);
const groups = [
  {title:'Linear acceleration', unit:'m/s²', color:'lime', scale:10, rows:[['acceleration',0,'X'],['acceleration',1,'Y'],['acceleration',2,'Z']]},
  {title:'Acceleration including gravity', unit:'m/s²', color:'cyan', scale:20, rows:[['accelerationIncludingGravity',0,'X'],['accelerationIncludingGravity',1,'Y'],['accelerationIncludingGravity',2,'Z']]},
  {title:'Rotation rate', unit:'°/s', color:'coral', scale:500, rows:[['rotationRate',0,'α'],['rotationRate',1,'β'],['rotationRate',2,'γ']]},
  {title:'Orientation', unit:'°', color:'violet', scale:180, rows:[['orientation',0,'α',360],['orientation',1,'β'],['orientation',2,'γ']]},
  {title:'Orientation quaternion', unit:'', color:'lime', scale:1, rows:[['quaternion',0,'qx'],['quaternion',1,'qy'],['quaternion',2,'qz'],['quaternion',3,'qw']]},
  {title:'Integrated velocity · estimated', unit:'m/s', color:'cyan', scale:5, rows:[['velocity',0,'X'],['velocity',1,'Y'],['velocity',2,'Z']]},
  {title:'Integrated position · estimated', unit:'m', color:'coral', scale:5, rows:[['position',0,'X'],['position',1,'Y'],['position',2,'Z']]},
];
const chartElements = new Map();
const latest = {packet:null, receivedAt:0, count:0, rate:0, rateStart:performance.now(), rateCount:0};
const integration = {lastTime:null, calibrationStart:null, bias:[0,0,0], biasSum:[0,0,0], biasCount:0, calibrated:false, velocity:[0,0,0], position:[0,0,0]};
let viewerSocket = null, phoneUrl = '', sessionToken = '';

function buildCharts() {
  $('charts').replaceChildren(...groups.map((group, groupIndex) => {
    const panel = document.createElement('section'); panel.className = 'sensor-group';
    const heading = document.createElement('div'); heading.className = 'group-head';
    const title = document.createElement('h3'); title.textContent = group.title;
    const unit = document.createElement('span'); unit.textContent = group.unit;
    heading.append(title, unit); panel.append(heading);
    const rows = group.rows.map(([key, axis, label, limit], rowIndex) => {
      const row = document.createElement('div'); row.className = 'bar-row';
      const axisLabel = document.createElement('span'); axisLabel.className = 'bar-label'; axisLabel.textContent = label;
      const track = document.createElement('div'); track.className = `bar-track${group.title === 'Orientation' && axis === 0 ? '' : ' signed'}`;
      const fill = document.createElement('i'); fill.className = `bar-fill ${group.color}`; track.append(fill);
      const value = document.createElement('output'); value.className = 'bar-value'; value.textContent = '—';
      row.append(axisLabel, track, value); panel.append(row);
      return {key, axis, limit:limit ?? group.scale, fill, value, unit:group.unit};
    });
    chartElements.set(groupIndex, rows);
    return panel;
  }));
}

function resetIntegration() {
  integration.lastTime = null; integration.calibrationStart = null; integration.bias = [0,0,0]; integration.biasSum = [0,0,0];
  integration.biasCount = 0; integration.calibrated = false;
  integration.velocity = [0,0,0]; integration.position = [0,0,0];
}

function estimatePosition(packet) {
  const acceleration = packet.acceleration;
  if (!acceleration?.every(Number.isFinite)) return;
  if (integration.calibrationStart === null) integration.calibrationStart = packet.t;
  if (integration.lastTime === null) integration.lastTime = packet.t;
  const dt = (packet.t - integration.lastTime) / 1000;
  integration.lastTime = packet.t;
  if (!integration.calibrated) {
    for (let axis=0; axis<3; axis++) integration.biasSum[axis] += acceleration[axis];
    integration.biasCount++;
    if (packet.t - integration.calibrationStart >= 500 && integration.biasCount >= 5) {
      integration.bias = integration.biasSum.map(value => value / integration.biasCount);
      integration.calibrated = true;
      integration.lastTime = packet.t;
    }
    return;
  }
  if (dt <= 0 || dt > 0.25) return;
  const corrected = acceleration.map((value, axis) => value - integration.bias[axis]);
  if (Math.hypot(...corrected) < 0.12) integration.velocity = [0,0,0];
  for (let axis=0; axis<3; axis++) {
    integration.velocity[axis] += corrected[axis] * dt;
    integration.position[axis] += integration.velocity[axis] * dt;
  }
}

function displayValue(value, unit) {
  if (!Number.isFinite(value)) return '—';
  const digits = Math.abs(value) < 10 ? 2 : 1;
  return `${value.toFixed(digits)}${unit ? ` ${unit}` : ''}`;
}

function updateBars(packet) {
  for (const rows of chartElements.values()) for (const row of rows) {
    let value = row.key === 'velocity' ? integration.velocity[row.axis]
      : row.key === 'position' ? integration.position[row.axis]
      : packet[row.key]?.[row.axis];
    if (!Number.isFinite(value)) { row.fill.style.width='0'; row.value.textContent='—'; continue; }
    let barValue = value;
    if (row.key === 'orientation' && row.axis === 0) barValue = ((value + 180) % 360) - 180;
    const width = Math.min(50, Math.abs(barValue) / row.limit * 50);
    row.fill.style.left = barValue < 0 ? `${50-width}%` : '50%';
    row.fill.style.width = `${width}%`;
    row.value.textContent = displayValue(value, row.unit);
  }
}

function setConnected(isConnected) {
  $('live-dot').classList.toggle('on', isConnected);
  $('status').textContent = isConnected ? 'Phone connected · receiving sensor events' : 'Waiting for a phone';
}

function connectViewer() {
  viewerSocket = new WebSocket(`ws://${location.host}/view`);
  viewerSocket.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.type === 'state') {
      phoneUrl = message.phoneUrl; sessionToken = new URL(phoneUrl).searchParams.get('token') || '';
      $('phone-link').textContent = phoneUrl; $('phone-count').textContent = String(message.phoneCount);
      $('sample-rate').textContent = message.latestRate ? `${message.latestRate} Hz` : '—';
      setConnected(message.phoneCount > 0);
    } else if (message.type === 'sample') {
      latest.packet = message; latest.receivedAt = Date.now(); latest.count++; latest.rateCount++;
      estimatePosition(message);
    }
  };
  viewerSocket.onclose = () => { setConnected(false); setTimeout(connectViewer, 1200); };
  viewerSocket.onerror = () => viewerSocket.close();
}

function render() {
  const now = performance.now();
  $('sample-count').textContent = latest.count.toLocaleString();
  if (latest.packet) {
    updateBars(latest.packet);
    $('packet-age').textContent = `${((Date.now()-latest.receivedAt)/1000).toFixed(1)} s ago`;
    $('sample-time').textContent = `Phone timestamp ${latest.packet.t.toFixed(0)} ms`;
  }
  if (now - latest.rateStart >= 1000) {
    latest.rate = Math.round(latest.rateCount * 1000 / (now-latest.rateStart));
    latest.rateCount=0; latest.rateStart=now;
    $('sample-rate').textContent = latest.rate ? `${latest.rate} Hz` : '—';
  }
  requestAnimationFrame(render);
}

buildCharts();
$('copy-link').onclick = async () => {
  if (!phoneUrl) return;
  try { await navigator.clipboard.writeText(phoneUrl); $('copy-link').textContent='Copied'; setTimeout(()=> $('copy-link').textContent='Copy link',1200); }
  catch { $('status').textContent='Select the phone link to copy it.'; }
};
$('recenter').onclick = () => { resetIntegration(); $('status').textContent='Position integrator reset · 0.5 s still calibration'; };
connectViewer(); render();
