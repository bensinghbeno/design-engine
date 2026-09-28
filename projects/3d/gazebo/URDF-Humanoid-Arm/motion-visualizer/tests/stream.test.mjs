import assert from 'node:assert/strict';
import test from 'node:test';
import {execFileSync} from 'node:child_process';
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import https from 'node:https';
import {randomBytes} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {Worker} from 'node:worker_threads';

const here = path.dirname(fileURLToPath(import.meta.url));

function clientFrame(text) {
  const payload = Buffer.from(text), mask = randomBytes(4);
  const header = Buffer.from([0x81, 0x80 | payload.length]);
  return Buffer.concat([header, mask, payload.map((byte, index) => byte ^ mask[index % 4])]);
}

function openRaw(port, requestPath, origin) {
  return new Promise((resolve, reject) => {
    const request = https.request({host: '127.0.0.1', port, path: requestPath, rejectUnauthorized: false, headers: {
      Connection: 'Upgrade', Upgrade: 'websocket', Origin: origin,
      'Sec-WebSocket-Version': '13', 'Sec-WebSocket-Key': randomBytes(16).toString('base64')}});
    request.on('upgrade', (_response, socket) => resolve(socket));
    request.on('response', response => resolve(response.statusCode));
    request.on('error', reject);
    request.end();
  });
}

test('stream worker relays valid phone samples and rejects bad tokens', async () => {
  const certDir = mkdtempSync(path.join(tmpdir(), 'motion-cert-'));
  execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=test',
    '-keyout', path.join(certDir, 'key.pem'), '-out', path.join(certDir, 'cert.pem')], {stdio: 'ignore'});
  const token = 'a'.repeat(32), port = 20000 + Math.floor(Math.random() * 20000);
  const worker = new Worker(path.join(here, '../stream-server.mjs'), {workerData: {port, token, certDir}});
  const messages = [];
  worker.on('message', message => messages.push(message));
  try {
    await new Promise(resolve => worker.once('message', resolve));
    assert.equal(messages[0].type, 'listening');
    const origin = `https://127.0.0.1:${port}`;
    assert.equal(await openRaw(port, '/ws?token=wrong', origin), 403);
    assert.equal(await openRaw(port, `/ws?token=${token}`, 'https://evil.example'), 403);
    const socket = await openRaw(port, `/ws?token=${token}`, origin);
    socket.write(clientFrame(JSON.stringify({t: 12.5, a: [0.1, 0.2, 0.3]})));
    socket.write(clientFrame(JSON.stringify({t: 13, a: [0.1, 'bad', 0.3]})));
    socket.write(clientFrame(JSON.stringify({t: 14, a: [1, 2, 3]})));
    await new Promise(resolve => setTimeout(resolve, 200));
    const samples = messages.filter(message => message.type === 'sample');
    assert.deepEqual(samples.map(({t, a}) => ({t, a})), [{t: 12.5, a: [0.1, 0.2, 0.3]}, {t: 14, a: [1, 2, 3]}]);
    assert.ok(messages.some(message => message.type === 'phone' && message.connected));
    socket.destroy();
  } finally {
    await worker.terminate();
    rmSync(certDir, {recursive: true, force: true});
  }
});
