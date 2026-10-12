// R10 candidate presentation check. Run only inside the isolated C109 QA
// container, with a synthetic fixture and a fresh browser process per role.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const demo = JSON.parse(fs.readFileSync('/qa-fixture.json', 'utf8'));
const fixture = demo.fixture;
const base = process.env.C109_QA_BASE || 'http://centrochange.local:8080';
if (!/^http:\/\/centrochange\.local:8080\/?$/.test(base)) throw new Error('C109 QA target only');
const args = ['--host-resolver-rules=MAP centrochange.local 127.0.0.1',
  '--no-proxy-server', '--no-first-run', '--disable-background-networking',
  '--disable-component-update', '--disable-default-apps', '--disable-sync',
  '--disable-extensions', '--disk-cache-size=0', '--media-cache-size=0'];

async function session(role, route, check) {
  const account = fixture.users[role];
  assert(account?.name && account?.password, `missing synthetic ${role} account`);
  const browser = await chromium.launch({headless:true, args});
  try {
    const context = await browser.newContext({viewport:{width:1440,height:900},
      locale:'it-IT', timezoneId:'Europe/Rome'});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${base}/login?redirect-to=${encodeURIComponent(route)}`);
    await page.locator('#login_email').fill(account.name);
    await page.locator('#login_password').fill(account.password);
    await page.locator('.form-login button[type="submit"]').click();
    await page.locator('#cc-desk-global-nav').waitFor({timeout:60000});
    await check(page);
    assert.deepEqual(errors, [], `${role}: JavaScript errors`);
    await context.close();
  } finally { await browser.close(); }
}

(async () => {
  const results = [];
  await session('m', '/app/patient', async page => {
    assert.match(await page.title(), /Pazienti · Centro Change/);
    await page.goto(`${base}/app/patient/${encodeURIComponent(fixture.patients[0])}`);
    await page.locator('.form-page').waitFor({timeout:60000});
    const labels = await page.locator('.form-page').innerText();
    assert.match(labels, /Dati del paziente/);
    assert.match(labels, /Secondo nome \(facoltativo\)/);
    assert.doesNotMatch(labels, /Patient Demographics|Middle Name \(optional\)|Medical History/);
    assert(await page.locator('#cc-desk-global-nav').isVisible());
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({path:'/qa-results/r10-native-patient-mobile.png',fullPage:false});
    results.push('manager_patient_form_italian_mobile');
  });
  await session('f', '/app/sales-invoice', async page => {
    await page.locator('.page-head').waitFor({timeout:60000});
    assert.match(await page.title(), /Fatture pazienti · Centro Change/);
    assert(await page.locator('#cc-desk-global-nav').isVisible());
    await page.goto(`${base}/app/sales-invoice/${encodeURIComponent(demo.invoices['Alfa bozza'])}`);
    await page.locator('.form-page').waitFor({timeout:60000});
    const labels = await page.locator('.form-page').innerText();
    assert.match(labels, /Profilo fiscale di prova|Data contabile/);
    assert.doesNotMatch(labels, /Request Fingerprint|Idempotency Key|DEV Fiscal Profile/);
    // The fields remain in the canonical ERPNext document and API. Only the
    // customer-facing form omits these implementation details.
    for (const field of ['cc_request_hash', 'cc_request_key']) {
      const control = page.locator(`.frappe-control[data-fieldname="${field}"]`);
      if (await control.count()) assert.equal(await control.isVisible(), false);
    }
    results.push('finance_invoice_list_native_navigation');
  });
  await session('s', '/app/cc-unified-desk?cc_view=home', async page => {
    const links = await page.locator('#cc-desk-global-nav').innerText();
    assert.match(links, /Agenda/);
    assert.doesNotMatch(links, /Builder|Frappe|ERPNext/);
    results.push('secretariat_client_navigation');
  });
  console.log(JSON.stringify({status:'PASS', checks:results}));
})().catch(error => {console.error(error.stack || error.message);process.exit(1);});
