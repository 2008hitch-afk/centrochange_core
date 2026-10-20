/* Read-only client localization inventory. Never submits a form. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const base = process.env.CC_BASE_URL || 'http://centrochange.local:8082';
const fixture = JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE, 'utf8'));
const users = (fixture.fixture || fixture).users;
const output = process.env.CC_LOCALE_OUTPUT;
assert(output && users?.m && users?.f, 'private fixture and output required');
fs.mkdirSync(output, {recursive:true, mode:0o700});
const routes = [
  ['patient','m'],['healthcare-practitioner','m'],['item','m'],['item-price','m'],
  ['appointment-type','m'],['cc-center-service','m'],['cc-package-template','m'],
  ['sales-invoice','m'],['purchase-invoice','f'],['payment-entry','f'],['bank-transaction','f']
];
const english = /\b(?:Occupation|Marital Status|Appointments and Encounters|Billing and Payments|Annual Billing|Total Unpaid|Charges|Free Followup Details|Address and Contacts|Internal|Immutable Incoming Source|Write your message|Get Items From|Save|Submit|Cancel|New|Search|No results|Required|Mandatory)\b/i;

async function login(page, user) {
  await page.goto(base+'/login', {waitUntil:'domcontentloaded'});
  await page.locator('#login_email').fill(user.name);
  await page.locator('#login_password').fill(user.password);
  await page.getByRole('button', {name:'Continua'}).click();
  await page.locator('#cc-desk-sidebar').waitFor({timeout:30000});
}

async function main() {
  const browser = await chromium.launch({headless:true,args:[
    '--host-resolver-rules=MAP centrochange.local 127.0.0.1',
    '--no-proxy-server','--disable-dev-shm-usage']});
  const rows=[];
  try {
    for (const width of [1440,390]) for (const role of ['m','f']) {
      const context=await browser.newContext({viewport:{width,height:900},locale:'it-IT',timezoneId:'Europe/Rome',serviceWorkers:'block'});
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      try {
        await login(page,users[role]);
        for (const [route,owner] of routes.filter(([,owner])=>owner===role)) {
          try {
            await page.goto(base+'/app/'+route,{waitUntil:'domcontentloaded'});
            await page.locator('.list-row .list-subject a').first().waitFor({timeout:20000});
            await page.locator('.list-row .list-subject a').first().click();
            await page.waitForFunction(()=>window.cur_frm?.doc?.name && document.querySelector('.form-layout'),null,{timeout:20000});
            const labels=await page.evaluate(()=>[...document.querySelectorAll('.form-layout .control-label,.form-layout .section-head,.form-layout .nav-link,.form-layout .form-tabs .nav-link,.form-layout [placeholder],.form-layout .grid-heading-row,.form-layout .btn')]
              .map(el=>el.getAttribute('placeholder')||el.innerText||'').map(s=>s.trim()).filter(Boolean));
            const unique=[...new Set(labels)];
            const matches=unique.filter(x=>english.test(x));
            await page.screenshot({path:path.join(output,`${route}-${role}-${width}.png`),fullPage:true,animations:'disabled'});
            rows.push({route,role,width,status:'PASS',matches,labels:unique});
          } catch(e) {rows.push({route,role,width,status:'FAIL',reason:String(e.message).slice(0,240)});}
        }
      } catch(e) {rows.push({route:'session',role,width,status:'FAIL',reason:String(e.message).slice(0,240)});}
      rows.push({route:'javascript',role,width,status:errors.length?'FAIL':'PASS',errors:errors.slice(0,10)});
      await context.close();
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(output,'locale-sweep.json'),JSON.stringify(rows,null,2));
  const fails=rows.filter(x=>x.status==='FAIL');
  console.log(JSON.stringify({forms:rows.filter(x=>x.labels).length,failures:fails.length,matches:rows.flatMap(x=>x.matches||[]).length}));
  if(fails.length)process.exitCode=1;
}
main().catch(e=>{console.error(e.stack);process.exitCode=1});
