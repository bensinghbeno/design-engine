export function parseSensorCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(line => line.trim());
  if (lines.length < 4) throw Error('Motion CSV needs a header and at least three samples.');
  const headers = lines[0].split(',').map(value => value.trim());
  const columns = Object.fromEntries(headers.map((name, index) => [name, index]));
  for (const name of ['seconds_elapsed', 'x', 'y', 'z']) {
    if (!(name in columns)) throw Error(`Motion CSV is missing the ${name} column.`);
  }
  const time = [], acceleration = [];
  for (const [index, line] of lines.slice(1).entries()) {
    const values = line.split(',');
    const sampleTime = Number(values[columns.seconds_elapsed]);
    const sample = ['x', 'y', 'z'].map(axis => Number(values[columns[axis]]));
    if (![sampleTime, ...sample].every(Number.isFinite)) throw Error(`Invalid numeric data on row ${index + 2}.`);
    time.push(sampleTime); acceleration.push(sample);
  }
  const start = time[0];
  for (let index = 0; index < time.length; index++) {
    time[index] -= start;
    if (index && time[index] <= time[index - 1]) throw Error('Motion CSV timestamps must increase.');
  }
  return {time, acceleration};
}

function integrate(values, time) {
  const result = values.map(() => [0, 0, 0]);
  for (let index = 1; index < values.length; index++) {
    const dt = time[index] - time[index - 1];
    for (let axis = 0; axis < 3; axis++) result[index][axis] = result[index - 1][axis]
      + 0.5 * (values[index - 1][axis] + values[index][axis]) * dt;
  }
  return result;
}

export function estimateTrajectory(time, acceleration, calibrationSeconds = 0.5) {
  if (time.length !== acceleration.length || time.length < 3 || time.at(-1) <= 0) throw Error('Motion data needs at least three matching samples.');
  let calibrationCount = time.findIndex(value => value >= calibrationSeconds);
  if (calibrationCount < 0) calibrationCount = time.length;
  calibrationCount = Math.max(3, calibrationCount);
  const bias = [0, 1, 2].map(axis => acceleration.slice(0, calibrationCount)
    .reduce((sum, sample) => sum + sample[axis], 0) / calibrationCount);
  const corrected = acceleration.map(sample => sample.map((value, axis) => value - bias[axis]));
  const velocity = integrate(corrected, time), duration = time.at(-1), finalVelocity = velocity.at(-1);
  for (let index = 0; index < velocity.length; index++) for (let axis = 0; axis < 3; axis++) {
    velocity[index][axis] -= time[index] / duration * finalVelocity[axis];
  }
  const position = integrate(velocity, time);
  const pathLength = position.slice(1).reduce((total, point, index) => total
    + Math.hypot(...point.map((value, axis) => value - position[index][axis])), 0);
  return {position, bias, pathLength};
}