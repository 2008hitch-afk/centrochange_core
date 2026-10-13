// Read-only browser review of every native client surface included in issue #75.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const fixture=JSON.parse(fs.readFileSync('/qa-fixture.json')).fixture;
const base='http://centrochange.local:8080';
const routes=[['pazienti','patient'],['professionisti','healthcare-practitioner'],['servizi','item'],['tariffe','item-price'],['fatture-pazienti','sales-invoice'],['fatture-professionisti','purchase-invoice'],['incassi','payment-entry'],['banca','bank-transaction'],['registro','cc-audit-event']];
(async()=>{
 let browser,context,page;const errors=[],results=[];
 async function open(state){browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage','--disable-gpu']});context=await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT',serviceWorkers:'block',...(state?{storageState:state}:{})});page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));}
 await open();await page.goto(base+'/login?redirect-to=/app/cc-unified-desk');await page.locator('#login_email').fill(fixture.users.m.name);await page.locator('#login_password').fill(fixture.users.m.password);await page.locator('.form-login button[type="submit"]').click();await page.locator('#cc-desk-sidebar').waitFor({timeout:90000});
 for(let i=0;i<routes.length;i++){
  const [label,route]=routes[i];await page.goto(base+'/app/'+route);await page.waitForTimeout(950);
  const data=await page.evaluate(()=>{const r=s=>{let e=document.querySelector(s);if(!e)return null;let x=e.getBoundingClientRect(),c=getComputedStyle(e);return {x:x.x,w:x.width,h:x.height,bg:c.backgroundColor}};return {url:location.href,title:document.title,sidebar:r('#cc-desk-sidebar'),nav:r('#cc-desk-global-nav'),list:r('.list-row-head'),form:r('.form-page'),head:r('.page-head'),dock:getComputedStyle(document.querySelector('#desk-dock')).display,oldbar:[...document.querySelectorAll('.cc-desk-routebar,.cc-desk-topnav')].some(x=>getComputedStyle(x).display!=='none'),overflow:document.documentElement.scrollWidth-innerWidth,body:document.body.className};});
  assert(data.sidebar&&data.nav&&data.head,`${label}: missing shell`);assert(Math.abs(data.nav.x-data.sidebar.w)<2,`${label}: misaligned shell`);assert.equal(data.dock,'none',`${label}: Frappe dock visible`);assert(!data.oldbar,`${label}: old horizontal bar`);assert(data.overflow<=2,`${label}: overflow`);assert(data.list||data.form,`${label}: no native list/form`);results.push({label,...data});
  await page.screenshot({path:'/qa-results/issue75-correction-native-'+label+'.jpg',type:'jpeg',quality:72});
  if(i===4){const state=await context.storageState();await browser.close();await open(state);}
 }
 await page.goto(base+'/app/patient');await page.locator('.list-row .list-subject a').first().click();await page.waitForTimeout(950);assert(await page.locator('.form-page').count()>0,'Patient detail form unavailable');await page.screenshot({path:'/qa-results/issue75-correction-native-patient-form.jpg',type:'jpeg',quality:72});
 for(const [device,width] of [['tablet',768],['telefono',390]]){
  await page.setViewportSize({width,height:844});await page.goto(base+'/app/patient');await page.waitForTimeout(950);
  assert(await page.locator('.cc-mobile-toggle').isVisible(),`${device}: mobile menu missing`);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)<=2,`${device}: native overflow`);
  await page.locator('.cc-mobile-toggle').click();await page.waitForFunction(()=>document.querySelector('#cc-desk-sidebar').getBoundingClientRect().x>=-1,null,{timeout:3000});
  await page.screenshot({path:'/qa-results/issue75-correction-native-'+device+'.jpg',type:'jpeg',quality:72});
 }
 assert.deepEqual(errors,[]);fs.writeFileSync('/qa-results/issue75-correction-native.json',JSON.stringify({results,errors},null,2));console.log('PASS native lists 9/9 and Patient form');await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
