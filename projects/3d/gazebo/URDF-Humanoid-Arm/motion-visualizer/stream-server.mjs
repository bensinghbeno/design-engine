import https from 'node:https';
import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {timingSafeEqual} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parentPort, workerData} from 'node:worker_threads';
import {acceptWebSocket} from './websocket.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const {port, token, certDir, sensorsDir} = workerData;
const pages = new Map([['', 'phone.html'], ['phone.html', 'phone.html'], ['phone.js', 'phone.js']]);
const MAX_RECORDED = 500000;
let nextPhone = 1;

function validToken(candidate) {
  const expected = Buffer.from(token), actual = Buffer.from(candidate || '');
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

const triple = value => Array.isArray(value) && value.length === 3 && value.every(Number.isFinite);

function validSample(sample) {
  if (!sample || !Number.isFinite(sample.t)) return false;
  if (!triple(sample.a ?? sample.p)) return false;
  if (sample.q !== undefined && !(Array.isArray(sample.q) && sample.q.length === 4 && sample.q.every(Number.isFinite))) return false;
  return true;
}

// Sensor Logger's columns plus optional orientation/pose, so saved sessions load through the CSV path.
async function saveSession(phone, samples) {
  const start = samples[0].t;
  const hasQuaternion = samples.some(sample => sample.q);
  const hasPose = samples.some(sample => sample.p);
  const header = ['time', 'seconds_elapsed', 'z', 'y', 'x',
    ...(hasQuaternion ? ['qx', 'qy', 'qz', 'qw'] : []), ...(hasPose ? ['px', 'py', 'pz'] : []), 'enabled'];
  const rows = samples.map(({t, a = [0, 0, 0], p, q, on, received}) => [
    BigInt(received) * 1000000n, (t - start) / 1000, a[2], a[1], a[0],
    ...(hasQuaternion ? (q ?? ['', '', '', '']) : []), ...(hasPose ? (p ?? ['', '', '']) : []),
    on === false ? 0 : 1,
  ].join(','));
  const csv = `${header.join(',')}\n${rows.join('\n')}\n`;
  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace('T', '-').slice(0, 15);
  const file = `live-${stamp}-${phone}.csv`;
  await mkdir(sensorsDir, {recursive: true});
  await writeFile(path.join(sensorsDir, file), csv);
  await writeFile(path.join(sensorsDir, 'live-latest.csv'), csv);
  return {file, samples: samples.length, seconds: (samples.at(-1).t - start) / 1000};
}

let server;
try {
  server = https.createServer({
    key: await readFile(path.join(certDir, 'key.pem')),
    cert: await readFile(path.join(certDir, 'cert.pem')),
  });
} catch (error) {
  parentPort.postMessage({type: 'error', message: `No TLS certificate (${error.message})`});
  process.exit(0);
}

server.on('request', async (request, response) => {
  const route = new URL(request.url, 'https://phone').pathname.slice(1);
  const send = (status, type, body) => {
    response.writeHead(status, {'Content-Type': type, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'});
    response.end(body);
  };
  if (request.method !== 'GET') return send(405, 'text/plain', 'GET only');
  if (!pages.has(route)) return send(404, 'text/plain', 'Not found');
  const file = pages.get(route);
  send(200, file.endsWith('.html') ? 'text/html' : 'text/javascript', await readFile(path.join(here, file)));
});

server.on('upgrade', (request, socket) => {
  const url = new URL(request.url, 'https://phone');
  if (url.pathname !== '/ws' || !validToken(url.searchParams.get('token'))
    || request.headers.origin !== `https://${request.headers.host}`) {
    return socket.end('HTTP/1.1 403 Forbidden\r\n\r\n');
  }
  const peer = acceptWebSocket(request, socket);
  if (!peer) return;
  const phone = nextPhone++;
  const recorded = [];
  parentPort.postMessage({type: 'phone', phone, connected: true});
  peer.on('message', text => {
    let message;
    try { message = JSON.parse(text); } catch { return; }
    if (typeof message?.enabled === 'boolean') {
      return parentPort.postMessage({type: 'clutch', phone, enabled: message.enabled});
    }
    if (!validSample(message)) return;
    const {t, a, p, q, xr, on = true} = message;
    parentPort.postMessage({type: 'sample', phone, t, a, p, q, xr, on});
    if (recorded.length < MAX_RECORDED && (!recorded.length || t > recorded.at(-1).t)) {
      recorded.push({t, a, p, q, on, received: Date.now()});
    }
  });
  peer.on('close', async () => {
    parentPort.postMessage({type: 'phone', phone, connected: false});
    if (recorded.length < 3) return;
    try { parentPort.postMessage({type: 'saved', phone, ...await saveSession(phone, recorded)}); }
    catch (error) { parentPort.postMessage({type: 'save-error', message: error.message}); }
  });
});

server.on('error', error => parentPort.postMessage({type: 'error', message: error.message}));
server.listen(port, '0.0.0.0', () => parentPort.postMessage({type: 'listening', port}));
