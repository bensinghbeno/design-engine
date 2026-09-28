import http from 'node:http';
import os from 'node:os';
import {randomBytes} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {Worker} from 'node:worker_threads';
import path from 'node:path';
import {acceptWebSocket} from './websocket.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT || 8766);
const streamPort = Number(process.env.STREAM_PORT || 8767);
const lanIp = process.env.LAN_IP || Object.values(os.networkInterfaces()).flat()
  .find(address => address?.family === 'IPv4' && !address.internal)?.address || '127.0.0.1';
const token = randomBytes(16).toString('hex');
const phoneUrl = `https://${lanIp}:${streamPort}/?token=${token}`;
const publicFiles = new Set(['index.html', 'app.js', 'motion.js', 'style.css']);
const vendorFiles = new Map([
  ['vendor/three.module.js', 'build/three.module.js'],
  ['vendor/three.core.js', 'build/three.core.js'],
  ['vendor/OrbitControls.js', 'examples/jsm/controls/OrbitControls.js'],
]);
const threeRoot = path.join(here, '../workspace-viewer/node_modules/three');
const viewers = new Set(), phones = new Set();
let streamState = {listening: false, error: ''};

const localHost = host => host === `127.0.0.1:${port}` || host === `localhost:${port}`;
const broadcast = message => { const text = JSON.stringify(message); for (const viewer of viewers) viewer.send(text); };
const session = () => ({phoneUrl, phones: phones.size, ...streamState});

const stream = new Worker(new URL('./stream-server.mjs', import.meta.url),
  {workerData: {port: streamPort, token, certDir: path.join(here, '.certs')}});
stream.on('message', message => {
  if (message.type === 'sample') return broadcast(message);
  if (message.type === 'phone') message.connected ? phones.add(message.phone) : phones.delete(message.phone);
  if (message.type === 'listening') streamState = {listening: true, error: ''};
  if (message.type === 'error') {
    streamState = {listening: false, error: message.message};
    console.error(`Phone stream unavailable: ${message.message}`);
  }
  broadcast({type: 'session', ...session()});
});
stream.on('error', error => { streamState = {listening: false, error: error.message}; console.error(error); });

const server = http.createServer(async (request, response) => {
  const send = (status, type, body) => {
    response.writeHead(status, {'Content-Type': type, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'});
    response.end(body);
  };
  if (request.method !== 'GET') return send(405, 'text/plain', 'GET only');
  if (!localHost(request.headers.host)) return send(403, 'text/plain', 'Local access only');
  const route = new URL(request.url, `http://127.0.0.1:${port}`).pathname.slice(1) || 'index.html';
  try {
    if (route === 'api/motion') return send(200, 'text/csv', await readFile(path.join(here, '../sensors/Accelerometer.csv')));
    if (route === 'api/session') return send(200, 'application/json', JSON.stringify(session()));
    let file;
    if (publicFiles.has(route)) file = path.join(here, route);
    else if (vendorFiles.has(route)) file = path.join(threeRoot, vendorFiles.get(route));
    else return send(404, 'text/plain', 'Not found');
    const type = route.endsWith('.html') ? 'text/html' : route.endsWith('.css') ? 'text/css' : 'text/javascript';
    return send(200, type, await readFile(file));
  } catch (error) {
    return send(500, 'text/plain', `Could not load motion visualizer: ${error.message}`);
  }
});

server.on('upgrade', (request, socket) => {
  const {host, origin} = request.headers;
  // Origin check stops other websites open in the desktop browser from reading the stream.
  if (!localHost(host) || origin !== `http://${host}` || new URL(request.url, 'http://local').pathname !== '/ws') {
    return socket.end('HTTP/1.1 403 Forbidden\r\n\r\n');
  }
  const viewer = acceptWebSocket(request, socket);
  if (!viewer) return;
  viewers.add(viewer);
  viewer.send(JSON.stringify({type: 'session', ...session()}));
  viewer.on('close', () => viewers.delete(viewer));
});

server.on('error', error => { console.error(error.message); process.exit(1); });
server.listen(port, '127.0.0.1', () => console.log(`Motion visualizer: http://127.0.0.1:${port}\n`
  + `Phone link (Chrome on Pixel, same Wi-Fi): ${phoneUrl}\nCtrl-C to stop. Gazebo is not required.`));
