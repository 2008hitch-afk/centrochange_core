/* Read-only browser proof for the client demo presentation delta. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const base = process.env.CC_BASE_URL || 'http://centrochange.local:8082';
const fixture = JSON.parse(fs.readFileSync(process.env.CC_DEMO_FIXTURE, 'utf8'));
const users = (fixture.fixture || fixture).users;
const output = process.env.CC_DEMO_OUTPUT;
assert(output && users?.m && users?.f, 'private fixture/output required');
fs.mkdirSync(output, {recursive:true, mode:0o700});

async function login(page, user) {
  await page.goto(base + '/login', {waitUntil:'domcontentloaded'});
  await page.locator('#login_email').fill(user.name);
  await page.locator('#login_password').fill(user.password);
  await page.getByRole('button', {name:'Continua'}).click();
  await page.locator('#cc-desk-sidebar').waitFor({timeout:30000});
}

async function check() {
  const browser = await chromium.launch({headless:true,args:[
    '--host-resolver-rules=MAP centrochange.local 127.0.0.1',
    '--no-proxy-server', '--disable-dev-shm-usage'
  ]});
  const results = [];
  try {
    for (const [role,width] of [['m',1440],['m',390],['f',1440]]) {
      const context = await browser.newContext({viewport:{width,height:900},locale:'it-IT',timezoneId:'Europe/Rome',serviceWorkers:'block'});
      const page = await context.newPage();
      const errors=[];
      page.on('pageerror',error=>errors.push(error.message));
      try {
        await login(page, users[role]);
        const landing = await page.evaluate(() => ({route:location.pathname+location.search,
          active:[...document.querySelectorAll('#cc-desk-sidebar a.active')].map(a=>a.textContent.trim())}));
        const expected = role==='m'?'agenda':'finance';
        assert(landing.route.includes(`cc_view=${expected}`),`${role} landing: ${landing.route}`);
        assert.equal(landing.active.length,1,`${role} landing has ${landing.active.join(', ')}`);
        if (role==='m') {
          assert.deepEqual(landing.active,['Agenda']);
          if (width===390) {
            const hint=page.locator('.cc-calendar-mobile-hint');
            await hint.waitFor({state:'visible'});
            const geometry=await page.locator('.calendar-shell').evaluate(el=>({before:el.scrollLeft,
              overflow:el.scrollWidth>el.clientWidth,after:(el.scrollLeft=el.scrollWidth,el.scrollLeft)}));
            assert(geometry.overflow && geometry.after>geometry.before,'mobile calendar cannot scroll to later days');
          }
          if (width===390) await page.locator('.cc-mobile-toggle').click();
          await page.locator('#cc-desk-sidebar a[href="/app/sales-invoice"]').click();
          await page.waitForURL(url=>new URL(url).pathname==='/app/sales-invoice',{timeout:20000});
          await page.locator('.list-row-container').first().waitFor({timeout:20000});
          const list=await page.evaluate(()=>({active:[...document.querySelectorAll('#cc-desk-sidebar a.active')].map(a=>a.textContent.trim()),
            text:document.querySelector('.listview-body')?.innerText||''}));
          assert.deepEqual(list.active,['Fatture pazienti']);
          assert(!list.text.includes('CC-MVP-POS-'),'raw POS fixture subject dominates invoice list');
          assert(list.text.includes('Paziente dimostrativo POS'),'readable POS demo subject absent');
        }
        assert.equal(errors.length,0,`JavaScript errors: ${errors.join('; ')}`);
        await page.screenshot({path:path.join(output,`client-demo-${role}-${width}.png`),fullPage:true,animations:'disabled'});
        results.push({role,width,status:'PASS',landing:landing.route});
      } catch(error) {
        results.push({role,width,status:'FAIL',reason:String(error.message).slice(0,240)});
      } finally {await context.close();}
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(output,'client-demo-readiness.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify({status:results.every(row=>row.status==='PASS')?'PASS':'FAIL',results}));
  if(results.some(row=>row.status!=='PASS')) process.exitCode=1;
}
check().catch(error=>{console.error(error.stack);process.exitCode=1});
