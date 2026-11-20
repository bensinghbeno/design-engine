// Run with server.mjs serving this workspace on localhost:8765.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';

const browser = await chromium.launch({executablePath:process.env.CHROME_PATH || '/usr/bin/google-chrome',
  headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const ready = page => page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Workspace ready'),null,{timeout:30000});
const complete = page => page.waitForFunction(()=>document.querySelector('#orientation-progress').textContent.startsWith('Orientation analysis complete'),null,{timeout:90000});
async function csv(page) {
  const event = page.waitForEvent('download');
  await page.locator('#export-coverage').click();
  const download = await event;
  assert.equal(download.suggestedFilename(),'orientation-coverage.csv');
  const stream = await download.createReadStream(), chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  const [header,...rows] = Buffer.concat(chunks).toString().trim().split('\n').map(row=>row.split(','));
  return rows.map(row=>Object.fromEntries(header.map((name,i)=>[name,row[i]])));
}
try {
  const page = await browser.newPage({viewport:{width:1440,height:1100}});
  const errors = [];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:8765'); await ready(page);
  assert.equal((await page.request.get('http://127.0.0.1:8765/orientation-worker.js')).status(),200);
  assert.equal(await page.locator('#colour-mode').inputValue(),'height');
  assert.ok(await page.locator('#height-key').isVisible());
  assert.ok(await page.locator('#coverage-key').isHidden());
  assert.ok(await page.locator('#analyze').isEnabled());
  assert.ok(await page.locator('#export-coverage').isDisabled());
  await page.selectOption('#probe-count','20'); await page.selectOption('#orientation-count','12');
  await page.locator('#analyze').click();
  assert.equal(await page.locator('#colour-mode').inputValue(),'coverage');
  assert.ok(await page.locator('#coverage-key').isVisible());
  assert.ok(await page.locator('#height-key').isHidden());
  await complete(page);
  assert.match(await page.locator('#coverage-summary').textContent(),/Complete · 20\/20 positions/);
  let rows = await csv(page);
  assert.equal(rows.length,20);
  for (const row of rows) {
    assert.equal(row.orientations_tested,'12');
    assert.equal(row.position_tolerance_m,'0.005');
    assert.equal(row.orientation_tolerance_deg,'10');
    assert.equal(row.ik_starts,'3');
    assert.equal(row.analysis_complete,'true');
    assert.equal(row.collisions_checked,'false');
    assert.equal(Number(row.found_fraction),Number(row.orientations_found)/12);
  }
  assert.ok(rows.some(row=>Number(row.found_fraction)<.5),'Five-joint rig must have restricted spots');
  assert.ok(await page.locator('#orientation-panel').textContent().then(text=>text.includes('not proof of impossibility')));
  console.log('PASS: real rig worker analysis, coverage legend, explicit uncertainty and CSV metadata.');

  // Mode switching preserves computed data; no silent IK rerun or invalidation.
  await page.selectOption('#colour-mode','height');
  assert.ok(await page.locator('#coverage-key').isHidden());
  await page.selectOption('#colour-mode','coverage');
  assert.equal((await csv(page)).length,20);
  await page.locator('#show-cloud').uncheck(); await page.locator('#show-cloud').check();

  // A long run must leave Tk-free browser interaction responsive, and preserve
  // only completed probes when cancelled, never infer the missing colours.
  await page.selectOption('#probe-count','200'); await page.selectOption('#orientation-count','48');
  assert.ok(await page.locator('#export-coverage').isDisabled());
  await page.locator('#analyze').click();
  await page.waitForFunction(()=>!document.querySelector('#export-coverage').disabled,null,{timeout:30000});
  await page.locator('#cancel-analysis').click();
  assert.match(await page.locator('#orientation-progress').textContent(),/^Cancelled/);
  assert.ok(await page.locator('#analyze').isEnabled());
  rows = await csv(page);
  assert.ok(rows.length>0 && rows.length<200);
  assert.ok(rows.every(row=>row.analysis_complete==='false'));
  const cancelledText = await page.locator('#orientation-progress').textContent();
  await page.waitForTimeout(300);
  assert.equal(await page.locator('#orientation-progress').textContent(),cancelledText);
  console.log('PASS: worker cancellation is responsive and partial exports remain explicitly partial.');

  // Lock changes terminate current analysis and invalidate both clouds.
  await page.locator('#analyze').click();
  await page.locator('#joints input[type=checkbox]').first().uncheck();
  assert.ok(await page.locator('#analyze').isDisabled());
  assert.ok(await page.locator('#cancel-analysis').isDisabled());
  assert.ok(await page.locator('#export-coverage').isDisabled());
  assert.ok(await page.locator('#coverage-summary').isHidden());
  assert.equal(await page.locator('#count').textContent(),'—');
  await page.waitForTimeout(300);
  assert.ok(await page.locator('#coverage-summary').isHidden());
  await page.selectOption('#samples','2000');
  await page.locator('#generate').click(); await ready(page);
  await page.selectOption('#probe-count','20'); await page.selectOption('#orientation-count','12');
  await page.locator('#position-tolerance').fill('0'); await page.locator('#position-tolerance').dispatchEvent('change');
  await page.locator('#analyze').click();
  assert.match(await page.locator('#status').textContent(),/Position tolerance/);
  assert.ok(await page.locator('#cancel-analysis').isDisabled());
  await page.locator('#position-tolerance').fill('5'); await page.locator('#position-tolerance').dispatchEvent('change');
  await page.locator('#analyze').click();
  await page.selectOption('#tip','upper_arm');
  assert.ok(await page.locator('#coverage-summary').isHidden());
  assert.ok(await page.locator('#cancel-analysis').isDisabled());
  console.log('PASS: locked joints, tip changes and invalid tolerances never leave stale coverage.');

  // Independent, known 6-DOF fixture: all three translations and rotations.
  // Its origin tool point stays inside the sliding range for every orientation.
  const axes = ['1 0 0','0 1 0','0 0 1','1 0 0','0 1 0','0 0 1'];
  const fixture = `<robot name="Cartesian wrist">${Array.from({length:7},(_,i)=>`<link name="l${i}"/>`).join('')}`
    + axes.map((axis,i)=>`<joint name="j${i}" type="${i<3?'prismatic':'continuous'}"><parent link="l${i}"/><child link="l${i+1}"/><axis xyz="${axis}"/>${i<3?'<limit lower="-1" upper="1" effort="1" velocity="1"/>':''}</joint>`).join('')+'</robot>';
  await page.locator('#upload').setInputFiles({name:'six.urdf',mimeType:'application/xml',buffer:Buffer.from(fixture)});
  await page.waitForFunction(()=>document.querySelector('#robot-name').textContent==='Cartesian wrist');
  await page.locator('#generate').click(); await ready(page);
  await page.locator('#analyze').click(); await complete(page);
  rows = await csv(page);
  assert.equal(rows.length,20);
  assert.ok(rows.every(row=>row.orientations_found==='12'),'Full Cartesian wrist should be green for every tested spot');
  console.log('PASS: capable 6DOF fixture finds every tested orientation (green).');

  // Model load during a fresh analysis terminates worker and clears results.
  await page.locator('#analyze').click();
  await page.selectOption('#example','circle'); await ready(page);
  assert.ok(await page.locator('#export-coverage').isDisabled());
  assert.ok(await page.locator('#coverage-summary').isHidden());
  // All joints locked gives exactly one known position, not 20 invented probes.
  await page.locator('#joints input[type=checkbox]').first().uncheck();
  await page.locator('#generate').click(); await ready(page);
  await page.locator('#analyze').click(); await complete(page);
  rows = await csv(page); assert.equal(rows.length,1); assert.equal(rows[0].orientations_found,'0');
  // Check actual spot inspection through the canvas; in this degenerate fixture
  // the one cloud point lies below the root along the displayed arm.
  const canvas = page.locator('canvas'); await canvas.scrollIntoViewIfNeeded();
  const box = await canvas.boundingBox();
  // Find rendered red pixels rather than guessing a projection-dependent
  // screen grid (small points can fall entirely between grid clicks).
  const image = (await canvas.screenshot()).toString('base64');
  const redPixels = await page.evaluate(async data => {
    const image = new Image(); image.src='data:image/png;base64,'+data; await image.decode();
    const target = document.createElement('canvas'); target.width=image.width; target.height=image.height;
    const ctx=target.getContext('2d'); ctx.drawImage(image,0,0);
    const pixels=ctx.getImageData(0,0,image.width,image.height).data, cells=new Map();
    for (let y=110;y<image.height-25;y++) for (let x=0;x<image.width;x++) {
      const i=(y*image.width+x)*4, [r,g,b]=pixels.slice(i,i+3);
      if (r>200 && g<170 && b<190 && r>g*1.4) cells.set(`${Math.floor(x/4)},${Math.floor(y/4)}`,[x/image.width,y/image.height]);
    }
    return [...cells.values()];
  },image);
  assert.ok(redPixels.length,'Restricted spot should actually render red');
  for (const [x,y] of redPixels) {
    await page.mouse.click(box.x+box.width*x,box.y+box.height*y);
    if (await page.locator('#probe-detail').isVisible()) break;
  }
  assert.ok(await page.locator('#probe-detail').isVisible(),'A tested coloured point should be pickable');
  assert.match(await page.locator('#probe-detail').textContent(),/0\/12 orientations found/);
  await page.setViewportSize({width:480,height:900});
  assert.ok(await page.locator('#coverage-key').isVisible());
  assert.ok(await canvas.isVisible());
  await page.goto('http://127.0.0.1:8765/?orientation=1'); await ready(page);
  await page.waitForFunction(()=>document.querySelector('#colour-mode').value==='coverage'
    && !document.querySelector('#cancel-analysis').disabled);
  await page.locator('#cancel-analysis').click();
  assert.match(await page.locator('#orientation-progress').textContent(),/^Cancelled/);
  assert.deepEqual(errors,[]);
  console.log('PASS: model reload cancels stale work, locked point deduplicates, spot picking, mobile layout and direct analysis link work.');
} finally { await browser.close(); }