import {createHash} from 'node:crypto';
import {EventEmitter} from 'node:events';

const GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';
const MAX_PAYLOAD = 64 * 1024;
const MAX_BUFFERED = 1024 * 1024;

function frame(opcode, payload) {
  const length = payload.length;
  const header = length < 126 ? Buffer.alloc(2) : length < 65536 ? Buffer.alloc(4) : Buffer.alloc(10);
  header[0] = 0x80 | opcode;
  if (length < 126) header[1] = length;
  else if (length < 65536) { header[1] = 126; header.writeUInt16BE(length, 2); }
  else { header[1] = 127; header.writeBigUInt64BE(BigInt(length), 2); }
  return Buffer.concat([header, payload]);
}

export function acceptWebSocket(request, socket) {
  const key = request.headers['sec-websocket-key'];
  if (!key || request.headers.upgrade?.toLowerCase() !== 'websocket') {
    socket.end('HTTP/1.1 400 Bad Request\r\n\r\n');
    return null;
  }
  const accept = createHash('sha1').update(key + GUID).digest('base64');
  socket.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
    + `Sec-WebSocket-Accept: ${accept}\r\n\r\n`);
  socket.setNoDelay(true);

  const peer = new EventEmitter();
  let buffer = Buffer.alloc(0), open = true;
  const shutdown = () => { if (!open) return; open = false; socket.destroy(); peer.emit('close'); };
  peer.send = text => {
    // Drop frames for slow readers instead of growing memory without bound.
    if (open && socket.writableLength < MAX_BUFFERED) socket.write(frame(0x1, Buffer.from(text)));
  };
  peer.close = () => { if (open) socket.write(frame(0x8, Buffer.alloc(0))); shutdown(); };

  socket.on('data', chunk => {
    buffer = Buffer.concat([buffer, chunk]);
    while (buffer.length >= 2) {
      const fin = buffer[0] & 0x80, opcode = buffer[0] & 0x0f, masked = buffer[1] & 0x80;
      let length = buffer[1] & 0x7f, offset = 2;
      if (length === 126) { if (buffer.length < 4) return; length = buffer.readUInt16BE(2); offset = 4; }
      else if (length === 127) { if (buffer.length < 10) return; length = Number(buffer.readBigUInt64BE(2)); offset = 10; }
      if (!masked || !fin || length > MAX_PAYLOAD) return peer.close();
      if (buffer.length < offset + 4 + length) return;
      const mask = buffer.subarray(offset, offset + 4);
      const payload = Buffer.from(buffer.subarray(offset + 4, offset + 4 + length));
      for (let index = 0; index < payload.length; index++) payload[index] ^= mask[index % 4];
      buffer = buffer.subarray(offset + 4 + length);
      if (opcode === 0x1) peer.emit('message', payload.toString('utf8'));
      else if (opcode === 0x8) return peer.close();
      else if (opcode === 0x9 && open) socket.write(frame(0xA, payload));
    }
  });
  socket.on('close', shutdown);
  socket.on('error', shutdown);
  return peer;
}
