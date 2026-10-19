// Read-only Owner UAT inventory on the served single-stack DEV. No request mocking.
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {assetResponseError} = require('./issue139_asset_response.cjs');

const base = process.env.CC_BASE_URL || 'http://centrochange.local:8082';
const fixture = JSON.parse(fs.readFileSync(process.env.CC_ISSUE137_FIXTURE, 'utf8'));
const users = (fixture.fixture || fixture).users;
const output = process.env.CC_ISSUE137_OUTPUT;
const role = process.env.CC_ISSUE137_ROLE || 'm';
const width = Number(process.env.CC_ISSUE137_WIDTH || 1440);
const height = width < 600 ? 844 : 900;
if (!users?.[role] || !output || ![390, 1440].includes(width)) throw Error('Private fixture, output, role and viewport required');
fs.mkdirSync(output, {recursive:true, mode:0o700});

const native = new Set(['patient','healthcare-practitioner','sales-invoice','purchase-invoice',
  'payment-entry','bank-transaction','item','item-price','appointment-type','cc-center-service','cc-package-template']);
const safePath = u => {try {const x=new URL(u,base); return x.pathname + x.search;} catch {return 'invalid-url';}};
const safePathOnly = u => {try {return new URL(u,base).pathname;} catch {return 'invalid-url';}};
const slug = (text, index) => `${String(index).padStart(2,'0')}-${text.normalize('NFKD').replace(/[^a-zA-Z0-9]+/g,'-').replace(/^-|-$/g,'').toLowerCase().slice(0,45)}`;

async function login(page) {
  await page.goto(base+'/login', {waitUntil:'domcontentloaded'});
  await page.locator('#login_email').fill(users[role].name);
  await page.locator('#login_password').fill(users[role].password);
  await page.getByRole('button',{name:'Continua'}).click();
  await page.waitForURL(url => /^\/(app|desk)(?:\/|$)/.test(new URL(url).pathname), {timeout:30000});
  await page.locator('#cc-desk-sidebar').waitFor({timeout:20000});
}

async function measure(page) {
  return page.evaluate(() => {
    const visible = el => {const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>1&&r.height>1&&s.display!=='none'&&s.visibility!=='hidden';};
    const rect = el => {if(!el)return null;const r=el.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)};};
    const icons=[...document.querySelectorAll('svg, .icon, .icon img, .sidebar-item-icon img')].filter(visible).map(el=>({tag:el.tagName,box:rect(el)}));
    const body=document.body.innerText || '';
    const shell=document.querySelector('#cc-desk-sidebar'), nav=document.querySelector('#cc-desk-global-nav');
    const activeSidebarLinks=[...document.querySelectorAll('#cc-desk-sidebar a.active')]
      .filter(visible).map(el=>el.textContent.trim());
    const list=document.querySelector('.list-row-head, .list-row-container, .listview-body');
    const form=document.querySelector('.form-page');
    const main=document.querySelector('#cc-main, .layout-main-section, .page-content');
    const technical=[...document.querySelectorAll('a,button')].filter(visible).filter(el=>/ERPNext|Marley|Frappe/i.test(el.innerText||el.getAttribute('aria-label')||'')).length;
    const clippedBadges=[...document.querySelectorAll('.list-row-container .es-badge')].filter(visible).filter(badge=>{
      const b=badge.getBoundingClientRect();
      for(let parent=badge.parentElement;parent;parent=parent.parentElement){
        if(!['hidden','clip'].includes(getComputedStyle(parent).overflowX))continue;
        const r=parent.getBoundingClientRect();
        if(b.left<r.left-2||b.right>r.right+2)return true;
      }
      return false;
    }).length;
    const center=document.querySelector('#center');
    return {
      pathname:location.pathname+location.search,title:document.title,
      shell:rect(shell),navbar:rect(nav),list:rect(list),form:rect(form),main:rect(main),
      activeSidebarLinks,
      pageHead:rect(document.querySelector('.page-head')),blank:body.trim().length<30,
      bodyChars:body.length,overflowPx:Math.max(0,document.documentElement.scrollWidth-innerWidth),
      maxIconPx:Math.round(Math.max(0,...icons.map(x=>Math.max(x.box.width,x.box.height)))),
      oversizedIcons:icons.filter(x=>Math.max(x.box.width,x.box.height)>96).length,
      clippedBadges,
      stylesheetCount:[...document.styleSheets].length,fontStatus:document.fonts.status,
      hasLoading:[...document.querySelectorAll('.loading, .cc-inline-loading')].some(visible),
      technicalBrandControls:technical,
      centerOptions:center?[...center.options].map(x=>x.textContent.trim()).filter(Boolean):[],
      visibleActionCount:[...document.querySelectorAll('button,a')].filter(visible).length
    };
  });
}

async function run() {
  const browserIp=process.env.CC_ISSUE139_BROWSER_IP || '127.0.0.1';
  if (!['127.0.0.1','127.0.0.2'].includes(browserIp)) throw Error('Unsupported browser loopback target');
  const browser=await chromium.launch({headless:true,args:[`--host-resolver-rules=MAP centrochange.local ${browserIp}`,'--no-proxy-server','--disable-dev-shm-usage']});
  const context=await browser.newContext({viewport:{width,height},locale:'it-IT',timezoneId:'Europe/Rome',serviceWorkers:'block'});
  const page=await context.newPage();
  const unexpectedMutations=[];
  page.on('request',req=>{
    if (['GET','HEAD','OPTIONS'].includes(req.method())) return;
    const url=safePathOnly(req.url());
    if (/\/api\/method\/(?:login|logout)$/.test(url)||url==='/socket.io/'||
        /\/api\/method\/frappe\.(?:core\.doctype\.session_default_settings\.session_default_settings\.get_session_default_values|desk\.desk_page\.getpage|desk\.listview\.get_list_settings|desk\.reportview\.get|desk\.form\.load\.getdoctype)$/.test(url)) return;
    unexpectedMutations.push({method:req.method(),path:url});
  });
  try {
    await login(page);
    const menu=await page.locator('#cc-desk-sidebar a[href]').evaluateAll(nodes=>nodes.map(x=>({label:x.textContent.trim(),href:x.getAttribute('href')})).filter(x=>x.label&&x.href));
    assert(menu.length>0,'No client sidebar links');
    const routes=[];const seen=new Set();
    for(const item of menu){const key=safePath(item.href);if(!seen.has(key)){seen.add(key);routes.push({...item,key});}}
    const results=[];
    for(let i=0;i<routes.length;i++){
      const item=routes[i], errors=[], assetErrors=[], assetConsoleErrors=[], apiErrors=[], realtimeErrors=[], resourceErrors=[], failedRequests=[];
      const onPageError=e=>errors.push(String(e.message).slice(0,300));
      const onConsole=m=>{
        if(m.type()!=='error')return;
        const message=m.text().slice(0,300);
        if(/socket\.io|realtime/i.test(message)||safePathOnly(m.location().url||'').startsWith('/socket.io/')) realtimeErrors.push(message);
        else if(/Refused to apply style|Refused to execute script/.test(message)||
          /Failed to load resource/.test(message)&&/\.(?:css|js|svg|woff2?|png)(?:\?|$)/i.test(m.location().url||''))
          assetConsoleErrors.push(message);
        else if(/Failed to load resource/.test(message))resourceErrors.push({message,path:safePathOnly(m.location().url||'')});
        else errors.push(message);
      };
      const onResponse=r=>{
        if(!/\.(?:css|js|svg|woff2?|png)(?:\?|$)/i.test(r.url()))return;
        const kind=/\.css(?:\?|$)/i.test(r.url())?'css':/\.js(?:\?|$)/i.test(r.url())?'js':'other';
        const problem=assetResponseError(r,kind);
        if(problem) assetErrors.push({path:safePath(r.url()),...problem});
      };
      const onApiResponse=r=>{if(r.status()>=400&&safePathOnly(r.url()).startsWith('/api/'))
        apiErrors.push({status:r.status(),path:safePath(r.url())});};
      const onOtherResponse=r=>{if(r.status()<400)return;const p=safePathOnly(r.url());
        if(p.startsWith('/socket.io/'))realtimeErrors.push(`HTTP ${r.status()} ${p}`);
        else if(!p.startsWith('/api/')&&!/\.(?:css|js|svg|woff2?|png)$/.test(p))
          resourceErrors.push({status:r.status(),path:p});};
      const onFailed=req=>failedRequests.push({path:safePath(req.url()),reason:req.failure()?.errorText||'failed'});
      page.on('pageerror',onPageError);page.on('console',onConsole);page.on('response',onResponse);page.on('response',onApiResponse);page.on('response',onOtherResponse);page.on('requestfailed',onFailed);
      let response,metrics=null, navigationError=null;
      try {
        response=await page.goto(new URL(item.href,base).href,{waitUntil:'domcontentloaded',timeout:30000});
        await page.waitForTimeout(1100);
        metrics=await measure(page);
      } catch(error){navigationError=String(error.message).slice(0,300);}
      const file=slug(item.label,i)+`.png`;
      try {await page.screenshot({path:path.join(output,`${role}-${width}-${file}`),fullPage:true,animations:'disabled',timeout:15000});}
      catch(error){errors.push('screenshot: '+String(error.message).slice(0,150));}
      page.off('pageerror',onPageError);page.off('console',onConsole);page.off('response',onResponse);page.off('response',onApiResponse);page.off('response',onOtherResponse);page.off('requestfailed',onFailed);
      const isNative=native.has(item.key.split('/').pop());
      const reasons=[];
      if(navigationError)reasons.push('NAVIGATION');
      if(!response||response.status()>=400)reasons.push('HTTP');
      if(metrics?.blank||!metrics?.main)reasons.push('BLANK_OR_MAIN_MISSING');
      if(isNative&&!metrics?.list&&!metrics?.form)reasons.push('NATIVE_LIST_FORM_MISSING');
      if(metrics?.oversizedIcons)reasons.push('OVERSIZED_ICONS');
      if(metrics?.clippedBadges)reasons.push('CLIPPED_STATUS_BADGES');
      if(metrics?.overflowPx>3)reasons.push('HORIZONTAL_OVERFLOW');
      if(!metrics?.shell||!metrics?.navbar)reasons.push('SHELL_MISSING');
      if(metrics?.activeSidebarLinks?.length!==1)reasons.push('SIDEBAR_ACTIVE_COUNT');
      if(assetErrors.length||assetConsoleErrors.length)reasons.push('ASSET_HTTP_OR_MIME_ERROR');
      if(apiErrors.length)reasons.push('API_HTTP_ERROR');
      if(realtimeErrors.length)reasons.push('REALTIME_ERROR');
      if(resourceErrors.length)reasons.push('RESOURCE_HTTP_ERROR');
      if(errors.length)reasons.push('JS_ERROR');
      const row={label:item.label,route:item.key,native:isNative,http:response?.status()||null,
        status:reasons.length?'FAIL':'PASS',reasons,metrics,errors,assetErrors,assetConsoleErrors,apiErrors,realtimeErrors,resourceErrors,failedRequests,screenshot:file};
      results.push(row);
      console.error(`${role} ${width} ${i+1}/${routes.length} ${item.label}: ${row.status}${reasons.length?' '+reasons.join(','):''}`);
    }
    const result={role,width,menuCount:menu.length,uniqueRoutes:routes.length,results,
      unexpectedMutations,summary:{pass:results.filter(x=>x.status==='PASS').length,fail:results.filter(x=>x.status==='FAIL').length}};
    fs.writeFileSync(path.join(output,`issue137-${role}-${width}.json`),JSON.stringify(result,null,2));
    console.log(JSON.stringify({role,width,summary:result.summary,uniqueRoutes:routes.length,unexpectedMutations:unexpectedMutations.length}));
  } finally {await browser.close();}
}
run().catch(e=>{console.error(e.stack);process.exitCode=1;});
