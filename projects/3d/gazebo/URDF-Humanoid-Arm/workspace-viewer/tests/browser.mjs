// Run with the viewer server already running on localhost:8765.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {examples} from '../examples.js';

const browser = await chromium.launch({executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
  headless:true, args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try {
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const errors = [];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765');
  await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Workspace ready'),null,{timeout:30000});
  assert.equal(await page.locator('#robot-name').textContent(),'arm_rig');
  assert.equal(await page.locator('#count').textContent(),'20,000');
  assert.match(await page.locator('#dof').textContent(),/2 sampled DOF/);
  const yBounds = (await page.locator('#by').textContent()).split(' → ').map(Number);
  assert.ok(yBounds[1]-yBounds[0]>.64, 'Yaw plus pitch must sweep in Y, not just a circle');
  console.log('PASS: actual rig loads, WebGL starts, cloud and bounds appear.');

  await page.selectOption('#samples','2000');
  for (const [example,dof] of [['circle',1],['sphere',2],['planar',2],['volume',3]]) {
    await page.selectOption('#example',example);
    await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Workspace ready'));
    assert.match(await page.locator('#dof').textContent(),new RegExp(`${dof} sampled DOF`));
    assert.equal(await page.locator('#count').textContent(),'2,000');
  }
  console.log('PASS: all four educational presets render and sample.');
  await page.locator('#joints input[type=checkbox]').first().uncheck();
  assert.match(await page.locator('#dof').textContent(),/2 sampled DOF/);
  assert.equal(await page.locator('#count').textContent(),'—');
  await page.locator('#generate').click();
  await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Workspace ready'));
  const download = page.waitForEvent('download');
  await page.locator('#export').click();
  assert.equal((await download).suggestedFilename(),'workspace.csv');
  console.log('PASS: joint locking invalidates old cloud; CSV export works.');

  await page.locator('#upload').setInputFiles({name:'circle.urdf',mimeType:'application/xml',buffer:Buffer.from(examples.circle.xml)});
  await page.waitForFunction(()=>document.querySelector('#robot-name').textContent==='One hinge');
  await page.locator('summary').click();
  await page.locator('#xml').fill('<robot><link name="a"/><link name="b"/></robot>');
  await page.locator('#apply').click();
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('root link'));
  assert.equal(await page.locator('#robot-name').textContent(),'One hinge');
  console.log('PASS: URDF upload works; invalid edits preserve last valid model.');

  await page.locator('#rig').click();
  await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Workspace ready'));
  await page.setViewportSize({width:480,height:900});
  assert.ok(await page.locator('canvas').isVisible());
  assert.deepEqual(errors,[]);
  console.log('PASS: rig reload, responsive canvas, no uncaught browser errors.');
} finally { await browser.close(); }