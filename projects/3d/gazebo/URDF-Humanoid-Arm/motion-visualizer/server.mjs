import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT || 8766);
const publicFiles = new Set(['index.html', 'app.js', 'motion.js', 'style.css']);
const vendorFiles = new Map([
  ['vendor/three.module.js', 'build/three.module.js'],
  ['vendor/three.core.js', 'build/three.core.js'],
  ['vendor/OrbitControls.js', 'examples/jsm/controls/OrbitControls.js'],
]);
const threeRoot = path.join(here, '../workspace-viewer/node_modules/three');

const server = http.createServer(async (request, response) => {
  const send = (status, type, body) => {
    response.writeHead(status, {'Content-Type': type, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'});
    response.end(body);
  };
  if (request.method !== 'GET') return send(405, 'text/plain', 'GET only');
  const host = request.headers.host;
  if (host !== `127.0.0.1:${port}` && host !== `localhost:${port}`) return send(403, 'text/plain', 'Local access only');
  const route = new URL(request.url, `http://127.0.0.1:${port}`).pathname.slice(1) || 'index.html';
  try {
    if (route === 'api/motion') return send(200, 'text/csv', await readFile(path.join(here, '../sensors/Accelerometer.csv')));
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
server.on('error', error => { console.error(error.message); process.exitCode = 1; });
server.listen(port, '127.0.0.1', () => console.log(`Motion visualizer: http://127.0.0.1:${port}\nCtrl-C to stop. Gazebo is not required.`));