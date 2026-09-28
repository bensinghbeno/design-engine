export function parseSensorCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(line => line.trim());
  if (lines.length < 4) throw Error('Motion CSV needs a header and at least three samples.');
  const headers = lines[0].split(',').map(value => value.trim());
  const columns = Object.fromEntries(headers.map((name, index) => [name, index]));
  for (const name of ['seconds_elapsed', 'x', 'y', 'z']) {
    if (!(name in columns)) throw Error(`Motion CSV is missing the ${name} column.`);
  }
  const hasQuaternion = ['qx', 'qy', 'qz', 'qw'].every(name => name in columns);
  const hasPose = ['px', 'py', 'pz'].every(name => name in columns);
  const hasEnabled = 'enabled' in columns;
  const time = [], acceleration = [], quaternion = [], position = [], enabled = [];
  for (const [index, line] of lines.slice(1).entries()) {
    const values = line.split(',');
    const sampleTime = Number(values[columns.seconds_elapsed]);
    const sample = ['x', 'y', 'z'].map(axis => Number(values[columns[axis]]));
    if (![sampleTime, ...sample].every(Number.isFinite)) throw Error(`Invalid numeric data on row ${index + 2}.`);
    time.push(sampleTime); acceleration.push(sample);
    if (hasQuaternion) {
      const q = ['qx', 'qy', 'qz', 'qw'].map(name => Number(values[columns[name]]));
      quaternion.push(q.every(Number.isFinite) ? q : null);
    }
    if (hasPose) {
      const p = ['px', 'py', 'pz'].map(name => Number(values[columns[name]]));
      position.push(p.every(Number.isFinite) ? p : null);
    }
    if (hasEnabled) enabled.push(values[columns.enabled].trim() !== '0');
  }
  const start = time[0];
  for (let index = 0; index < time.length; index++) {
    time[index] -= start;
    if (index && time[index] <= time[index - 1]) throw Error('Motion CSV timestamps must increase.');
  }
  const parsed = {time, acceleration};
  if (hasQuaternion) parsed.quaternion = quaternion;
  if (hasPose && position.some(Boolean)) parsed.position = position;
  if (hasEnabled) parsed.enabled = enabled;
  return parsed;
}

export function rotateVector([x, y, z], [qx, qy, qz, qw]) {
  const tx = 2 * (qy * z - qz * y), ty = 2 * (qz * x - qx * z), tz = 2 * (qx * y - qy * x);
  return [
    x + qw * tx + qy * tz - qz * ty,
    y + qw * ty + qz * tx - qx * tz,
    z + qw * tz + qx * ty - qy * tx,
  ];
}

// Angle of the phone's top edge in the horizontal plane; undoing it keeps +Y "phone top at enable".
export function headingAngle(quaternion) {
  const [hx, hy] = rotateVector([0, 1, 0], quaternion);
  return Math.hypot(hx, hy) < 1e-6 ? 0 : Math.atan2(hx, hy);
}

export function rotateYaw([x, y, z], angle) {
  const cos = Math.cos(angle), sin = Math.sin(angle);
  return [x * cos - y * sin, x * sin + y * cos, z];
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

// Live streams have no end point for drift correction, so velocity is zeroed whenever a short window looks still.
// Chrome rounds readings to 0.1 m/s², so a hand-held "still" phone reads ~0.2 m/s² RMS; real moves read 0.4+.
// With orientation, samples are rotated into a gravity-aligned frame so phone tilt cannot leak into Z.
export function createLiveEstimator({calibrationSeconds = 0.5, maxGap = 0.25, stillWindow = 0.3, stillRms = 0.3,
  biasSeconds = 2} = {}) {
  let start, last, bias, sum, count, lastAcceleration, velocity, position, window, windowSum, still, yaw, paused;
  const reset = () => {
    start = null; last = null; bias = null; sum = [0, 0, 0]; count = 0; still = false; yaw = null; paused = false;
    lastAcceleration = [0, 0, 0]; velocity = [0, 0, 0]; position = [0, 0, 0]; window = []; windowSum = 0;
  };
  const clearMotion = () => { velocity = [0, 0, 0]; lastAcceleration = [0, 0, 0]; window = []; windowSum = 0; last = null; };
  reset();
  return {
    reset,
    hold() { paused = true; clearMotion(); },
    resume() { paused = false; clearMotion(); },
    get paused() { return paused; },
    get calibrating() { return bias === null; },
    get still() { return still; },
    get worldFrame() { return yaw !== null; },
    get bias() { return bias; },
    update(t, acceleration, quaternion) {
      if (start === null) start = t;
      if (yaw === null && quaternion) yaw = headingAngle(quaternion);
      const aligned = quaternion && yaw !== null
        ? rotateYaw(rotateVector(acceleration, quaternion), yaw)
        : acceleration;
      if (!bias) {
        for (let axis = 0; axis < 3; axis++) sum[axis] += aligned[axis];
        count++; last = t;
        if (t - start >= calibrationSeconds && count >= 3) bias = sum.map(value => value / count);
        return position.slice();
      }
      const corrected = aligned.map((value, axis) => value - bias[axis]);
      const dt = last === null ? 0 : t - last; last = t;
      if (dt > 0 && dt <= maxGap) {
        const energy = corrected.reduce((total, value) => total + value * value, 0);
        window.push([t, energy]); windowSum += energy;
        while (window[0][0] <= t - stillWindow) windowSum -= window.shift()[1];
        still = t - window[0][0] >= 0.8 * stillWindow && Math.sqrt(Math.max(0, windowSum) / window.length) < stillRms;
        if (still) {
          velocity = [0, 0, 0];
          const blend = Math.min(1, dt / biasSeconds);
          bias = bias.map((value, axis) => value + (aligned[axis] - value) * blend);
        } else if (!paused) {
          for (let axis = 0; axis < 3; axis++) {
            const nextVelocity = velocity[axis] + 0.5 * (lastAcceleration[axis] + corrected[axis]) * dt;
            position[axis] += 0.5 * (velocity[axis] + nextVelocity) * dt;
            velocity[axis] = nextVelocity;
          }
        }
      } else {
        window = []; windowSum = 0;
      }
      lastAcceleration = corrected;
      return position.slice();
    },
  };
}

// ARCore/WebXR poses are measured, not integrated, so the clutch only re-anchors the reference pose.
export function createPoseTracker() {
  let reference = null, yaw = 0, origin = [0, 0, 0], held = [0, 0, 0], paused = false;
  return {
    reset() { reference = null; origin = [0, 0, 0]; held = [0, 0, 0]; paused = false; },
    hold() { paused = true; reference = null; origin = held.slice(); },
    resume() { paused = false; reference = null; origin = held.slice(); },
    get paused() { return paused; },
    get position() { return held.slice(); },
    update(position, quaternion) {
      if (paused) return held.slice();
      if (!reference) { reference = position.slice(); yaw = quaternion ? headingAngle(quaternion) : 0; }
      const delta = position.map((value, axis) => value - reference[axis]);
      held = rotateYaw(delta, yaw).map((value, axis) => value + origin[axis]);
      return held.slice();
    },
  };
}