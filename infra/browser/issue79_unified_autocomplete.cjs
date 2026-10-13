// Read-only acceptance on the actual Frappe Desk route. In preview mode only
// this Chromium context receives the candidate CSS; DEV files are untouched.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const base = process.env.CC_BASE_URL || 'http://centrochange.local:8082';
const fixturePath = process.env.CC_ISSUE79_FIXTURE;
const mode = process.env.CC_ISSUE79_ASSET_MODE || 'live';
const output = process.env.CC_ISSUE79_OUTPUT || '/tmp/issue79-browser';
if (!fixturePath || !['live', 'preview'].includes(mode)) throw Error('Set CC_ISSUE79_FIXTURE and CC_ISSUE79_ASSET_MODE=live|preview');
const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8')).fixture || JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
const css = fs.readFileSync(path.resolve(__dirname, '../../app/centrochange_core/centrochange_core/centro_change_core/page/cc_unified_desk/cc_unified_desk.css'), 'utf8');
const customerLabel=value=>String(value||'').replace(/CC-HTTP-[A-Za-z0-9]+\s+/g,'');
const professionalLabel=value=>({a:'Alfa',b:'Beta',c:'Gamma'}[customerLabel(value)]||customerLabel(value));
fs.mkdirSync(output, {recursive:true});

async function login(page, role) {
  await page.goto(base + '/login?redirect-to=/app/cc-unified-desk%3Fcc_view%3Dagenda');
  await page.locator('#login_email').fill(fixture.users[role].name);
  await page.locator('#login_password').fill(fixture.users[role].password);
  await page.getByRole('button', {name:'Continua'}).click();
  await page.locator('#new-booking').waitFor();
  await page.goto(base + '/app/cc-unified-desk?cc_view=agenda');
  await page.locator('#new-booking').waitFor();
  assert.match(page.url(), /\/app\/cc-unified-desk\?cc_view=agenda/);
}

const select = (page, field) => page.locator(`#modal-fields select[name="${field}"]`);
const input = (page, field) => select(page, field).locator('xpath=preceding-sibling::div[contains(@class,"cc-combobox")]').locator('input');
const list = (page, field) => select(page, field).locator('xpath=preceding-sibling::div[contains(@class,"cc-combobox")]').locator('.cc-options');

async function geometry(page, field) {
  return page.evaluate(field => {
    const element=document.querySelector(`#modal-fields select[name="${field}"]`).previousElementSibling;
    const menu=element.querySelector('.cc-options'), rect=menu.getBoundingClientRect();
    const first=menu.querySelector('[role="option"]');
    const target=first?.getBoundingClientRect();
    const hit=target && document.elementFromPoint(target.left+Math.min(target.width/2,20),target.top+Math.min(target.height/2,15));
    const dialog=element.closest('dialog');
    return {comboboxPosition:getComputedStyle(element).position,menuDisplay:getComputedStyle(menu).display,
      menuRect:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},dialogBottom:dialog.getBoundingClientRect().bottom,
      optionCount:menu.querySelectorAll('[role="option"]').length,optionHit:!!first&&(hit===first||first.contains(hit)),
      inputExpanded:element.querySelector('input').getAttribute('aria-expanded')};
  }, field);
}

async function testRole(browser, role, viewport) {
  console.error('TEST',role,viewport.width);
  const context=await browser.newContext({viewport,locale:'it-IT',serviceWorkers:'block'});
  const page=await context.newPage(), errors=[], bookingWrites=[];
  page.on('pageerror', e=>errors.push(e.message));
  page.on('request', req=>{if(req.method()!=='GET' && /booking\.(?:create|reschedule)/.test(req.url()))bookingWrites.push(req.url());});
  const checks=[];
  try {
    await login(page, role);
    if(mode==='preview') await page.addStyleTag({content:css});
    if(['m','s'].includes(role)) {
      const center=page.locator('#center');
      if(await center.locator('option', {hasText:'Centro A'}).count()) {
        await center.selectOption({label:'Centro A'});
        await page.waitForFunction(()=>document.querySelector('#practitioner-options label')?.querySelector('[data-practitioner-filter]'));
        await page.waitForTimeout(150);
      }
    }
    await page.locator('#new-booking').click();
    await page.locator('#modal').waitFor({state:'visible'});
    checks.push('route/modal');
    const availablePatients=await page.evaluate(async center=>{
      const url='/api/method/centrochange_core.operations.workspace.patient_search?'+new URLSearchParams({center,query:''});
      const response=await fetch(url,{credentials:'same-origin'});
      if(!response.ok)throw Error('Patient search denied: '+response.status);
      return (await response.json()).message.patients.map(row=>({id:row.name,label:row.patient_name}));
    },await page.locator('#center').inputValue());
    const availableProfessionals=await select(page,'practitioner').locator('option').evaluateAll(rows=>rows.filter(x=>x.value).map(x=>({id:x.value,label:x.textContent.trim()})));
    if(role==='a')assert(!availablePatients.some(x=>/Zeta/i.test(customerLabel(x.label))));
    if(role==='b')assert(!availablePatients.some(x=>/Alfa/i.test(customerLabel(x.label))));
    if(role==='c')assert.equal(availablePatients.length,0);

    if(availablePatients.length) {
      const candidate=availablePatients.find(x=>/Alfa/i.test(customerLabel(x.label))) || availablePatients[0];
      const display=customerLabel(candidate.label);
      const query=display.slice(0,Math.min(3,display.length));
      await input(page,'patient').fill(query);
      await list(page,'patient').locator('[role="option"]').first().waitFor();
      const geo=await geometry(page,'patient');
      assert.equal(geo.comboboxPosition,'relative'); assert(geo.optionHit && geo.menuRect.y < geo.dialogBottom,JSON.stringify(geo));
      assert.equal(geo.inputExpanded,'true');
      const labels=await list(page,'patient').locator('[role="option"]').allTextContents();
      assert(labels.some(x=>x.toLocaleLowerCase('it-IT').includes(query.toLocaleLowerCase('it-IT'))),JSON.stringify({role,query,labels}));
      await page.screenshot({path:path.join(output, `${role}-${viewport.width}-booking.png`)});
      await list(page,'patient').locator('[role="option"]').first().click();
      const patientId=await select(page,'patient').inputValue();
      assert(availablePatients.some(x=>x.id===patientId));
      checks.push('patient visible/hit/click/canonical');
    } else {
      await input(page,'patient').fill('Alfa');
      await page.waitForTimeout(450);
      assert.equal(await list(page,'patient').locator('[role="option"]').count(),0);
      checks.push('patient isolation/empty');
    }

    if(availableProfessionals.length) {
      const candidate=availableProfessionals.find(x=>/Beta/i.test(professionalLabel(x.label))) || availableProfessionals[0];
      const display=professionalLabel(candidate.label);
      const query=display.slice(0,Math.min(3,display.length));
      await input(page,'practitioner').fill(query.toLocaleLowerCase('it-IT'));
      await list(page,'practitioner').locator('[role="option"]').first().waitFor();
      const geo=await geometry(page,'practitioner');
      assert.equal(geo.comboboxPosition,'relative'); assert(geo.optionHit && geo.menuRect.y < geo.dialogBottom,JSON.stringify(geo));
      if(role==='m')await page.screenshot({path:path.join(output, `${role}-${viewport.width}-practitioner.png`)});
      await input(page,'practitioner').press('ArrowDown');
      assert(await input(page,'practitioner').getAttribute('aria-activedescendant'));
      await input(page,'practitioner').press('Enter');
      const professionalId=await select(page,'practitioner').inputValue();
      assert(availableProfessionals.some(x=>x.id===professionalId));
      checks.push('professional visible/hit/keyboard/canonical');
    } else checks.push('professional list empty for role/center');

    await input(page,'patient').fill('NO-SYNTHETIC-MATCH-79');
    await page.waitForTimeout(450);
    assert.equal(await list(page,'patient').locator('[role="option"]').count(),0);
    assert.match(await list(page,'patient').innerText(),/Nessun risultato autorizzato/);
    await input(page,'patient').press('Escape');
    assert.equal(await input(page,'patient').getAttribute('aria-expanded'),'false');
    await input(page,'patient').focus();
    await list(page,'patient').waitFor({state:'visible'});
    await page.locator('#modal-title').click();
    await page.waitForTimeout(180);
    assert.equal(await input(page,'patient').getAttribute('aria-expanded'),'false');
    await input(page,'patient').focus();
    await list(page,'patient').waitFor({state:'visible'});
    checks.push('empty/Escape/blur/reopen');
    if(role==='m' && viewport.width===1440) {
      const delayed='Alf';
      await page.route('**/api/method/centrochange_core.operations.workspace.patient_search*',async route=>{
        if(new URL(route.request().url()).searchParams.get('query')===delayed)await new Promise(resolve=>setTimeout(resolve,700));
        await route.continue();
      });
      await input(page,'patient').fill(delayed);
      await page.waitForTimeout(230);
      await input(page,'patient').fill('NO-SYNTHETIC-MATCH-79');
      await page.waitForTimeout(950);
      assert.equal(await list(page,'patient').locator('[role="option"]').count(),0);
      await page.unroute('**/api/method/centrochange_core.operations.workspace.patient_search*');
      checks.push('stale-response rejected');
    }
    assert.deepEqual(bookingWrites,[]); assert.deepEqual(errors,[]);
    return {role,viewport:viewport.width,checks,patients:availablePatients.length,professionals:availableProfessionals.length,errors,bookingWrites};
  } finally {await context.close();}
}

(async()=>{
  const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server']});
  const results=[];
  try {
    for(const role of ['m','s','a','b','c']) results.push(await testRole(browser,role,{width:1440,height:900}));
    results.push(await testRole(browser,'m',{width:390,height:844}));
    console.log(JSON.stringify({status:'PASS',mode,route:'/app/cc-unified-desk?cc_view=agenda',results,mutations:'NONE'}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error.stack);process.exitCode=1});
