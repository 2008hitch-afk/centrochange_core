/* Read-only visual rehearsal of native Frappe Form fields. CSS is injected only
   into this Chromium session; the shared DEV and its data are not changed. */
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const fixture = JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE, 'utf8'));
const users = (fixture.fixture || fixture).users;
const css = fs.readFileSync(process.env.CC_CANDIDATE_CSS, 'utf8');
const output = process.env.CC_OUTPUT_DIR;
const managerMode = process.env.CC_FORM_MANAGER === '1';
assert(output && (managerMode ? users?.m && users?.f : users?.s && users?.f), 'Private fixture and output path required');
fs.mkdirSync(output, {recursive:true, mode:0o700});
const base = process.env.CC_BASE_URL || 'http://centrochange.local:8082';
const browserIp = process.env.CC_BROWSER_IP || '127.0.0.1';
assert(['127.0.0.1','127.0.0.2'].includes(browserIp), 'Only isolated/DEV loopback targets allowed');
const forms = [
  ['patient','s'], ['healthcare-practitioner','s'],
  ['sales-invoice','f'], ['purchase-invoice','f'],
  ['item','s'], ['item-price','f'], ['appointment-type','s'],
  ['cc-center-service','s'], ['cc-package-template','s'],
  ['payment-entry','f'], ['bank-transaction','f'],
];
const requested = new Set((process.env.CC_ROUTES || '').split(',').filter(Boolean));

async function inspect(page) {
  return page.evaluate(() => {
    const visible = e => {const r=e.getBoundingClientRect(),s=getComputedStyle(e);
      return r.width>8 && r.height>8 && s.visibility!=='hidden' && s.display!=='none';};
    const fields=[...document.querySelectorAll('.form-page .frappe-control')].filter(visible);
    const controls=fields.flatMap(field=>[...field.querySelectorAll('.control-input .form-control')]
      .filter(visible).map(input=>{const s=getComputedStyle(input);
        return {field:field.dataset.fieldname||'',tag:input.tagName,empty:!input.value,
          editable:!input.disabled&&!input.readOnly,border:parseFloat(s.borderTopWidth),
          borderStyle:s.borderTopStyle,background:s.backgroundColor};}));
    const readonly=fields.flatMap(field=>[...field.querySelectorAll('.like-disabled-input')]
      .filter(visible).map(el=>{const s=getComputedStyle(el);return {
        field:field.dataset.fieldname||'',border:parseFloat(s.borderTopWidth),
        borderStyle:s.borderTopStyle,background:s.backgroundColor};}));
    return {route:location.pathname,client:document.body.classList.contains('cc-client-desk'),
      native:document.body.classList.contains('cc-native-view'),form:!!document.querySelector('.form-page'),
      controls,readonly};
  });
}

(async()=>{
  const browser=await chromium.launch({headless:true,args:[
    `--host-resolver-rules=MAP centrochange.local ${browserIp}`,
    '--no-proxy-server','--disable-dev-shm-usage']});
  const results=[];
  try {
    for (const width of [1440,390]) for (const role of managerMode ? ['m','f'] : ['s','f']) {
      const context=await browser.newContext({viewport:{width,height:900},locale:'it-IT',serviceWorkers:'block'});
      const page=await context.newPage();
      try {
        await page.goto(base+'/login');
        await page.locator('#login_email').fill(users[role].name);
        await page.locator('#login_password').fill(users[role].password);
        await page.getByRole('button',{name:'Continua'}).click();
        await page.waitForURL(u=>u.pathname.startsWith('/app/'),{timeout:12000});
        for (const [route] of forms.filter(x=>(managerMode ? (x[1]==='f'?'f':'m')===role : x[1]===role) && (!requested.size || requested.has(x[0])))) {
          const result={route,role,width};
          try {
            await page.goto(base+'/app/'+route,{waitUntil:'domcontentloaded'});
            const first=page.locator('.list-row .list-subject a,.list-row .level-left a[href]').first();
            if (await first.count()) {
              await first.click({timeout:8000});
              await page.locator('.form-page').waitFor({timeout:8000});
            }
            result.before=await inspect(page);
            if (!result.before.controls.some(x=>x.editable)) {
              await page.goto(base+'/app/'+route+'/new',{waitUntil:'domcontentloaded'});
              await page.locator('.form-page').waitFor({timeout:8000});
              result.before=await inspect(page);
              result.newUnsavedForm=true;
            }
            await page.screenshot({path:path.join(output,`${route}-${role}-${width}-before.png`),fullPage:true});
            await page.addStyleTag({content:css});
            result.after=await inspect(page);
            await page.screenshot({path:path.join(output,`${route}-${role}-${width}-after.png`),fullPage:true});
            const editable=result.after.controls.filter(x=>x.editable);
            const empty=editable.filter(x=>x.empty);
            result.status=!editable.length?'BLOCKED':editable.every(x=>x.border>=1&&x.borderStyle==='solid')
              && result.after.client && result.after.native?'PASS':'FAIL';
            if (!editable.length) result.reason='NO_EDITABLE_CONTROL_FOR_THIS_ROLE_OR_RECORD';
            result.counts={editable:editable.length,empty:empty.length,
              beforeInvisible:result.before.controls.filter(x=>x.editable&&x.border<1).length,
              afterInvisible:editable.filter(x=>x.border<1).length};
            if (route==='patient' && width===1440 && result.status==='PASS') {
              const field=page.locator('.form-page .frappe-control[data-fieldname="last_name"]:visible').first();
              await field.locator('input').focus();
              result.focus=await field.locator('input').evaluate(e=>({
                width:parseFloat(getComputedStyle(e).outlineWidth),
                color:getComputedStyle(e).outlineColor}));
              await page.screenshot({path:path.join(output,'patient-focus.png'),fullPage:true});
              await field.evaluate(e=>e.classList.add('has-error'));
              result.error=await field.locator('input').evaluate(e=>getComputedStyle(e).borderColor);
              await page.screenshot({path:path.join(output,'patient-error-preview.png'),fullPage:true});
              result.readonlyDistinct=result.after.readonly.some(x=>x.border>=1&&x.borderStyle==='dashed');
              result.dropdownVisible=result.after.controls.some(x=>x.field==='report_preference'&&x.tag==='SELECT'&&x.border>=1);
              if (result.focus.width<2 || !result.readonlyDistinct || !result.dropdownVisible || result.error!=='rgb(180, 35, 24)') result.status='FAIL';
              if (managerMode && process.env.CC_CLONE_SAVE === '1') {
                try {
                await field.evaluate(e=>e.classList.remove('has-error'));
                const first=page.locator('.frappe-control[data-fieldname="first_name"] input');
                const last=page.locator('.frappe-control[data-fieldname="last_name"] input');
                const sex=page.locator('.frappe-control[data-fieldname="sex"] input');
                const marker=`UX-SINTETICO-${Date.now()}`;
                await first.fill(marker);
                await last.fill('Prova');
                await sex.fill('Male');
                await sex.press('Tab');
                const invite=page.getByLabel('Invita come utente');
                if (await invite.count() && await invite.isChecked()) await invite.uncheck();
                await page.getByRole('button',{name:'Salva',exact:true}).click();
                await page.waitForFunction(()=>window.cur_frm && !cur_frm.is_new(),{timeout:12000});
                const saved=await page.evaluate(()=>({name:cur_frm.doc.name,first:cur_frm.doc.first_name}));
                await page.reload();
                await page.locator('.form-page').waitFor({timeout:10000});
                const persisted=await page.locator('.frappe-control[data-fieldname="first_name"] input').inputValue();
                result.syntheticSave={status:saved.first===marker&&persisted===marker?'PASS':'FAIL',
                  persistedAfterRefresh:persisted===marker};
                } catch (error) {
                  result.syntheticSave={status:'FAIL',reason:String(error.message).split('\n')[0]};
                }
              }
            }
          } catch (error) {result.status='BLOCKED';result.reason=String(error.message).split('\n')[0];}
          results.push(result);
          console.log(`${width} ${route} ${result.status}`);
        }
      } finally {await context.close();}
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(results,null,2),{mode:0o600});
  console.log(JSON.stringify({pass:results.filter(x=>x.status==='PASS').length,
    fail:results.filter(x=>x.status==='FAIL').length,
    blocked:results.filter(x=>x.status==='BLOCKED').length,total:results.length}));
  if (results.some(x=>x.status==='FAIL')) process.exitCode=2;
})().catch(error=>{console.error(error.message);process.exitCode=1;});
