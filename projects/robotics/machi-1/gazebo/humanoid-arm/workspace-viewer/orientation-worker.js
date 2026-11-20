import {analysisRequest, analyzeProbe} from './orientation-analysis.js';

// All IK work is off the render/UI thread. Cancellation terminates this
// worker, so even a long failed solve cannot block a user action.
self.onmessage = event => {
  try {
    const {model,probes,targets,options} = analysisRequest(event.data);
    self.postMessage({type:'started',total:probes.length});
    for (let i=0; i<probes.length; i++) {
      const result = analyzeProbe(model,probes[i],targets,{...options,seed:12345+i*1009});
      self.postMessage({type:'probe',index:i,total:probes.length,result});
    }
    self.postMessage({type:'done',total:probes.length});
  } catch (error) {
    self.postMessage({type:'error',message:error.message || String(error)});
  }
};