// Issue #75 premium native review. Runs against the deployed single-stack site.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const fixture=JSON.parse(fs.readFileSync('/qa-fixture.json')).fixture;
const base='http://centrochange.local:8080';
const native=[
 ['servizi','item'],['tariffe','item-price'],['pazienti','patient'],
 ['professionisti','healthcare-practitioner'],['tipi-seduta','appointment-type'],
 ['servizi-centro','cc-center-service'],['modelli-pacchetto','cc-package-template'],
 ['fatture-pazienti','sales-invoice'],['fatture-professionisti','purchase-invoice'],
 ['incassi','payment-entry'],['banca','bank-transaction']
];
const slice=Number(process.env.CC_TEST_SLICE||0);
const selected=slice ? native.slice((slice-1)*4,slice*4) : native;
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage','--disable-gpu']});
 const context=await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT',serviceWorkers:'block',recordVideo:{dir:'/qa-results/video',size:{width:1440,height:900}}});
 const page=await context.newPage(),errors=[],results=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>{
  window.__ccVisible=el=>{if(!el)return false;const r=el.getBoundingClientRect(),c=getComputedStyle(el);return r.width>0&&r.height>0&&c.display!=='none'&&c.visibility!=='hidden'};
  window.__ccEarlyBrand=[];
  const scan=()=>{for(const el of document.querySelectorAll('img,.navbar-brand,.app-logo')){
   const r=el.getBoundingClientRect(),c=getComputedStyle(el);
   if(r.width&&r.height&&c.display!=='none'&&c.visibility!=='hidden'&&/erpnext|frappe|marley/i.test([el.src,el.alt,el.textContent].join(' ')))
    window.__ccEarlyBrand.push({url:location.href,at:performance.now(),value:[el.src,el.alt,el.textContent].join(' ').slice(0,180)});
  }};
  const start=()=>{new MutationObserver(scan).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['src','style','class']});scan()};
  if(document.documentElement)start();else document.addEventListener('DOMContentLoaded',start,{once:true});
 });
 await page.goto(base+'/login?redirect-to=/app/cc-unified-desk');
 await page.locator('#login_email').fill(fixture.users.m.name);
 await page.locator('#login_password').fill(fixture.users.m.password);
 await page.locator('.form-login button[type=submit]').click();
 await page.locator('#cc-desk-sidebar').waitFor({timeout:90000});
 for(const [label,route] of selected){
  console.log('CHECK',label);
  await page.goto(base+'/app/'+route);
  await page.locator('.list-row-head').waitFor({timeout:30000});
  await page.waitForTimeout(500);
  const list=await page.evaluate(()=>({shell:window.__ccVisible(document.querySelector('#cc-desk-sidebar')),rows:[...document.querySelectorAll('.list-row')].filter(window.__ccVisible).length,
   color:getComputedStyle(document.querySelector('.list-row-head')).backgroundColor,overflow:document.documentElement.scrollWidth-innerWidth,early:window.__ccEarlyBrand||[]}));
  assert(list.shell&&list.rows>0&&list.overflow<=2,`${label} list layout ${JSON.stringify(list)}`);
  assert.deepEqual(list.early,[],`${label} upstream branding on list`);
  await page.screenshot({path:`/qa-results/${label}-list.jpg`,type:'jpeg',quality:76});
  await page.locator('.list-row .list-subject a').first().click();
  await page.locator('.form-layout').waitFor({timeout:30000});
  await page.waitForTimeout(650);
  const form=await page.evaluate(()=>({shell:window.__ccVisible(document.querySelector('#cc-desk-sidebar')),title:document.querySelector('.page-head')?.innerText?.slice(0,130),
   width:document.querySelector('.form-layout')?.getBoundingClientRect().width,overflow:document.documentElement.scrollWidth-innerWidth,
   tabs:[...document.querySelectorAll('.form-tabs-list .nav-item')].filter(window.__ccVisible).map(x=>x.innerText.trim()),
   css:getComputedStyle(document.body).getPropertyValue('--theme-accent').trim(),early:window.__ccEarlyBrand||[],doctype:cur_frm?.doctype}));
  assert(form.shell&&form.width>550&&form.overflow<=2,`${label} form layout ${JSON.stringify(form)}`);
  assert.equal(form.css,'#12665f',`${label} premium CSS absent`);
  assert.deepEqual(form.early,[],`${label} upstream branding on form`);
  if(label==='servizi'){
   assert.deepEqual(form.tabs,['Dettagli','Tariffe','Collegamenti'],'service operational tabs');
   assert(form.width>850,'service form still reserves space for hidden sidebar');
   assert(await page.locator('button:has-text("Dettagli tecnici")').count(),'technical Item path missing');
  }
  await page.screenshot({path:`/qa-results/${label}-form.jpg`,type:'jpeg',quality:76});
  results.push({label,list:{rows:list.rows,color:list.color},form:{title:form.title,width:form.width,tabs:form.tabs,doctype:form.doctype}});
 }
 assert.deepEqual(errors,[],'browser JavaScript errors');
 fs.writeFileSync('/qa-results/premium-native.json',JSON.stringify({results,errors},null,2));
 console.log('PASS premium native lists and forms',results.length);
 await context.close();await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
