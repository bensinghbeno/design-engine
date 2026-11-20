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

export function createOrientationTracker() {
  let held = [0, 0, 0, 1], paused = false;
  return {
    reset() { held = [0, 0, 0, 1]; paused = false; },
    hold() { paused = true; },
    resume() { paused = false; },
    get paused() { return paused; },
    get quaternion() { return held.slice(); },
    update(quaternion) {
      if (paused) return held.slice();
      held = quaternion.slice();
      return held.slice();
    },
  };
}
