// Read-only Chromium checks on the served single-stack DEV. No request mocking.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

const base = process.env.CC_BASE_URL || 'http://centrochange.local:8082';
const fixture = JSON.parse(fs.readFileSync(process.env.CC_ISSUE79_FIXTURE, 'utf8'));
const users = (fixture.fixture || fixture).users;
const output = process.env.CC_GOAL02_OUTPUT;
if (!output || !users) throw Error('Private fixture and output directory required');

async function login(page, user) {
  await page.goto(base + '/login');
  await page.locator('#login_email').fill(user.name);
  await page.locator('#login_password').fill(user.password);
  await page.getByRole('button', {name:'Continua'}).click();
  await page.waitForURL(/\/app\//);
}

async function open(page, suffix) {
  await page.goto(base + suffix, {waitUntil:'domcontentloaded'});
  await page.locator('#cc-main').waitFor({timeout:20000});
  return page.locator('#cc-main').innerText();
}

async function principal(browser, role, viewport) {
  const context = await browser.newContext({viewport,locale:'it-IT',serviceWorkers:'block'});
  const page = await context.newPage();
  const errors = [], writes = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', req => {if (!['GET','HEAD'].includes(req.method()) && !/\/api\/method\/login/.test(req.url())) writes.push(req.url());});
  try {
    await login(page,users[role]);
    const agenda = ['m','s','a','b','c'].includes(role);
    const landing = agenda ? '/app/cc-unified-desk?cc_view=agenda' : '/app/cc-unified-desk?cc_view=finance';
    const landingText = await open(page,landing);
    assert.match(landingText, agenda ? /Agenda/ : /Finanza/);
    if (role === 'c') {
      assert.match(landingText,/Nessun professionista assegnato/);
      assert.equal(await page.locator('#new-booking').isVisible(),false);
    }
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),true,'horizontal overflow');
    if (role === 'm' && viewport.width === 1440) {
      await page.screenshot({path:path.join(output,'goal02-manager-agenda.png'),fullPage:true});
      const notices = await open(page,'/app/cc-unified-desk?cc_view=agenda&cc_ops_view=Notifiche');
      assert.match(notices,/Notifiche/);
      await page.screenshot({path:path.join(output,'goal02-manager-notifications.png'),fullPage:true});
      const audit = await open(page,'/app/cc-unified-desk?cc_view=audit');
      assert.match(audit,/Registro|modifiche/i);
      await page.screenshot({path:path.join(output,'goal02-manager-audit.png'),fullPage:true});
      const finance = await open(page,'/app/cc-unified-desk?cc_view=finance');
      assert.match(finance,/Finanza/);
      await page.screenshot({path:path.join(output,'goal02-manager-finance.png'),fullPage:true});
      const ts = await open(page,'/app/cc-unified-desk?cc_view=finance&cc_fin_view=TS');
      assert.match(ts,/TS|Tessera/i);
      await page.screenshot({path:path.join(output,'goal02-manager-ts.png'),fullPage:true});
    }
    if (role === 'f') {
      const finance = await open(page,'/app/cc-unified-desk?cc_view=finance');
      assert.match(finance,/Finanza/);
      if (viewport.width === 1440) {
        const comparison = page.getByRole('button',{name:'Confronta fattura professionista'});
        await comparison.waitFor();
        await comparison.click();
        await page.locator('#compare-compensation').waitFor();
        await page.locator('#compare-compensation').click();
        await page.getByRole('heading',{name:'Confronta atteso e ricevuto'}).waitFor();
        assert.equal(await page.locator('#modal [name=expectations]').count(),1);
        await page.screenshot({path:path.join(output,'goal02-finance-comparison.png'),fullPage:true});
      }
    }
    if (role === 't') {
      assert.equal(await page.getByRole('button',{name:'Confronta fattura professionista'}).count(),0);
    }
    assert.deepEqual(errors,[],role+' JavaScript errors');
    assert.deepEqual(writes,[],role+' unexpected writes');
    return {role,width:viewport.width,landing:agenda?'agenda':'finance',checks:'PASS',page_errors:0,writes:0};
  } finally {await context.close();}
}

async function administrator(browser) {
  const credentials = JSON.parse(fs.readFileSync(process.env.CC_GOAL02_ADMIN_FIXTURE,'utf8'));
  const context = await browser.newContext({locale:'it-IT',serviceWorkers:'block'});
  const page = await context.newPage();
  const errors=[];page.on('pageerror', e=>errors.push(e.message));
  try {
    await login(page,credentials);
    await page.goto(base+'/app', {waitUntil:'domcontentloaded'});
    await page.locator('body').waitFor();
    assert(!/Accesso non autorizzato/.test(await page.locator('body').innerText()));
    assert.deepEqual(errors,[]);
    return {role:'Administrator',checks:'PASS',page_errors:0};
  } finally {await context.close();}
}

(async()=>{
  const browser = await chromium.launch({headless:true,args:['--host-resolver-rules=MAP centrochange.local 127.0.0.1','--no-proxy-server']});
  const results=[];
  try {
    for (const role of ['m','s','a','b','c','f','t']) results.push(await principal(browser,role,{width:1440,height:900}));
    for (const role of ['m','f']) results.push(await principal(browser,role,{width:390,height:844}));
    results.push(await administrator(browser));
    console.log(JSON.stringify({status:'PASS',runtime:'live',roles:results,mutations:'NONE'}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error.stack);process.exitCode=1});
