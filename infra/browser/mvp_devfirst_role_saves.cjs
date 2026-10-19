// Exact synthetic fixture only. Browser saves must survive refresh; output omits identities.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const fixture=JSON.parse(fs.readFileSync(process.env.CC_ROLE_FIXTURE,'utf8'));
const output=process.env.CC_ROLE_OUTPUT;
const base=process.env.CC_BASE_URL;
const checks=[];
let stage='start';
async function setCenter(page){
  await page.waitForFunction(center=>Array.from(document.querySelector('#center')?.options||[]).some(option=>option.value===center),fixture.centers[0]);
  await page.locator('#center').evaluate((element,center)=>{element.value=center;element.dispatchEvent(new Event('change',{bubbles:true}));},fixture.centers[0]);
}

async function login(browser,role,width){
  const context=await browser.newContext({locale:'it-IT',viewport:{width,height:844},serviceWorkers:'block'});
  const page=await context.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(e.name));
  await page.goto(base+'/login?redirect-to=/centrochange');
  await page.locator('#login_email').fill(fixture.users[role].name);
  await page.locator('#login_password').fill(fixture.users[role].password);
  await page.getByRole('button',{name:'Continua'}).click();
  await setCenter(page);
  await page.locator('#week-date').fill('2099-01-12');
  await page.locator('#week-date').dispatchEvent('change');
  await page.waitForFunction(()=>!document.querySelector('#main-content')?.textContent.includes('Caricamento'));
  return {page,context,errors};
}

async function choose(page,name,value){
  const select=page.locator('#modal select[name='+name+']');
  const input=select.locator('xpath=preceding-sibling::div[contains(@class,"cc-combobox")]').locator('input');
  await input.fill(name==='patient'?'OWN':value);
  await select.locator('xpath=preceding-sibling::div[contains(@class,"cc-combobox")]').locator('[role="option"]').first().click();
  assert.equal(await select.inputValue(),value);
}

async function save(page,method){
  const pending=page.waitForResponse(r=>r.url().includes(method)&&r.request().method()==='POST');
  await page.locator('#modal-submit').click();
  const response=await pending;
  assert.equal(response.status(),200,'save rejected');
  await page.locator('#modal').waitFor({state:'hidden'});
  return (await response.json()).message;
}

(async()=>{
  const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage']});
  try{
    stage='manager booking desktop';
    let {page,context,errors}=await login(browser,'m',1440);
    await page.locator('#new-booking').click();
    await choose(page,'patient',fixture.patients[0]);
    await choose(page,'practitioner',fixture.practitioners[0]);
    await page.locator('#modal select[name=service]').selectOption(fixture.catalog['Appointment Type'][0]);
    await page.locator('#modal [name=date]').fill('2099-01-12');
    await page.locator('#modal [name=time]').fill('09:00');
    await page.locator('#modal [name=reason]').fill(fixture.tag+' role-save');
    const booked=await save(page,'scheduling.booking.book');
    assert(booked.name);
    await page.reload();
    await setCenter(page);
    await page.locator('#week-date').fill('2099-01-12');
    await page.locator('#week-date').dispatchEvent('change');
    await page.locator('[data-name="'+booked.name+'"]').waitFor();
    checks.push({role:'m',viewport:'desktop',step:'booking-save-refresh',pass:true});
    assert.deepEqual(errors,[]);
    await context.close();

    stage='secretariat note mobile';
    ({page,context,errors}=await login(browser,'s',390));
    await page.locator('[data-name="'+booked.name+'"]').click();
    await page.getByRole('tab',{name:'Note'}).click();
    await page.getByRole('button',{name:'Aggiungi nota organizzativa'}).click();
    await page.locator('#modal textarea[name=content]').fill(fixture.tag+' mobile organizational note');
    await save(page,'operations.notes.add_note');
    await page.reload();
    await setCenter(page);
    await page.locator('#week-date').fill('2099-01-12');
    await page.locator('#week-date').dispatchEvent('change');
    await page.locator('[data-name="'+booked.name+'"]').click();
    await page.getByRole('tab',{name:'Note'}).click();
    await page.getByText(fixture.tag+' mobile organizational note').waitFor();
    checks.push({role:'s',viewport:'mobile',step:'note-save-refresh',pass:true});
    assert.deepEqual(errors,[]);
    await context.close();

    stage='professional private note desktop';
    ({page,context,errors}=await login(browser,'a',1440));
    await page.locator('[data-name="'+booked.name+'"]').click();
    await page.getByRole('tab',{name:'Note'}).click();
    await page.getByRole('button',{name:'Aggiungi nota riservata'}).click();
    await page.locator('#modal textarea[name=content]').fill(fixture.tag+' private note');
    await save(page,'operations.notes.add_note');
    await page.reload();
    await setCenter(page);
    await page.locator('#week-date').fill('2099-01-12');
    await page.locator('#week-date').dispatchEvent('change');
    await page.locator('[data-name="'+booked.name+'"]').click();
    await page.getByRole('tab',{name:'Note'}).click();
    await page.getByText(fixture.tag+' private note').waitFor();
    checks.push({role:'a',viewport:'desktop',step:'private-note-save-refresh',pass:true});
    assert.deepEqual(errors,[]);
    await context.close();

    for(const role of ['b','c']){
      stage=role+' denied';
      ({page,context,errors}=await login(browser,role,390));
      const status=await page.evaluate(async patient=>{
        const response=await fetch('/api/resource/Patient/'+encodeURIComponent(patient));
        return response.status;
      },fixture.patients[0]);
      assert.equal(status,403);
      checks.push({role,viewport:'mobile',step:'direct-patient-denied',pass:true});
      assert.deepEqual(errors,[]);
      await context.close();
    }
    fs.writeFileSync(path.join(output,'role-saves.json'),JSON.stringify({status:'PASS',checks}));
    console.log(JSON.stringify({status:'PASS',checks:checks.length}));
  }finally{await browser.close();}
})().catch(e=>{fs.writeFileSync(path.join(output,'role-saves-error.json'),JSON.stringify({stage,type:e.name,detail:String(e.message).slice(0,160)}));console.error(e.name+': '+stage);process.exitCode=2;});
