import https from 'node:https';
import {readFile} from 'node:fs/promises';
import {timingSafeEqual} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parentPort, workerData} from 'node:worker_threads';
import {acceptWebSocket} from './websocket.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const {port, token, certDir} = workerData;
const pages = new Map([['', 'phone.html'], ['phone.html', 'phone.html'], ['phone.js', 'phone.js']]);
let nextPhone = 1;

function validToken(candidate) {
  const expected = Buffer.from(token), actual = Buffer.from(candidate || '');
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

function validSample(sample) {
  return sample && Number.isFinite(sample.t) && Array.isArray(sample.a) && sample.a.length === 3
    && sample.a.every(Number.isFinite);
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
  parentPort.postMessage({type: 'phone', phone, connected: true});
  peer.on('message', text => {
    let sample;
    try { sample = JSON.parse(text); } catch { return; }
    if (validSample(sample)) parentPort.postMessage({type: 'sample', phone, t: sample.t, a: sample.a});
  });
  peer.on('close', () => parentPort.postMessage({type: 'phone', phone, connected: false}));
});

server.on('error', error => parentPort.postMessage({type: 'error', message: error.message}));
server.listen(port, '0.0.0.0', () => parentPort.postMessage({type: 'listening', port}));
