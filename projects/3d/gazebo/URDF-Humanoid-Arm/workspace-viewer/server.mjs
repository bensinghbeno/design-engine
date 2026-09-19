import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';

const here = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT || 8765);
const run = promisify(execFile);
const publicFiles = new Set(['index.html', 'app.js', 'kinematics.js', 'examples.js', 'style.css',
  'orientation.js', 'orientation-analysis.js', 'orientation-worker.js']);
const vendorFiles = new Map([
  ['vendor/three.module.js', 'build/three.module.js'],
  ['vendor/three.core.js', 'build/three.core.js'],
  ['vendor/OrbitControls.js', 'examples/jsm/controls/OrbitControls.js'],
]);

const server = http.createServer(async (req, res) => {
  const send = (status, type, body) => {
    res.writeHead(status, {'Content-Type': type, 'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff'});
    res.end(body);
  };
  // Only serve the viewer and one fixed, trusted project Xacro. Uploaded XML
  // is parsed in the browser; it is never executed as Xacro on the server.
  if (req.method !== 'GET') return send(405, 'text/plain', 'GET only');
  const host = req.headers.host;
  if (host !== `127.0.0.1:${port}` && host !== `localhost:${port}`) {
    return send(403, 'text/plain', 'Local access only');
  }
  const route = new URL(req.url, `http://127.0.0.1:${port}`).pathname.slice(1) || 'index.html';
  try {
    if (route === 'api/rig') {
      const env = {...process.env,
        PATH: '/opt/ros/noetic/bin:/usr/bin:/bin',
        PYTHONPATH: '/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages',
        PYTHONNOUSERSITE: '1'};
      const {stdout} = await run('/opt/ros/noetic/bin/xacro',
        [path.join(here, '../urdf/rig.urdf.xacro')], {env, timeout: 15000, maxBuffer: 5e6});
      return send(200, 'application/xml', stdout);
    }
    let file;
    if (publicFiles.has(route)) file = path.join(here, route);
    else if (vendorFiles.has(route)) file = path.join(here, 'node_modules/three', vendorFiles.get(route));
    else return send(404, 'text/plain', 'Not found');
    const type = route.endsWith('.html') ? 'text/html' : route.endsWith('.css') ? 'text/css' : 'text/javascript';
    send(200, type, await readFile(file));
  } catch (error) {
    send(500, 'text/plain', route === 'api/rig'
      ? `Could not expand the project Xacro. Check ROS Noetic/xacro installation.\n${error.message}`
      : 'Could not load viewer assets. Run npm ci in workspace-viewer.');
  }
});
server.on('error', error => { console.error(error.message); process.exitCode = 1; });
server.listen(port, '127.0.0.1', () => console.log(`Workspace viewer: http://127.0.0.1:${port}\nCtrl-C to stop. Gazebo is not required.`));