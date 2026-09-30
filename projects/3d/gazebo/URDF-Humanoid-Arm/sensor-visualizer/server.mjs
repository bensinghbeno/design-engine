import http from 'node:http';
import https from 'node:https';
import os from 'node:os';
import {randomBytes} from 'node:crypto';
import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {acceptWebSocket} from '../motion-visualizer/websocket.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);
const viewerPort = Number(process.env.VIEWER_PORT || 8770);
const phonePort = Number(process.env.PHONE_PORT || 8771);
const lanIp = process.env.LAN_IP || Object.values(os.networkInterfaces()).flat()
  .find(address => address?.family === 'IPv4' && !address.internal)?.address || '127.0.0.1';
const stateDir = path.join(here, '.state');
const certDir = path.join(here, '.certs');
await mkdir(stateDir, {recursive: true});
let token;
try { token = (await readFile(path.join(stateDir, 'token'), 'utf8')).trim(); } catch { token = ''; }
if (!/^[0-9a-f]{32}$/.test(token)) {
  token = randomBytes(16).toString('hex');
  await writeFile(path.join(stateDir, 'token'), `${token}\n`, {mode: 0o600});
}
const phoneUrl = `https://${lanIp}:${phonePort}/?token=${token}`;
const localHost = host => host === `127.0.0.1:${viewerPort}` || host === `localhost:${viewerPort}`;
const viewers = new Set(), phones = new Set();
let latest = null, latestRate = 0, rateStart = 0, rateSamples = 0;
const staticTypes = new Map([
  ['index.html', 'text/html'], ['app.js', 'text/javascript'], ['style.css', 'text/css'],
]);
const phoneTypes = new Map([['', ['phone.html', 'text/html']], ['phone.html', ['phone.html', 'text/html']], ['phone.js', ['phone.js', 'text/javascript']]]);

function broadcast(object) {
  const text = JSON.stringify(object);
  for (const viewer of viewers) viewer.send(text);
}
function sessionState() { return {type: 'state', phoneUrl, phoneCount: phones.size, latestRate}; }
function validSensorPacket(packet) {
  const vector = value => Array.isArray(value) && value.length === 3 && value.every(item => item === null || Number.isFinite(item));
  return packet && Number.isFinite(packet.t)
    && vector(packet.acceleration) && vector(packet.accelerationIncludingGravity)
    && vector(packet.rotationRate) && vector(packet.orientation)
    && Array.isArray(packet.quaternion) && packet.quaternion.length === 4
    && packet.quaternion.every(item => item === null || Number.isFinite(item));
}

const key = await readFile(path.join(certDir, 'key.pem'));
const cert = await readFile(path.join(certDir, 'cert.pem'));

const viewerServer = http.createServer(async (request, response) => {
  const send = (status, type, content) => {
    response.writeHead(status, {'Content-Type': type, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'});
    response.end(content);
  };
  if (request.method !== 'GET' || !localHost(request.headers.host)) return send(403, 'text/plain', 'Local dashboard only');
  const route = new URL(request.url, `http://127.0.0.1:${viewerPort}`).pathname.slice(1) || 'index.html';
  if (!staticTypes.has(route)) return send(404, 'text/plain', 'Not found');
  try { send(200, staticTypes.get(route), await readFile(path.join(here, route))); }
  catch { send(500, 'text/plain', 'Could not read dashboard assets'); }
});
viewerServer.on('upgrade', (request, socket) => {
  const host = request.headers.host;
  if (!localHost(host) || request.headers.origin !== `http://${host}` || request.url !== '/view') {
    return socket.end('HTTP/1.1 403 Forbidden\r\n\r\n');
  }
  const viewer = acceptWebSocket(request, socket);
  if (!viewer) return;
  viewers.add(viewer);
  viewer.send(JSON.stringify(sessionState()));
  if (latest) viewer.send(JSON.stringify(latest));
  viewer.on('close', () => viewers.delete(viewer));
});

const phoneServer = https.createServer({key, cert}, async (request, response) => {
  const route = new URL(request.url, `https://phone:${phonePort}`).pathname.slice(1);
  const item = phoneTypes.get(route);
  if (request.method !== 'GET' || !item) {
    response.writeHead(404, {'Content-Type': 'text/plain'}); response.end('Not found'); return;
  }
  try {
    response.writeHead(200, {'Content-Type': item[1], 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'});
    response.end(await readFile(path.join(here, item[0])));
  } catch { response.writeHead(500); response.end('Could not read phone client'); }
});
phoneServer.on('upgrade', (request, socket) => {
  const url = new URL(request.url, `https://phone:${phonePort}`);
  const expectedOrigin = `https://${request.headers.host}`;
  if (url.pathname !== '/phone' || url.searchParams.get('token') !== token || request.headers.origin !== expectedOrigin) {
    return socket.end('HTTP/1.1 403 Forbidden\r\n\r\n');
  }
  const phone = acceptWebSocket(request, socket);
  if (!phone) return;
  phones.add(phone);
  broadcast(sessionState());
  phone.on('message', text => {
    let packet;
    try { packet = JSON.parse(text); } catch { return; }
    if (!validSensorPacket(packet)) return;
    latest = {type: 'sample', ...packet};
    rateSamples++;
    const now = Date.now();
    if (now - rateStart >= 1000) { latestRate = Math.round(rateSamples * 1000 / (now - rateStart)); rateSamples = 0; rateStart = now; }
    broadcast(latest);
  });
  phone.on('close', () => { phones.delete(phone); broadcast(sessionState()); });
});

for (const [server, port, host] of [[viewerServer, viewerPort, '127.0.0.1'], [phoneServer, phonePort, '0.0.0.0']]) {
  server.on('error', error => { console.error(error.message); process.exitCode = 1; });
  server.listen(port, host, () => console.log(`Listening on ${host}:${port}`));
}
console.log(`Sensor dashboard: http://127.0.0.1:${viewerPort}`);
console.log(`Phone link: ${phoneUrl}`);
console.log('The phone and computer must be on the same Wi-Fi. Accept the certificate warning in Chrome.');
