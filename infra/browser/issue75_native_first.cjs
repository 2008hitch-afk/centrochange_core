// Issue #75: native-first visual acceptance on the sole DEV site.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const fixture=JSON.parse(fs.readFileSync('/qa-fixture.json')).fixture;
const base='http://centrochange.local:8080';
const routes=[
 ['home','/app/cc-unified-desk?cc_view=home'],
 ['agenda','/app/cc-unified-desk?cc_view=agenda'],
 ['ricerca-pazienti','/app/cc-unified-desk?cc_view=agenda&cc_ops_view=Pazienti'],
 ['pazienti','/app/patient'],
 ['professionisti','/app/healthcare-practitioner'],
 ['catalogo','/app/item'],
 ['finanza','/app/cc-unified-desk?cc_view=finance'],
 ['report','/app/cc-unified-desk?cc_view=professional'],
 ['registro','/app/cc-unified-desk?cc_view=audit'],
 ['home-ritorno','/app/cc-unified-desk?cc_view=home']
];
(async()=>{
 const errors=[];
 let browser,context,page;
 async function openBrowser(state){
  browser=await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server','--disable-dev-shm-usage','--disable-gpu']});
  context=await browser.newContext({viewport:{width:1440,height:900},locale:'it-IT',serviceWorkers:'block',...(state?{storageState:state}:{})});
  page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 }
 await openBrowser();
 await page.goto(base+'/login?redirect-to=/app/cc-unified-desk');
 await page.locator('#login_email').fill(fixture.users.m.name);
 await page.locator('#login_password').fill(fixture.users.m.password);
 await page.locator('.form-login button[type="submit"]').click();
 await page.locator('#cc-desk-sidebar').waitFor({timeout:90000});
 const watchChrome=()=>{const start=()=>{window.__ccVisualLeaks=[];const visible=e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return r.width>0&&r.height>0&&c.display!=='none'&&c.visibility!=='hidden'};const check=()=>{if(!document.body.classList.contains('cc-client-desk'))return;for(const e of document.querySelectorAll('#desk-dock,.body-sidebar-container,.cc-desk-routebar,.cc-desk-topnav'))if(visible(e))window.__ccVisualLeaks.push({url:location.href,node:e.id||e.className});for(const e of document.querySelectorAll('img[alt],.navbar-brand,.app-logo'))if(visible(e)&&/ERPNext|Frappe/i.test(e.alt||e.textContent||''))window.__ccVisualLeaks.push({url:location.href,node:'upstream-brand'});};new MutationObserver(check).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['class','style']});check();};if(document.body)start();else document.addEventListener('DOMContentLoaded',start,{once:true});};
 await page.addInitScript(watchChrome);
 await page.evaluate(watchChrome);
 const results=[];
 for(let i=0;i<routes.length;i++){
  const [name,path]=routes[i];
  if(i){
   const link=page.locator('#cc-desk-sidebar a[href="'+path+'"]');
   if(await link.count()){
    const details=link.first().locator('xpath=ancestor::details');
    if(await details.count()) await details.first().evaluate(el=>el.open=true);
    await link.first().click();
   } else await page.goto(base+path);
  } else await page.goto(base+path);
  if(name==='agenda'){
   await page.locator('#center').selectOption(fixture.centers[0]);
   await page.waitForFunction(()=>document.querySelectorAll('.calendar-day-header').length===7,null,{timeout:30000});
  }
  if(name==='finanza'){
   await page.locator('#center').selectOption(fixture.centers[0]);
   await page.waitForFunction(()=>document.querySelector('#finance-content')?.innerText.includes('100,00'),null,{timeout:30000});
  }
  if(name==='report'){
   await page.locator('#professional-center').selectOption(fixture.centers[0]);
  }
  if(['pazienti','professionisti','catalogo'].includes(name)) await page.locator('.list-row-head').waitFor({timeout:30000});
  if(name==='registro') await page.locator('#audit-content tbody tr').first().waitFor({timeout:30000});
  await page.waitForTimeout(1100);
  const data=await page.evaluate(()=>{
   const box=s=>{const x=document.querySelector(s);if(!x)return null;const r=x.getBoundingClientRect(),c=getComputedStyle(x);return {x:r.x,y:r.y,w:r.width,h:r.height,display:c.display,background:c.backgroundColor,border:c.borderTopColor}};
   const visible=s=>[...document.querySelectorAll(s)].filter(e=>{let r=e.getBoundingClientRect(),c=getComputedStyle(e);return r.width>0&&r.height>0&&c.visibility!=='hidden'&&c.display!=='none'}).length;
   return {url:location.href,sidebar:box('#cc-desk-sidebar'),nav:box('#cc-desk-global-nav'),main:box('.main-section'),body:box('#body'),nativeSidebar:visible('.body-sidebar-container'),dock:visible('#desk-dock'),oldBar:visible('.cc-desk-routebar, .cc-unified-nav, .navbar-horizontal'),pageHead:box('.page-head'),listHead:box('.list-row-head'),rows:visible('.list-row'),overflow:document.documentElement.scrollWidth-innerWidth,tabler:!!document.querySelector('#cc-tabler-core'),brand:[...document.querySelectorAll('img[alt],.navbar-brand,.app-logo')].filter(x=>{let r=x.getBoundingClientRect();return r.width&&r.height&&/ERPNext|Frappe/i.test(x.alt||x.textContent||'')}).length};
  });
  assert(data.sidebar&&data.nav&&data.main&&data.body,`${name}: shell incomplete`);
  assert(Math.abs(data.sidebar.x)<2&&data.sidebar.w>=210,`${name}: sidebar clipped ${JSON.stringify(data.sidebar)}`);
  assert(Math.abs(data.nav.x-data.sidebar.w)<2&&Math.abs(data.body.x-data.sidebar.w)<2,`${name}: shell alignment ${JSON.stringify(data)}`);
  assert.equal(data.nativeSidebar+data.dock+data.oldBar+data.brand,0,`${name}: upstream chrome visible`);
  assert(data.overflow<=2,`${name}: overflow ${data.overflow}`);
  assert.equal(data.tabler,false,`${name}: global Tabler overlay returned`);
  assert.equal(await page.evaluate(()=>getComputedStyle(document.body).fontFamily.includes('Times New Roman')),false,`${name}: Frappe CSS missing`);
  assert.equal(await page.evaluate(()=>[...document.querySelectorAll('link[rel=stylesheet]')].filter(x=>x.href.includes('/frappe/dist/css/')).every(x=>!!x.sheet)),true,`${name}: Frappe CSS unavailable`);
  if(name==='ricerca-pazienti'){
   const actions=await page.locator('#create-patient,#assign-by-uid,#issue-package').count();
   assert.equal(actions,3,'patient actions missing');
   const widths=await page.locator('#create-patient,#assign-by-uid,#issue-package').evaluateAll(nodes=>nodes.map(x=>x.getBoundingClientRect().width));
   assert(widths.every(w=>w<230),`patient actions oversized: ${widths}`);
  }
  if(name==='professionisti'){assert.equal(await page.locator('input[placeholder=Reparto]').count(),0,'Medical Department quick filter persists');}
  if(['pazienti','professionisti','catalogo'].includes(name)){
   assert(data.rows>0&&data.listHead,`${name}: native list missing`);
   assert(data.listHead.background!=='rgba(0, 0, 0, 0)',`${name}: native list header not styled`);
  }
  await page.screenshot({path:'/qa-results/issue75-native-first-'+name+'.jpg',type:'jpeg',quality:75,animations:'disabled'});
  assert.deepEqual(await page.evaluate(()=>window.__ccVisualLeaks||[]),[],`${name}: upstream chrome flashed`);
  results.push({name,...data});
  // The 512 MiB QA limit is retained. Recycle Chromium while keeping the
  // authenticated cookie/localStorage session after the sixth screenshot.
  if([4,7].includes(i)){const leaks=await page.evaluate(()=>window.__ccVisualLeaks||[]);assert.deepEqual(leaks,[],'chrome flashed during first session');const state=await context.storageState(),url=page.url();await browser.close();await openBrowser(state);await page.goto(url);await page.locator('#cc-desk-sidebar').waitFor();await page.evaluate(watchChrome);}
 }
 await page.goBack();await page.waitForTimeout(750);
 assert.equal(await page.locator('#cc-desk-sidebar').count(),1,'back navigation lost sidebar');
 await page.goForward();await page.reload();await page.locator('#cc-desk-sidebar').waitFor();
 assert.equal(await page.locator('#cc-desk-global-nav').count(),1,'refresh duplicated navbar');
 assert.deepEqual(await page.evaluate(()=>window.__ccVisualLeaks||[]),[],'chrome flashed during second session');
 assert.deepEqual(errors,[]);
 fs.writeFileSync('/qa-results/issue75-native-first-visual.json',JSON.stringify({results,errors},null,2));
 console.log('PASS native-first visual walkthrough',results.map(x=>x.name).join(' -> '));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
