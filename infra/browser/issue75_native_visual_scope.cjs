/* Read-only visual comparison on the served DEV. Candidate CSS is browser-only. */
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const fixture=JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE,'utf8'));
const users=(fixture.fixture||fixture).users;
const css=fs.readFileSync(process.env.CC_CANDIDATE_CSS,'utf8');
const output=process.env.CC_OUTPUT_DIR;
assert(output&&users?.s&&users?.f,'Private fixture and output required');
fs.mkdirSync(output,{recursive:true,mode:0o700});
const base=process.env.CC_BASE_URL||'http://centrochange.local:8082';
const target=process.env.CC_BROWSER_IP||'127.0.0.1';
assert(['127.0.0.1','127.0.0.2'].includes(target),'Loopback browser target required');
const routes=[
  ['patient','s'],['healthcare-practitioner','s'],['item','s'],
  ['appointment-type','s'],['cc-center-service','s'],['cc-package-template','s'],
  ['sales-invoice','f'],['purchase-invoice','f'],['item-price','f'],
  ['payment-entry','f'],['bank-transaction','f'],
];

async function measure(page) {
  return page.evaluate(()=>{
    const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);
      return r.width>2&&r.height>2&&s.display!=='none'&&s.visibility!=='hidden';};
    const rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();
      return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right};};
    const icons=[...document.querySelectorAll('.icon,.es-icon,button svg,#cc-desk-sidebar svg')]
      .filter(vis).map(e=>Math.max(e.getBoundingClientRect().width,e.getBoundingClientRect().height));
    const fields=[...document.querySelectorAll('.form-page .frappe-control')].filter(vis);
    const inputs=fields.flatMap(f=>[...f.querySelectorAll('.control-input .form-control')]
      .filter(vis).map(e=>{const s=getComputedStyle(e);return {
        field:f.dataset.fieldname||'',empty:!e.value,editable:!e.disabled&&!e.readOnly,
        border:parseFloat(s.borderTopWidth),style:s.borderTopStyle};}));
    const readonly=fields.flatMap(f=>[...f.querySelectorAll('.like-disabled-input')]
      .filter(vis).map(e=>({field:f.dataset.fieldname||'',border:parseFloat(getComputedStyle(e).borderTopWidth),
        style:getComputedStyle(e).borderTopStyle})));
    const sidebar=rect(document.querySelector('#cc-desk-sidebar'));
    const main=rect([...document.querySelectorAll('.layout-main-section,.form-layout,.page-content,#cc-main')].find(vis));
    return {pathname:location.pathname,client:document.body.classList.contains('cc-client-desk'),
      native:document.body.classList.contains('cc-native-view'),
      list:!!document.querySelector('.list-row-head,.list-row-container,.listview-body'),
      form:!!document.querySelector('.form-page'),sidebar,main,
      overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),
      maxIcon:Math.round(Math.max(0,...icons)),oversizedIcons:icons.filter(x=>x>96).length,
      activeLinks:document.querySelectorAll('#cc-desk-sidebar a.active').length,
      modal:!!document.querySelector('.modal.show'),inputs,readonly,
      bodyChars:(document.body.innerText||'').trim().length};
  });
}

async function capture(page,route,role,width,kind,rows) {
  const before=await measure(page);
  const name=`${route}-${role}-${width}-${kind}`;
  await page.screenshot({path:path.join(output,name+'-before.png'),fullPage:true,animations:'disabled'});
  const previewStyle=await page.addStyleTag({content:css});
  const after=await measure(page);
  await page.screenshot({path:path.join(output,name+'-preview.png'),fullPage:true,animations:'disabled'});
  await previewStyle.evaluate(e=>e.remove());
  const reasons=[];
  if(!after.client||!after.native||!(kind==='list'?after.list:after.form)) {
    rows.push({route,role,width,kind,status:'BLOCKED',reason:'ROLE_CANNOT_OPEN_NATIVE_SURFACE',before,after});
    console.error(`${width} ${route} ${kind} BLOCKED ROLE_CANNOT_OPEN_NATIVE_SURFACE`);
    return;
  }
  if(after.bodyChars<40)reasons.push('BLANK');
  if(after.modal)reasons.push('MODAL_OBSCURES_VIEW');
  if(after.oversizedIcons)reasons.push('OVERSIZED_ICON');
  if(after.overflow>3)reasons.push('HORIZONTAL_OVERFLOW');
  if(width===1440&&after.sidebar&&after.main&&after.main.w>0&&after.main.x<after.sidebar.right-3)reasons.push('SIDEBAR_OVERLAP');
  if(after.activeLinks>1)reasons.push('MULTIPLE_ACTIVE_LINKS');
  if(kind==='form'&&after.inputs.some(x=>x.editable&&(x.border<1||x.style!=='solid')))
    reasons.push('INVISIBLE_EDITABLE');
  if(kind==='form'&&after.readonly.some(x=>x.border<1||x.style!=='dashed'))reasons.push('READONLY_NOT_DISTINCT');
  const row={route,role,width,kind,status:reasons.length?'FAIL':'PASS',reasons,before,after};
  rows.push(row);
  console.error(`${width} ${route} ${kind} ${row.status}${reasons.length?' '+reasons.join(','):''}`);
}

(async()=>{
  const browser=await chromium.launch({headless:true,args:[
    `--host-resolver-rules=MAP centrochange.local ${target}`,
    '--no-proxy-server','--disable-dev-shm-usage']});
  const rows=[];
  const selected=new Set((process.env.CC_ONLY_ROUTES||'').split(',').filter(Boolean));
  assert([...selected].every(x=>routes.some(y=>y[0]===x)),'Unknown route filter');
  try {
    const onlyRole=process.env.CC_ONLY_ROLE;
    assert(!onlyRole||['s','f'].includes(onlyRole),'Unsupported role filter');
    for(const width of [1440,390]) for(const role of (onlyRole?[onlyRole]:['s','f'])) {
      const context=await browser.newContext({viewport:{width,height:900},locale:'it-IT',
        timezoneId:'Europe/Rome',serviceWorkers:'block'});
      const page=await context.newPage();
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      try {
        await page.goto(base+'/login');
        await page.locator('#login_email').fill(users[role].name);
        await page.locator('#login_password').fill(users[role].password);
        await page.getByRole('button',{name:'Continua'}).click();
        await page.locator('#cc-desk-sidebar').waitFor({timeout:15000});
        for(const [route,owner] of routes.filter(x=>x[1]===role&&(!selected.size||selected.has(x[0])))) {
          try {
            await page.goto(base+'/app/'+route,{waitUntil:'domcontentloaded'});
            await page.waitForTimeout(900);
            await capture(page,route,role,width,'list',rows);
            const first=page.locator('.list-row .list-subject a,.list-row .level-left a[href]').first();
            if(!await first.count()) {rows.push({route,role,width,kind:'form',status:'BLOCKED',reason:'NO_RECORD'});continue;}
            await first.click({timeout:8000});
            await page.locator('.form-page').waitFor({timeout:8000});
            await page.waitForTimeout(500);
            // Dismiss only the permission explanation in this read-only
            // browser session, so the underlying native document is visible.
            await page.evaluate(()=>{
              for(const dialog of document.querySelectorAll('.modal.show'))
                dialog.querySelector('.modal-header button')?.click();
            });
            await page.keyboard.press('Escape');
            await capture(page,route,role,width,'form',rows);
          } catch(e){rows.push({route,role,width,status:'BLOCKED',reason:String(e.message).split('\n')[0]});}
        }
      } finally {await context.close();}
      if(errors.length)rows.push({role,width,status:'FAIL',reason:`JS_PAGE_ERROR_COUNT_${errors.length}`});
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(rows,null,2),{mode:0o600});
  console.log(JSON.stringify({pass:rows.filter(x=>x.status==='PASS').length,
    fail:rows.filter(x=>x.status==='FAIL').length,
    blocked:rows.filter(x=>x.status==='BLOCKED').length,total:rows.length}));
  if(rows.some(x=>x.status==='FAIL'))process.exitCode=2;
})().catch(e=>{console.error(e.message);process.exitCode=1});
