// Dependency-free, root-frame pose IK for an ordered URDF root-to-tip chain.
// Coverage is sampled SO(3) freedom, not a certificate of reachability: a failed
// local solve means only "no solution found". Collisions/dynamics are not tested.
export const DEFAULT_IK_OPTIONS = Object.freeze({
  positionTolerance: 0.005, orientationTolerance: Math.PI / 18,
  maxIterations: 70, restarts: 3,
});

const TAU = 2 * Math.PI;
const finite = Number.isFinite;
const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
const add = (a, b) => a.map((v, i) => v + b[i]);
const sub = (a, b) => a.map((v, i) => v - b[i]);
const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const norm = a => Math.hypot(...a);
const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);

function vector(a, n, label) {
  if (!(Array.isArray(a) || ArrayBuffer.isView(a)) || a.length !== n || !Array.from(a).every(finite)) {
    throw new TypeError(`${label} must contain ${n} finite numbers`);
  }
  return Array.from(a);
}
function unit(q) {
  const n = norm(q);
  if (!finite(n) || n < 1e-15) throw new RangeError('Degenerate quaternion/axis');
  return q.map(x => x / n);
}
function multiply(a, b) {
  const [x,y,z,w] = a, [X,Y,Z,W] = b;
  return [w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z];
}
function rotate(q, v) {
  const t = cross(q, v).map(x => 2*x), u = cross(q, t);
  return v.map((x, i) => x + q[3]*t[i] + u[i]);
}
function matrixQuaternion(m) {
  // Stable trace/largest-diagonal extraction, including rotations of pi.
  const trace = m[0] + m[5] + m[10];
  let q;
  if (trace > 0) {
    const s = 2 * Math.sqrt(trace + 1);
    q = [(m[6]-m[9])/s, (m[8]-m[2])/s, (m[1]-m[4])/s, s/4];
  } else {
    const i = m[0] > m[5] ? (m[0] > m[10] ? 0 : 2) : (m[5] > m[10] ? 1 : 2);
    const j = (i+1)%3, k = (i+2)%3;
    const s = 2 * Math.sqrt(1 + m[i*5] - m[j*5] - m[k*5]);
    q = [0, 0, 0, (m[j*4+k]-m[k*4+j])/s];
    q[i] = s/4; q[j] = (m[i*4+j]+m[j*4+i])/s; q[k] = (m[i*4+k]+m[k*4+i])/s;
  }
  return unit(q);
}
function prepare(model) {
  if (!model || !Array.isArray(model.joints)) throw new TypeError('Expected model.joints array');
  const offset = vector(model.offset, 3, 'model.offset'), names = new Set();
  let length = norm(offset);
  const joints = model.joints.map(j => {
    if (!j || typeof j.name !== 'string' || !j.name || names.has(j.name)) throw new TypeError('Invalid/duplicate joint name');
    names.add(j.name);
    if (!['fixed', 'continuous', 'revolute', 'prismatic'].includes(j.type)) throw new TypeError(`Invalid type for ${j.name}`);
    const m = vector(j.origin, 16, `${j.name}.origin`);
    // Origins must be rigid, column-major transforms, never scaled/sheared.
    const columns = [m.slice(0,3), m.slice(4,7), m.slice(8,11)];
    const dot = (a,b) => a.reduce((s,x,i) => s+x*b[i], 0);
    if ([m[3],m[7],m[11],m[15]-1].some(x => Math.abs(x)>1e-6) ||
        columns.some((a,i) => columns.some((b,k) => Math.abs(dot(a,b)-(i===k ? 1 : 0))>1e-5)) ||
        dot(cross(columns[0],columns[1]),columns[2]) < 0.99999) throw new RangeError('Origin must be a rigid transform');
    const fixed = j.type === 'fixed';
    const axis = fixed ? (j.axis === undefined ? [1,0,0] : vector(j.axis,3,'axis')) : unit(vector(j.axis,3,'axis'));
    const value = j.value === undefined ? 0 : j.value;
    const min = j.min === undefined && fixed ? 0 : j.min;
    const max = j.max === undefined && fixed ? 0 : j.max;
    if (![value,min,max].every(finite) || min>max || !finite(max-min)) throw new RangeError(`Invalid value/bounds for ${j.name}`);
    if (j.enabled !== undefined && typeof j.enabled !== 'boolean') throw new TypeError('enabled must be boolean');
    const enabled = j.enabled !== false;
    const translation = m.slice(12,15);
    length += norm(translation) + (j.type === 'prismatic' ? Math.max(Math.abs(min),Math.abs(max),Math.abs(value)) : 0);
    return {name:j.name, type:j.type, axis, value, min, max, enabled,
      active:!fixed && enabled && max>min, wrap:j.type==='continuous' && max-min>=TAU-1e-10,
      translation, rotation:matrixQuaternion(m)};
  });
  if (!finite(length)) throw new RangeError('Model length overflow');
  return {joints, offset, length:Math.max(length, 1e-3)};
}
function values(model, positions) {
  if (!positions || typeof positions !== 'object' || Array.isArray(positions)) throw new TypeError('Expected positions object');
  return model.joints.map(j => {
    const v = own(positions,j.name) ? positions[j.name] : j.value;
    if (!finite(v)) throw new TypeError(`Non-finite position for ${j.name}`);
    return v;
  });
}
function pose(model, values, derivatives = false) {
  let position = [0,0,0], orientation = [0,0,0,1];
  const frames = [];
  model.joints.forEach((j,i) => {
    position = add(position, rotate(orientation,j.translation));
    orientation = unit(multiply(orientation,j.rotation));
    const axis = rotate(orientation,j.axis);
    if (derivatives && j.active) frames.push({axis, point:position, type:j.type, index:i});
    if (j.type === 'prismatic') position = add(position, axis.map(x => x*values[i]));
    else if (j.type !== 'fixed') {
      const h = values[i]/2, s = Math.sin(h);
      orientation = unit(multiply(orientation,[...j.axis.map(x => x*s),Math.cos(h)]));
    }
  });
  position = add(position,rotate(orientation,model.offset));
  // Geometric Jacobian in root coordinates, evaluated at the offset tool point.
  const columns = frames.map(f => f.type==='prismatic' ? [...f.axis,0,0,0] : [...cross(f.axis,sub(position,f.point)),...f.axis]);
  return {position, orientation, columns};
}

export function forwardPose(model, positions = {}) {
  const prepared = prepare(model), result = pose(prepared,values(prepared,positions));
  if (!result.position.every(finite)) throw new RangeError('Forward pose overflow');
  return {position:result.position, orientation:result.orientation};
}

function radicalInverse(index, base) {
  let value = 0, factor = 1/base;
  while (index) { value += (index%base)*factor; index = Math.floor(index/base); factor /= base; }
  return value;
}
export function orientationTargets(count) {
  if (!Number.isInteger(count) || count<1 || count>96) throw new RangeError('count must be an integer in 1..96');
  // Halton(2,3,5) through Shoemake's volume-preserving S^3 mapping. The
  // sequence is global, prefix-stable, includes roll, and adds no baseline pose.
  return Array.from({length:count}, (_,i) => {
    const u = radicalInverse(i+1,2), a = TAU*radicalInverse(i+1,3), b = TAU*radicalInverse(i+1,5);
    return unit([Math.sqrt(1-u)*Math.sin(a),Math.sqrt(1-u)*Math.cos(a),Math.sqrt(u)*Math.sin(b),Math.sqrt(u)*Math.cos(b)]);
  });
}

function angularError(target, current) {
  let q = unit(multiply(target,[-current[0],-current[1],-current[2],current[3]]));
  // q and -q encode the same rotation. At pi, choose a deterministic axis
  // sign using the largest component instead of dividing by sin(angle).
  let sign = q[3] < 0 ? -1 : 1;
  if (Math.abs(q[3]) < 1e-14) {
    const largest = [0,1,2].reduce((a,b) => Math.abs(q[a])>=Math.abs(q[b]) ? a : b);
    sign = q[largest] < 0 ? -1 : 1;
  }
  q = q.map(x => x*sign);
  const s = norm(q.slice(0,3)), angle = 2*Math.atan2(s,Math.abs(q[3]));
  return s < 1e-15 ? [0,0,0] : q.slice(0,3).map(x => x*angle/s);
}
function assess(model, q, target, derivatives = false) {
  const p = pose(model,q,derivatives), dp = sub(target.position,p.position), dr = angularError(target.orientation,p.orientation);
  // Normalize translation by chain length: radians and linear errors have
  // comparable task weights, independent of the model's physical units.
  const residual = [...dp.map(x => x/model.length),...dr];
  const score = residual.reduce((s,x) => s+x*x,0);
  return {positionError:norm(dp), orientationError:norm(dr), residual,
    score:finite(score) ? score : Infinity, columns:p.columns};
}
function constrain(j,v) {
  if (!j.enabled || j.type==='fixed') return j.value;
  if (j.min===j.max) return j.min;
  if (j.wrap) {
    if (v>=j.min && v<=j.max) return v;
    // Reduce separately to avoid overflowing v-min. Full-turn continuous
    // intervals are periodic; limited continuous and revolute joints are not.
    return clamp(j.min + ((v%TAU-j.min%TAU)%TAU+TAU)%TAU,j.min,j.max);
  }
  return clamp(v,j.min,j.max);
}
function linearSolve(a,b) {
  // Partial-pivot Gaussian elimination of the small damped 6x6 task matrix.
  const m = a.map((row,i) => [...row,b[i]]);
  for (let k=0;k<6;k++) {
    let pivot = k;
    for (let i=k+1;i<6;i++) if (Math.abs(m[i][k])>Math.abs(m[pivot][k])) pivot=i;
    if (!finite(m[pivot][k]) || Math.abs(m[pivot][k])<1e-18) return null;
    [m[k],m[pivot]] = [m[pivot],m[k]];
    for (let i=k+1;i<6;i++) {
      const factor = m[i][k]/m[k][k];
      for (let j=k;j<=6;j++) m[i][j] -= factor*m[k][j];
    }
  }
  const x = Array(6).fill(0);
  for (let i=5;i>=0;i--) {
    let v = m[i][6];
    for (let j=i+1;j<6;j++) v -= m[i][j]*x[j];
    x[i] = v/m[i][i];
  }
  return x.every(finite) ? x : null;
}
function settings(options) {
  if (!options || typeof options!=='object' || Array.isArray(options)) throw new TypeError('Expected options object');
  const o = {...DEFAULT_IK_OPTIONS,...options};
  for (const key of ['positionTolerance','orientationTolerance']) {
    if (!finite(o[key]) || o[key]<=0) throw new RangeError(`${key} must be finite and positive`);
  }
  for (const [key,max] of [['maxIterations',200],['restarts',8]]) {
    if (!Number.isInteger(o[key]) || o[key]<1 || o[key]>max) throw new RangeError(`${key} must be an integer in 1..${max}`);
  }
  if (o.seed!==undefined && !finite(o.seed)) throw new TypeError('seed must be finite');
  return o;
}

export function solvePose(model, target, seed = {}, options = {}) {
  const m = prepare(model), o = settings(options);
  if (!target || typeof target!=='object') throw new TypeError('Expected target pose');
  const t = {position:vector(target.position,3,'target.position'), orientation:unit(vector(target.orientation,4,'target.orientation'))};
  const initial = values(m,seed).map((v,i) => constrain(m.joints[i],v));
  const active = m.joints.map((j,i) => j.active ? i : -1).filter(i => i>=0);
  let state = (o.seed ?? 0x5eed1234) >>> 0, iterations = 0;
  const random = () => { state = (Math.imul(state,1664525)+1013904223)>>>0; return state/4294967296; };
  let bestQ = initial.slice(), best = assess(m,initial,t);
  const success = (q,e) => finite(e.score) && finite(e.positionError) && finite(e.orientationError) &&
    e.positionError<=o.positionTolerance && e.orientationError<=o.orientationTolerance &&
    q.every((v,i) => finite(v) && (m.joints[i].active ? v>=m.joints[i].min && v<=m.joints[i].max : v===constrain(m.joints[i],v)));
  const result = () => {
    // Re-evaluate the actual returned pose; never infer success from step size.
    const checked = assess(m,bestQ,t);
    return {success:success(bestQ,checked), positions:Object.fromEntries(m.joints.map((j,i) => [j.name,bestQ[i]])),
      positionError:checked.positionError, orientationError:checked.orientationError, iterations};
  };
  if (success(bestQ,best) || !active.length || !finite(best.score)) return result();
  for (let restart=0;restart<o.restarts;restart++) {
    // Try the known positional seed first, then midpoint and seeded random
    // starts. Redundancy, joint limits and singularities still cause local minima.
    let q = initial.slice();
    if (restart) for (const i of active) {
      const j = m.joints[i], f = restart===1 ? 0.5 : random();
      q[i] = constrain(j,j.min+f*(j.max-j.min));
    }
    let damping = 0.02;
    for (let iteration=0;iteration<o.maxIterations;iteration++) {
      const e = assess(m,q,t,true);
      if (e.score<best.score || success(q,e)) { best=e; bestQ=q.slice(); }
      if (success(q,e)) return result();
      if (!finite(e.score)) break;
      iterations++;
      // Prismatic variables are measured in chain lengths; revolute in radians.
      const scales = active.map(i => m.joints[i].type==='prismatic' ? m.length : 1);
      const columns = e.columns.map((c,k) => c.map((v,r) => v*scales[k]/(r<3 ? m.length : 1)));
      let accepted = false;
      for (let attempt=0;attempt<4 && !accepted;attempt++) {
        const a = Array.from({length:6},(_,r) => Array.from({length:6},(_,s) =>
          columns.reduce((sum,c) => sum+c[r]*c[s],r===s ? damping*damping : 0)));
        // DLS: dq = J^T (J J^T + lambda^2 I)^-1 error.
        const taskStep = linearSolve(a,e.residual);
        if (!taskStep) { damping*=4; continue; }
        const step = columns.map(c => c.reduce((sum,v,r) => sum+v*taskStep[r],0));
        if (!step.every(finite)) { damping*=4; continue; }
        let ratio = 1;
        step.forEach((v,k) => { ratio=Math.max(ratio,Math.abs(v)/(m.joints[active[k]].type==='prismatic' ? 0.2 : 0.35)); });
        for (let backtrack=0;backtrack<8;backtrack++) {
          const factor = 2**(-backtrack)/ratio, candidate = q.slice();
          active.forEach((i,k) => { candidate[i]=constrain(m.joints[i],q[i]+step[k]*scales[k]*factor); });
          if (!candidate.every(finite)) continue;
          const next = assess(m,candidate,t);
          if (finite(next.score) && (next.score<e.score || success(candidate,next))) {
            q=candidate; accepted=true; damping=Math.max(1e-5,damping*0.5);
            if (next.score<best.score || success(q,next)) { best=next; bestQ=q.slice(); }
            if (success(q,next)) return result();
            break;
          }
        }
        if (!accepted) damping*=4;
      }
      if (!accepted) break;
    }
  }
  return result();
}

export function coverageColor(fraction) {
  const f = finite(fraction) ? clamp(fraction,0,1) : 0;
  const red = [0.95,0.16,0.2], yellow = [1,0.75,0.15], green = [0.16,0.85,0.45];
  const a = f<=0.5 ? red : yellow, b = f<=0.5 ? yellow : green;
  const t = f<=0.5 ? 2*f : 2*f-1;
  return a.map((v,i) => v+(b[i]-v)*t);
}