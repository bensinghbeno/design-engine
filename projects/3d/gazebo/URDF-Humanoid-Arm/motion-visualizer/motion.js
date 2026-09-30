export function parseSensorCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(line => line.trim());
  if (lines.length < 4) throw Error('Motion CSV needs a header and at least three samples.');
  const headers = lines[0].split(',').map(value => value.trim());
  const columns = Object.fromEntries(headers.map((name, index) => [name, index]));
  for (const name of ['seconds_elapsed', 'qx', 'qy', 'qz', 'qw']) {
    if (!(name in columns)) throw Error(`Motion CSV is missing the ${name} column.`);
  }
  const hasEnabled = 'enabled' in columns;
  const time = [], quaternion = [], enabled = [];
  for (const [index, line] of lines.slice(1).entries()) {
    const values = line.split(',');
    const sampleTime = Number(values[columns.seconds_elapsed]);
    const q = ['qx', 'qy', 'qz', 'qw'].map(name => Number(values[columns[name]]));
    if (![sampleTime, ...q].every(Number.isFinite)) throw Error(`Invalid numeric data on row ${index + 2}.`);
    time.push(sampleTime);
    quaternion.push(q);
    if (hasEnabled) enabled.push(values[columns.enabled].trim() !== '0');
  }
  const start = time[0];
  for (let index = 0; index < time.length; index++) {
    time[index] -= start;
    if (index && time[index] <= time[index - 1]) throw Error('Motion CSV timestamps must increase.');
  }
  const parsed = {time, quaternion};
  if (hasEnabled) parsed.enabled = enabled;
  return parsed;
}

function normalizedQuaternion(quaternion) {
  const length = Math.hypot(...quaternion);
  if (!Number.isFinite(length) || length < 1e-9) throw Error('Orientation quaternion must have a nonzero length.');
  return quaternion.map(value => value / length);
}

function multiplyQuaternions(a, b) {
  const [ax, ay, az, aw] = a, [bx, by, bz, bw] = b;
  return [
    aw * bx + ax * bw + ay * bz - az * by,
    aw * by - ax * bz + ay * bw + az * bx,
    aw * bz + ax * by - ay * bx + az * bw,
    aw * bw - ax * bx - ay * by - az * bz,
  ];
}

export function relativeQuaternion(reference, current) {
  const [x, y, z, w] = normalizedQuaternion(reference);
  return normalizedQuaternion(multiplyQuaternions(normalizedQuaternion(current), [-x, -y, -z, w]));
}

export function createOrientationTracker() {
  let reference = null, base = [0, 0, 0, 1], held = [0, 0, 0, 1], paused = false;
  return {
    reset() { reference = null; base = [0, 0, 0, 1]; held = [0, 0, 0, 1]; paused = false; },
    hold() { paused = true; reference = null; base = held.slice(); },
    resume() { paused = false; reference = null; base = held.slice(); },
    get paused() { return paused; },
    get quaternion() { return held.slice(); },
    update(quaternion) {
      if (paused) return held.slice();
      const current = normalizedQuaternion(quaternion);
      if (!reference) { reference = current; base = held.slice(); return held.slice(); }
      held = normalizedQuaternion(multiplyQuaternions(relativeQuaternion(reference, current), base));
      return held.slice();
    },
  };
}
