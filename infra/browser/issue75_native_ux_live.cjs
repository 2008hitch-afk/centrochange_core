/* Read-only native Form UX proof. Screenshots remain in a private directory. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const base = process.env.CC_BASE_URL || 'http://centrochange.local:8082';
const fixture = JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE, 'utf8'));
const users = (fixture.fixture || fixture).users;
const output = process.env.CC_UX_OUTPUT;
assert(output && users?.m && users?.f, 'private fixture and output required');
fs.mkdirSync(output, {recursive:true, mode:0o700});
const routes = [
  ['patient','m'],['healthcare-practitioner','m'],['sales-invoice','m'],
  ['purchase-invoice','f'],['payment-entry','f'],['bank-transaction','f'],
  ['item','m'],['item-price','m'],['appointment-type','m'],
  ['cc-center-service','m'],['cc-package-template','m']
];

async function login(page, user) {
  await page.goto(base+'/login', {waitUntil:'domcontentloaded'});
  await page.locator('#login_email').fill(user.name);
  await page.locator('#login_password').fill(user.password);
  await page.getByRole('button', {name:'Continua'}).click();
  await page.locator('#cc-desk-sidebar').waitFor({timeout:30000});
}

async function run() {
  const browser = await chromium.launch({headless:true,args:[
    '--host-resolver-rules=MAP centrochange.local 127.0.0.1',
    '--no-proxy-server','--disable-dev-shm-usage']});
  const rows = [];
  try {
    for (const width of [1440,390]) for (const role of ['m','f']) {
      const context = await browser.newContext({viewport:{width,height:900},locale:'it-IT',
        timezoneId:'Europe/Rome',serviceWorkers:'block'});
      const page = await context.newPage();
      const errors=[];
      page.on('pageerror', e=>errors.push(e.message));
      try {
        await login(page, users[role]);
        if (role==='m') {
          await page.locator('.calendar-shell').waitFor({state:'visible'});
          const agenda = await page.evaluate(() => ({
            heading:document.querySelector('.calendar-shell')?.getBoundingClientRect().width,
            days:document.querySelectorAll('.calendar-shell [data-date]').length,
            active:[...document.querySelectorAll('#cc-desk-sidebar a.active')].map(x=>x.textContent.trim())}));
          assert.deepEqual(agenda.active,['Agenda']);
          await page.screenshot({path:path.join(output,`agenda-${width}.png`),fullPage:true,animations:'disabled'});
          rows.push({route:'agenda',role,width,status:'PASS',agenda});
        }
        for (const [route,owner] of routes.filter(([,owner])=>owner===role)) {
          try {
          await page.goto(base+'/app/'+route, {waitUntil:'domcontentloaded'});
          await page.locator('.list-row .list-subject a').first().waitFor({timeout:20000});
          await page.locator('.list-row .list-subject a').first().click();
          await page.waitForFunction(() => window.cur_frm?.doc?.name &&
            document.querySelector('.form-layout'),null,{timeout:20000});
          const data=await page.evaluate(() => {
            const f=window.cur_frm;
            const help=document.querySelector('.cc-native-help');
            const context=document.querySelector('.cc-finance-context');
            const inputs=[...document.querySelectorAll('.form-layout input:not([type=hidden]),.form-layout select,.form-layout textarea')];
            const required=[...document.querySelectorAll('.form-layout .reqd')];
            return {doctype:f.doctype,docstatus:f.doc.docstatus||0,help:help?.innerText||context?.innerText||'',
              editable:inputs.filter(x=>!x.disabled&&!x.readOnly).length,
              required:required.length,hasSave:!!document.querySelector('.page-actions .btn-primary'),
              native:!!document.querySelector('.form-layout'),
              body:document.body.className,overflow:document.documentElement.scrollWidth-innerWidth};
          });
          assert(data.native && (data.editable>0 || data.docstatus!==0),
            `${route}: draft has no native editable fields`);
          assert(data.help.includes('Come compilare'),`${route}: field guidance absent`);
          assert(data.body.includes('cc-native-view'),`${route}: not native client route`);
          assert(data.overflow<=2,`${route}: horizontal overflow ${data.overflow}`);
          await page.screenshot({path:path.join(output,`${route}-${role}-${width}.png`),
            fullPage:true,animations:'disabled'});
          rows.push({route,role,width,status:'PASS',...data});
          } catch(e) {
            rows.push({route,role,width,status:'FAIL',reason:String(e.message).slice(0,320)});
          }
        }
        assert.equal(errors.length,0,`JS errors ${role}/${width}: ${errors.join('; ')}`);
      } catch(e) {
        rows.push({route:'session',role,width,status:'FAIL',reason:String(e.message).slice(0,320)});
      } finally {await context.close();}
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(output,'issue75-native-ux.json'),JSON.stringify(rows,null,2));
  const status=rows.some(x=>x.status!=='PASS')?'FAIL':'PASS';
  console.log(JSON.stringify({status,passed:rows.filter(x=>x.status==='PASS').length,total:rows.length}));
  if(status!=='PASS') process.exitCode=1;
}
run().catch(e=>{console.error(e.stack);process.exitCode=1});
