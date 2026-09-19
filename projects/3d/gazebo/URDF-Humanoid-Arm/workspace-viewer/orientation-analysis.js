import {orientationTargets, solvePose, forwardPose, DEFAULT_IK_OPTIONS} from './orientation.js';

// Pick separated *actual samples*, not voxels, centroids, or interpolated
// positions. Unexamined cloud points receive no orientation classification.
export function selectProbes(candidates, count) {
  if (!Number.isInteger(count) || count < 1 || count > 250) throw Error('Probe count must be 1..250');
  if (!Array.isArray(candidates) || candidates.length > 512) throw Error('At most 512 probe candidates supported');
  for (const c of candidates) {
    if (!c || !Array.isArray(c.position) || c.position.length !== 3 || !c.position.every(Number.isFinite)) {
      throw Error('Invalid probe position');
    }
  }
  if (!candidates.length) return [];
  const result = [], distances = candidates.map(()=>Infinity);
  let next = 0;
  while (result.length < Math.min(count,candidates.length)) {
    const chosen = candidates[next]; result.push(chosen);
    for (let i=0; i<candidates.length; i++) {
      const d = candidates[i].position.reduce((sum,x,k)=>sum+(x-chosen.position[k])**2,0);
      distances[i] = Math.min(distances[i],d);
    }
    next = distances.reduce((best,d,i)=>d>distances[best] ? i : best,0);
    if (distances[next] < 1e-18) break; // repeated position / point workspace
  }
  return result;
}

export function analyzeProbe(model, probe, targets, options = {}) {
  const settings = {...DEFAULT_IK_OPTIONS,...options};
  if (!Array.isArray(targets) || targets.length < 1 || targets.length > 96) throw Error('Need 1..96 target orientations');
  // A red point must still be position-reachable. Verify the supplied seed
  // with the same enabled/frozen bounds used by the IK solver.
  const seed = {};
  for (const j of model.joints) {
    seed[j.name] = j.type === 'fixed' || j.enabled === false ? (j.value ?? 0)
      : j.max === j.min ? j.min : Math.max(j.min,Math.min(j.max,probe.seed[j.name] ?? j.value ?? 0));
  }
  const known = forwardPose(model,seed);
  if (Math.hypot(...known.position.map((v,i)=>v-probe.position[i])) > 1e-7) {
    throw Error('Probe must have a known reachable position under the selected joint ranges');
  }
  let solved = 0;
  for (let i=0; i<targets.length; i++) {
    const result = solvePose(model,{position:probe.position,orientation:targets[i]},seed,
      {...settings,seed:(options.seed ?? 12345)+i*104729});
    if (result.success) solved++;
  }
  return {position:probe.position.slice(),solved,tested:targets.length,fraction:solved/targets.length};
}

export function analysisRequest(data) {
  const {model,candidates,probeCount,orientationCount,options} = data;
  // Validate settings before worker computation (including a zero-result run).
  const targets = orientationTargets(orientationCount);
  const probes = selectProbes(candidates,probeCount);
  if (!probes.length) throw Error('Generate a reachable workspace first');
  return {model,probes,targets,options:{...DEFAULT_IK_OPTIONS,...options}};
}