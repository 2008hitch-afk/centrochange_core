// Six-section regression after the issue #75 navigation update. No credentials in output.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');

const fixture = JSON.parse(fs.readFileSync('/qa-fixture.json', 'utf8')).fixture;
const account = fixture.users.m;
const base = 'http://centrochange.local:8080';
const center = encodeURIComponent(fixture.centers[0]);
const practitioner = encodeURIComponent(fixture.practitioners[0]);
const pages = [
  ['home', '/app/cc-unified-desk?cc_view=home'],
  ['agenda', `/app/cc-unified-desk?cc_view=agenda&center=${center}&date=2026-09-28`],
  ['pazienti', '/app/patient'],
  ['professionisti', '/app/healthcare-practitioner'],
  ['finanza', `/app/cc-unified-desk?cc_view=finance&center=${center}&start=2026-09-28&end=2026-10-31`],
  ['report', `/app/cc-unified-desk?cc_view=professional&center=${center}&practitioner=${practitioner}&start=2026-09-28&end=2026-10-31`],
];

(async () => {
  const browser = await chromium.launch({headless: true, args: [
    '--host-resolver-rules=MAP centrochange.local 127.0.0.1', '--no-proxy-server',
    '--no-first-run', '--disable-background-networking', '--disable-extensions',
  ]});
  try {
    const context = await browser.newContext({viewport: {width: 1440, height: 900}, locale: 'it-IT'});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${base}/login?redirect-to=${encodeURIComponent(pages[0][1])}`);
    await page.locator('#login_email').fill(account.name);
    await page.locator('#login_password').fill(account.password);
    await page.locator('.form-login button[type="submit"]').click();
    await page.locator('#cc-desk-sidebar').waitFor({timeout: 90000});
    const checks = [];
    for (const [name, route] of pages) {
      await page.goto(base + route);
      await page.locator('#cc-desk-sidebar').waitFor({timeout: 60000});
      if (name === 'finanza') {
        await page.locator('#center').selectOption(fixture.centers[0]);
        await page.waitForFunction(() => document.querySelector('#finance-content')?.innerText.includes('100,00'), null, {timeout: 30000});
      }
      await page.waitForTimeout(1500);
      const body = await page.locator('body').innerText();
      assert(body.length > 200, `${name}: blank page`);
      assert(!/not permitted|access denied|non autorizzato|internal server error/i.test(body.slice(0, 1200)), `${name}: access error`);
      assert(!await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), `${name}: horizontal overflow`);
      await page.screenshot({path: `/qa-results/issue75-six-${name}.png`, fullPage: false});
      checks.push({section: name, url: new URL(page.url()).pathname + new URL(page.url()).search,
        title: await page.title(), visible_chars: body.length, data_visible: /Alfa|Beta|Theta|Centro Change/.test(body)});
    }
    assert.deepEqual(errors, [], 'JavaScript page errors');
    console.log(JSON.stringify({status: 'PASS', sections: checks, page_errors: errors}));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.stack || error.message); process.exit(1); });
