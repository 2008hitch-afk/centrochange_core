// Reproduce the Healthcare Link dependency without widening DocPerm.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const fixture=JSON.parse(fs.readFileSync('/qa-fixture.json')).fixture;
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:900},locale:'it-IT'});
  const denied=[],errors=[];
  page.on('response',r=>{if(r.status()===403&&r.url().includes('Medical%20Department'))denied.push(r.url());});
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://centrochange.local:8080/login?redirect-to=/app/healthcare-practitioner');
  await page.locator('#login_email').fill(fixture.users.m.name);
  await page.locator('#login_password').fill(fixture.users.m.password);
  await page.locator('.form-login button[type="submit"]').click();
  await page.locator('.list-row-head').waitFor({timeout:30000});
  assert.equal(await page.locator('input[placeholder="Reparto"]').count(),0);
  await page.locator('.list-row .list-subject a').first().click();
  await page.locator('.form-page').waitFor({timeout:30000});
  assert.match(await page.locator('.page-head:visible').last().innerText(),/Professionista (Alfa|Beta)/);
  const department=page.locator('.frappe-control[data-fieldname="department"]');
  assert(await department.count()>0,'Healthcare field changed unexpectedly');
  assert.equal(await department.isVisible(),false,'unused department Link visible to client');
  assert.deepEqual(denied,[],'Medical Department request still triggered by client form/list');
  assert.deepEqual(errors,[],'JavaScript error in Practitioner form');
  await page.screenshot({path:'/qa-results/issue75-native-first-practitioner-form.jpg',type:'jpeg',quality:75});
  console.log(JSON.stringify({status:'PASS',standard_filter_removed:true,client_form_field_hidden:true,direct_permission:'tested separately as 403'}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
